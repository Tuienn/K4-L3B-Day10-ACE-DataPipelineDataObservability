# Phần người 5: Gemini RAG và điều phối pipeline

## Chạy sau khi ghép module của nhóm

Tại thư mục gốc repo, dùng Python 3.11–3.13:

```bash
uv sync
# Điền các giá trị dưới đây trong .env hiện có; không ghi đè hoặc commit API key.
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

Cấu hình `.env` (model có thể thay bằng model Gemini mà tài khoản truy cập được):

```dotenv
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GOOGLE_API_KEY=<key của bạn>
```

Nếu dùng pip: tạo/kích hoạt môi trường rồi `python -m pip install -e .` trước khi chạy `python script/run_phase1.py`. Cài editable package tránh lỗi `No module named pipelines`.

Không dùng `LLM_PROVIDER=google`: router hiện tại nhận `gemini`. Gemini sinh câu trả lời từ context retrieval; mock chỉ trích metadata để debug. Không có fallback sang mock khi Gemini trả lời lỗi. Evaluator có sẵn vẫn có heuristic fallback cho LLM judge; kiểm tra trường `judge.reasoning` trong answers JSON trước khi nhận xét điểm judge. `RUN_RAGAS=1` bật đánh giá Ragas tùy chọn; mặc định tắt. Gemini có thể cho câu trả lời khác giữa các lần chạy dù temperature=0, nên repaired metrics không được bảo đảm giống baseline tuyệt đối.

## Contract bàn giao

Giữ nguyên chữ ký hàm trong scaffold. Các module sau vẫn do người 1–4 triển khai; chạy thật sẽ dừng ở `NotImplementedError` nếu chưa hoàn thành.

- Người 1: `fetch_source_records(settings)` lưu raw response/raw records và trả `list[PaperRecord]`; `load_raw_records(path)` trả cùng kiểu. Baseline dùng raw records hiện có; `REFRESH_SOURCE=1` yêu cầu fetch lại.
- Người 2: `build_clean_dataframe(records, run_date)` trả DataFrame. Index cần các cột `paper_id`, `title`, `published`, `summary`, `authors_joined`, `categories_joined`, `abs_url`, `pdf_url`, `text_for_embedding`; observability cần thêm `age_days` và các helper theo scaffold. Metadata đưa vào Chroma nên là chuỗi, ngày dùng ISO, không phải Timestamp/list/null. `build_test_set(df, output_path)` trả list câu hỏi và lưu JSON, mỗi câu có `id`, `question_type`, `question`, `ground_truth`, `ground_truth_doc_ids` (list ID).
- Người 3: `run_data_quality_checks(df, settings, report_name)` nhận tên stage `baseline`, `corrupted`, `repaired`, trả dict có boolean `success`; `build_freshness_report(df, settings, report_path)` trả dict có boolean `is_fresh`. Hai hàm reporting giữ nguyên chữ ký scaffold. `source_summary` baseline có `source_api`, `source_query`, `raw_records`, `clean_records`, `run_date`, `llm_provider`, `model_name`, `embedding_model`, `top_k`, `freshness_threshold_days`.
- Người 4: `corrupt_clean_dataframe(df, output_log_path)` trả DataFrame bẩn và ghi log. Phải cập nhật cả `text_for_embedding`, `age_days` và helper bị ảnh hưởng khi thay nội dung/ngày. Không chạy cleaning để khử trùng dữ liệu bẩn trước quality checks. Repair được người 5 nối bằng `load_raw_records` → `build_clean_dataframe`, dùng đúng raw snapshot và thời điểm baseline; không cần đổi API scaffold.

## Trình tự và bằng chứng

Baseline: raw → clean → quality/freshness gate → tạo hoặc đọc lại test set → index → Gemini QA/evaluation → report. Gate baseline và repaired fail sẽ dừng trước index. Riêng corrupted chủ động bỏ qua gate thất bại để đo suy giảm trong thí nghiệm, vẫn lưu cảnh báo.

Ba stage có collection, clean artifacts, embedding manifests, answers và metrics riêng. Test set dùng chung. `data/results/baseline_run.json` được ghi chỉ khi baseline hoàn tất, lưu thời điểm, cấu hình không chứa secrets và hash của raw records, clean JSON, test set, baseline metrics. Corruption flow từ chối chạy nếu thiếu manifest hoặc các đầu vào này thay đổi. Khi đổi provider/model/top_k, làm lại baseline. Khi thay corpus khiến bộ đề cũ tham chiếu bài không còn tồn tại, chạy baseline với `REFRESH_TEST_SET=1`; không tái tạo đề giữa các stage.

Baseline freshness lưu ở `data/quality/freshness_report.json`; corrupted/repaired lưu ở các file riêng có tiền tố stage. Báo cáo cuối nằm ở `data/reports/phase1_report.md` và `data/reports/corruption_report.md`.

## Kiểm thử phần tích hợp

```bash
uv run --extra dev pytest -q tests
```

Tests dùng pandas thật và thay module đồng đội, index, Gemini bằng test doubles để kiểm tra điều phối, gate, bảo toàn snapshot/bộ đề và lỗi provider. Đây không phải bằng chứng GX, Chroma, MiniLM hoặc Gemini thật đã chạy thành công. Sau khi ghép đủ module, cần chạy lại hai lệnh pipeline với dependencies/model/key thật và kiểm tra artifacts trước khi nộp.

## Sau khi pull các module đồng đội

Trước khi chạy Gemini, kiểm tra các hàm còn thiếu mà không tải model hoặc gọi API:

```bash
uv run python script/run_phase1.py --check
uv run python script/run_corruption_flow.py --check
```

`--check` kiểm tra placeholder trong source và credential có được cấu hình, không xác nhận key/model hoạt động hoặc dependencies đã import được. Pipeline cũng kiểm tra placeholder khi được gọi trực tiếp. Nếu reporting/corruption còn `NotImplementedError`, hoàn thiện/merge phần tương ứng trước; không dùng báo cáo hoặc số liệu giả để vượt bước này.

Tối ưu người 5:

- LLM client và structured judge được tái sử dụng trong cùng process; Gemini đặt timeout 60 giây và tối đa 2 lần retry ở client.
- MiniLM cache tối đa 32 batch/query trong RAM. Khi repair tạo lại cùng nội dung, không cần encode lại trong cùng process; kết quả trả về là bản sao để tránh sửa nhầm cache.
- Tính embedding trước khi xóa collection cũ, tránh mất index khi tải/chạy model thất bại. Truy vấn giới hạn `top_k` theo số document và từ chối giá trị không dương.
- Retrieval vẫn giữ exact-title boost theo scaffold, kể cả tiêu đề có dấu nháy đơn. Metric ghi `retrieval_mode=semantic_with_exact_title_boost`, không nên diễn giải đó là kết quả semantic search thuần túy.
- Token F1 đếm số lần xuất hiện của token. `evaluation_version=2` ngăn dùng baseline cũ để so sánh với cách tính mới.
- Metrics có `judge_llm_samples` và `judge_heuristic_samples`; answers có `judge.backend`. Điểm fallback phải được diễn giải là heuristic, không phải Gemini judge.
- `datasets` chỉ import khi bật Ragas; SDK provider khác chỉ import khi sử dụng provider đó.

## Kết quả kiểm chứng sau khi tích hợp code mới

- 22 tests pass: điều phối, gate, giữ nguyên bộ đề/raw, cache, Token F1, provenance của judge, xử lý lỗi và giới hạn truy xuất.
- Đã dùng các module ingestion/cleaning/testset/GX thật trên bản sao snapshot: 24 bài sạch, 10 câu hỏi, quality và freshness đều pass.
- MiniLM và Chroma thật đã index đủ 24 tài liệu. Một câu hỏi smoke được Gemini trả lời và Gemini chấm điểm thành công, không dùng heuristic fallback. Đây chỉ là kiểm tra kết nối/tích hợp một câu; không thay thế baseline chính thức 10 câu hoặc báo cáo so sánh ba trạng thái.
- Thời điểm kiểm tra, `corrupt_clean_dataframe`, `generate_phase1_report` và `generate_corruption_report` vẫn là placeholder trong code đã pull. Cần merge phần này rồi chạy lại hai pipeline đầy đủ.

Kiểm chứng chạy trong môi trường tạm, không ghi đè raw/clean/eval artifacts của nhóm và không thay `.env`. Sau khi ghép đủ phần việc, dùng các lệnh ở đầu tài liệu để tạo kết quả chính thức.
