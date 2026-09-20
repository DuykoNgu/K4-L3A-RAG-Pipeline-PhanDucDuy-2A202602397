# Individual contribution report

Giới hạn khuyến nghị: 1 trang, không chép lại README hoặc mô tả lý thuyết chung. Báo cáo không phải một bài pipeline cá nhân; mục đích là ghi nhận ownership và bằng chứng đóng góp trong sản phẩm nhóm.

---

## Thông tin

- Thành viên 1: Đinh Trường An — 2A202602393
- Thành viên 2: Phan Đức Duy — 2A202602397
- Nhóm: K4-L3A-RAG-Pipeline
- Repository/branch: `DuykoNgu/K4-L3A-RAG-Pipeline-PhanDucDuy-2A202602397`, `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Corpus IELTS | Bổ sung 3 tài liệu legal và 5 bài news đã chuẩn hóa | `data/landing/`, `data/standardized/`, commit `2ffebaf` | Done |
| RAG pipeline | Hoàn thiện chunking, embedding/indexing, dense search, BM25, RRF, fallback và generation citation | `src/task4_chunking_indexing.py` đến `src/task10_generation.py`, commit `1353fbe` | Done |
| Evaluation | Tạo 15 grounded golden cases và hoàn thiện evaluation report | `group_project/evaluation/golden_dataset.json`, `group_project/evaluation/RESULT.md` | Done |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

Mô tả tối đa hai quyết định mà bạn trực tiếp tham gia:

1. **Quyết định:** Dùng hybrid retrieval với dense search, BM25 và RRF.
   **Lý do/evidence:** Dense bắt ngữ nghĩa; BM25 hỗ trợ thuật ngữ chính xác. RRF được thực hiện một lần trong pipeline.
   **Trade-off:** Tăng chi phí tính toán so với dense-only nhưng giảm phụ thuộc vào một kiểu matching.

2. **Quyết định:** Dùng cosine score gốc của dense search để kích hoạt PageIndex fallback.
   **Lý do/evidence:** RRF score không cùng thang đo với cosine score; pipeline giữ riêng `best_dense_score` và so sánh với threshold `0.3`.
   **Trade-off:** Threshold hiện là giá trị khởi đầu và cần calibration trên query in-domain/out-of-domain.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `python -m pytest -q`.
- Kết quả trước/sau nếu có: `20 passed` sau khi bổ sung golden dataset và report.
- Lỗi đã phát hiện và cách xử lý: golden dataset rỗng và evaluation report còn placeholder; đã bổ sung 15 cases grounded và hoàn thiện report.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: A/B hiện dùng deterministic lexical proxy thay vì LLM-as-judge; faithfulness và answer relevance là chỉ số tái lập được từ golden answer/context, không phải đánh giá ngữ nghĩa bởi evaluator model.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Chạy LLM-as-judge trên cùng 15 cases để đối chiếu với baseline deterministic và đo generation quality.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-20
- Tên thành viên: Đinh Trường An; Phan Đức Duy
