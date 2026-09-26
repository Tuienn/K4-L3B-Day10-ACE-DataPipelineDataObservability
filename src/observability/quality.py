from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any

import great_expectations as gx
import great_expectations.expectations as gxe
import pandas as pd

from core.config import Settings

logger = logging.getLogger(__name__)


def evaluate_freshness_sla(df: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    """Kiểm tra độ tươi mới của dữ liệu (Freshness SLA):
    Cảnh báo is_fresh = False nếu tỷ lệ bài báo có age_days > settings.freshness_threshold_days vượt quá 25%.
    """
    total_rows = len(df)
    if total_rows == 0:
        return {
            "total_rows": 0,
            "stale_rows": 0,
            "stale_ratio": 0.0,
            "threshold_days": settings.freshness_threshold_days,
            "max_stale_ratio": 0.25,
            "is_fresh": False,
            "latest_published": "",
            "oldest_published": "",
        }

    threshold_days = settings.freshness_threshold_days
    if "age_days" in df.columns:
        stale_rows = int((df["age_days"] > threshold_days).sum())
    else:
        stale_rows = 0

    stale_ratio = stale_rows / total_rows
    is_fresh = bool(stale_ratio <= 0.25)

    latest_published = ""
    oldest_published = ""
    if "published" in df.columns:
        valid_dates = df["published"].dropna().astype(str).loc[lambda s: s.str.strip() != ""]
        if not valid_dates.empty:
            latest_published = str(valid_dates.max())
            oldest_published = str(valid_dates.min())

    return {
        "total_rows": total_rows,
        "stale_rows": stale_rows,
        "stale_ratio": round(stale_ratio, 4),
        "threshold_days": threshold_days,
        "max_stale_ratio": 0.25,
        "is_fresh": is_fresh,
        "latest_published": latest_published,
        "oldest_published": oldest_published,
    }


def build_freshness_report(
    df: pd.DataFrame,
    settings: Settings,
    report_path: Path | str | None = None,
) -> dict[str, Any]:
    """Tổng hợp freshness report và lưu ra file JSON."""
    if report_path is None:
        target_path = settings.paths.freshness_report
    else:
        target_path = Path(report_path)

    report = evaluate_freshness_sla(df, settings)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report


def run_data_quality_checks(
    df: pd.DataFrame,
    settings: Settings,
    report_name: str,
) -> dict[str, Any]:
    """Chốt kiểm định chất lượng dữ liệu sử dụng Great Expectations 1.x Ephemeral Context.

    4 Hàng Rào Kiểm Định (Expectations) Bắt Buộc:
    1. ExpectTableRowCountToBeBetween: 5 đến 5000 dòng.
    2. ExpectColumnValuesToNotBeNull: paper_id, title, text_for_embedding không được null.
    3. ExpectColumnValuesToBeUnique: paper_id là duy nhất.
    4. ExpectColumnValueLengthsToBeBetween: summary có độ dài tối thiểu 30 ký tự.

    Giám Sát Độ Tươi Mới (Freshness SLA):
    - Đánh giá tỷ lệ bài báo cũ qua evaluate_freshness_sla().
    - Trả về dict kết quả chứa {"success": bool, ...}.
    """
    # 1. Cấu hình Ephemeral Context trên GX 1.x
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    # 2. Thiết lập 4 Expectations bắt buộc
    suite = gx.ExpectationSuite(name=f"papers_quality_suite_{report_name}")
    suite.add_expectation(gxe.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="paper_id"))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="title"))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="text_for_embedding"))
    suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="paper_id"))
    suite.add_expectation(gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30))

    # 3. Thực thi validation qua Batch
    validation_results = batch.validate(suite)
    gx_success = bool(validation_results.success)

    # 4. Kiểm tra Freshness SLA
    freshness = evaluate_freshness_sla(df, settings)
    overall_success = bool(gx_success and freshness["is_fresh"])

    # 5. Xác định đường dẫn file báo cáo
    if report_name == "baseline":
        report_path = settings.paths.baseline_quality_report
    elif report_name == "corrupted":
        report_path = settings.paths.corrupted_quality_report
    else:
        report_path = settings.paths.quality_dir / f"{report_name}_quality_report.json"

    result_payload: dict[str, Any] = {
        "report_name": report_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": overall_success,
        "gx_success": gx_success,
        "is_fresh": freshness["is_fresh"],
        "total_rows": len(df),
        "freshness": freshness,
        "statistics": {
            "evaluated_expectations": len(validation_results.results),
            "successful_expectations": sum(1 for r in validation_results.results if r.success),
            "unsuccessful_expectations": sum(1 for r in validation_results.results if not r.success),
            "success_percent": round(
                100 * sum(1 for r in validation_results.results if r.success) / max(1, len(validation_results.results)),
                2,
            ),
        },
        "validation_results": validation_results.to_json_dict(),
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result_payload, f, ensure_ascii=False, indent=2)

    return result_payload

