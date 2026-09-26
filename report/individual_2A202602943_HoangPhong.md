# Member Role Report - Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Hoàng Phong |
| MSSV | 2A202602943 |
| Khóa/Lớp | K4 / L3B |
| Tên nhóm | ACE |
| Vai trò chính | Data Corruption Suite |
| Repository | K4-L3B-Day10-ACE-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Tiêm sáu kịch bản lỗi | `src/ingestion/corruption.py`, `corrupt_clean_dataframe` | Clean dataframe có schema paper | Corrupted dataframe với các trường dẫn xuất được dựng lại | Hoàn thành |
| Audit log và artifact corrupted | `data/results/corruption_log.json`, dữ liệu corrupted trong `data/clean/` | Clean dataset baseline | Log có paper ID, before/after và số lượng affected | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Bàn giao dữ liệu và audit log cho quality gate, evaluation và corruption flow | Observability, evaluation và pipeline | Các module sau có thể dùng cùng dataset và log để kiểm tra tác động của lỗi |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Xây dựng sáu phép biến đổi dữ liệu xác định được | `src/ingestion/corruption.py` | Drop, blank, noise, truncate, stale date và duplicate rows | Đọc implementation và đối chiếu từng operation trong log |
| Ghi audit log không làm thay đổi input | `data/results/corruption_log.json` | Input 24 dòng, output 21 dòng, 6 operation và các paper ID bị tác động | Kiểm tra các trường `input_rows`, `output_rows`, `operations` |

Output chính: `corruption_log.json` ghi nhận đủ sáu operation với tổng số tác động theo từng operation là 5, 2, 2, 2, 6 và 2. Hàm sao chép dataframe đầu vào, nên dữ liệu clean gốc không bị sửa tại chỗ.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Pipeline cần một bộ dữ liệu lỗi có kiểm soát để chứng minh quality gate phát hiện được vấn đề và để đánh giá ảnh hưởng của dữ liệu bẩn đến retrieval/RAG. Các lỗi phải tái lập được, có paper ID cụ thể và không làm mất khả năng truy vết về bản ghi trước khi biến đổi.

### Cách triển khai

`corrupt_clean_dataframe` kiểm tra schema tối thiểu, tạo bản sao sâu của dataframe và chọn dòng theo quy tắc xác định. Với 24 bản ghi, hàm loại 5 bản ghi mới nhất, làm rỗng 2 summary, chèn noise vào 2 summary, cắt 2 title còn 7 ký tự, lùi ngày 6 bản ghi 365 ngày và nhân bản 2 dòng. Sau các phép biến đổi, hàm dựng lại `summary_chars` và `text_for_embedding`, đồng thời giữ `age_days` nhất quán với ngày đã lùi. Audit log lưu before/after và paper ID cho từng thay đổi.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Clean dataframe có `paper_id`, `title`, `summary`, tác giả, category, `published`, `age_days`, `summary_chars` và `text_for_embedding` |
| Output | Corrupted dataframe; log JSON gồm số dòng đầu vào/đầu ra và sáu operation |
| Module phụ thuộc | `ingestion.cleaning.format_text_for_embedding`, `core.utils.write_json` |
| Module sử dụng output | Quality checks, evaluation và corruption flow |
| Điều kiện lỗi cần xử lý | Thiếu cột bắt buộc, ít hơn 6 dòng, hoặc ngày xuất bản không parse được |

### Cách xác minh

```bash
python -c "from core.config import load_settings; from ingestion.corruption import corrupt_clean_dataframe; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); c=corrupt_clean_dataframe(df, s.paths.corruption_log); print(f'Tín hiệu hoàn thành: Corrupted {len(c)} dòng')"
```

- **Điều kiện môi trường:** Chạy sau khi cài dependencies trong `requirements.txt` và cài project editable, hoặc cấu hình `PYTHONPATH=src` để Python tìm thấy các package nội bộ.
- **Kết quả mong đợi:** In ra tín hiệu hoàn thành với số dòng corrupted và tạo/cập nhật `data/results/corruption_log.json`.
- **Kết quả thực tế:** Artifact hiện có ghi `input_rows = 24`, `output_rows = 21`; sáu operation là `drop_latest_records`, `blank_summary`, `inject_noise`, `truncate_title`, `stale_date`, `duplicate_rows`.
- **Artifact/log:** `data/results/corruption_log.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần tạo corruption đủ rõ để quality gate phát hiện nhưng vẫn giữ được khả năng tái lập và đối chiếu từng bản ghi.
- **Các phương án đã cân nhắc:** Chọn dòng ngẫu nhiên bằng seed; hoặc chọn theo cursor và thứ tự ngày xuất bản cố định.
- **Phương án đã chọn:** Dùng lựa chọn xác định, drop theo ngày mới nhất và ghi đầy đủ before/after.
- **Lý do:** Kết quả lặp lại trên cùng snapshot, dễ audit, dễ so sánh baseline/corrupted và không phụ thuộc trạng thái random của tiến trình.
- **Bằng chứng quyết định phù hợp:** `corruption_log.json` có cùng operation, số lượng và paper ID cụ thể; `corrupt_clean_dataframe` không sửa input tại chỗ.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Corruption có thể làm các trường dẫn xuất như `summary_chars` và `text_for_embedding` giữ giá trị cũ.
- **Lệnh hoặc bước tái hiện:** Đọc implementation của `corrupt_clean_dataframe` sau khi biến đổi summary/title/date.
- **Nguyên nhân gốc:** Các trường dẫn xuất không tự cập nhật khi dataframe bị mutate.
- **Cách xử lý:** Dựng lại `summary_chars` và `text_for_embedding` sau cả sáu phép biến đổi; ép `age_days` và `summary_chars` về kiểu số nguyên.
- **Cách xác minh sau khi sửa:** Đối chiếu code với log và kiểm tra các operation có before/after tương ứng.
- **Điều học được:** Dữ liệu lỗi cần được phản ánh đến cả các trường được dùng để embedding/index, nếu không retrieval có thể vẫn dùng nội dung sạch cũ.

### Blocker còn tồn tại

- **Phạm vi bị ảnh hưởng:** Đánh giá định lượng ba trạng thái và báo cáo comparison.
- **Những gì đã loại trừ:** Không suy diễn các metric RAG từ corruption log; `src/pipelines/corruption_flow.py` và `generate_corruption_report` hiện còn `NotImplementedError`.
- **Bước tiếp theo:** Hoàn thiện corruption flow, tạo `corrupted_metrics.json`, `repaired_metrics.json` và `data/reports/corruption_report.md` bằng cùng evaluation set.

## 7. Hiểu biết về luồng end-to-end

1. Crossref được lưu thành raw snapshot, sau đó cleaning chuẩn hóa bản ghi và tạo `text_for_embedding`; embedding/index dùng văn bản này để đưa tài liệu vào vector store.
2. Evaluation set chứa câu hỏi, loại câu hỏi và ground-truth document IDs. Retrieval được so với các ID này, còn câu trả lời được đối chiếu với ground truth để tính các metric answer quality.
3. Quality checks kiểm tra schema, null, uniqueness và độ dài nội dung. Freshness monitoring tập trung vào `age_days`, tỷ lệ bản ghi quá 180 ngày và ngưỡng SLA.
4. Cùng một test set giúp thay đổi metric phản ánh trạng thái dữ liệu thay vì khác biệt do câu hỏi hoặc ground truth khác nhau.
5. Repair chỉ được xem là thành công khi có dữ liệu repaired dựng lại từ raw, quality/freshness phục hồi và metrics RAG được so sánh với baseline trên cùng test set.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | Chưa có artifact | Chưa có artifact | Chưa có artifact | Chưa thể kết luận suy giảm hoặc phục hồi retrieval |
| `mean_token_f1` | Chưa có artifact | Chưa có artifact | Chưa có artifact | Cần kết quả evaluation thực tế |
| `judge_accuracy` | Chưa có artifact | Chưa có artifact | Chưa có artifact | Chưa có judge output đủ ba trạng thái |
| `mean_judge_score` | Chưa có artifact | Chưa có artifact | Chưa có artifact | Chưa có comparison report để đối chiếu |
| Quality checks | Chưa có artifact gắn ba trạng thái | Chưa có artifact gắn ba trạng thái | Chưa có artifact gắn ba trạng thái | Log chứng minh dữ liệu đã bị biến đổi, không tự nó là quality result |
| Freshness status | Chưa có artifact gắn ba trạng thái | Có chủ đích tạo stale date | Chưa có artifact | Cần chạy quality/freshness trên từng trạng thái |

### Kết luận từ số liệu

1. Drop latest records, blank summary, truncate title, stale date và duplicate rows làm thay đổi số dòng hoặc nội dung/schema của dữ liệu; `corruption_log.json` xác nhận sáu operation và là bằng chứng đầu vào cho quality/freshness evaluation. Chưa có corrupted metrics nên chưa khẳng định mức giảm của agent metric.
2. Repair dự kiến dựng lại dữ liệu từ raw records, nhưng hiện chưa có `repaired_metrics.json` và comparison report để chứng minh mức phục hồi. Vì vậy chưa kết luận repair đã phục hồi RAG.

Chưa thể xác định corruption nào ảnh hưởng rõ nhất đến agent vì chưa có metrics ba trạng thái. Về mặt dữ liệu, `drop_latest_records` làm giảm coverage từ 24 xuống 19 trước khi duplicate rows đưa output lên 21; `blank_summary` và `truncate_title` trực tiếp làm mất thông tin dùng cho embedding, còn `stale_date` tác động đến freshness SLA.

Kết quả cần kiểm tra thêm là output có 21 dòng thay vì 24: đây là hệ quả kết hợp của drop 5 dòng và duplicate 2 dòng, không phải lỗi đếm. Log đã xác nhận các con số này.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Corruption cần deterministic và có audit log để cùng một snapshot luôn tạo ra cùng phạm vi lỗi.
2. Khi mutate dữ liệu, phải dựng lại các cột dẫn xuất trước khi quality check hoặc embedding; nếu không artifact sẽ không phản ánh lỗi thật.
3. Corruption log chứng minh dữ liệu đã thay đổi, nhưng chỉ metrics trên cùng evaluation set mới chứng minh được ảnh hưởng đến RAG.

### Nếu có thêm thời gian

Hoàn thiện `corruption_flow.py` và `generate_corruption_report`, sau đó chạy baseline/corrupted/repaired trong cùng cấu hình. Đo đầy đủ retrieval hit rate, token F1, judge metrics, quality và freshness; bổ sung test kiểm tra tính deterministic và bảo đảm clean input không bị mutate.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh phần việc Data Corruption Suite được khai báo trong `docs/TEAM.md`.
- [x] Tôi phân biệt artifact đã kiểm chứng với metric chưa có.
- [x] Tôi không khẳng định RAG suy giảm hoặc repair thành công khi chưa có số liệu tương ứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này tập trung vào phần việc của Hoàng Phong, không sao chép báo cáo nhóm.

**Họ và tên:** Hoàng Phong
**MSSV:** 2A202602943
**Ngày xác nhận:** 2026-09-26
