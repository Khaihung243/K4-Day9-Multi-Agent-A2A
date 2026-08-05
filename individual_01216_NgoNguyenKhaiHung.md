# Member Role Report — Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                  |
| --------------- | ------------------------- |
| Họ và tên       | Ngô Nguyễn Khải Hưng      |
| MSSV            | 2A202601216               |
| Khóa/Lớp        | K4                        |
| Vai trò chính   | Lead / System Architect & Multi-Agent Developer |
| Ngày hoàn thành | 2026-08-05                |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | ------------------ | -------------- | ----------------- | ------------------------------------- |
| Data Indexing & Loading | `src/data_loader.py` | 9 file CSV Olist trong `data/` | Data Loader Object với Indexing O(1) | Hoàn thành |
| Multi-Agent Engine Package | `src/agents/*.py` | Order & Case info | 7 Agents (`CoordinatorAgent`, `CustomerAgent`, `OrderProductAgent`, `PaymentAgent`, `DeliveryAgent`, `PolicyAgent`, `VerifierAgent`) | Hoàn thành |
| Pipeline Execution & Output | `main.py` | 50 file JSON trong `input/` | 50 file JSON trong `output/`, `output.zip`, `logging/trace.jsonl`, `logging/metadata.json` | Hoàn thành |
| System Architecture | `architecture.md` | Sơ đồ luồng A2A Handoff | Tài liệu kiến trúc Multi-Agent | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ----------------------------- | ------- |
| Debug & Audit quy tắc EC_POLICY_V2 | Toàn nhóm | Đảm bảo tính toán chính xác 100% sai số tiền hàng, thời gian trễ và căn chỉnh schema |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------- | --------------------------- | ------------------------- | --------------- |
| Xây dựng Data Indexer | [src/data_loader.py](file:///c:/23020382_Ng%C3%B4%20Nguy%E1%BB%85n%20Kh%E1%BA%A3i%20H%C6%B0ng/K4-Day9-Multi-Agent-A2A/src/data_loader.py) | Trích xuất dữ liệu tức thì cho 9 CSV | Chạy script kiểm tra |
| Tách biệt 7 Agent A2A | [src/agents/](file:///c:/23020382_Ng%C3%B4%20Nguy%E1%BB%85n%20Kh%E1%BA%A3i%20H%C6%B0ng/K4-Day9-Multi-Agent-A2A/src/agents/) | 7 file Agent riêng biệt + Handoff dữ liệu chuẩn | Kiểm tra `logging/trace.jsonl` |
| Chạy 50 case & đóng gói | [main.py](file:///c:/23020382_Ng%C3%B4%20Nguy%E1%BB%85n%20Kh%E1%BA%A3i%20H%C6%B0ng/K4-Day9-Multi-Agent-A2A/main.py) | 50 file JSON, `output.zip`, `logging/trace.jsonl`, `logging/metadata.json` | Đếm số file trong output.zip |

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Xử lý 50 case khiếu nại thương mại điện tử từ dữ liệu Olist phức tạp bằng kiến trúc Multi-Agent A2A tách biệt các file Agent, đối soát cước vận chuyển, độ lệch giao hàng, phương thức thanh toán và áp dụng các quy tắc ưu tiên trong `EC_POLICY_V2`.

### Cách triển khai
- **Modular Agent Design**: Tách riêng vai trò từng Agent vào từng file Python độc lập trong package `src/agents/` (`customer_agent.py`, `order_product_agent.py`, `payment_agent.py`, `delivery_agent.py`, `policy_agent.py`, `verifier_agent.py`, `coordinator_agent.py`).
- **Quy tắc EC_POLICY_V2**: Lập trình ma trận quyết định chính xác cho 6 loại Primary Issue và 5 loại Secondary Issue.
- **Logging & Trace**: Lưu file trace và metadata trực tiếp vào thư mục `logging/`.

### Input, output và contract

| Thành phần | Mô tả |
| ---------- | ------ |
| Input | `input/EC_001.json` $\rightarrow$ `input/EC_050.json` và 9 file CSV trong `data/` |
| Output | `output/EC_001.json` $\rightarrow$ `output/EC_050.json`, `output.zip`, `logging/trace.jsonl`, `logging/metadata.json` |
| Module phụ thuộc | Python standard library (`csv`, `json`, `datetime`, `zipfile`, `os`, `shutil`) |

## 5. Một quyết định kỹ thuật quan trọng
- **Bối cảnh**: Tổ chức cấu trúc thư mục source code giữa file chung duy nhất hay chia tách thành package module.
- **Các phương án đã cân nhắc**: 
  1. Gộp toàn bộ Agent vào một file `agents.py`.
  2. Chia tách từng Agent thành từng module riêng trong `src/agents/`.
- **Phương án đã chọn**: Phương án 2 (`src/agents/`).
- **Lý do**: Dễ bảo trì, phân định rõ vai trò và luồng handoff của từng Agent theo chuẩn kiến trúc Agent-to-Agent.

## 6. Một lỗi hoặc blocker đã xử lý
- **Triệu chứng**: Cần lưu vết trace log và metadata đúng vị trí quy định của hệ thống.
- **Cách xử lý**: Cấu hình `main.py` tự động ghi log vào thư mục `logging/trace.jsonl` và `logging/metadata.json`, đồng thời sao chép ra thư mục gốc.

## 7. Hiểu biết về luồng end-to-end
1. **Dữ liệu được nạp & Indexing**: Khi khởi chạy, `DataLoader` sẽ quét 9 CSV và tạo map chỉ mục O(1) theo `order_id`, `customer_id`, `product_id`.
2. **Handoff giữa 7 Agents**: Coordinator điều phối `CustomerAgent`, `OrderProductAgent`, `PaymentAgent`, `DeliveryAgent` trích xuất thông tin, chuyển giao bằng chứng cho `PolicyAgent` đưa ra quyết định và `VerifierAgent` định dạng output cuối cùng.
3. **Trace & Submission**: Mọi bước trao đổi giữa các Agent đều được lưu lại trong `logging/trace.jsonl` và file nộp bài `output.zip` được tự động nén.

## 8. Cam kết của thành viên
- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.

**Họ và tên:** Ngô Nguyễn Khải Hưng  
**MSSV:** 2A202601216  
**Ngày xác nhận:** 2026-08-05
