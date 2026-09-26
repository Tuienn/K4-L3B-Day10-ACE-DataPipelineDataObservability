# Member Role Report — Day 10: Data Pipeline & Data Observability

> Báo cáo vai trò cá nhân của thành viên tham gia bài thực hành Day 10. Nội dung phản ánh trung thực phần việc kỹ thuật đã thực hiện, kết quả đo lường thực tế từ pipeline và mức độ hiểu biết về hệ thống Data Observability cho RAG.

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| **Họ và tên** | **Trịnh Quốc Hoàng** |
| **MSSV** | **2A202602847** |
| **Khóa / Lớp / Buổi học** | K4 / L3B / Day 10 |
| **Tên nhóm** | **ACE** |
| **Vai trò chính** | **Kỹ sư Data Observability & Đánh giá RAG** (Phụ trách Đo lường suy giảm hiệu năng, Phục hồi dữ liệu Idempotent Repair và Lập báo cáo đối chiếu 3 trạng thái Baseline – Corrupted – Repaired) |
| **Repository** | `https://github.com/Tuienn/K4-L3B-Day10-ACE-DataPipelineDataObservability` |
| **Ngày hoàn thành** | 2026-09-26 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu (Ownership)

| Module / Deliverable | File / Hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Corruption Flow & Orchestration** | `src/pipelines/corruption_flow.py`, `script/run_corruption_flow.py` | Baseline clean data, raw records snapshot, benchmark test set | Luồng chạy toàn tuyến Phase 2 / Phase 8, Chroma collection `papers-corrupted` & `papers-repaired` | **Hoàn thành** |
| **Idempotent Data Repair** | Hàm `repair_from_raw_snapshot()` trong `src/pipelines/corruption_flow.py` | `data/raw/crossref_records.json` (Lineage Anchor) | Dữ liệu sạch tái lập `papers_clean_repaired.csv`, `papers_clean_repaired.json` | **Hoàn thành** |
| **State Comparison Reporting** | Hàm `generate_corruption_report()` trong `src/observability/reporting.py` | Metrics & Quality reports của Baseline, Corrupted, Repaired | Báo cáo markdown đối chiếu 3 trạng thái tại `data/reports/corruption_report.md` | **Hoàn thành** |
| **Degradation & Recovery Metrics** | Tích hợp `src/evaluation/metrics.py` | Vector indices và benchmark `data/eval/test_set.json` | `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json` | **Hoàn thành** |

### Việc hỗ trợ ngoài phạm vi chính 

| Hoạt động | Thành viên / Module được hỗ trợ | Kết quả và bằng chứng |
| :--- | :--- | :--- |
| **Fix Unicode Console Encoding trên Windows** | Toàn nhóm (`script/run_phase1.py`, `script/run_corruption_flow.py`) | Xử lý triệt để lỗi `UnicodeEncodeError: 'charmap'` bằng cách cấu hình `sys.stdout.reconfigure(encoding="utf-8")`, giúp in bảng báo cáo tiếng Việt mượt mà trên PowerShell. |
| **Kiểm tra Schema & Freshness với Quality Gate** | Hoàng Phong (`corruption.py`) & Vũ Minh Trí (`quality.py`) | Đảm bảo tập dữ liệu sau khi tiêm 6 lỗi vẫn giữ đầy đủ các cột bắt buộc nhưng vi phạm các điều kiện kiểm định (Row count, Unique, Summary length, Stale date) để Great Expectations 1.x và Freshness SLA kích hoạt cảnh báo đỏ chuẩn xác. |
| **Hỗ trợ Baseline Pipeline** | Nguyễn Ngọc Tuyền (`phase1.py`) | Đảm bảo giao diện chữ ký hàm của `LocalEmbeddingIndex.build` và `evaluate_pipeline` tương thích hoàn toàn giữa luồng Phase 1 và Phase 2. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File / Hàm / Artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| **Đo lường Silent Failure trên dữ liệu bẩn** | `src/pipelines/corruption_flow.py`, `src/evaluation/metrics.py` | Ghi nhận sự sụt giảm: Hit Rate giảm từ **100% xuống 50%**, Token F1 giảm từ **1.0000 xuống 0.7788**. | Đọc `data/results/corrupted_metrics.json` |
| **Kiểm định chất lượng dữ liệu bẩn** | `src/observability/quality.py` | Bắt trọn 3/6 Expectation thất bại, Freshness SLA cảnh báo `is_fresh = False` (38.1% bài cũ). | Đọc `data/quality/corrupted_quality_report.json` |
| **Tự phục hồi dữ liệu Idempotent** | Hàm `repair_from_raw_snapshot()` | Khôi phục nguyên vẹn 24 bản ghi sạch từ raw snapshot, cập nhật Vector Store sạch `papers-repaired`. | File `data/clean/papers_clean_repaired.csv` |
| **Tái đánh giá & Chứng minh phục hồi** | `src/pipelines/corruption_flow.py` | Phục hồi hoàn hảo: Hit Rate đạt **100%**, Token F1 đạt **1.0000**, GX Quality Gate đạt **PASS (True)**. | Đọc `data/results/repaired_metrics.json` |
| **Lập báo cáo đối chiếu 3 trạng thái** | `src/observability/reporting.py` | File báo cáo markdown chi tiết với bảng 3 cột trực quan và phân tích sâu sắc. | Đọc `data/reports/corruption_report.md` |

### Mô tả một output cụ thể:
Output nổi bật nhất mà tôi bàn giao là **Báo cáo đối chiếu 3 trạng thái** ([data/reports/corruption_report.md](file:///d:/DATA/IT/AIA/lab/K4-L3B-Day10-ACE-DataPipelineDataObservability/data/reports/corruption_report.md)) cùng bảng in trực tiếp trên Console Terminal khi chạy `python script/run_corruption_flow.py`. Báo cáo này đặt song song 3 mốc: **Baseline vs Corrupted vs Repaired**, minh chứng bằng số liệu thực tế định lượng rằng:
1. Dữ liệu hỏng gây ra suy giảm hiệu năng nghiêm trọng (Silent Failure) mà chương trình không hề crash.
2. Great Expectations 1.x cùng Freshness SLA đóng vai trò chốt chặn tin cậy (kích hoạt FAIL).
3. Cơ chế Idempotent Repair từ snapshot thô giúp phục hồi toàn bộ năng lực của Agent về 100%.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. **Minh chứng hiện tượng Silent Failure:** Trong các hệ thống RAG thực tế, lỗi dữ liệu (dữ liệu bị cắt ngắn, nhiễu, trễ pipeline, trùng lặp) thường không làm văng exception trong code (`exit code 0`), nhưng lại làm mô hình trả lời sai hoặc không tìm thấy thông tin. Cần một quy trình đo lường định lượng được mức độ suy giảm này.
2. **Cơ chế phục hồi dữ liệu an toàn (Self-Healing / Repair):** Khi dữ liệu sạch bị hỏng, hệ thống không thể trông chờ vào việc gọi lại API ngoài (vì nguy cơ Rate Limit 429, phụ thuộc mạng hoặc API bên thứ ba thay đổi dữ liệu). Cần một cơ chế phục hồi nội tại, đáng tin cậy và có tính chất **Idempotent** (chạy lại bao nhiêu lần vẫn cho ra kết quả sạch duy nhất).

### Cách triển khai
Tôi xây dựng toàn bộ pipeline trong `src/pipelines/corruption_flow.py` theo chu trình 6 bước tự động:
1. **Kiểm tra Baseline:** Đọc metrics và dữ liệu sạch baseline; nếu chưa có thì kích hoạt chạy đánh giá baseline.
2. **Tiêm lỗi thực nghiệm (Corruption):** Nhận DataFrame sạch từ `clean_df`, tiêm 6 kịch bản lỗi qua `corrupt_clean_dataframe()`, lưu ra `papers_clean_corrupted.csv` và `.json`.
3. **Index Vector bẩn & Đo lường suy thoái:** Xây dựng ChromaDB collection `papers-corrupted`, thực hiện truy vấn và thẩm định qua `evaluate_pipeline()`, lưu kết quả vào `corrupted_metrics.json` và `corrupted_answers.json`.
4. **Kiểm định chất lượng:** Chạy chốt kiểm soát `run_data_quality_checks()` trên dữ liệu bẩn. Quan sát Great Expectations 1.x đánh trượt và Freshness SLA báo động đỏ `is_fresh = False`.
5. **Idempotent Repair:** Triển khai hàm `repair_from_raw_snapshot()`:
   - Đọc trực tiếp từ file snapshot thô ban đầu `data/raw/crossref_records.json` (Lineage Anchor).
   - Tái thực thi toàn bộ logic làm sạch `build_clean_dataframe()`.
   - Ghi đè có kiểm soát vào `papers_clean_repaired.*` và khôi phục lại `papers_clean.*`.
6. **Index Vector phục hồi & Tái đánh giá:** Xây dựng collection `papers-repaired`, tái đánh giá với đúng bộ test set 10 câu hỏi, xuất báo cáo `data/reports/corruption_report.md` và in bảng 3 cột ra console.

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | `data/clean/papers_clean.json`, `data/raw/crossref_records.json`, `data/eval/test_set.json` |
| **Output** | `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md`, collection ChromaDB `papers-corrupted`, `papers-repaired` |
| **Module phụ thuộc** | `src/ingestion/corruption.py` (cung cấp hàm tiêm lỗi), `src/observability/quality.py` (kiểm định GX 1.x), `src/evaluation/metrics.py` (chấm điểm retrieval & F1) |
| **Module sử dụng output** | Toàn nhóm dùng để làm tài liệu thuyết minh bảo vệ bài lab (CP6), điền vào `report/group_report.md` và nghiệm thu VLearn LMS |
| **Điều kiện lỗi cần xử lý** | Thiếu file baseline ban đầu; lỗi encoding khi in tiếng Việt trên console Windows; lỗi xung đột collection ChromaDB khi chạy lại nhiều lần (xử lý bằng cách xóa collection cũ trước khi tạo mới) |

### Cách xác minh
Thực thi lệnh chạy toàn tuyến Phase 2:
```bash
python script/run_corruption_flow.py
```
- **Kết quả mong đợi:** Toàn bộ 6 bước chạy thông suốt, console in ra bảng đối chiếu 3 cột rõ ràng, và file `data/reports/corruption_report.md` được sinh ra hoàn chỉnh.
- **Kết quả thực tế:** Pipeline chạy hoàn tất 100%, ghi nhận đầy đủ sự suy giảm ở Corrupted và sự phục hồi tuyệt đối ở Repaired.
- **Artifact kiểm chứng:**
  - `data/reports/corruption_report.md`
  - `data/results/corrupted_metrics.json`
  - `data/results/repaired_metrics.json`

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương án triển khai logic phục hồi dữ liệu (`repair`) khi phát hiện dữ liệu trong Vector Store bị lỗi/nhiễu.
- **Các phương án đã cân nhắc:**
  - *Phương án 1 (Reverse Mutation / Patch Script):* Viết hàm quét qua các dòng bị lỗi trong DataFrame và sửa ngược lại (ví dụ: gỡ bỏ chuỗi noise marker, xóa các dòng trùng lặp, nối lại tiêu đề bị cắt).
  - *Phương án 2 (Idempotent Rebuild from Lineage Anchor):* Sử dụng nguyên lý **Data Lineage**: quay trở lại bản ghi thô nguyên bản (`data/raw/crossref_records.json` đã lưu ở bước Ingestion), chạy lại toàn bộ quy trình `build_clean_dataframe()` và tái tạo mới hoàn toàn chỉ mục Vector Store.
- **Phương án đã chọn:** **Phương án 2 (Idempotent Rebuild from Lineage Anchor).**
- **Lý do lựa chọn:**
  - *Tính đúng đắn (Correctness):* Phương án 1 mang tính chắp vá, tiềm ẩn nguy cơ không thể khôi phục các dữ liệu đã bị mất vĩnh viễn (như 20% bài báo mới nhất bị drop hoặc các tiêu đề bị cắt mất thông tin gốc).
  - *Tính bất biến (Idempotency):* Phương án 2 đảm bảo tính xác định cao nhất. Dù pipeline gặp bất kỳ sự cố nào, việc re-run từ bản snapshot thô luôn đưa hệ thống về một trạng thái sạch duy nhất đã được kiểm chứng.
  - *Chi phí & Tốc độ:* Vì đọc từ snapshot local nên hoàn toàn không tốn chi phí gọi mạng, không lo bị giới hạn tần suất API (Rate Limit 429).
- **Bằng chứng quyết định phù hợp:** Kết quả thực tế cho thấy sau khi chạy Repair theo Phương án 2, Retrieval Hit Rate và Token F1 quay trở lại mức **1.0000 (100%)**, số bản ghi trở về đúng **24 dòng**, và 100% các bài kiểm định GX 1.x đều đạt **PASS**.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng / Lỗi nguyên văn:**
  ```text
  UnicodeEncodeError: 'charmap' codec can't encode character '\u1ea9' in position 9: character maps to <undefined>
  ```
- **Lệnh hoặc bước tái hiện:** Chạy `python script/run_corruption_flow.py` trên môi trường terminal Windows PowerShell.
- **Nguyên nhân gốc (Root cause):** Mặc định trên hệ điều hành Windows, luồng xuất chuẩn `sys.stdout` của Python sử dụng bảng mã `cp1252` thay vì `utf-8`. Khi pipeline in các thông báo tiến trình hoặc tiêu đề bảng có chứa tiếng Việt có dấu (như ký tự `ẩ` trong `Chuẩn bị`), bộ giải mã `cp1252` không thể ánh xạ được và gây crash chương trình.
- **Cách xử lý:** Thêm đoạn mã tái cấu hình encoding chuẩn cho `stdout` và `stderr` ngay tại phần đầu của các file entrypoint:
  ```python
  import sys

  if hasattr(sys.stdout, "reconfigure"):
      sys.stdout.reconfigure(encoding="utf-8", errors="replace")
  if hasattr(sys.stderr, "reconfigure"):
      sys.stderr.reconfigure(encoding="utf-8", errors="replace")
  ```
- **Cách xác minh sau khi sửa:** Chạy lại `python script/run_corruption_flow.py`, chương trình in bảng tổng kết tiếng Việt với đầy đủ các ký tự có dấu và đường kẻ box Unicode một cách trơn tru, không phát sinh lỗi.
- **Điều học được:** Khi phát triển các pipeline dữ liệu và công cụ CLI đa nền tảng (cross-platform), luôn phải chủ động kiểm soát bảng mã của môi trường xuất/nhập (I/O encoding) để tránh các lỗi crash liên quan đến Unicode trên môi trường Windows.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   - API Crossref trả về payload JSON thô chứa danh sách các bài báo nghiên cứu.
   - Pipeline bóc tách (`parse_crossref_payload`), làm sạch thẻ HTML/XML rác (`<jats:p>`), lưu 2 file raw artifact (`crossref_response.json`, `crossref_records.json`).
   - Bước làm sạch (`build_clean_dataframe`) khử trùng lặp theo `paper_id`, tính `age_days`, tạo trường ngữ cảnh tổng hợp `text_for_embedding` (gồm Title, Authors, Published, Categories, Summary).
   - Mô hình `sentence-transformers/all-MiniLM-L6-v2` chuyển đổi chuỗi văn bản này thành các dense vector 384 chiều và nạp kèm metadata vào cơ sở dữ liệu vector ChromaDB.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   - Benchmark test set gồm 10 câu hỏi bao phủ 4 dạng nghiệp vụ: `summary`, `authors`, `date`, `categories`.
   - Mỗi câu hỏi đi kèm `ground_truth` (câu trả lời mẫu) và `ground_truth_doc_ids` (DOI của bài báo chứa thông tin chuẩn).
   - **Đo Retrieval:** Khi truy vấn, nếu danh sách `retrieved_doc_ids` từ ChromaDB chứa ít nhất một DOI nằm trong `ground_truth_doc_ids`, hệ thống ghi nhận một lượt tìm trúng (`retrieval_hit = True`). Tỷ lệ này trên toàn bộ tập test tạo nên `retrieval_hit_rate`.
   - **Đo Answer Quality:** So sánh giữa câu trả lời sinh ra (`answer`) và `ground_truth` bằng chỉ số `token_f1` (đo độ trùng khớp từ vựng) và `judge_accuracy` (thẩm định tính đúng đắn về mặt ngữ nghĩa).

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Quality checks (Great Expectations 1.x):** Tập trung vào tính toàn vẹn cấu trúc dữ liệu (**Data Validity, Completeness, Uniqueness**): kiểm tra số lượng dòng, các cột không được null, `paper_id` không trùng lặp, độ dài tóm tắt không bị rỗng/quá ngắn.
   - **Freshness monitoring (Freshness SLA):** Tập trung vào tính kịp thời và độ mới của thông tin (**Data Timeliness**): đo lường `age_days`. Dù dữ liệu đúng schema 100% nhưng nếu có hơn 25% số bài báo đã cũ hơn 180 ngày, hệ thống vẫn gióng cờ cảnh báo `is_fresh = False` vì tri thức đã quá hạn.

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   - Để đảm bảo tính khách quan và khoa học của thực nghiệm (**Controlled Experiment**).
   - Nếu thay đổi câu hỏi kiểm thử giữa các trạng thái, sự biến động của chỉ số có thể đến từ độ khó của câu hỏi chứ không phản ánh đúng tác động của sự cố dữ liệu. Giữ cố định test set giúp cô lập biến số duy nhất là **chất lượng dữ liệu trong Vector Store**.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - **Về mặt Data Quality:** Báo cáo `data/quality/repaired_quality_report.json` đạt `success = True`, vượt qua 6/6 Expectations và Freshness SLA đạt `is_fresh = True`.
   - **Về mặt RAG Performance:** Báo cáo `data/results/repaired_metrics.json` ghi nhận `retrieval_hit_rate` và `mean_token_f1` phục hồi trọn vẹn từ mức sụt giảm về lại mức ban đầu (100%).
   - **Về mặt Bằng chứng:** File `data/reports/corruption_report.md` ghi nhận sự đồng thuận tuyệt đối giữa trạng thái Baseline và Repaired.

---

## 8. Phân tích kết quả

### Metrics chính (Số liệu thực nghiệm từ pipeline)

| Metric / Signal | Trạng thái 1: Baseline | Trạng thái 2: Corrupted | Trạng thái 3: Repaired | Nhận xét của cá nhân |
| :--- | :---: | :---: | :---: | :--- |
| **`retrieval_hit_rate`** | **1.0000 (100%)** | **0.5000 (50.0%)** | **1.0000 (100%)** | Dữ liệu bẩn làm mất một nửa khả năng tìm trúng văn bản; sau repair phục hồi tuyệt đối 100%. |
| **`mean_token_f1`** | **1.0000 (100%)** | **0.7788 (77.9%)** | **1.0000 (100%)** | Điểm F1 giảm mạnh 22.1% do mất ngữ cảnh summary; khôi phục hoàn hảo sau repair. |
| **`judge_accuracy`** | **1.0000 (100%)** | **0.8000 (80.0%)** | **1.0000 (100%)** | Độ chính xác câu trả lời sụt giảm 20% khi dữ liệu bị lỗi; lấy lại phong độ sau khi phục hồi. |
| **`mean_judge_score`** | **5.00 / 5.0** | **4.00 / 5.0** | **5.00 / 5.0** | Điểm đánh giá chất lượng giảm xuống 4.0; quay lại mức tối đa 5.0/5.0. |
| **Quality checks (GX 1.x)** | **PASS (6/6)** | **FAIL (3/6 trượt)** | **PASS (6/6)** | GX 1.x phát hiện chính xác vi phạm về số dòng, tính duy nhất và độ dài summary. |
| **Freshness status** | **PASS (4.2% cũ)** | **FAIL (38.1% cũ)** | **PASS (4.2% cũ)** | Dữ liệu bị tiêm lỗi lùi ngày làm tỷ lệ bài cũ vượt ngưỡng 25%; repair đã kéo về ngưỡng an toàn. |

### Kết luận từ số liệu (Causal Chains)

1. **Chuỗi sự cố (Corruption → Quality Alert → AI Degradation):**
   - `Drop 20% latest records` + `Truncate title` + `Blank summary` $\longrightarrow$ Great Expectations báo FAIL (3/6 checks trượt) & Freshness SLA vi phạm (38.1% > 25%) $\longrightarrow$ Vector Store mất mát thông tin dẫn đến `retrieval_hit_rate` sụt giảm nghiêm trọng từ 100% xuống 50%, kéo theo `mean_token_f1` rơi từ 1.0000 xuống 0.7788.
2. **Chuỗi phục hồi (Lineage Anchor → Idempotent Repair → Metric Recovery):**
   - Kích hoạt `repair_from_raw_snapshot()` đọc lại bản gốc `crossref_records.json` $\longrightarrow$ Khôi phục đủ 24 bản ghi sạch, GX checks đạt 6/6 PASS và Freshness đạt 4.2% $\longrightarrow$ ChromaDB collection `papers-repaired` đồng bộ hoàn toàn, đưa `retrieval_hit_rate` và `mean_token_f1` trở lại 100%.

### Corruption nào ảnh hưởng rõ nhất và vì sao?
- **Ảnh hưởng nặng nhất đến Retrieval:** Kịch bản **Drop latest records** và **Truncate title**. Khi tiêu đề bị cắt ngắn dưới 8 ký tự, cơ chế Exact Title Lookup bị vô hiệu hóa hoàn toàn, đồng thời vector embedding bị mất ngữ nghĩa tiêu đề, khiến mô hình tìm sai tài liệu và làm Hit Rate giảm một nửa (50%).
- **Ảnh hưởng nặng nhất đến Answer Quality:** Kịch bản **Blank summary**. Khi tóm tắt bị xóa trắng, ngữ cảnh phục vụ việc trích xuất câu trả lời cho các câu hỏi dạng `summary` không còn, trực tiếp kéo tụt Token F1.

### Kết quả nào khác với kỳ vọng ban đầu?
- Ban đầu tôi dự đoán Token F1 sẽ rơi xuống dưới 50% khi dữ liệu bị tiêm lỗi. Tuy nhiên thực tế Token F1 chỉ giảm về **77.88%**. Khi phân tích sâu vào `corrupted_answers.json`, tôi phát hiện lý do: trong 10 câu hỏi của benchmark, chỉ có 3 câu thuộc dạng `summary` bị triệt tiêu ngữ cảnh; các câu hỏi về `authors`, `date`, `categories` của những bài báo không bị drop vẫn giữ được một phần câu trả lời đúng. Điều này cho thấy hệ thống benchmark phân bổ đa dạng câu hỏi đã phản ánh rất chân thực mức độ ảnh hưởng cục bộ của từng dạng lỗi.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Dữ liệu thô là tài sản vô giá (Raw Preservation is King):** Việc lưu giữ nguyên vẹn payload gốc từ API làm mỏ neo dòng đời (Lineage Anchor) là chìa khóa để tái thiết hệ thống sau sự cố mà không lo phụ thuộc vào nhà cung cấp bên ngoài.
2. **Data Observability ngăn chặn Silent Failure:** Không thể chỉ dựa vào việc code không báo lỗi để khẳng định hệ thống AI hoạt động tốt. Cần các chốt chặn kiểm định định lượng tự động như Great Expectations 1.x và Freshness SLA ngay tại cổng nạp Vector Database.
3. **Tính Idempotent trong Data Engineering:** Mọi pipeline chuyển đổi và sửa lỗi dữ liệu phải được thiết kế bất biến qua nhiều lần chạy, đảm bảo dữ liệu luôn hội tụ về trạng thái chuẩn mực duy nhất.

### Nếu có thêm thời gian
Tôi sẽ xây dựng **Cơ chế Tự động Kích hoạt Phục hồi (Automated Self-Healing / Auto-Repair Pipeline)**: Khi Great Expectations hoặc Freshness SLA phát hiện vi phạm ngưỡng chất lượng tại chốt kiểm soát, hệ thống sẽ tự động gửi cảnh báo webhook và tự động kích hoạt quy trình `repair_from_raw_snapshot()` để rollback/rebuild Vector Store mà không cần kỹ sư phải can thiệp thủ công bằng lệnh CLI.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trịnh Quốc Hoàng  
**Ngày xác nhận:** 2026-09-26  
