# Hồ Sơ Nhóm ACE — Data Pipeline & Data Observability

- **Tên nhóm:** ACE
- **Khóa / Lớp / Buổi học:** K4 / L3B / Day 10
- **Repository:** `K4-L3B-Day10-ACE-DataPipelineDataObservability`
- **Số lượng thành viên:** 5
- **Trưởng nhóm:** Đỗ Mạnh Nghĩa — 2A202606971
- **Đề tài:** Xây dựng pipeline dữ liệu cho RAG, kiểm soát chất lượng và độ mới của dữ liệu, tiêm lỗi thực nghiệm, phục hồi và đối chiếu Baseline – Corrupted – Repaired.

## 1. Danh sách thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò cụ thể | Phạm vi phụ trách | Checkpoint |
|---:|---|---|---|---|---|
| 1 | Đỗ Mạnh Nghĩa | 2A202606971 | Trưởng nhóm; Thu thập dữ liệu & Cất giữ bản gốc; Làm sạch dữ liệu & Chuẩn bị văn bản tạo vector | Điều phối nhóm; `src/ingestion/crossref.py`, `src/ingestion/cleaning.py` | CP0, CP1; điều phối CP6 |
| 2 | Vũ Minh Trí | 2A202602629 | Thiết lập chốt kiểm soát dữ liệu (Observability Gate); Tạo bộ đề đánh giá chuẩn (Benchmark Test Set) | `src/observability/quality.py` với Great Expectations 1.x và Freshness SLA; `src/evaluation/testset.py` | CP1, CP2; hỗ trợ CP4, CP5 |
| 3 | Nguyễn Ngọc Tuyền | 2A202603010 | Chạy toàn tuyến dữ liệu sạch (Baseline Pipeline) | `script/run_phase1.py`, `src/pipelines/phase1.py`; tích hợp embedding, ChromaDB, RAG và đánh giá baseline | CP2, CP3 |
| 4 | Hoàng Phong | 2A202602943 | Tiêm lỗi dữ liệu thực nghiệm (Data Corruption Suite) | `src/ingestion/corruption.py`; 6 kịch bản lỗi, dữ liệu corrupted và nhật ký tiêm lỗi | CP4 |
| 5 | Trịnh Quốc Hoàng | 2A202602847 | Đo lường suy giảm, phục hồi dữ liệu & Đối chiếu 3 trạng thái | `script/run_corruption_flow.py`, `src/pipelines/corruption_flow.py`; tích hợp `src/evaluation/metrics.py`, `src/observability/reporting.py` | CP4, CP5 |

Tất cả thành viên cùng tham gia CP6: chuẩn bị demo, giải thích luồng end-to-end và đối chiếu sản phẩm bàn giao. Phân công theo deliverable; người phụ trách chính phối hợp với các thành viên liên quan để bảo đảm input/output giữa các bước nhất quán.

## 2. Tự khai báo phần việc và sản phẩm bàn giao

Phần dưới đây tổng hợp phần việc hoàn thành theo thông tin khai báo của nhóm. Các đường dẫn là sản phẩm bàn giao tương ứng, không phải bảng xác nhận trạng thái đồng bộ lên repository hoặc kết quả kiểm thử tại thời điểm cập nhật hồ sơ.

### Đỗ Mạnh Nghĩa — 2A202606971

**Vai trò:** Trưởng nhóm; phụ trách ingestion và cleaning.

**Công việc đã hoàn thành:**

- Điều phối phân công, thống nhất raw schema, clean schema, định danh `paper_id` và đường dẫn artifact dùng chung.
- Hoàn thiện thu thập và phân tích payload Crossref trong `src/ingestion/crossref.py`, hỗ trợ đọc snapshot cục bộ khi nguồn trực tuyến không khả dụng.
- Lưu raw response và raw records để bảo toàn nguồn gốc dữ liệu và cung cấp đầu vào đáng tin cậy cho bước repair.
- Hoàn thiện `src/ingestion/cleaning.py`: loại bỏ JATS/XML và khoảng trắng thừa, xử lý trường thiếu, khử trùng lặp theo `paper_id`, chuẩn hóa ngày xuất bản, tính `age_days` và tạo `text_for_embedding`.
- Bàn giao dữ liệu sạch cho kiểm định, tạo benchmark và xây dựng chỉ mục vector.

**Đầu vào:** Crossref API hoặc snapshot `data/raw/crossref_response.json`.

**Sản phẩm bàn giao:** `data/raw/crossref_response.json`, `data/raw/crossref_records.json`, `data/clean/papers_clean.csv`, `data/clean/papers_clean.json`.

**Cách đối chiếu:** Kiểm tra raw snapshot, schema dữ liệu sạch, tính duy nhất của `paper_id`, cách tính `age_days` và cấu trúc văn bản embedding.

### Vũ Minh Trí — 2A202602629

**Vai trò:** Phụ trách Observability Gate và Benchmark Test Set.

**Công việc đã hoàn thành:**

- Hoàn thiện `src/observability/quality.py` theo API Great Expectations 1.x với ephemeral context và pandas dataframe batch.
- Thiết lập 4 nhóm kiểm định: số lượng bản ghi, trường không được rỗng, định danh duy nhất và độ dài văn bản.
- Tích hợp Freshness SLA: xác định dữ liệu cũ khi `age_days > 180`, cảnh báo khi tỷ lệ dữ liệu cũ vượt 25%; phân biệt kết quả chất lượng với trạng thái freshness.
- Hoàn thiện `src/evaluation/testset.py`, xây dựng benchmark 10 câu hỏi bao phủ `summary`, `authors`, `date`, `categories`, kèm ground truth và định danh tài liệu liên quan.
- Bàn giao một evaluation set dùng chung cho baseline, corrupted và repaired để bảo đảm phép so sánh nhất quán.

**Đầu vào:** Cleaned dataset và dữ liệu từng trạng thái cần kiểm định.

**Sản phẩm bàn giao:** `data/eval/test_set.json`; báo cáo trong `data/quality/`, gồm `baseline_quality_report.json`, `corrupted_quality_report.json`, `freshness_report.json`.

**Cách đối chiếu:** Kiểm tra cấu hình GX 1.x, kết quả từng expectation, ngưỡng Freshness SLA và độ bao phủ benchmark.

### Nguyễn Ngọc Tuyền — 2A202603010

**Vai trò:** Phụ trách chạy toàn tuyến dữ liệu sạch (Baseline Pipeline).

**Công việc đã hoàn thành:**

- Tích hợp luồng baseline trong `src/pipelines/phase1.py` và entrypoint `script/run_phase1.py`.
- Kết nối ingestion → cleaning → quality/freshness → embedding/index → RAG → evaluation → báo cáo pha 1.
- Tích hợp các module `src/retrieval/` để tạo embedding bằng `sentence-transformers/all-MiniLM-L6-v2`, nạp collection `papers-baseline` trong ChromaDB và truy vấn RAG trên dữ liệu sạch.
- Sử dụng benchmark do Vũ Minh Trí bàn giao để ghi nhận metrics và câu trả lời baseline làm mốc so sánh.
- Kiểm tra sự nhất quán giữa đường dẫn cấu hình, dữ liệu sạch, chỉ mục vector và báo cáo pha 1.

**Đầu vào:** Raw/cleaned dataset, cấu hình pipeline, Quality Gate và benchmark.

**Sản phẩm bàn giao:** `data/embeddings/papers_embeddings.json`, collection `papers-baseline` trong `data/chroma/`, `data/results/baseline_metrics.json`, `data/results/baseline_answers.json`, `data/reports/phase1_report.md`.

**Cách đối chiếu:** Chạy `python script/run_phase1.py`, kiểm tra artifact baseline và đối chiếu metrics với báo cáo pha 1.

### Hoàng Phong — 2A202602943

**Vai trò:** Phụ trách tiêm lỗi dữ liệu thực nghiệm (Data Corruption Suite).

**Công việc đã hoàn thành:**

- Hoàn thiện `src/ingestion/corruption.py`, tạo dữ liệu lỗi từ bản sao dữ liệu sạch, bảo toàn raw snapshot dùng để phục hồi.
- Triển khai 6 kịch bản: mất 20% bản ghi mới nhất, xóa rỗng tóm tắt, chèn nhiễu vào tóm tắt, cắt ngắn tiêu đề dưới 8 ký tự, lùi ngày xuất bản và nhân bản dòng dữ liệu.
- Cập nhật các trường dẫn xuất chịu ảnh hưởng, gồm `age_days` và `text_for_embedding`, để lỗi dữ liệu được phản ánh vào đầu vào kiểm định và retrieval.
- Ghi nhật ký tiêm lỗi, mô tả dạng lỗi và phạm vi bản ghi bị tác động.
- Bàn giao dữ liệu corrupted cho bước đánh giá suy giảm, kiểm định quality/freshness và phục hồi.

**Đầu vào:** Cleaned dataset baseline.

**Sản phẩm bàn giao:** `data/clean/papers_clean_corrupted.csv`, `data/clean/papers_clean_corrupted.json`, `data/results/corruption_log.json`.

**Cách đối chiếu:** Đọc corruption log, đối chiếu dữ liệu trước/sau tiêm lỗi và kiểm tra đủ 6 kịch bản.

### Trịnh Quốc Hoàng — 2A202602847

**Vai trò:** Phụ trách đo lường suy giảm, phục hồi dữ liệu và đối chiếu 3 trạng thái.

**Công việc đã hoàn thành:**

- Tích hợp luồng corrupted → evaluate → repair → evaluate → compare trong `src/pipelines/corruption_flow.py` và `script/run_corruption_flow.py`.
- Tạo chỉ mục riêng cho `papers-corrupted` và `papers-repaired`, sử dụng cùng evaluation set và cấu hình đánh giá với baseline.
- Đo lường `retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`, `mean_judge_score`; đối chiếu thêm tín hiệu quality và freshness.
- Phục hồi dữ liệu bằng cách dựng lại dữ liệu sạch từ raw records qua cleaning; kiểm tra tính idempotent để chạy repair nhiều lần không tạo thêm bản ghi hoặc làm sai lệch dữ liệu.
- Tích hợp `src/evaluation/metrics.py` và `src/observability/reporting.py` để xuất bảng Baseline – Corrupted – Repaired, phân tích tác động của lỗi và mức phục hồi dựa trên kết quả pipeline.

**Đầu vào:** Baseline metrics, dữ liệu corrupted, corruption log, raw snapshot và benchmark chung.

**Sản phẩm bàn giao:** Dữ liệu repaired trong `data/clean/`; embedding corrupted/repaired trong `data/embeddings/`; `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, answer artifacts tương ứng và `data/reports/corruption_report.md`.

**Cách đối chiếu:** Chạy `python script/run_corruption_flow.py`, so sánh metrics của 3 trạng thái trên cùng test set, kiểm tra dữ liệu repaired và tính nhất quán của báo cáo.

## 3. Bảng tự chấm tỷ lệ đóng góp

Nhóm thống nhất tự đánh giá tỷ lệ đóng góp bằng nhau: mỗi thành viên **20%**, tổng cộng **100%**. Tỷ lệ phản ánh phần việc kỹ thuật, phối hợp tích hợp, kiểm tra sản phẩm và chuẩn bị trình bày; không quy đổi trực tiếp số lượng file hoặc commit thành điểm học phần.

| STT | Họ và tên | MSSV | Cơ sở tự đánh giá | Tỷ lệ đóng góp | Ý kiến thống nhất |
|---:|---|---|---|---:|---|
| 1 | Đỗ Mạnh Nghĩa | 2A202606971 | Điều phối nhóm; thu thập, lưu raw snapshot, làm sạch và chuẩn hóa dữ liệu | 20% | Đồng ý phân bổ 20% mỗi thành viên |
| 2 | Vũ Minh Trí | 2A202602629 | Quality Gate GX 1.x, Freshness SLA và benchmark dùng chung | 20% | Đồng ý phân bổ 20% mỗi thành viên |
| 3 | Nguyễn Ngọc Tuyền | 2A202603010 | Tích hợp baseline; embedding/index, RAG, metrics và báo cáo pha 1 | 20% | Đồng ý phân bổ 20% mỗi thành viên |
| 4 | Hoàng Phong | 2A202602943 | Triển khai 6 kịch bản tiêm lỗi, dữ liệu corrupted và corruption log | 20% | Đồng ý phân bổ 20% mỗi thành viên |
| 5 | Trịnh Quốc Hoàng | 2A202602847 | Đánh giá suy giảm, repair idempotent và báo cáo đối chiếu 3 trạng thái | 20% | Đồng ý phân bổ 20% mỗi thành viên |
| | **Tổng cộng** | | **5 thành viên thống nhất cách phân bổ** | **100%** | **Thống nhất toàn nhóm** |

## 4. Nguyên tắc phối hợp chung

- Dùng chung schema, định danh tài liệu và đường dẫn trong `src/core/config.py`; giữ tương thích chữ ký hàm giữa các module.
- Bàn giao theo thứ tự: raw → clean → quality/benchmark → baseline → corruption → repair → comparison report.
- Dùng cùng evaluation set cho 3 trạng thái; tách collection vector để kết quả so sánh không bị trộn dữ liệu.
- Số liệu trong báo cáo lấy từ artifact sinh bởi pipeline; không sửa tay metrics hoặc suy diễn kết quả từ tỷ lệ đóng góp.
- Mỗi thành viên chịu trách nhiệm phần việc của mình và có khả năng giải thích luồng end-to-end, tác động của corruption, tín hiệu phát hiện lỗi và cách xác minh repair.
