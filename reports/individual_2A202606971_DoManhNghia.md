# Báo cáo cá nhân — Đỗ Mạnh Nghĩa

> Day 10: Data Pipeline & Data Observability.

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Đỗ Mạnh Nghĩa |
| MSSV | 2A202606971 |
| Khóa/Lớp | K4 / L3B |
| Tên nhóm | ACE — 5 thành viên |
| Vai trò chính | Trưởng nhóm; Thu thập dữ liệu & Cất giữ bản gốc; Làm sạch dữ liệu & Chuẩn bị văn bản tạo vector |
| Repository | https://github.com/Tuienn/K4-L3B-Day10-ACE-DataPipelineDataObservability |
| Ngày lập báo cáo | 2026-09-26 |
| Tỷ lệ đóng góp | 20%, theo phân bổ thống nhất tại `docs/TEAM.md` |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Ingestion và lưu raw — CP0 | `src/ingestion/crossref.py`: `parse_crossref_payload`, `fetch_source_records`, `load_raw_records` | Crossref API hoặc snapshot JSON | Raw response và raw records trong `data/raw/` | Hoàn thành; đã kiểm tra đọc và parse snapshot |
| Cleaning và chuẩn bị embedding — CP1 | `src/ingestion/cleaning.py`: `build_clean_dataframe`, `format_text_for_embedding` | `PaperRecord` và ngày chạy | DataFrame sạch; CSV/JSON trong `data/clean/` | Hoàn thành; đã kiểm tra nội dung và tính lặp lại |
| Điều phối nhóm | Phân công tại `docs/TEAM.md` | Yêu cầu checkpoint và phần việc của 5 thành viên | Owner, thứ tự bàn giao và tỷ lệ đóng góp rõ ràng | Đã ghi nhận trong hồ sơ nhóm |

Tôi phụ trách ingestion và cleaning. Quality Gate, benchmark, baseline orchestration, corruption và comparison flow thuộc các thành viên được phân công; tôi phối hợp qua dữ liệu đầu vào và contract chung.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động phối hợp | Thành viên/module liên quan | Nội dung bàn giao |
|---|---|---|
| Thống nhất trường kiểm định và benchmark | Vũ Minh Trí — quality/testset | `paper_id`, `summary`, `age_days` và metadata sạch |
| Thống nhất đầu vào embedding/index | Nguyễn Ngọc Tuyền — baseline | `text_for_embedding`, metadata và ID ổn định |
| Cung cấp dữ liệu nền cho thực nghiệm | Hoàng Phong — corruption | Cleaned dataset để tạo bản sao tiêm lỗi |
| Cung cấp nguồn phục hồi | Trịnh Quốc Hoàng — repair | Raw records và hàm cleaning dùng lại khi repair |

Các dòng trên mô tả phạm vi phối hợp theo phân công, không nhận ownership mã nguồn của thành viên khác.

## 3. Kết quả theo vai trò

| Nhiệm vụ | File/hàm/artifact | Kết quả kiểm tra | Cách xác minh |
|---|---|---|---|
| Parse Crossref | `parse_crossref_payload`; `data/raw/crossref_response.json` | 24 items chuyển thành 24 records | Đọc snapshot và gọi parser |
| Đọc raw records | `load_raw_records`; `data/raw/crossref_records.json` | 24 records | Nạp JSON qua hàm của module |
| Làm sạch | `build_clean_dataframe`; `data/clean/papers_clean.json` | DataFrame dựng lại và JSON hiện có đều có 24 dòng; ID duy nhất; không có title rỗng | Kiểm tra số dòng, ID và title |
| Chuẩn hóa văn bản | `_clean_text`, `_clean_str` | Không còn thẻ XML trong title/summary dựng lại; mẫu JATS xử lý đúng | Kiểm tra pattern thẻ và mẫu cụ thể |
| Tạo văn bản embedding | `format_text_for_embedding` | Mỗi dòng đủ 5 nhãn Title, Authors, Published, Categories, Summary | Kiểm tra từng chuỗi |
| Tính lặp lại và deduplicate | `build_clean_dataframe` | Chạy lại cùng raw/ngày hoặc thêm một record trùng đều cho DataFrame giống nhau | So sánh `DataFrame.equals` |
| Tính tuổi dữ liệu | `age_days`; `data/quality/test_quality_report.json` | Tại 2026-09-26: tuổi 66–182 ngày; 1/24 dòng quá 180 ngày | Tính lại từ raw và đọc quality artifact |

Output quan trọng nhất của tôi là dữ liệu sạch với định danh ổn định và văn bản embedding đủ ngữ cảnh. Raw được giữ riêng để tái dựng dữ liệu sau corruption, tránh lấy bản đã bị lỗi làm nguồn repair.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Crossref trả dữ liệu lồng nhau: title có thể là danh sách, abstract chứa JATS/XML, ngày thiếu tháng/ngày và metadata không đầy đủ. Nạp trực tiếp vào embedding có thể đưa cả nhiễu văn bản và bản ghi trùng vào chỉ mục. Tôi chuẩn hóa dữ liệu thành contract chung trước khi downstream sử dụng.

### Cách triển khai

1. Parser đọc `message.items`, lấy DOI làm `paper_id`, bỏ records thiếu DOI/title. Ghép tên tác giả từ `given` và `family`, chuyển subject thành categories và dùng URL DOI khi thiếu URL.
2. Thay thẻ XML/HTML bằng khoảng trắng rồi chuẩn hóa whitespace để tránh dính từ khi bỏ thẻ.
3. Trích ngày từ `date-parts`, mặc định tháng/ngày là 1 khi thiếu; hỗ trợ `date-time`. Published được lấy theo thứ tự published → created → deposited.
4. Fetch dùng snapshot nếu đã có và không yêu cầu refresh. Nhánh gọi API có timeout và retry cho 429 cùng các lỗi server được cấu hình; nếu không lấy được payload thì fallback snapshot. Thiếu cả hai nguồn sẽ phát sinh lỗi rõ ràng.
5. Cleaning chuẩn hóa authors/categories, tạo các cột joined, tính `summary_chars` và `age_days = max(0, run_date - published)` theo ngày.
6. Ghép `text_for_embedding` thành 5 phần; khử trùng lặp theo `paper_id`, giữ dòng đầu tiên và sắp xếp ổn định theo published giảm dần.

**Giới hạn hiện tại:** Ngày thiếu/không parse được đang nhận `age_days = 0`; ngày tương lai cũng bị đưa về 0. Điều này có thể che khuất lỗi freshness, nên cần kiểm định ngày riêng. Summary rỗng được chuyển cho Quality Gate kiểm tra, không bị cleaning tự động loại bỏ.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | Crossref payload hoặc list `PaperRecord`; `run_date` cố định khi cần tái hiện |
| Raw schema | `paper_id`, `title`, `summary`, `authors`, `categories`, `primary_category`, `published`, `updated`, `abs_url`, `pdf_url`, `comment` |
| Clean output | Metadata và `authors_joined`, `categories_joined`, `age_days`, `summary_chars`, `text_for_embedding` |
| Module phụ thuộc | `src/core/config.py`, `src/core/utils.py`, pandas, requests |
| Module sử dụng output | Quality Gate, testset, retrieval/index, baseline và repair flow |
| Điều kiện lỗi | API timeout/429, thiếu snapshot hoặc JSON lỗi, thiếu DOI/title, ngày sai, records trùng |

### Cách xác minh

Lệnh PowerShell sau tái hiện các kiểm tra chính đã thực hiện từ gốc repository; cố định ngày để kết quả không phụ thuộc thời điểm chạy:

```powershell
@'
import sys
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path('src').resolve()))
from ingestion.crossref import load_raw_records, _clean_text, _extract_date
from ingestion.cleaning import build_clean_dataframe
records = load_raw_records(Path('data/raw/crossref_records.json'))
run_date = datetime(2026, 9, 26, tzinfo=timezone.utc)
df = build_clean_dataframe(records, run_date)
assert len(df) == 24 and df.paper_id.is_unique
assert not df.title.eq('').any()
assert not df.title.str.contains(r'<[^>]+>').any()
assert not df.summary.str.contains(r'<[^>]+>').any()
assert df.text_for_embedding.map(lambda text: all(
    label in text for label in ('Title:', 'Authors:', 'Published:', 'Categories:', 'Summary:')
)).all()
assert df.equals(build_clean_dataframe(records, run_date))
assert df.equals(build_clean_dataframe(records + records[:1], run_date))
assert _clean_text('<jats:p>  Retrieval   augmented </jats:p>') == 'Retrieval augmented'
assert _extract_date({'date-parts': [[2026]]}) == '2026-01-01'
print(f'Clean rows={len(df)}, stale_rows={int((df.age_days > 180).sum())}')
'@ | & ../.venv/Scripts/python.exe -
```

- **Kết quả mong đợi:** Đọc đủ dữ liệu, ID duy nhất, văn bản đúng cấu trúc và cleaning lặp lại nhất quán.
- **Kết quả thực tế:** Các kiểm tra tương ứng đạt; 24 dòng sạch, 1 dòng quá 180 ngày tại ngày đối chiếu.
- **Bằng chứng:** Mã nguồn ingestion/cleaning, 2 raw JSON, clean CSV/JSON và kết quả kiểm tra trực tiếp trên snapshot. Lần đối chiếu này không kiểm thử nhánh API trực tuyến hoặc toàn tuyến RAG.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần tái hiện baseline và có nguồn tin cậy cho repair.
- **Các phương án:** Luôn gọi API mới mỗi lần chạy; hoặc giữ snapshot và chỉ refresh khi được yêu cầu.
- **Lựa chọn:** Lưu raw response và raw records riêng; mặc định dùng snapshot sẵn có, refresh có kiểm soát và fallback khi API không khả dụng.
- **Lý do:** Nguồn sống thay đổi có thể làm lệch phép so sánh. Snapshot giữ đầu vào ổn định, giảm phụ thuộc mạng và bảo toàn lineage; đổi lại cần monitoring để phát hiện dữ liệu cũ.
- **Bằng chứng:** Snapshot parse được 24 records; cùng raw và ngày cho kết quả cleaning giống nhau. Đây là bằng chứng cho cleaning, chưa chứng minh toàn bộ repair/index idempotent.

## 6. Một vấn đề dữ liệu đã xử lý

- **Triệu chứng:** Abstract có thể chứa `<jats:p>` và khoảng trắng thừa, đưa markup không cần thiết vào embedding.
- **Tái hiện:** Truyền `<jats:p>  Retrieval   augmented </jats:p>` vào `_clean_text`.
- **Nguyên nhân gốc:** Abstract được biểu diễn bằng văn bản có markup; đọc JSON không tự bỏ thẻ.
- **Xử lý:** Thay thẻ bằng khoảng trắng rồi chuẩn hóa bằng `split()` và `join()`; áp dụng chuẩn hóa tương tự trong cleaning.
- **Xác minh:** Mẫu trả về `Retrieval augmented`; title/summary của 24 dòng dựng lại không chứa pattern thẻ XML.
- **Điều học được:** Số lượng records chưa đủ chứng minh đầu vào embedding tốt; cần kiểm tra nội dung. Đây là tình huống dữ liệu đã kiểm tra, không phải trích dẫn exception runtime.

## 7. Hiểu biết về luồng end-to-end

1. **Crossref đến index:** Lưu payload raw → parse records → cleaning metadata/văn bản → quality/freshness → MiniLM embedding → ChromaDB với ID gắn `paper_id`.
2. **Evaluation:** Benchmark gồm câu hỏi, đáp án tham chiếu và document IDs. Hit Rate đo retrieval đúng tài liệu; Token F1 đo trùng token đáp án; judge metrics đánh giá câu trả lời theo bộ chấm được cấu hình.
3. **Quality và freshness:** Quality xét null, unique, độ dài và số dòng; freshness xét tuổi dữ liệu. Dữ liệu có thể đủ trường nhưng vẫn quá cũ.
4. **Cùng test set:** Giữ câu hỏi, ground truth và cấu hình ổn định để đánh giá tác động của trạng thái dữ liệu, tránh thay cả đề và dữ liệu cùng lúc.
5. **Repair thành công:** Cần kiểm tra clean repaired, quality/freshness, index, metrics so với baseline và tính lặp lại. Lệnh chạy xong chưa đủ chứng minh phục hồi.

## 8. Phân tích kết quả

### Kết quả có bằng chứng cho phần việc cá nhân

Tại 2026-09-26, dữ liệu dựng lại có 24 dòng, ID duy nhất, tuổi 66–182 ngày. Có 1/24 bài quá 180 ngày, khoảng 4,17%, dưới ngưỡng 25%.

`data/quality/test_quality_report.json` hiện có ghi `gx_success = true`, 6/6 expectations thành công và `is_fresh = true`. Đây là báo cáo với `report_name = test`, không phải kết quả đánh giá toàn bộ baseline RAG.

### Metrics chính của 3 trạng thái

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
|---|---|---|---|---|
| `retrieval_hit_rate` | Chưa có artifact | Chưa có artifact | Chưa có artifact | Chưa kết luận suy giảm/phục hồi retrieval |
| `mean_token_f1` | Chưa có artifact | Chưa có artifact | Chưa có artifact | Chưa kết luận chất lượng câu trả lời |
| `judge_accuracy` | Chưa có artifact | Chưa có artifact | Chưa có artifact | Cần kết quả judge cùng cấu hình |
| `mean_judge_score` | Chưa có artifact | Chưa có artifact | Chưa có artifact | Cần kết quả judge cùng cấu hình |
| Quality checks | Chưa có báo cáo gắn trạng thái | Chưa có báo cáo gắn trạng thái | Chưa có báo cáo gắn trạng thái | Quality test hiện có đạt 6/6 |
| Freshness status | Chưa có báo cáo gắn trạng thái | Chưa có báo cáo gắn trạng thái | Chưa có báo cáo gắn trạng thái | Dữ liệu sạch đối chiếu có stale ratio khoảng 4,17% |

Artifact đánh giá 3 trạng thái chưa có trong bản repository được đọc khi lập báo cáo. Tôi không điền số liệu giả hoặc dùng quality test thay metrics RAG.

### Chuỗi nguyên nhân và bằng chứng cần đối chiếu

1. **Giả thuyết:** Xóa summary/mất records → độ dài văn bản/số dòng thay đổi → context thiếu thông tin → Hit Rate hoặc Token F1 có thể giảm. Cần corruption log, quality report và metrics để xác nhận.
2. **Giả thuyết:** Dựng clean từ raw rồi rebuild index → nội dung được khôi phục → metrics có thể trở về gần baseline. Cần repaired artifacts và comparison report để xác nhận.

Chưa đủ số liệu xác định lỗi nào ảnh hưởng mạnh nhất hoặc kết quả RAG nào khác kỳ vọng. Với freshness, một bài quá 180 ngày vẫn có thể cùng tồn tại với `is_fresh = true`, vì SLA xét tỷ lệ quá hạn của toàn dataset.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Raw snapshot, ID ổn định và contract rõ ràng giúp phối hợp, tái hiện và phục hồi dữ liệu.
2. Cleaning và kiểm định có vai trò khác nhau; cần kiểm tra nội dung, độ mới và ngày không hợp lệ, ngoài trạng thái chạy lệnh.
3. Văn bản embedding phải giữ thông tin cần trả lời; dữ liệu thiếu/nhiễu có thể khiến RAG trả lời sai dù retrieval và LLM vẫn hoạt động.

### Nếu có thêm thời gian

Tôi sẽ bổ sung trạng thái ngày hợp lệ và kiểm định ngày thiếu/sai/tương lai, tránh `age_days = 0` che khuất lỗi freshness. Đo cải thiện bằng tập records có lỗi ngày, kiểm tra tỷ lệ phát hiện và bảo đảm records hợp lệ giữ nguyên kết quả. Tôi cũng muốn thêm fingerprint raw để xác nhận các lần so sánh dùng cùng snapshot.

## 10. Cam kết của thành viên

Báo cáo phân biệt phần việc theo TEAM.md, kết quả kiểm tra trực tiếp và phần chưa có artifact. Các mục về mức hiểu dành cho tôi tự rà soát trước khi nộp:

- [ ] Tôi đã rà soát và xác nhận đúng phần việc, mức hiểu của mình.
- [ ] Tôi có thể giải thích luồng end-to-end và phần ingestion/cleaning.
- [x] Kết quả định lượng có nguồn đối chiếu; phần chưa có metrics được nêu rõ.
- [x] Báo cáo không khẳng định toàn tuyến RAG đã chạy thành công khi chưa có bằng chứng.
- [x] Báo cáo không chứa nội dung `.env`, API key, token hoặc secret.
- [x] Nội dung được viết riêng cho vai trò của Đỗ Mạnh Nghĩa.

**Họ và tên:** Đỗ Mạnh Nghĩa  
**Ngày lập báo cáo:** 2026-09-26
