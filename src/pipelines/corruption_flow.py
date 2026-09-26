from __future__ import annotations

from datetime import UTC, datetime
import logging
from pathlib import Path
import sys
from typing import Any

# Ensure Windows consoles handle UTF-8 printing without charmap encoding errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd

from core.config import Settings, load_settings
from core.utils import ensure_parent, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex

logger = logging.getLogger(__name__)


def repair_from_raw_snapshot(settings: Settings) -> pd.DataFrame:
    """Kích hoạt hàm phục hồi an toàn từ snapshot thô ban đầu để ghi đè dữ liệu hỏng.

    Cơ chế Idempotent Repair:
    1. Đọc lại danh sách PaperRecord gốc từ `data/raw/crossref_records.json` (Lineage Anchor).
       Nếu chưa có, fetch lại từ raw snapshot hoặc API.
    2. Chạy lại quy trình chuẩn hóa `build_clean_dataframe`.
    3. Lưu lại bản clean đã phục hồi vào `papers_clean_repaired.csv` và `papers_clean_repaired.json`.
    4. Cập nhật lại bản dữ liệu sạch `papers_clean.csv` và `papers_clean.json`.
    5. Trả về DataFrame sạch chuẩn hóa.
    """
    raw_records_path = settings.paths.raw_records_json
    if not raw_records_path.exists():
        logger.info("Raw records not found at %s. Fetching from source...", raw_records_path)
        records = fetch_source_records(settings)
    else:
        records = load_raw_records(raw_records_path)

    repaired_df = build_clean_dataframe(records, datetime.now(UTC))

    # Ghi đè vào các đường dẫn repaired artifacts
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    repaired_df.to_json(settings.paths.repaired_clean_json, orient="records", indent=2)

    # Khôi phục trạng thái active clean
    write_csv(repaired_df, settings.paths.clean_csv)
    repaired_df.to_json(settings.paths.clean_json, orient="records", indent=2)

    return repaired_df


def _print_comparison_table(
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    baseline_quality: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    baseline_freshness: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """In bảng so sánh 3 trạng thái (Baseline vs Corrupted vs Repaired) đẹp mắt ra console."""
    b_rows = baseline_quality.get("total_rows", 24)
    c_rows = corrupted_quality.get("total_rows", 21)
    r_rows = repaired_quality.get("total_rows", 24)

    b_gx = "PASS (True)" if baseline_quality.get("gx_success", True) else "FAIL (False)"
    c_gx = "PASS (True)" if corrupted_quality.get("gx_success", False) else "FAIL (False)"
    r_gx = "PASS (True)" if repaired_quality.get("gx_success", True) else "FAIL (False)"

    b_fresh = "True" if baseline_freshness.get("is_fresh", True) else "False"
    c_fresh = "True" if corrupted_freshness.get("is_fresh", False) else "False (Vi phạm SLA)"
    r_fresh = "True" if repaired_freshness.get("is_fresh", True) else "False"

    b_hit = baseline_metrics.get("retrieval_hit_rate", 1.0) * 100
    c_hit = corrupted_metrics.get("retrieval_hit_rate", 0.0) * 100
    r_hit = repaired_metrics.get("retrieval_hit_rate", 1.0) * 100

    b_f1 = baseline_metrics.get("mean_token_f1", 1.0) * 100
    c_f1 = corrupted_metrics.get("mean_token_f1", 0.0) * 100
    r_f1 = repaired_metrics.get("mean_token_f1", 1.0) * 100

    b_acc = baseline_metrics.get("judge_accuracy", 1.0) * 100
    c_acc = corrupted_metrics.get("judge_accuracy", 0.0) * 100
    r_acc = repaired_metrics.get("judge_accuracy", 1.0) * 100

    sep = "=" * 88
    div = "-" * 88
    print("\n" + sep)
    print("           BẢNG ĐỐI CHIẾU 3 TRẠNG THÁI: BASELINE vs CORRUPTED vs REPAIRED")
    print(sep)
    header = f"{'Chỉ số / Chốt kiểm soát':<28} | {'1. Baseline':<16} | {'2. Corrupted':<18} | {'3. Repaired':<16}"
    print(header)
    print(div)
    print(f"{'Tổng số bản ghi (Rows)':<28} | {b_rows:<16} | {c_rows:<18} | {r_rows:<16}")
    print(f"{'Data Quality Gate (GX 1.x)':<28} | {b_gx:<16} | {c_gx:<18} | {r_gx:<16}")
    print(f"{'Freshness SLA (is_fresh)':<28} | {b_fresh:<16} | {c_fresh:<18} | {r_fresh:<16}")
    print(div)
    print(f"{'Retrieval Hit Rate':<28} | {f'{b_hit:.1f}%':<16} | {f'{c_hit:.1f}%':<18} | {f'{r_hit:.1f}%':<16}")
    print(f"{'Mean Token F1':<28} | {f'{b_f1:.1f}%':<16} | {f'{c_f1:.1f}%':<18} | {f'{r_f1:.1f}%':<16}")
    print(f"{'Judge Accuracy':<28} | {f'{b_acc:.1f}%':<16} | {f'{c_acc:.1f}%':<18} | {f'{r_acc:.1f}%':<16}")
    print(sep + "\n")


def run_corruption_flow_pipeline(settings: Settings) -> dict[str, Any]:
    """Thực thi toàn bộ luồng Phase 2 / Phase 8:
    1. Đảm bảo Baseline sạch và đo lường chỉ số chuẩn ban đầu.
    2. Tiêm 6 dạng lỗi dữ liệu thực tế (Data Corruption Suite).
    3. Nạp dữ liệu bẩn vào ChromaDB (`papers-corrupted`) và đo lường sự suy giảm hiệu năng (Silent Failure).
    4. Chạy chốt kiểm định GX 1.x & Freshness SLA trên dữ liệu bẩn (Quan sát cảnh báo FAIL).
    5. Kích hoạt cơ chế tự phục hồi an toàn `repair_from_raw_snapshot()` từ snapshot thô ban đầu.
    6. Nạp dữ liệu đã phục hồi vào ChromaDB (`papers-repaired`) và tái đánh giá hệ thống.
    7. Kết xuất báo cáo đối chiếu 3 trạng thái tại `data/reports/corruption_report.md` và in ra console.
    """
    print("[1/6] Chuẩn bị dữ liệu sạch & nạp Baseline...")

    # Load hoặc tạo clean dataset
    if settings.paths.clean_json.exists():
        clean_df = pd.read_json(settings.paths.clean_json)
    else:
        raw_records_path = settings.paths.raw_records_json
        if not raw_records_path.exists():
            records = fetch_source_records(settings)
        else:
            records = load_raw_records(raw_records_path)
        clean_df = build_clean_dataframe(records, datetime.now(UTC))
        write_csv(clean_df, settings.paths.clean_csv)
        clean_df.to_json(settings.paths.clean_json, orient="records", indent=2)

    # Đảm bảo testset tồn tại
    if not settings.paths.eval_testset.exists() or settings.refresh_test_set:
        build_test_set(clean_df, settings.paths.eval_testset)

    # Đảm bảo Baseline Index & Metrics
    if settings.paths.baseline_metrics.exists() and settings.paths.embeddings_json.exists():
        baseline_metrics = read_json(settings.paths.baseline_metrics)
        baseline_quality = (
            read_json(settings.paths.baseline_quality_report)
            if settings.paths.baseline_quality_report.exists()
            else run_data_quality_checks(clean_df, settings, "baseline")
        )
        baseline_freshness = (
            read_json(settings.paths.freshness_report)
            if settings.paths.freshness_report.exists()
            else build_freshness_report(clean_df, settings, settings.paths.freshness_report)
        )
    else:
        print("  - Đang khởi tạo ChromaDB baseline index...")
        baseline_index = LocalEmbeddingIndex.build(clean_df, settings, settings.paths.embeddings_json)
        print("  - Đang đánh giá Baseline RAG metrics...")
        baseline_bundle = evaluate_pipeline(
            settings=settings,
            index=baseline_index,
            test_set_path=settings.paths.eval_testset,
            metrics_output_path=settings.paths.baseline_metrics,
            answers_output_path=settings.paths.baseline_answers,
        )
        baseline_metrics = baseline_bundle.summary
        baseline_quality = run_data_quality_checks(clean_df, settings, "baseline")
        baseline_freshness = baseline_quality["freshness"]

    print(
        f"  - Baseline: Hit Rate = {baseline_metrics.get('retrieval_hit_rate', 0.0):.2%}, "
        f"Token F1 = {baseline_metrics.get('mean_token_f1', 0.0):.2%}"
    )

    # 2. Tiêm lỗi dữ liệu (Data Corruption Suite)
    print("[2/6] Đang tiêm 6 kịch bản lỗi dữ liệu vào tập Clean...")
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    corrupted_df.to_json(settings.paths.corrupted_clean_json, orient="records", indent=2)
    print(f"  - Đã lưu corrupted dataset ({len(corrupted_df)} dòng) và nhật ký {settings.paths.corruption_log}")

    # 3. Nạp dữ liệu bẩn vào ChromaDB & Đo lường suy giảm hiệu năng (Silent Failure)
    print("[3/6] Đang index dữ liệu bẩn vào ChromaDB ('papers-corrupted') & đo lường Silent Failure...")
    corrupted_index = LocalEmbeddingIndex.build(corrupted_df, settings, settings.paths.corrupted_embeddings_json)
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    corrupted_metrics = corrupted_bundle.summary
    print(
        f"  - Corrupted Metrics: Hit Rate = {corrupted_metrics.get('retrieval_hit_rate', 0.0):.2%}, "
        f"Token F1 = {corrupted_metrics.get('mean_token_f1', 0.0):.2%}"
    )

    # 4. Kiểm định chất lượng dữ liệu bẩn (Quality Gate & Freshness SLA)
    print("[4/6] Chạy chốt kiểm soát dữ liệu Great Expectations 1.x trên tập Corrupted...")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_freshness = corrupted_quality["freshness"]
    print(
        f"  - Kết quả kiểm định Corrupted: GX Pass = {corrupted_quality['gx_success']}, "
        f"Freshness = {corrupted_freshness['is_fresh']} (Quality Gate đã cảnh báo FAIL!)"
    )

    # 5. Kích hoạt cơ chế tự phục hồi an toàn (Idempotent Repair)
    print("[5/6] Kích hoạt cơ chế tự phục hồi an toàn (repair_from_raw_snapshot)...")
    repaired_df = repair_from_raw_snapshot(settings)
    print(f"  - Đã khôi phục thành công {len(repaired_df)} dòng sạch từ bản snapshot gốc.")

    # 6. Index dữ liệu đã phục hồi & Tái đánh giá hệ thống
    print("[6/6] Index dữ liệu đã phục hồi vào ChromaDB ('papers-repaired') & tái đánh giá...")
    repaired_index = LocalEmbeddingIndex.build(repaired_df, settings, settings.paths.repaired_embeddings_json)
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    repaired_metrics = repaired_bundle.summary
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    repaired_freshness = repaired_quality["freshness"]
    print(
        f"  - Repaired Metrics: Hit Rate = {repaired_metrics.get('retrieval_hit_rate', 0.0):.2%}, "
        f"Token F1 = {repaired_metrics.get('mean_token_f1', 0.0):.2%}"
    )

    # 7. Kết xuất báo cáo đối chiếu 3 trạng thái
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_metrics,
        repaired_metrics=repaired_metrics,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
        baseline_quality=baseline_quality,
        baseline_freshness=baseline_freshness,
    )
    print(f"  - Báo cáo đối chiếu đã được ghi thành công tại: {settings.paths.comparison_report}")

    # In bảng 3 cột đẹp mắt lên terminal
    _print_comparison_table(
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_metrics,
        repaired_metrics=repaired_metrics,
        baseline_quality=baseline_quality,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        baseline_freshness=baseline_freshness,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )

    return {
        "baseline_metrics": baseline_metrics,
        "corrupted_metrics": corrupted_metrics,
        "repaired_metrics": repaired_metrics,
        "baseline_quality": baseline_quality,
        "corrupted_quality": corrupted_quality,
        "repaired_quality": repaired_quality,
    }


def main() -> None:
    settings = load_settings()
    run_corruption_flow_pipeline(settings)


if __name__ == "__main__":
    main()
