# Demo giao diện PaperLab

Trong thư mục dự án, với `.venv` đang được kích hoạt:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Mở http://localhost:8501. Nếu chưa có dữ liệu baseline, chạy `python script/run_phase1.py` trước.

## Kịch bản trình diễn

1. Giới thiệu 24 bài báo và các chỉ số Hit Rate, Token F1 ở đầu trang.
2. Trong **Hỏi đáp → Xem kết quả baseline**, chọn câu hỏi mẫu, xem câu trả lời, đáp án tham chiếu và tài liệu nguồn. Chế độ này đọc kết quả đã lưu, không chạy lại model.
3. Chuyển sang **Hỏi đáp trực tiếp**, chọn bài báo và dạng câu hỏi, bấm **Tìm câu trả lời** để truy vấn ChromaDB thật. Lần đầu cần nạp MiniLM; các lần sau dùng model đã cache. Không cần API key cho phần hỏi đáp này.
4. Mở **Kho bài báo** và tìm theo tác giả hoặc tiêu đề.
5. Mở **Chất lượng dữ liệu**, trình bày kiểm định GX, Freshness SLA và tải báo cáo Markdown.

Chỉ số trên dashboard phản ánh lần chạy baseline đã lưu. Nút **Đọc lại kết quả** cập nhật giao diện sau khi chạy lại pipeline. Giao diện chưa mô phỏng Corruption/Repair khi các pha này chưa hoàn thiện.
