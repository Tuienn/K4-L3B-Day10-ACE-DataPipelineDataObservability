# Báo Cáo Đối Chiếu 3 Trạng Thái: Baseline vs Corrupted vs Repaired

> **Thời gian thực thi:** 2026-09-26 05:16:39 UTC  
> **Mục tiêu:** Chứng minh hiện tượng **Silent Failure** khi dữ liệu bị lỗi, vai trò cảnh báo của **Data Quality Gate (GX 1.x)** và năng lực tự phục hồi an toàn (**Idempotent Repair**).

---

## 1. Bảng Tổng Hợp Đối Chiếu 3 Trạng Thái

| Tiêu chí / Chỉ số đo lường | Trạng thái 1: Baseline (Dữ liệu sạch) | Trạng thái 2: Corrupted (Bị tiêm lỗi) | Trạng thái 3: Repaired (Đã phục hồi) | Biến động do Corruption | Mức độ phục hồi | Đánh giá trạng thái |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Tổng số bản ghi (Rows)** | **24** | **21** | **24** | -3 dòng | Phục hồi đủ 24 | Khôi phục 100% dung lượng |
| **Great Expectations 1.x** | **PASS (True)** | **FAIL (False)** | **PASS (True)** | ❌ Bị đánh trượt | ✅ Đạt chuẩn 100% | Bắt trọn 100% vi phạm schema |
| **Freshness SLA (`is_fresh`)** | **True** (4.2% cũ) | **False** (38.1% cũ) | **True** (4.2% cũ) | ❌ Vi phạm SLA (>25%) | ✅ Về ngưỡng an toàn | Phát hiện chính xác dữ liệu ôi |
| **Tổng thể Quality Gate** | **PASS (True)** | **FAIL (False)** | **PASS (True)** | ❌ Chặn toàn tuyến | ✅ Mở cổng triển khai | Chốt kiểm soát hoạt động chuẩn |
| **Retrieval Hit Rate** | **1.0000 (100.0%)** | **0.5000 (50.0%)** | **1.0000 (100.0%)** | **-50.0%** | **+50.0%** | Lấy lại 100% độ nhạy tìm kiếm |
| **Mean Token F1** | **1.0000 (100.0%)** | **0.7788 (77.9%)** | **1.0000 (100.0%)** | **-22.1%** | **+22.1%** | Trả lời chính xác từng từ khóa |
| **Judge Accuracy** | **1.0000 (100.0%)** | **0.8000 (80.0%)** | **1.0000 (100.0%)** | **-20.0%** | **+20.0%** | Thẩm định câu trả lời đúng chuẩn |
| **Mean Judge Score** | **5.00 / 5.0** | **4.00 / 5.0** | **5.00 / 5.0** | **-1.00** | **+1.00** | Điểm chất lượng tối đa |

---

## 2. Phân Tích Hiện Tượng "Silent Failure" & Vai Trò Của Data Observability

### 2.1. Bản chất của Silent Failure trong hệ thống RAG
Khi 6 kịch bản lỗi dữ liệu được tiêm vào pipeline:
1. **Drop latest records (mất 20% bài mới):** Các câu hỏi về công trình mới nhất không thể tìm thấy context tương ứng.
2. **Blank summary:** Phần tóm tắt rỗng làm triệt tiêu ngữ cảnh trả lời câu hỏi `summary`.
3. **Inject noise:** Ký tự rác phá vỡ không gian vector ngữ nghĩa, kéo giảm similarity score.
4. **Truncate title:** Tiêu đề bị cắt dưới 8 ký tự làm vô hiệu hóa khả năng Exact Lookup và giảm độ tương đồng truy xuất.
5. **Stale date:** Đẩy ngày xuất bản lùi 365 ngày, làm sai lệch câu trả lời thời gian và vi phạm SLA độ tươi mới.
6. **Duplicate rows:** Trùng lặp `paper_id` gây nhiễu top-k và lãng phí context window.

> ⚠️ **Hiện tượng Silent Failure:** Chương trình không hề ném ra ngoại lệ (exception) hay crash chương trình (`exit code 0`). Nhưng Retrieval Hit Rate rơi từ **100.0%** xuống **50.0%**, và Token F1 sụt giảm từ **100.0%** xuống **77.9%**. Nếu không có hệ thống Data Observability, AI sẽ âm thầm cung cấp thông tin sai lệch cho người dùng cuối.

### 2.2. Vai trò chốt chặn của Great Expectations 1.x & Freshness SLA
- **Great Expectations 1.x:** Bắt trọn vẹn sự cố thông qua các Expectation:
  - `ExpectTableRowCountToBeBetween`: Phát hiện biến động số dòng bất thường.
  - `ExpectColumnValuesToBeUnique`: Báo động đỏ ngay khi xuất hiện trùng lặp khóa chính `paper_id`.
  - `ExpectColumnValueLengthsToBeBetween`: Đánh trượt các dòng bị xóa trắng summary (< 30 ký tự).
- **Freshness Monitor:** Tỷ lệ bài cũ tăng vọt lên **38.1%** (vượt ngưỡng cho phép 25%), lập tức hạ cờ `is_fresh = False`.

---

## 3. Cơ Chế Phục Hồi Dữ Liệu An Toàn (Idempotent Repair)

### 3.1. Điểm tựa dòng đời dữ liệu (Lineage Anchor)
Hệ thống kích hoạt cơ chế `repair_from_raw_snapshot()` dựa trên 2 file lưu trữ thô bất biến:
- `data/raw/crossref_response.json` (API payload nguyên gốc).
- `data/raw/crossref_records.json` (Danh sách PaperRecord bóc tách ban đầu).

### 3.2. Tính chất Idempotent (Bất biến qua các lần chạy lặp lại)
- Quy trình Repair chạy lại toàn bộ bước làm sạch và chuẩn hóa ngữ cảnh `build_clean_dataframe()`.
- Ghi đè có kiểm soát vào `papers_clean_repaired.csv` / `papers_clean_repaired.json` và đồng bộ lại Vector Collection `papers-repaired`.
- Dù kích hoạt bao nhiêu lần, kết quả luôn hội tụ về trạng thái chuẩn hóa duy nhất với 24 bản ghi sạch.

### 3.3. Kết quả sau phục hồi
- Chốt kiểm định chất lượng: **GX 1.x đạt PASS (True)**, **Freshness SLA đạt True** (4.2% <= 25%).
- Hiệu năng RAG: **Retrieval Hit Rate đạt 100.0%**, **Mean Token F1 đạt 100.0%**, phục hồi trọn vẹn 100% năng lực hệ thống ban đầu.

---

## 4. Kết Luận
Thực nghiệm đã chứng minh:
1. **Dữ liệu hỏng tạo ra suy thoái âm thầm (Silent Degradation)** nguy hiểm hơn nhiều so với lỗi dừng hệ thống (Runtime Crash).
2. **Data Observability (Great Expectations 1.x + Freshness SLA)** là thành phần sống còn để phát hiện sớm lỗi dữ liệu trước khi đẩy vào Vector Database.
3. **Cất giữ bản thô (Raw Preservation) kết hợp Idempotent Repair** cung cấp khả năng tự phục hồi (Self-healing) tin cậy, giúp hệ thống RAG hoạt động bền vững trong môi trường sản xuất.
