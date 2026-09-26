from datetime import UTC, datetime
import logging
from pathlib import Path
from typing import Any

import great_expectations as gx
import great_expectations.expectations as gxe
import pandas as pd

from core.config import Settings
from core.utils import safe_slug, write_json

logger = logging.getLogger(__name__)

MAX_STALE_RATIO = 0.25


def evaluate_freshness_sla(df: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    """Kiểm tra độ tươi mới của dữ liệu (Freshness SLA):
    Cảnh báo is_fresh = False nếu tỷ lệ bài báo có age_days > settings.freshness_threshold_days vượt quá 25%.
    """
    total_rows = int(len(df))
    threshold_days = settings.freshness_threshold_days

    if total_rows == 0:
        return {
            "total_rows": 0,
            "stale_rows": 0,
            "stale_ratio": 0.0,
            "invalid_age_rows": 0,
            "threshold_days": threshold_days,
            "max_stale_ratio": MAX_STALE_RATIO,
            "is_fresh": False,
            "latest_published": None,
            "oldest_published": None,
        }

    if "age_days" in df.columns:
        age_days = pd.to_numeric(df["age_days"], errors="coerce")
        valid_age = age_days.notna() & age_days.ge(0)
        invalid_age_rows = int((~valid_age).sum())
        stale_rows = int((valid_age & age_days.gt(threshold_days)).sum())
    else:
        invalid_age_rows = total_rows
        stale_rows = 0

    stale_ratio = stale_rows / total_rows
    is_fresh = bool(
        invalid_age_rows == 0
        and stale_ratio <= MAX_STALE_RATIO
    )

    latest_published = None
    oldest_published = None
    if "published" in df.columns:
        valid_dates = pd.to_datetime(df["published"], errors="coerce", utc=True).dropna()
        if not valid_dates.empty:
            latest_published = valid_dates.max().date().isoformat()
            oldest_published = valid_dates.min().date().isoformat()

    return {
        "total_rows": total_rows,
        "stale_rows": stale_rows,
        "stale_ratio": round(stale_ratio, 4),
        "invalid_age_rows": invalid_age_rows,
        "threshold_days": threshold_days,
        "max_stale_ratio": MAX_STALE_RATIO,
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
    write_json(target_path, report)

    return report


def run_data_quality_checks(
    df: pd.DataFrame,
    settings: Settings,
    report_name: str,
) -> dict[str, Any]:
    """Chốt kiểm định chất lượng dữ liệu sử dụng Great Expectations 1.x Ephemeral Context.

    4 loại Expectation bắt buộc:
    1. ExpectTableRowCountToBeBetween: đúng số dòng cấu hình (24).
    2. ExpectColumnValuesToNotBeNull: paper_id, title, text_for_embedding không được null.
    3. ExpectColumnValuesToBeUnique: paper_id là duy nhất.
    4. ExpectColumnValueLengthsToBeBetween: summary có độ dài tối thiểu 30 ký tự.

    Giám Sát Độ Tươi Mới (Freshness SLA):
    - Đánh giá tỷ lệ bài báo cũ qua evaluate_freshness_sla().
    - Trả về dict kết quả chứa {"success": bool, ...}.
    """
    required_columns = {
        "paper_id",
        "title",
        "summary",
        "published",
        "age_days",
        "text_for_embedding",
    }
    missing_columns = sorted(required_columns.difference(df.columns))
    if missing_columns:
        raise ValueError(f"Missing columns required by the quality gate: {missing_columns}")

    safe_report_name = safe_slug(report_name)

    # 1. Cấu hình Ephemeral Context bằng Fluent API của GX 1.x.
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name=f"papers_{safe_report_name}_source")
    data_asset = data_source.add_dataframe_asset(name=f"papers_{safe_report_name}_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe(f"papers_{safe_report_name}_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    # 2. Thiết lập 4 loại Expectation bắt buộc. NotBeNull được áp dụng
    # cho ba cột, vì vậy validation có tổng cộng sáu expectation results.
    suite = context.suites.add(
        gx.ExpectationSuite(name=f"papers_quality_suite_{safe_report_name}")
    )
    suite.add_expectation(
        gxe.ExpectTableRowCountToBeBetween(
            min_value=settings.max_results,
            max_value=settings.max_results,
        )
    )
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="paper_id"))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="title"))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="text_for_embedding"))
    suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="paper_id"))
    suite.add_expectation(
        gxe.ExpectColumnValueLengthsToBeBetween(
            column="summary",
            min_value=30,
            max_value=20_000,
        )
    )

    # Ephemeral Context không giữ suite sau khi process kết thúc, nên lưu
    # cấu hình suite thành artifact để có bằng chứng nghiệm thu.
    suite_path = settings.paths.gx_dir / f"{safe_report_name}_suite.json"
    write_json(suite_path, suite.to_json_dict())

    # 3. Thực thi validation qua Batch
    validation_results = batch.validate(suite)
    gx_success = bool(validation_results.success)

    # 4. Kiểm tra Freshness SLA
    freshness_path = (
        settings.paths.freshness_report
        if report_name == "baseline"
        else settings.paths.quality_dir / f"{safe_report_name}_freshness_report.json"
    )
    freshness = build_freshness_report(df, settings, freshness_path)
    overall_success = bool(gx_success and freshness["is_fresh"])

    # 5. Xác định đường dẫn file báo cáo
    if report_name == "baseline":
        report_path = settings.paths.baseline_quality_report
    elif report_name == "corrupted":
        report_path = settings.paths.corrupted_quality_report
    else:
        report_path = settings.paths.quality_dir / f"{safe_report_name}_quality_report.json"

    validation_payload = validation_results.to_json_dict()

    result_payload: dict[str, Any] = {
        "report_name": report_name,
        "timestamp": datetime.now(UTC).isoformat(),
        "success": overall_success,
        "gx_success": gx_success,
        "is_fresh": freshness["is_fresh"],
        "total_rows": len(df),
        "suite_path": str(suite_path),
        "freshness_report_path": str(freshness_path),
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
        "validation_results": validation_payload,
    }

    write_json(report_path, result_payload)

    return result_payload

