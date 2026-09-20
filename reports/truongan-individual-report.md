# Individual contribution report

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
| Evaluation | Tạo 15 grounded golden cases và hoàn thiện evaluation result report | `group_project/evaluation/golden_dataset.json`, `group_project/evaluation/RESULT.md` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Dùng hybrid retrieval với dense search, BM25 và RRF.
   **Lý do/evidence:** Dense bắt ngữ nghĩa; BM25 hỗ trợ thuật ngữ chính xác. RRF được thực hiện một lần trong pipeline.
   **Trade-off:** Tăng chi phí tính toán so với dense-only nhưng giảm phụ thuộc vào một kiểu matching.

2. **Quyết định:** Dùng cosine score gốc của dense search để kích hoạt PageIndex fallback.
   **Lý do/evidence:** RRF score không cùng thang đo với cosine score; code giữ riêng `best_dense_score` và so sánh với threshold `0.3`.
   **Trade-off:** Threshold hiện là giá trị khởi đầu và cần calibration trên query in-domain/out-of-domain.

## Kiểm thử và kết quả

- Test đã dùng: `python -m pytest -q`.
- Kết quả: `20 passed`.
- Lỗi đã phát hiện và xử lý: golden dataset rỗng và evaluation report còn placeholder; đã bổ sung 15 cases grounded và report hoàn chỉnh.

## Điều còn hạn chế

- A/B hiện dùng deterministic lexical proxy thay vì LLM-as-judge; vì vậy faithfulness và answer relevance là chỉ số tái lập được từ golden answer/context, không phải đánh giá ngữ nghĩa bởi evaluator model.
- Nếu có thêm thời gian, thay đổi đầu tiên sẽ là chạy thêm LLM-as-judge trên cùng 15 cases để đối chiếu với baseline deterministic và đo generation quality.

## Xác nhận đóng góp

Nội dung trên phản ánh các thay đổi có thể đối chiếu bằng file, commit và test trong repository.

- Ngày: 2026-09-20
- Tên thành viên: Đinh Trường An; Phan Đức Duy
