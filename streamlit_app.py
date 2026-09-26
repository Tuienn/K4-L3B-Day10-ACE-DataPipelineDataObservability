from __future__ import annotations

import json
from pathlib import Path
import sys
from time import perf_counter

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from core.config import load_settings

st.set_page_config(page_title="PaperLab · RAG Demo", page_icon="📚", layout="wide")


def read_optional(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        st.warning(f"Không đọc được {path.name}: {exc}")
        return default


@st.cache_resource(show_spinner="Đang nạp MiniLM và chỉ mục ChromaDB…")
def load_index(manifest_version: int, database_version: int):
    from retrieval.index import LocalEmbeddingIndex

    return LocalEmbeddingIndex.load(load_settings())


def show_sources(result, documents):
    by_id = {doc["paper_id"]: doc for doc in documents}
    st.subheader("Tài liệu được truy xuất")
    for position, (paper_id, context) in enumerate(
        zip(result["retrieved_doc_ids"], result["retrieved_contexts"]), 1
    ):
        document = by_id.get(paper_id, {})
        metadata = document.get("metadata", {})
        with st.expander(f"{position}. {document.get('title', paper_id)}", expanded=position == 1):
            st.caption(f"DOI: {paper_id} · Xuất bản: {metadata.get('published', '—')}")
            st.write(context)
            url = metadata.get("abs_url", "")
            if url.startswith(("https://", "http://")):
                st.link_button("Mở bài báo", url)


def main():
    settings = load_settings()
    paths = settings.paths
    metrics = read_optional(paths.baseline_metrics, {})
    quality = read_optional(paths.baseline_quality_report, {})
    freshness = read_optional(paths.freshness_report, quality.get("freshness", {}))
    manifest = read_optional(paths.embeddings_json, {})
    documents = manifest.get("documents", [])
    answers = read_optional(paths.baseline_answers, [])
    papers = read_optional(paths.clean_json, [])

    st.markdown("""<style>
    .stApp {background: #f5f7fb;}
    .block-container {padding-top: 2.2rem; padding-bottom: 3rem;}
    [data-testid="stMetric"] {background: white; border: 1px solid #e3e8ef;
        border-radius: 14px; padding: 18px;}
    [data-testid="stMetricValue"] {color: #2157a5;}
    h1, h2, h3 {color: #15304f;}
    </style>""", unsafe_allow_html=True)

    with st.sidebar:
        st.title("📚 PaperLab")
        st.caption("Data Pipeline & Observability")
        st.divider()
        st.markdown("**Trạng thái: Baseline**")
        st.write("Crossref → Clean → ChromaDB → Evaluation → Quality Gate")
        if quality:
            if quality.get("success"):
                st.success("Quality Gate: PASS")
            else:
                st.error("Quality Gate: FAIL")
            st.caption(f"Lần kiểm định: {quality.get('timestamp', '—')}")
        else:
            st.info("Chưa có báo cáo chất lượng.")
        if st.button("↻ Đọc lại kết quả", use_container_width=True):
            st.session_state.pop("demo_result", None)
            load_index.clear()
            st.rerun()
        st.caption("Các chỉ số phản ánh lần chạy baseline được lưu.")

    st.title("Từ bài báo đến câu trả lời")
    st.write("Khám phá tài liệu nghiên cứu và theo dõi chất lượng dữ liệu của pipeline RAG.")
    columns = st.columns(4)
    columns[0].metric("Bài báo sạch", len(papers))
    columns[1].metric("Câu hỏi kiểm thử", metrics.get("samples", "—"))
    hit_rate = metrics.get("retrieval_hit_rate")
    token_f1 = metrics.get("mean_token_f1")
    columns[2].metric("Retrieval Hit Rate", f"{hit_rate:.0%}" if hit_rate is not None else "—")
    columns[3].metric("Token F1", f"{token_f1:.4f}" if token_f1 is not None else "—")
    st.write("")
    qa_tab, library_tab, quality_tab = st.tabs(["💬 Hỏi đáp", "📄 Kho bài báo", "🛡 Chất lượng dữ liệu"])

    with qa_tab:
        mode = st.radio("Chế độ demo", ["Xem kết quả baseline", "Hỏi đáp trực tiếp"], horizontal=True)
        if mode == "Xem kết quả baseline":
            st.caption("Xem câu trả lời và tài liệu nguồn từ lần đánh giá đã chạy; không thực hiện truy vấn mới.")
            if answers:
                selected = st.selectbox(
                    "Chọn câu hỏi mẫu", range(len(answers)),
                    format_func=lambda i: f"{i + 1:02d}. {answers[i]['question']}",
                )
                result = answers[selected]
                st.subheader("Câu trả lời")
                st.write(result["answer"] or "Tài liệu không có thông tin cho mục này.")
                st.caption(f"Retrieval hit: {'Có' if result['retrieval_hit'] else 'Không'} · Token F1: {result['token_f1']:.4f}")
                with st.expander("Đáp án tham chiếu"):
                    st.write(result["ground_truth"])
                show_sources(result, documents)
            else:
                st.info("Chưa có kết quả baseline. Chạy python script/run_phase1.py trước.")
        else:
            st.caption("Truy vấn chỉ mục ChromaDB hiện có và trả lời từ tài liệu được tìm thấy.")
            if not documents:
                st.info("Chưa có chỉ mục. Chạy python script/run_phase1.py trước.")
            else:
                selected_paper = st.selectbox(
                    "Chọn bài báo", range(len(documents)),
                    format_func=lambda i: documents[i]["title"],
                )
                question_type = st.selectbox("Bạn muốn hỏi gì?", ["Tóm tắt", "Tác giả", "Ngày xuất bản", "Lĩnh vực", "Câu hỏi tự nhập"])
                title = documents[selected_paper]["title"]
                templates = {
                    "Tóm tắt": f"What is the summary of the paper '{title}'?",
                    "Tác giả": f"Who authored the paper '{title}'?",
                    "Ngày xuất bản": f"When was the paper '{title}' published?",
                    "Lĩnh vực": f"What categories does the paper '{title}' belong to?",
                }
                with st.form("ask_form"):
                    if question_type == "Câu hỏi tự nhập":
                        question = st.text_area("Câu hỏi", placeholder="What is the summary of the paper '…'?")
                    else:
                        question = templates[question_type]
                        st.write(question)
                    top_k = st.slider("Số tài liệu nguồn", 1, min(8, len(documents)), min(settings.top_k, len(documents), 8))
                    submitted = st.form_submit_button("Tìm câu trả lời", type="primary")
                st.caption("Baseline hỗ trợ 4 dạng câu hỏi trên; câu hỏi khác được trả lời bằng câu đầu của phần tóm tắt.")
                if submitted:
                    st.session_state.pop("demo_result", None)
                    if not question.strip():
                        st.warning("Hãy nhập câu hỏi trước khi tìm kiếm.")
                    else:
                        try:
                            started = perf_counter()
                            with st.spinner("Đang tìm tài liệu và câu trả lời…"):
                                from retrieval.qa import answer_question

                                database = paths.chroma_dir / "chroma.sqlite3"
                                index = load_index(paths.embeddings_json.stat().st_mtime_ns, database.stat().st_mtime_ns)
                                answer = answer_question(question.strip(), settings, index, top_k=top_k)
                            st.session_state["demo_result"] = {
                                "question": answer.question,
                                "answer": answer.answer,
                                "retrieved_doc_ids": answer.retrieved_doc_ids,
                                "retrieved_contexts": answer.retrieved_contexts,
                                "seconds": perf_counter() - started,
                            }
                        except Exception as exc:
                            st.error("Không thể truy vấn chỉ mục. Kiểm tra model MiniLM và chạy lại baseline nếu cần.")
                            with st.expander("Chi tiết lỗi"):
                                st.text(str(exc))
                if result := st.session_state.get("demo_result"):
                    st.subheader("Câu trả lời")
                    st.caption(result["question"])
                    st.write(result["answer"] or "Tài liệu không có thông tin cho mục này.")
                    st.caption(f"Thời gian: {result['seconds']:.2f} giây · {len(result['retrieved_doc_ids'])} tài liệu nguồn")
                    show_sources(result, documents)

    with library_tab:
        search = st.text_input("Tìm theo tiêu đề, tác giả hoặc DOI")
        df = pd.DataFrame(papers)
        if not df.empty:
            if search.strip():
                mask = df[["title", "authors_joined", "paper_id"]].astype(str).apply(
                    lambda column: column.str.contains(search.strip(), case=False, regex=False)
                ).any(axis=1)
                df = df[mask]
            st.caption(f"Hiển thị {len(df)} / {len(papers)} bài báo")
            st.dataframe(
                df[["title", "authors_joined", "published", "age_days", "paper_id"]].rename(columns={
                    "title": "Tiêu đề", "authors_joined": "Tác giả", "published": "Xuất bản",
                    "age_days": "Tuổi (ngày)", "paper_id": "DOI",
                }), use_container_width=True, hide_index=True,
            )
        else:
            st.info("Chưa có dữ liệu sạch.")

    with quality_tab:
        left, right = st.columns(2)
        with left:
            st.subheader("Great Expectations")
            if quality:
                stats = quality.get("statistics", {})
                st.write(f"**{stats.get('successful_expectations', 0)} / {stats.get('evaluated_expectations', 0)}** kiểm tra đạt")
                checks = quality.get("validation_results", {}).get("results", [])
                for check in checks:
                    config = check.get("expectation_config", {})
                    name = config.get("type", config.get("expectation_type", "Expectation"))
                    column = config.get("kwargs", {}).get("column", "Toàn bộ bảng")
                    st.write(f"{'✅' if check.get('success') else '❌'} {column} · {name}")
            else:
                st.info("Chưa có kết quả kiểm định.")
        with right:
            st.subheader("Freshness SLA")
            if freshness:
                st.metric("Tỷ lệ bài quá hạn", f"{freshness['stale_ratio']:.2%}")
                st.write(f"{freshness['stale_rows']} / {freshness['total_rows']} bài quá {freshness['threshold_days']} ngày.")
                st.write(f"Ngưỡng cho phép: **{freshness['max_stale_ratio']:.0%}**")
                st.write(f"Trạng thái: **{'PASS' if freshness['is_fresh'] else 'FAIL'}**")
                st.caption(f"Khoảng xuất bản: {freshness['oldest_published']} → {freshness['latest_published']}")
            else:
                st.info("Chưa có báo cáo freshness.")
        st.divider()
        st.info("Bộ test dùng tên bài chính xác và câu trả lời trích từ dữ liệu. Điểm baseline chưa đánh giá đầy đủ câu hỏi diễn đạt tự do.")
        fallback_count = sum("Fallback heuristic" in item.get("judge", {}).get("reasoning", "") for item in answers)
        if fallback_count:
            st.caption(f"LLM judge dùng heuristic fallback ở {fallback_count}/{len(answers)} câu.")
        if metrics.get("ragas", {}).get("skipped"):
            st.caption("Ragas chưa được chạy trong lần đánh giá này.")
        if paths.baseline_report.exists():
            report = paths.baseline_report.read_text(encoding="utf-8")
            st.download_button("Tải báo cáo Phase 1", report, file_name="phase1_report.md", mime="text/markdown")
            with st.expander("Xem báo cáo đầy đủ"):
                st.markdown(report)


if __name__ == "__main__":
    main()
