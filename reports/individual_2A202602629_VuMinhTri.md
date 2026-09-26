# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Vũ Minh Trí |
| MSSV | 2A202602629 |
| Khóa/Lớp | K4 / L3B |
| Tên nhóm | ACE — 5 thành viên |
| Vai trò chính | Thiết lập chốt kiểm soát dữ liệu (Data Observability & Quality Gates) với Great Expectations 1.x & Freshness SLA; Xây dựng bộ dữ liệu đánh giá chuẩn (Benchmark Test Set) |
| Repository | https://github.com/Tuienn/K4-L3B-Day10-ACE-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26 |
| Tỷ lệ đóng góp | 20%, theo phân bổ thống nhất tại `docs/TEAM.md` |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Data Observability & Quality Gates (Bước 4) | `src/observability/quality.py`<br>- `run_data_quality_checks`<br>- `evaluate_freshness_sla`<br>- `build_freshness_report` | Cleaned DataFrame (`papers_clean.json`, `papers_clean_corrupted.json`, `papers_clean_repaired.json`), `Settings` | Báo cáo kiểm định GX 1.x (`data/quality/baseline_quality_report.json`, `corrupted_quality_report.json`, `repaired_quality_report.json`), Freshness SLA report (`data/quality/freshness_report.json`), cấu hình suite (`data/quality/gx/`), dict kết quả `{"success": bool, "gx_success": bool, "is_fresh": bool}` | Hoàn thành; kiểm định chính xác cho cả 3 pha (Baseline PASS, Corrupted FAIL, Repaired PASS) |
| Benchmark Test Set Generation (Bước 5) | `src/evaluation/testset.py`<br>- `build_test_set` | Cleaned DataFrame (`papers_clean.json`), đường dẫn lưu file | Bộ dữ liệu đánh giá 10 câu hỏi Ground Truth phủ 4 dạng bài toán (`data/eval/test_set.json`) kèm `ground_truth_doc_ids` | Hoàn thành; test set dùng chung cố định làm thước đo chuẩn cho Baseline, Corrupted và Repaired |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Thống nhất Data Contract & Schema | Đỗ Mạnh Nghĩa (Module `crossref.py`, `cleaning.py`) | Thống nhất cấu trúc các trường `paper_id`, `title`, `summary`, `published`, `age_days`, `text_for_embedding` và kiểu dữ liệu chuẩn để Quality Gate kiểm định ổn định |
| Bàn giao Benchmark & Gate cho Baseline | Nguyễn Ngọc Tuyền (Module `phase1.py`) | Cung cấp chốt kiểm định `baseline_quality_report.json` và bộ đề `test_set.json` làm điều kiện tiên quyết trước khi nạp ChromaDB và chạy RAG evaluation pha 1 |
| Tích hợp Quality Gate cho Corruption & Repair | Hoàng Phong, Trịnh Quốc Hoàng (`corruption.py`, `corruption_flow.py`) | Thiết kế `run_data_quality_checks` hỗ trợ đa trạng thái qua `report_name` (`"corrupted"`, `"repaired"`), cho phép hệ thống tự động phát hiện vi phạm khi tiêm lỗi và xác nhận tính hợp lệ khi phục hồi |
| Xử lý xung đột và đồng bộ Git | Thành viên Nghĩa (nhánh `nghia`) | Giải quyết triệt để merge conflict ở `crossref.py` và `cleaning.py`, merge an toàn vào nhánh `tri` và đưa lên nhánh `main` thành công |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Thiết lập chốt kiểm định Great Expectations 1.x | `run_data_quality_checks`<br>`src/observability/quality.py` | 6 Expectations thuộc 4 nhóm kiểm định schema; xuất report JSON và suite JSON | Chạy trên dữ liệu sạch đạt 6/6 (100%); chạy trên dữ liệu lỗi phát hiện chính xác vi phạm (trượt row count, trượt unique, trượt length) |
| Xây dựng hệ thống giám sát Freshness SLA | `evaluate_freshness_sla`, `build_freshness_report`<br>`src/observability/quality.py` | Tính `age_days`, tỷ lệ bài cũ (>180 ngày). Ngưỡng cảnh báo SLA max 25%; xuất `freshness_report.json` | Baseline có 1/24 bài cũ (4.17% <= 25% -> `is_fresh=True`). Corrupted có 8/21 bài cũ (38.1% > 25% -> `is_fresh=False`) |
| Sinh bộ dữ liệu đánh giá chuẩn (Benchmark Test Set) | `build_test_set`<br>`src/evaluation/testset.py` | `data/eval/test_set.json` gồm 10 câu hỏi thuộc 4 dạng (`summary`, `authors`, `date`, `categories`), kèm Ground Truth và ID tài liệu đối chứng | Kiểm tra cấu trúc JSON đủ 10 câu hỏi, đúng phân bổ 4 dạng, `ground_truth_doc_ids` liên kết chính xác với `paper_id` |
| Tách biệt và tổng hợp tín hiệu Quality Gate | `src/observability/quality.py` | Tách biệt `gx_success` (chất lượng dữ liệu) và `is_fresh` (độ mới); logic tổng hợp `overall_success = gx_success and is_fresh` | Kiểm tra kết quả trả về `{"success": bool, "gx_success": bool, "is_fresh": bool}` trong các file report tại `data/quality/` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Báo cáo kiểm định chất lượng dữ liệu baseline `data/quality/baseline_quality_report.json` và bộ đề benchmark `data/eval/test_set.json`. Đặc biệt, `baseline_quality_report.json` chứng minh toàn bộ 24 bản ghi sạch vượt qua 6/6 expectations của Great Expectations 1.x (100% success) và thỏa mãn Freshness SLA với tỷ lệ bài cũ chỉ 4.17% (< 25%), kích hoạt cờ `success = True` cho phép pipeline nạp vector index vào ChromaDB.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Trong các hệ thống RAG (Retrieval-Augmented Generation), lỗi dữ liệu (dữ liệu thiếu, trùng lặp, bị cắt ngắn, hoặc dữ liệu quá cũ) thường gây ra hiện tượng **Silent Failure**: chương trình không hề ném ra ngoại lệ (exception) hay crash (`exit code 0`), nhưng LLM sinh câu trả lời sai lệch, ảo giác hoặc rỗng do context đầu vào bị hỏng. 
Phần việc của tôi giải quyết 2 bài toán cốt lõi:
1. **Chốt chặn tự động (Quality & Freshness Gate):** Ngăn chặn dữ liệu hỏng hoặc dữ liệu cũ đi vào Vector Database trước khi gây tác hại cho downstream agent.
2. **Thước đo chuẩn mực (Benchmark Test Set):** Cung cấp bộ câu hỏi Ground Truth độc lập và cố định để đo lường định lượng mức độ suy giảm của hệ thống khi có sự cố và mức độ phục hồi sau khi sửa.

### Cách triển khai

1. **Kiến trúc Great Expectations 1.x Ephemeral Context:**
   - Sử dụng Fluent API mới nhất của GX 1.x (`gx.get_context(mode="ephemeral")`) để kiểm định trực tiếp trên bộ nhớ (in-memory) mà không cần tạo thư mục cấu hình cồng kềnh.
   - Đăng ký nguồn dữ liệu Pandas qua `context.data_sources.add_pandas()`, tạo DataFrame Asset và Batch Definition qua `add_batch_definition_whole_dataframe()`.
   - Thiết lập 4 nhóm chốt kiểm định bắt buộc gồm 6 Expectations:
     - `ExpectTableRowCountToBeBetween(min=24, max=24)`: Kiểm soát tính toàn vẹn số lượng bản ghi (Completeness).
     - `ExpectColumnValuesToNotBeNull`: Áp dụng cho 3 cột cốt lõi `paper_id`, `title`, `text_for_embedding` (Completeness).
     - `ExpectColumnValuesToBeUnique(column="paper_id")`: Đảm bảo tính duy nhất, chống trùng lặp khóa chính (Uniqueness).
     - `ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30, max_value=20_000)`: Ngăn chặn abstract bị xóa rỗng hoặc rác ngắn (Validity).
   - Do Ephemeral Context không tự lưu suite xuống đĩa, hàm chủ động serialize suite qua `suite.to_json_dict()` và ghi ra `data/quality/gx/{report_name}_suite.json` làm bằng chứng nghiệm thu.

2. **Giám sát Freshness SLA (`evaluate_freshness_sla`):**
   - Xử lý phòng thủ: Ép kiểu `df["age_days"]` sang số bằng `pd.to_numeric(..., errors="coerce")`, kiểm tra các dòng không hợp lệ (`invalid_age_rows`).
   - Đếm số bản ghi có `age_days > threshold_days` (180 ngày).
   - Đánh giá trạng thái `is_fresh`: Đạt khi không có dòng `age_days` không hợp lệ và tỷ lệ bài cũ (`stale_ratio`) không vượt quá ngưỡng `MAX_STALE_RATIO = 0.25` (25%).
   - Tách biệt rành mạch giữa `gx_success` và `is_fresh`, tổng hợp trạng thái `overall_success = bool(gx_success and freshness["is_fresh"])`.

3. **Sinh bộ đề Benchmark Test Set (`build_test_set`):**
   - Nhận vào Cleaned DataFrame, kiểm tra điều kiện tiên quyết `len(df) >= 4`.
   - Phân bổ 10 câu hỏi bao phủ 4 dạng bài toán: `summary` (3 câu), `authors` (3 câu), `date` (2 câu), `categories` (2 câu).
   - Tự động bóc tách Ground Truth: sử dụng hàm `first_sentence()` cho tóm tắt nội dung chính, chuỗi tác giả đã join (`authors_joined`), ngày chuẩn (`published`), và danh mục (`categories_joined`).
   - Mỗi câu hỏi được gắn kèm `ground_truth_doc_ids = [paper_id]` để làm cơ sở tính toán `retrieval_hit_rate` cho Retrieval component.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | `df: pd.DataFrame` (chứa các cột `paper_id`, `title`, `summary`, `published`, `age_days`, `text_for_embedding`), `settings: Settings`, `report_name: str` |
| Output | Dict kết quả validation (`{"report_name": str, "success": bool, "gx_success": bool, "is_fresh": bool, "freshness": dict, "statistics": dict, "validation_results": dict}`); các file artifact JSON trong `data/quality/` và `data/eval/test_set.json` |
| Module phụ thuộc | `src/core/config.py` (`Settings`, `Paths`), `src/core/utils.py` (`write_json`, `safe_slug`, `first_sentence`), `great_expectations` 1.x, `pandas` |
| Module sử dụng output | `src/pipelines/phase1.py` (Baseline), `src/pipelines/corruption_flow.py` (Corruption & Repair), `src/evaluation/metrics.py` (tính toán Hit Rate, Token F1, Judge Accuracy) |
| Điều kiện lỗi cần xử lý | Thiếu các cột bắt buộc của Data Contract (`ValueError`), DataFrame rỗng, trường `age_days` bị null hoặc chuỗi không hợp lệ, dữ liệu ít hơn 4 dòng khi tạo test set |

### Cách xác minh

Lệnh thực tế đã chạy từ gốc repository:

```powershell
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'src'); from core.config import load_settings; from observability.quality import run_data_quality_checks, evaluate_freshness_sla; from evaluation.testset import build_test_set; import pandas as pd; df = pd.read_json('data/clean/papers_clean.json'); settings = load_settings(); res = run_data_quality_checks(df, settings, 'test'); print('Quality success:', res['success'], 'GX:', res['gx_success'], 'Fresh:', res['is_fresh']); q = build_test_set(df, 'data/eval/test_set.json'); print('Test set len:', len(q))"
```

- **Kết quả mong đợi:** Kiểm định Quality Gate trả về `success: True`, `gx_success: True`, `is_fresh: True`; sinh thành công test set gồm đúng 10 câu hỏi.
- **Kết quả thực tế:**
  ```text
  Quality success: True GX: True Fresh: True
  Test set len: 10
  ```
- **Artifact/log:**
  - `data/quality/test_quality_report.json` và `data/quality/baseline_quality_report.json` (ghi nhận 6/6 successful expectations).
  - `data/quality/freshness_report.json` (ghi nhận `total_rows: 24`, `stale_rows: 1`, `stale_ratio: 0.0417`, `is_fresh: true`).
  - `data/eval/test_set.json` (ghi nhận danh sách 10 câu hỏi chuẩn hóa).

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương thức vận hành Great Expectations: sử dụng cấu hình tập trung dạng File-based Context truyền thống (`great_expectations init` tạo thư mục `great_expectations/` và file YAML) hay sử dụng Ephemeral Context (GX 1.x Fluent API).
- **Các phương án đã cân nhắc:**
  1. *Phương án 1 (File-based GX Context):* Tạo thư mục `great_expectations/`, định nghĩa datasource và suites qua file YAML tĩnh.
  2. *Phương án 2 (Ephemeral Context bằng Fluent API):* Khởi tạo context ngay trên bộ nhớ bằng `gx.get_context(mode="ephemeral")`, định nghĩa datasource và expectations trực tiếp bằng Python code, chủ động serialize cấu hình ra artifact JSON.
- **Phương án đã chọn:** Phương án 2 (Ephemeral Context với GX 1.x Fluent API).
- **Lý do:**
  - *Tính độc lập và tính tái lập (Reproducibility):* Môi trường Git làm việc nhóm 5 người thường xuyên gặp xung đột khi các file uncommitted trong thư mục `great_expectations/` bị ghi đè hoặc sai lệch đường dẫn giữa các máy (Windows vs Linux).
  - *Tối ưu cho In-memory Pipeline:* Dữ liệu của nhóm luân chuyển dưới dạng `pd.DataFrame`, việc dùng Fluent API Pandas Datasource trực tiếp nhanh hơn, không tốn I/O đĩa trung gian và dễ dàng tham số hóa các ngưỡng (như `settings.max_results`) vào expectation.
  - *Bảo toàn tính kiểm toán (Auditability):* Dù chạy ephemeral trên RAM, hàm vẫn ghi lại toàn bộ cấu hình `suite.to_json_dict()` ra thư mục `data/quality/gx/` và kết quả validation ra `data/quality/`, đảm bảo có đầy đủ artifact minh chứng mà không cần duy trì thư mục cấu hình cồng kềnh.
- **Bằng chứng quyết định phù hợp:** Toàn bộ pipeline baseline và corruption flow chạy độc lập trên máy tính mà không phụ thuộc vào bất kỳ thư mục GX cục bộ nào; các báo cáo `baseline_suite.json`, `corrupted_suite.json`, `repaired_suite.json` được sinh tự động, chuẩn xác 100%.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  1. Cảnh báo lỗi và deprecation khi chuyển từ GX v0.18 sang GX 1.x: Gọi trực tiếp `gx.ExpectationSuite(...)` mà không đăng ký vào context dẫn đến lỗi khi validate batch.
  2. Khi tiêm lỗi dữ liệu (corruption), trường `age_days` có thể bị chuyển thành `None` hoặc kiểu chuỗi không hợp lệ, khiến dòng lệnh tính `df["age_days"] > threshold_days` văng ngoại lệ:
     `TypeError: '>' not supported between instances of 'NoneType' and 'int'`.
- **Lệnh hoặc bước tái hiện:**
  Chạy `evaluate_freshness_sla` trên DataFrame đã bị tiêm lỗi ngày hoặc thiếu trường `age_days`.
- **Nguyên nhân gốc:**
  - GX 1.x thay đổi hoàn toàn kiến trúc sang Fluent API: luồng xử lý bắt buộc phải đi qua Context -> DataSource -> DataAsset -> BatchDefinition -> Batch, và Suite phải được gán vào Context qua `context.suites.add(suite)`.
  - Chưa xử lý phòng thủ dữ liệu bẩn (defensive coding): Khi dữ liệu bị corrupt, các cột số có thể lẫn lộn giá trị rác hoặc rỗng, phép so sánh logic thông thường của Pandas sẽ bị crash.
- **Cách xử lý:**
  - Trong `src/observability/quality.py`, chuẩn hóa toàn bộ hàm theo GX 1.x Fluent API:
    ```python
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name=f"papers_{safe_report_name}_source")
    data_asset = data_source.add_dataframe_asset(name=f"papers_{safe_report_name}_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe(f"papers_{safe_report_name}_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})
    suite = context.suites.add(gx.ExpectationSuite(name=f"papers_quality_suite_{safe_report_name}"))
    ```
  - Bổ sung phòng ngự cho Freshness SLA bằng `pd.to_numeric(df["age_days"], errors="coerce")`, lọc rõ `valid_age = age_days.notna() & age_days.ge(0)`, và kiểm tra chặt chẽ `invalid_age_rows == 0`.
- **Cách xác minh sau khi sửa:**
  Chạy kiểm thử trên cả DataFrame sạch và DataFrame bị tiêm lỗi dữ liệu; hàm xử lý trơn tru, không ném exception mà trả về chính xác `is_fresh: False` và `gx_success: False`.
- **Điều học được:**
  Module Data Observability sinh ra để kiểm soát dữ liệu bất thường, do đó mã nguồn của Observability phải có khả năng phòng thủ cao nhất: tuyệt đối không được giả định dữ liệu đầu vào luôn đúng kiểu hoặc không bị null.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   - Dữ liệu thô được Ingestion fetch từ Crossref REST API (hoặc đọc snapshot JSON), bóc tách thành danh sách `PaperRecord` và lưu vào `data/raw/`.
   - Cleaning chuẩn hóa văn bản, loại bỏ thẻ JATS/XML, khử trùng lặp theo `paper_id`, tính `age_days` và ghép chuỗi chuẩn hóa `text_for_embedding` (đủ 5 nhãn Title, Authors, Published, Categories, Summary).
   - Dữ liệu sạch đi qua **Data Observability Gate (GX 1.x & Freshness SLA)**: nếu đạt chuẩn mới được đi tiếp.
   - Module Embedding dùng `sentence-transformers/all-MiniLM-L6-v2` chuyển hóa `text_for_embedding` thành vector 384 chiều, sau đó lưu trữ và đánh chỉ mục vào ChromaDB collection `papers-baseline`.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   - Evaluation set gồm 10 câu hỏi đại diện cho 4 tác vụ truy vấn thông tin khoa học (`summary`, `authors`, `date`, `categories`).
   - `ground_truth_doc_ids` (chứa DOI của bài báo nguồn) được dùng để đối chiếu với danh sách các document IDs do ChromaDB trả về ở bước Retrieval (`top_k=4`). Nếu ID đúng nằm trong top_k, `retrieval_hit_rate` ghi nhận 1 (thành công), ngược lại ghi nhận 0.
   - Ground Truth text dùng để đo chất lượng câu trả lời sinh ra từ LLM thông qua:
     - `mean_token_f1`: Đo độ trùng lặp từ vựng giữa câu trả lời và ground truth.
     - `judge_accuracy` và `mean_judge_score`: Dùng LLM Judge chấm điểm theo thang rubric 1–5 về tính chính xác và tính đầy đủ.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Quality checks (GX 1.x):** Đo lường tính toàn vẹn cấu trúc và quy tắc dữ liệu nội tại (Data Quality Dimensions) như Completeness (không null, đủ dòng), Uniqueness (không trùng ID), Validity (độ dài tóm tắt hợp lệ). Dữ liệu có thể được xuất bản từ 10 năm trước nhưng vẫn vượt qua 100% Quality Checks nếu schema không bị lỗi.
   - **Freshness monitoring (SLA):** Đo lường tính thời sự của thông tin (Timeliness/Freshness). Một tập dữ liệu hoàn hảo về mặt cấu trúc vẫn có thể bị coi là "ôi thiu" (stale) nếu quá 25% số lượng bài báo có tuổi đời vượt quá 180 ngày so với ngày vận hành hệ thống.

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   - Để đảm bảo nguyên tắc kiểm chứng thực nghiệm (Controlled Experiment): trong nghiên cứu khoa học, ta chỉ được phép thay đổi một biến số duy nhất (ở đây là **trạng thái chất lượng dữ liệu**).
   - Nếu mỗi trạng thái dùng một bộ câu hỏi khác nhau, độ biến thiên của metrics sẽ bị nhiễu do độ khó của câu hỏi chứ không phản ánh đúng tác động của việc tiêm lỗi dữ liệu hay hiệu quả của thuật toán phục hồi dữ liệu.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - **Về mặt Data Quality & Observability:** Artifact `data/quality/repaired_quality_report.json` phải ghi nhận `gx_success: True` (vượt qua 6/6 expectations) và `data/quality/repaired_freshness_report.json` ghi nhận `is_fresh: True` (tỷ lệ bài cũ quay về mức an toàn 4.17%).
   - **Về mặt Data Artifacts:** File `papers_clean_repaired.json` phục hồi đầy đủ 24 bản ghi sạch, định danh ID duy nhất, không còn abstract rỗng.
   - **Về mặt RAG Agent Metrics:** `data/results/repaired_metrics.json` chứng minh:
     - `retrieval_hit_rate` phục hồi từ 0.50 (50%) lên 1.00 (100%).
     - `mean_token_f1` phục hồi từ 0.7788 lên 1.0000.
     - `judge_accuracy` phục hồi từ 0.80 lên 1.00.
     - `mean_judge_score` phục hồi từ 4.00 lên 5.00/5.0.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 (100%) | 0.5000 (50%) | 1.0000 (100%) | Giảm mạnh một nửa khi dữ liệu bị lỗi; phục hồi hoàn hảo 100% sau repair |
| `mean_token_f1` | 1.0000 (100%) | 0.7788 (77.9%) | 1.0000 (100%) | Độ trùng khớp từ ngữ sụt giảm 22.1% do context bị nhiễu/rỗng; phục hồi hoàn toàn |
| `judge_accuracy` | 1.0000 (100%) | 0.8000 (80%) | 1.0000 (100%) | 20% câu trả lời bị LLM Judge đánh trượt ở pha corrupted; đạt chuẩn 100% ở repaired |
| `mean_judge_score` | 5.00 / 5.0 | 4.00 / 5.0 | 5.00 / 5.0 | Điểm đánh giá chất lượng giảm 1.0 điểm do thiếu hụt thông tin trong context |
| Quality checks | PASS (6/6 đạt) | FAIL (3 vi phạm) | PASS (6/6 đạt) | GX 1.x phát hiện chính xác vi phạm số dòng, trùng lặp và tóm tắt rỗng |
| Freshness status | True (4.17% cũ) | False (38.1% cũ) | True (4.17% cũ) | Tỷ lệ bài cũ tăng vọt vượt ngưỡng 25% ở pha corrupted; đưa về mức an toàn sau repair |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. **[Data corruption] → [quality/freshness signal thay đổi] → [agent metric thay đổi]:**
   Khi tiêm 6 kịch bản lỗi (xóa 20% bài mới, xóa summary, chèn nhiễu, cắt ngắn title, lùi ngày xuất bản, nhân bản dòng) → Quality Gate hạ cờ cảnh báo (`gx_success: False`, vi phạm 3 expectations về row count, uniqueness, length; `is_fresh: False` do tỷ lệ cũ vọt lên 38.1%) → RAG Agent bị suy giảm nghiêm trọng: `retrieval_hit_rate` rơi tự do từ 100% xuống 50%, `mean_token_f1` giảm từ 1.0 xuống 0.7788, minh chứng rõ rệt hiện tượng **Silent Failure**.

2. **[Repair action] → [quality/freshness signal phục hồi] → [agent metric phục hồi]:**
   Khi thực hiện Idempotent Repair tái tạo từ raw snapshot (`crossref_records.json`) kết hợp chạy lại `build_clean_dataframe()` và re-indexing → Quality Gate phục hồi hoàn toàn (`gx_success: True`, 6/6 expectations đạt chuẩn; `is_fresh: True`, tỷ lệ cũ quay về 4.17%) → Toàn bộ chỉ số RAG Agent phục hồi nguyên vẹn: `retrieval_hit_rate` trở lại 100%, `mean_token_f1` đạt 1.0, `judge_accuracy` đạt 1.0 và `mean_judge_score` đạt 5.0/5.0.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Dạng lỗi **Drop latest records (mất bài báo mới nhất)** và **Blank summary (xóa rỗng tóm tắt)** ảnh hưởng nghiêm trọng nhất.
- Khi bài báo bị xóa khỏi cơ sở dữ liệu, câu hỏi kiểm thử tương ứng hoàn toàn không thể tìm thấy context trong Vector Store, khiến `retrieval_hit_rate` sụt giảm lập tức.
- Khi summary bị xóa trắng hoặc bị chèn nhiễu, vector ngữ nghĩa của tài liệu bị biến dạng, đồng thời context đưa vào prompt cho LLM không chứa thông tin trả lời, dẫn đến việc LLM buộc phải từ chối trả lời hoặc sinh câu trả lời sai lệch (hallucination).

Kết quả nào khác với kỳ vọng ban đầu?

Ban đầu, tôi dự đoán khi `retrieval_hit_rate` sụt giảm 50%, thì `judge_accuracy` cũng sẽ sụt giảm tương ứng xuống quanh mức 50%. Tuy nhiên, kết quả thực tế cho thấy `judge_accuracy` chỉ giảm xuống **80%** (0.8000).
- *Giải thích:* Trong 4 dạng câu hỏi của benchmark, các câu hỏi về tác giả (`authors`) hoặc danh mục (`categories`) của những bài báo không bị xóa vẫn được LLM trả lời tương đối tốt nếu một phần metadata lọt vào top-k còn lại, hoặc do câu hỏi về `date` có dạng ngắn. Điều này khẳng định tầm quan trọng của việc kết hợp cả chỉ số kỹ thuật thô (`retrieval_hit_rate`, `token_f1`) lẫn chỉ số ngữ nghĩa (`judge_accuracy`, `judge_score`) để có cái nhìn toàn diện nhất.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về Data Pipeline:** Pipeline dữ liệu trong các hệ thống AI/RAG không chỉ đơn thuần là luân chuyển dữ liệu từ API sang Vector DB, mà phải có cơ chế lưu trữ snapshot thô bất biến (Raw Preservation) và thuật toán làm sạch có tính chất Idempotent (chạy nhiều lần vẫn ra một kết quả duy nhất) để làm điểm tựa tự phục hồi khi có sự cố.
2. **Về Data Quality & Observability:** Kiểm tra dữ liệu không chỉ là `assert` đơn giản trong code mà cần hệ thống Observability chuẩn mực. Phải phân tách rõ ràng giữa kiểm tra cấu trúc schema (Quality Dimensions) và kiểm tra độ mới (Freshness SLA). Thiếu một trong hai sẽ không thể phát hiện trọn vẹn các hình thức suy thoái dữ liệu.
3. **Về ảnh hưởng của Data đến RAG Agent:** "Garbage in, Garbage out" trong RAG thể hiện dưới dạng Silent Failure cực kỳ nguy hiểm. Hệ thống không hề báo lỗi crash, nhưng người dùng sẽ nhận được câu trả lời sai. Data Observability chính là chốt chặn phòng thủ hàng đầu bảo vệ độ tin cậy của AI Agent.

### Nếu có thêm thời gian

Tôi sẽ xây dựng cơ chế **Quality Gate tích hợp Alerting thời gian thực (Webhook/Slack notification)** và **Automated Circuit Breaker**:
- *Lý do:* Hiện tại khi Quality Gate phát hiện dữ liệu lỗi (`overall_success = False`), pipeline ghi nhận báo cáo nhưng chưa có cơ chế tự động gửi cảnh báo khẩn cấp tới kỹ sư dữ liệu hoặc tự động ngắt (circuit break) luồng indexing để bảo vệ Vector Store sản xuất.
- *Cách đo lường cải thiện:* Giả lập sự cố dữ liệu bẩn từ API nguồn và đo lường thời gian từ lúc phát hiện lỗi đến khi cảnh báo được kích hoạt (Mean Time to Detect - MTTD), đồng thời xác nhận Vector Database sản xuất được bảo vệ nguyên vẹn 100% không bị ô nhiễm dữ liệu lỗi.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Vũ Minh Trí  
**Ngày xác nhận:** 2026-09-26
