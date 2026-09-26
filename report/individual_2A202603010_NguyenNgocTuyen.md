# Báo cáo cá nhân — Nguyễn Ngọc Tuyền

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Nguyễn Ngọc Tuyền |
| MSSV | 2A202603010 |
| Khóa / Lớp | K4 / L3B |
| Nhóm | ACE |
| Bài lab | Day 10 — Data Pipeline & Data Observability |
| Phần việc | Bước 6 trong `phases.txt`: Chạy toàn tuyến dữ liệu sạch (Baseline Pipeline) |
| Checkpoint liên quan | CP2, CP3 |
| Repository | [K4-L3B-Day10-ACE-DataPipelineDataObservability](https://github.com/Tuienn/K4-L3B-Day10-ACE-DataPipelineDataObservability) |
| Commit bàn giao cá nhân | [`9413848`](https://github.com/Tuienn/K4-L3B-Day10-ACE-DataPipelineDataObservability/commit/9413848a91a67081936bab89cce84306656b5766) — Implement step 6 baseline pipeline orchestration |
| Nhánh bàn giao | `tuienn` |
| Ngày lập báo cáo | 26/09/2026 |

Báo cáo tập trung vào phần điều phối baseline mà tôi phụ trách. Số liệu được đối chiếu từ các artifact hiện có trong repository sau khi nhóm tích hợp. Lần lập báo cáo này không chạy lại toàn bộ pipeline hoặc tạo lại metrics.

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

Tôi phụ trách nối các module của nhóm thành một luồng baseline hoàn chỉnh theo bước 6. Đầu ra của bước này là mốc tham chiếu để nhóm đánh giá sự suy giảm khi tiêm lỗi và mức phục hồi sau repair.

| Module / Deliverable | File / Hàm | Đầu vào | Đầu ra | Trạng thái |
| --- | --- | --- | --- | --- |
| Điều phối baseline | `src/pipelines/phase1.py` — `run_phase1_pipeline(settings)` | Settings và các module ingestion, cleaning, retrieval, evaluation, observability | Dữ liệu sạch, index, kết quả đánh giá, quality/freshness và báo cáo pha 1 | Đã bàn giao code; bản tích hợp có artifact baseline |
| Điểm vào chương trình | `main()` trong `src/pipelines/phase1.py`, được `script/run_phase1.py` gọi | Cấu hình qua `load_settings()` | Chạy luồng baseline từ terminal | Sử dụng entrypoint có sẵn, không cần thay đổi script trong commit cá nhân |
| Kiểm tra hợp đồng dữ liệu | Logic điều phối trong commit `9413848` | Clean DataFrame và evaluation set | Phát hiện dữ liệu sạch rỗng, bộ đề rỗng hoặc tham chiếu đến bài không còn tồn tại | Đã kiểm thử trên bản bàn giao cá nhân |

Commit cá nhân `9413848` chỉ thay đổi `src/pipelines/phase1.py`. Bản đang có trên `main` đã được nhóm tích hợp và cập nhật tiếp; báo cáo phân biệt đóng góp ban đầu của tôi với kết quả chung của phiên bản hiện tại.

### Phối hợp với các thành viên

- **Đỗ Mạnh Nghĩa:** bàn giao ingestion và cleaning; thống nhất cách đọc raw records, schema DataFrame và cột `text_for_embedding`.
- **Vũ Minh Trí:** bàn giao quality/freshness checks và bộ đề 10 câu hỏi; thống nhất đầu vào kiểm định và ground-truth document IDs.
- **Trịnh Quốc Hoàng:** phối hợp phần evaluation/reporting và đầu ra baseline để dùng trong luồng so sánh ba trạng thái.
- **Hoàng Phong:** sử dụng dữ liệu sạch làm đầu vào cho corruption; phần tiêm lỗi thuộc phạm vi của thành viên này.

Tôi không nhận phần triển khai thuật toán cleaning, các expectations GX, sáu kịch bản corruption hoặc repair là công việc cá nhân của mình.

## 3. Kết quả theo vai trò

### Sản phẩm bàn giao

| Công việc | Kết quả / Bằng chứng |
| --- | --- |
| Nối các bước xử lý bằng API có sẵn | Commit `9413848` có hàm `run_phase1_pipeline(settings)` và `main()` |
| Lưu dữ liệu sạch để các bước sau sử dụng | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` |
| Kết nối embedding và ChromaDB | `data/embeddings/papers_embeddings.json` ghi 24 tài liệu, collection `papers-baseline`, model `sentence-transformers/all-MiniLM-L6-v2` |
| Kết nối đánh giá baseline | `data/results/baseline_metrics.json`, `data/results/baseline_answers.json` có 10 câu hỏi |
| Kết nối quality và freshness | `data/quality/baseline_quality_report.json`, `data/quality/freshness_report.json` |
| Kết nối sinh báo cáo | `data/reports/phase1_report.md` tổng hợp nguồn dữ liệu, index, metrics và kiểm định |

Một đầu ra quan trọng là **`baseline_metrics.json`**. File này cung cấp mốc định lượng để thành viên phụ trách corruption/repair so sánh với hai trạng thái còn lại. Kết quả không chỉ thể hiện bằng thông báo chạy xong mà còn có answers và quality reports để đối chiếu.

### Bằng chứng kiểm tra

Bản bàn giao cá nhân đã vượt qua **7 kiểm thử điều phối với các module phụ thuộc được giả lập**: đúng thứ tự gọi hàm; tái sử dụng bộ đề; refresh nguồn; phát hiện tham chiếu tài liệu không hợp lệ; dừng khi dữ liệu sạch rỗng; chuyển kết quả quality thất bại vào báo cáo; và không che lỗi khi reporting chưa triển khai. Kết quả này kiểm chứng bản `9413848`, không thay thế việc chạy thật phiên bản đã được nhóm cập nhật sau đó.

Đối với phiên bản hiện có trong repo, việc lập báo cáo đã đối chiếu trực tiếp các JSON, manifest và Markdown. Báo cáo pha 1 ghi thời điểm chạy `2026-09-26T05:22:04.154164+00:00`, tương đương khoảng 12:22 ngày 26/09/2026 theo giờ Việt Nam.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Các thành viên phát triển module riêng, nhưng những module này chỉ tạo thành hệ thống khi được gọi đúng thứ tự, truyền đúng dữ liệu và lưu đúng đường dẫn. Phần việc của tôi là điều phối các bước đó để tạo baseline có thể kiểm tra và dùng lại trong thí nghiệm tiếp theo.

### Trình tự theo bước 6

1. **Nạp cấu hình và dữ liệu nguồn.** Dùng `load_settings()` để lấy đường dẫn, tên collection và tham số. Nếu có raw records và không yêu cầu refresh, đọc snapshot bằng `load_raw_records()`; nếu không, gọi `fetch_source_records(settings)`.
2. **Làm sạch và lưu dữ liệu.** Truyền records cùng thời điểm chạy cho `build_clean_dataframe()`, sau đó lưu CSV/JSON. Dữ liệu sạch rỗng phải được phát hiện trước khi xây index.
3. **Xây dựng chỉ mục vector.** Gọi `LocalEmbeddingIndex.build()` với dữ liệu sạch, settings và đường dẫn embedding manifest. Module retrieval sử dụng MiniLM và ChromaDB để xây collection baseline.
4. **Tạo hoặc đọc lại bộ đề.** Dùng `build_test_set()` khi chưa có bộ đề hoặc bật `REFRESH_TEST_SET`; nếu không, đọc bộ đề đã lưu. Cách này giúp giữ một mốc đánh giá chung.
5. **Đánh giá baseline.** Gọi `evaluate_pipeline()` với index và bộ đề, nhận `EvaluationBundle`; module đánh giá ghi metrics và câu trả lời chi tiết ra các đường dẫn cấu hình.
6. **Kiểm định và báo cáo.** Gọi `run_data_quality_checks()`, `build_freshness_report()` rồi chuyển kết quả cùng thông tin nguồn vào `generate_phase1_report()`.

Thứ tự này bám theo mô tả bước 6 trong `phases.txt`: **Ingest → Clean → Index → Test set → Evaluation → Quality/Freshness → Report**. Trong bản tích hợp hiện tại, nếu quality thất bại, pipeline ghi báo cáo rồi ném `RuntimeError`. Vì kiểm định diễn ra sau index/evaluation, không nên mô tả phiên bản này là cơ chế chặn dữ liệu bẩn trước khi index.

### Input, output và contract

| Thành phần | Contract sử dụng |
| --- | --- |
| Cấu hình | `Settings` chứa `Paths`, collection, embedding model, `top_k` và các cờ refresh |
| Raw records | Danh sách `PaperRecord` do module ingestion trả về |
| Dữ liệu sạch | DataFrame có `paper_id`, `title`, `summary`, `published`, `authors_joined`, `categories_joined`, `text_for_embedding`, `age_days` và metadata cần cho index |
| Bộ đề | Mỗi câu có `id`, `question_type`, `question`, `ground_truth`, `ground_truth_doc_ids` |
| Kết quả đánh giá | `EvaluationBundle.summary` chứa metrics; `answers` chứa bằng chứng theo từng câu |
| Quality/Freshness | Dict kết quả với trạng thái `success`, `gx_success`, `is_fresh` và thống kê liên quan |
| Báo cáo | Hàm reporting nhận source summary, metrics, quality, freshness và đường dẫn Markdown |
| Bước dùng tiếp đầu ra | Corruption/repair dùng clean dataset, bộ đề và baseline metrics làm mốc so sánh |

Tôi sử dụng đường dẫn qua `settings.paths` để tránh gắn pipeline vào đường dẫn máy cá nhân. Cấu hình bí mật không được đưa vào `source_summary` hoặc báo cáo.

### Cách tái hiện

Sau khi cài dependencies và cấu hình môi trường theo hướng dẫn chung, chạy tại thư mục gốc repository:

```bash
uv run python script/run_phase1.py
```

Hoặc trong môi trường Python đã cài project:

```bash
python script/run_phase1.py
```

Đây là lệnh tái hiện của baseline, không phải khẳng định đã chạy lại trong lần lập báo cáo này. Khi kiểm tra lần chạy mới, cần đối chiếu đồng thời clean dataset, embedding manifest, metrics, answers, quality/freshness và `phase1_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

**Quyết định:** Tái sử dụng raw snapshot và bộ đề khi không bật cờ refresh.

- **Bối cảnh:** Crossref là nguồn có thể thay đổi. Nếu mỗi lần chạy đều lấy corpus mới và sinh đề mới, biến động metrics có thể đến từ thay đổi dữ liệu hoặc bộ đề, thay vì từ corruption/repair.
- **Phương án 1:** Luôn gọi API và luôn tạo lại bộ đề. Cách này cập nhật nguồn thường xuyên nhưng khó giữ mốc so sánh ổn định, đồng thời phụ thuộc mạng.
- **Phương án 2:** Ưu tiên snapshot và evaluation set đã lưu; chỉ làm mới theo cấu hình.
- **Phương án chọn:** Phương án 2, dựa trên `REFRESH_SOURCE` và `REFRESH_TEST_SET`.
- **Đánh đổi:** Dữ liệu không tự động là mới nhất; cần kiểm tra freshness và chủ động refresh khi cần.
- **Bằng chứng:** Kiểm thử bản bàn giao xác nhận không sinh lại bộ đề khi file đã tồn tại. Các answers hiện có của baseline, corrupted và repaired khớp với cùng 10 câu hỏi, đáp án chuẩn và document IDs trong `test_set.json`.

## 6. Một lỗi hoặc blocker đã xử lý

### Bộ đề tham chiếu đến tài liệu không còn trong corpus

- **Triệu chứng ở kiểm thử bản bàn giao:** Pipeline gặp bộ đề có `ground_truth_doc_ids` không thuộc tập `paper_id` của dữ liệu sạch.
- **Thông báo:** `Evaluation references missing papers; rerun with REFRESH_TEST_SET=1.`
- **Nguyên nhân:** Corpus đã thay đổi nhưng bộ đề cũ vẫn được tái sử dụng.
- **Cách xử lý trong commit `9413848`:** Đối chiếu các ground-truth IDs với dữ liệu sạch và dừng trước bước evaluation nếu tham chiếu không hợp lệ.
- **Cách xác minh:** Kiểm thử truyền vào một ID không tồn tại và xác nhận hàm evaluation không được gọi.
- **Điều học được:** Phải kiểm tra tính tương thích giữa dataset và evaluation set, không chỉ kiểm tra file có tồn tại hay không.

Bản `phase1.py` hiện tại sau tích hợp chỉ kiểm tra bộ đề rỗng, chưa giữ lại kiểm tra tham chiếu này. Đây là điểm nên bổ sung lại khi nhóm củng cố pipeline; không coi kiểm thử của commit cá nhân là bằng chứng rằng phiên bản hiện tại vẫn có đầy đủ kiểm tra đó.

### Phụ thuộc reporting khi tích hợp

Ở thời điểm bàn giao ban đầu, `generate_phase1_report()` còn là placeholder, nên phần điều phối chưa thể hoàn tất báo cáo end-to-end. Tôi giữ nguyên contract và xác nhận lỗi không bị che thành kết quả thành công. Hiện tại nhóm đã triển khai reporting và repo có `data/reports/phase1_report.md`; blocker này không còn trong bản source đang dùng để lập báo cáo.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến index như thế nào?** Payload được parse thành raw records; cleaning tạo DataFrame chuẩn hóa và `text_for_embedding`; MiniLM mã hóa văn bản thành vector; ChromaDB lưu vector cùng nội dung và metadata để truy vấn.
2. **Bộ đề dùng để đo chất lượng ra sao?** `ground_truth_doc_ids` cho biết tài liệu đúng cần truy xuất; Hit Rate đếm câu hỏi tìm được ít nhất một ID đúng. Đáp án chuẩn được dùng để tính Token F1 và chấm câu trả lời.
3. **Quality khác freshness thế nào?** Quality kiểm tra các ràng buộc như số dòng, giá trị null, ID trùng và độ dài summary. Freshness kiểm tra tuổi dữ liệu; trong lab, tỷ lệ bài có `age_days > 180` không được vượt 25%.
4. **Vì sao giữ nguyên bộ đề cho ba trạng thái?** Để câu hỏi và tiêu chuẩn chấm giữ nguyên, giúp so sánh tác động của việc thay đổi corpus. Nếu tạo lại đáp án từ dữ liệu bẩn, đánh giá có thể che đi lỗi cần phát hiện.
5. **Repair thành công dựa trên điều gì?** Cần đối chiếu dữ liệu đã phục hồi, quality/freshness, index và metrics trên cùng bộ đề. Việc script kết thúc không đủ để kết luận đã phục hồi. Muốn chứng minh idempotence còn cần chạy repair lặp lại và kiểm tra tính nhất quán.

## 8. Phân tích kết quả

### Metrics và tín hiệu hiện có trong repository

Số liệu dưới đây lấy từ các file `*_metrics.json`, `*_quality_report.json` và freshness report tương ứng. Corrupted/Repaired là kết quả chung được dùng để giải thích vai trò của baseline, không phải phần triển khai riêng của tôi.

| Metric / Signal | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
| Số câu hỏi | 10 | 10 | 10 |
| Số bản ghi | 24 | 21 | 24 |
| `retrieval_hit_rate` | 1.0000 | 0.5000 | 1.0000 |
| `mean_token_f1` | 1.0000 | 0.7788 | 1.0000 |
| `judge_accuracy` | 1.0000 | 0.8000 | 1.0000 |
| `mean_judge_score` | 5.00 | 4.00 | 5.00 |
| GX expectations đạt | 6/6 | 3/6 | 6/6 |
| Overall Quality Gate | PASS | FAIL | PASS |
| Số bài quá 180 ngày | 1/24 | 8/21 | 1/24 |
| Tỷ lệ bài cũ | 4.17% | 38.10% | 4.17% |
| Freshness | PASS | FAIL | PASS |

Nguồn đối chiếu:

- [Baseline metrics](../data/results/baseline_metrics.json) và [baseline answers](../data/results/baseline_answers.json).
- [Corrupted metrics](../data/results/corrupted_metrics.json) và [corrupted answers](../data/results/corrupted_answers.json).
- [Repaired metrics](../data/results/repaired_metrics.json) và [repaired answers](../data/results/repaired_answers.json).
- [Baseline quality](../data/quality/baseline_quality_report.json), [corrupted quality](../data/quality/corrupted_quality_report.json), [repaired quality](../data/quality/repaired_quality_report.json).
- [Baseline freshness](../data/quality/freshness_report.json), [corrupted freshness](../data/quality/corrupted_freshness_report.json), [repaired freshness](../data/quality/repaired_freshness_report.json).

### Diễn giải baseline

Baseline có 24 tài liệu được index và 10 câu hỏi thuộc bốn nhóm: 3 câu summary, 3 câu authors, 2 câu date, 2 câu categories. Cả 10 câu đều truy xuất được tài liệu đúng; Mean Token F1 bằng 1.0 theo cách tính của module evaluation hiện tại. Quality đạt cả 6 expectations, và chỉ 1/24 bài quá ngưỡng tuổi nên freshness vẫn đạt.

Cần hiểu đúng giới hạn của kết quả:

- `qa.py` hiện kết hợp semantic search với exact-title lookup và trích câu trả lời từ metadata. Vì vậy Hit Rate không phải thước đo của semantic search thuần túy, và bộ số liệu này không chứng minh Gemini trực tiếp sinh toàn bộ câu trả lời.
- Cả 10 answers của từng trạng thái đều có `judge.reasoning` ghi sử dụng **fallback heuristic**. Do đó `judge_accuracy` và `mean_judge_score` ở đây là điểm chấm dự phòng, không phải bằng chứng Gemini judge hoạt động thành công.
- Token F1 hiện tính trên tập token viết thường, tách theo khoảng trắng; chỉ số này không đánh giá đầy đủ độ đúng ngữ nghĩa.
- Ragas được ghi là `skipped`. Kết quả trên 10 câu hỏi không đủ để kết luận hệ thống đạt chất lượng tương tự trên mọi câu hỏi mới.

### Hai chuỗi nguyên nhân và bằng chứng

**1. Dữ liệu bị thay đổi → cảnh báo → suy giảm retrieval/answer quality.**

Corruption log ghi nhận việc xóa 5 bài mới nhất. Năm câu không retrieval hit trong corrupted answers (`eval_001` đến `eval_005`) đều tham chiếu tới các bài đã bị xóa. Đây là bằng chứng trực tiếp về ảnh hưởng của mất dữ liệu đối với Hit Rate, từ 10/10 xuống 5/10, tức giảm **50 điểm phần trăm**.

Corrupted quality report đồng thời ghi ba kiểm tra thất bại: số dòng, tính duy nhất của `paper_id` và độ dài `summary`. Với artifact này, expectation số dòng được cấu hình đúng 24 dòng, trong khi dữ liệu corrupted còn 21 dòng. Tỷ lệ bài cũ tăng lên 38.10%, vượt SLA 25%. Token F1 giảm từ 1.0000 xuống 0.7788, tương đương khoảng **0.2212** trên thang 0–1.

**2. Dựng lại dữ liệu nguồn → kiểm định phục hồi → metrics trở lại mốc baseline.**

Hai file `papers_clean.json` và `papers_clean_repaired.json` hiện có nội dung JSON bằng nhau. Repaired có đủ 24 dòng, quality đạt 6/6 và freshness trở lại 1/24 bài cũ. Trên cùng bộ đề, Hit Rate và Token F1 trở lại 1.0. Các bằng chứng này hỗ trợ kết luận bộ artifact hiện tại đã phục hồi về mốc baseline; chúng không tự chứng minh mọi lần repair trong tương lai đều thành công.

### Corruption ảnh hưởng rõ nhất và kết quả cần thận trọng

Việc xóa các bài mới nhất có ảnh hưởng rõ nhất đến retrieval trong bộ đề hiện tại vì ánh xạ được trực tiếp cả 5 câu mất hit tới 5 tài liệu bị xóa. Tuy nhiên, các lỗi được tiêm cùng trong một luồng; chưa có thí nghiệm tách riêng từng lỗi để xếp hạng tác động độc lập lên Token F1.

Một điểm dễ hiểu nhầm là điểm judge baseline đạt tối đa nhưng toàn bộ lượt chấm đều dùng fallback. Vì vậy tôi đọc cả answers, không chỉ dựa vào metrics tổng hợp, để tránh kết luận quá mức về năng lực của LLM.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Điều phối pipeline là quản lý phụ thuộc dữ liệu.** Cần giữ nhất quán schema, đường dẫn và thứ tự thực thi; từng module chạy riêng không đồng nghĩa cả hệ thống đã tích hợp đúng.
2. **Metrics cần đi cùng bằng chứng.** Baseline metrics, answers, quality và freshness phải được đọc cùng nhau; điểm cao không có nghĩa mọi thành phần, đặc biệt LLM judge, đã hoạt động như kỳ vọng.
3. **Baseline là nền tảng của thí nghiệm corruption/repair.** Giữ corpus nguồn và bộ đề ổn định giúp nhóm xác định thay đổi đến từ đâu và kiểm tra phục hồi có ý nghĩa.

### Nếu có thêm thời gian

- Khôi phục kiểm tra ground-truth IDs trong bản pipeline hiện tại và bổ sung kiểm thử tái lập trong repo để phát hiện trường hợp corpus đổi nhưng bộ đề chưa đổi.
- Ghi rõ provider/model và số lượt judge fallback vào metrics để người đọc không nhầm điểm heuristic với đánh giá bằng LLM.
- Nếu chuyển sang triển khai phục vụ người dùng, đánh giá phương án đưa Quality Gate lên trước index để chặn dữ liệu không đạt; thay đổi này cần được thống nhất vì khác thứ tự thực nghiệm ở bước 6.
- Mở rộng bộ đề và chạy riêng từng loại corruption để đo tác động độc lập, thay vì suy ra từ một lần tiêm đồng thời sáu lỗi.

## 10. Cam kết của thành viên

Các mục dưới đây dành cho tôi tự rà soát và xác nhận trước khi nộp:

- [ ] Báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [ ] Tôi có thể giải thích luồng end-to-end và phần baseline mình phụ trách.
- [ ] Tôi đã đối chiếu các kết luận với code và artifact được dẫn trong báo cáo.
- [ ] Tôi phân biệt kết quả của commit cá nhân, bản tích hợp của nhóm và các lần kiểm thử giả lập.
- [ ] Tôi không nhận phần triển khai corruption/repair hoặc các module của đồng đội là đóng góp riêng.
- [ ] Báo cáo không chứa API key, token hoặc nội dung file `.env`.
- [ ] Tôi đã đọc lại nội dung và xác nhận trước khi nộp.

**Họ và tên:** Nguyễn Ngọc Tuyền

**Ngày lập báo cáo:** 26/09/2026

**Ngày xác nhận:** Điền sau khi tự rà soát.
