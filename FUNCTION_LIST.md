import os

# Create content for the FUNCTION_LIST.md
markdown_content = """# ĐỒ ÁN: HỆ THỐNG THƯƠNG MẠI ĐIỆN TỬ TÍCH HỢP TRỢ LÝ AI (FORTE_X)
## DANH SÁCH CHỨC NĂNG KIỂM THỬ HỆ THỐNG (FUNCTION LIST FOR REGRESSION TESTING)

Tài liệu này định nghĩa danh sách các chức năng phân cấp từ hạ tầng cốt lõi, nghiệp vụ e-commerce cơ bản, đến các tác vụ kiểm thử định lượng nâng cao thông qua RAG Pipeline và LLM-as-a-Judge. Cấu trúc danh sách phục vụ trực tiếp cho AI Agent chạy đợt tổng kiểm thử tự động (Final Regression Testing).

---

### 1. Tầng Hạ tầng & Quản trị Hệ thống (Core & Administrative Infrastructure)

| ID | Chức năng (Function) | Kịch bản Kiểm thử cho AI Agent (Test Scenario) | Mức độ | Trạng thái dự kiến |
| :--- | :--- | :--- | :---: | :---: |
| **SYS-01** | Khởi tạo Chỉ mục Vector (FAISS Indexing) | Chạy lệnh `python manage.py build_ai_index`. Xác thực file `chatbot.index` và `meta.json` được sinh mới và ghi thành công xuống đĩa cứng (Disk Persistence). | **[P0]** | `Pass` |
| **SYS-02** | Đồng bộ Đồ thị Kiến thức (Neo4j Graph Sync) | Chạy lệnh `python manage.py sync_to_neo4j`. Kiểm tra số lượng nút (đảm bảo đủ 280 sản phẩm: 143 synthetic + 137 Tiki) và các mối quan hệ phân cấp danh mục `[:CHILD_OF]` trên Neo4j Browser. | **[P0]** | `Pass` |
| **SYS-03** | Distributed Tracing Middleware | Giả lập request đi xuyên suốt hệ thống qua API Gateway -> Chatbot Service -> Product/Order Service. Kiểm tra xem mã định danh duy nhất `X-Trace-Id` có được truyền dẫn đồng bộ trong Header và log của các dịch vụ không. | **[P1]** | `Pass` |

---

### 2. Nghiệp vụ E-commerce Cơ bản (Core E-commerce Functions)

| ID | Chức năng (Function) | Kịch bản Kiểm thử cho AI Agent (Test Scenario) | Mức độ | Trạng thái dự kiến |
| :--- | :--- | :--- | :---: | :---: |
| **PROD-01**| Tìm kiếm Sản phẩm (Text Search) | Gửi request tìm kiếm từ khóa tiếng Việt có dấu, không dấu, viết hoa, viết thường (ví dụ: "áo sơ mi nam", "dien thoai"). Hệ thống phải trả về đúng danh sách sản phẩm liên quan từ Postgres. | **[P0]** | `Pass` |
| **PROD-02**| Lọc Danh mục Phân cấp (Hierarchical Sub-category Filter) | **[Mới nâng cấp]** Click danh mục cha (`Books & Office`) -> Trả về tất cả sản phẩm thuộc cha + mảng danh mục con trực tiếp. Click tiếp danh mục con (`Phụ kiện`) -> Thu hẹp danh sách trả về đúng các sản phẩm là phụ kiện. | **[P0]** | `Pass` |
| **ORD-01** | Đặt hàng & Trừ Kho (Inventory Atomicity) | Khởi tạo một luồng checkout đơn hàng với sản phẩm A (số lượng mua: 2). Kiểm tra tính toàn vẹn dữ liệu: trường `stock_quantity` của sản phẩm A trong Postgres phải tự động trừ chính xác đi 2 đơn vị. | **[P1]** | `Pass` |
| **ORD-02** | Đồng bộ Trạng thái Đơn hàng (State Machine) | Cập nhật trạng thái đơn hàng từ `Processing` sang `Delivered`. Kiểm tra xem các Service phụ thuộc (Notification Service, User Order History) có nhận đúng Event qua Message Broker để cập nhật không. | **[P1]** | `Pass` |

---

### 3. Hệ thống Trợ lý AI Nâng cao (Advanced AI & RAG Pipeline)

| ID | Chức năng (Function) | Kịch bản Kiểm thử cho AI Agent (Test Scenario) | Mức độ | Trạng thái dự kiến |
| :--- | :--- | :--- | :---: | :---: |
| **AI-01** | Phân loại Ý định (Intent Classification) | Gửi câu hỏi test ý định người dùng: "Chào shop/Hello" -> Phải phân loại vào Intent: `greeting`. Gửi câu hỏi: "Tư vấn cho tôi laptop tầm 20tr" -> Phải phân loại vào Intent: `product_search`. | **[P0]** | `Pass` |
| **AI-02** | Trích xuất Thực thể (Named Entity Recognition - NER) | Gửi câu hỏi: "Tìm giày Nike dưới 2 triệu". Chatbot phải trích xuất đúng cấu trúc tham số: `brand="nike"`, `price_max=2000000`, `category="giày"`. | **[P0]** | `Pass` |
| **AI-03** | Truy vấn Đồ thị Khớp Giá (Neo4j Cypher Guard) | **[Bug Fix]** Gửi câu hỏi lọc giá (ví dụ: "máy tính dưới 15 triệu"). Xác thực câu lệnh Cypher sinh ra tự động sử dụng hàm ép kiểu `toInteger(p.price)` chính xác, tuyệt đối không trả về sản phẩm có giá vượt ngưỡng. | **[P0]** | `Pass` |
| **AI-04** | Tìm kiếm Ngữ nghĩa Fallback (Hybrid Search Engine) | Gửi câu hỏi mang tính mô tả phong cách, phi cấu trúc (ví dụ: "áo mặc đi tiệc sang trọng"). Khi Neo4j trả về rỗng, hệ thống phải tự động kích hoạt luồng fallback sang FAISS để tìm kiếm theo vector embedding. | **[P1]** | `Pass` |
| **AI-05** | Chống Ảo tưởng Dữ liệu (Anti-Hallucination Guardrail) | Gửi câu hỏi bẫy về sản phẩm không tồn tại trong hệ thống (ví dụ: "Tư vấn iPhone 25", "Alienware X99"). Chatbot phải nhận biết được và trả về câu fallback an toàn theo kịch bản thay vì tự bịa cấu trúc thông số. | **[P1]** | `Pass` |
| **AI-06** | Trích dẫn Mã định danh (Source Citation Mapping) | Kiểm tra câu trả lời tư vấn sản phẩm của mô hình `llama3.2:3b`. Câu trả lời bắt buộc phải đính kèm thẻ trích dẫn nguồn dạng `[ID: xxx]` khớp chính xác với ID thực tế của sản phẩm được cung cấp trong Context. | **[P1]** | `Pass` |

---

### 4. Đánh giá Định lượng & Giám khảo Tự động (LLM-as-a-Judge)

| ID | Chức năng (Function) | Kịch bản Kiểm thử cho AI Agent (Test Scenario) | Mức độ | Trạng thái dự kiến |
| :--- | :--- | :--- | :---: | :---: |
| **EVAL-01**| Đánh giá tuần tự giải phóng RAM (Sequential Isolation) | Khởi chạy script `evaluate_models.py`. Hệ thống phải chạy đánh giá tuần tự từng model một (`llama3.2:3b` -> giải phóng bộ nhớ -> nạp model tiếp theo) để tránh hiện tượng sập VRAM/RAM do nạp đồng thời. | **[P1]** | `Pass` |
| **EVAL-02**| Trọng tài Nội bộ (Local LLM Judge Execution) | Xác thực Class `LocalLLMJudge` gọi chính xác mô hình `qwen2.5:7b` chạy cục bộ để chấm điểm hai chỉ số `Relevance` (Độ liên quan) và `Faithfulness` (Độ trung thực) trên thang điểm 1.0 - 5.0. | **[P1]** | `Pass` |
| **EVAL-03**| Xuất Bản đồ Kết quả (Automated Metric Reporting) | Kiểm tra sau khi kết thúc chu trình test nghiệm thu, thư mục `results/charts/` và `results/` phải tự động sinh/cập nhật đầy đủ file dữ liệu cấu trúc tổng hợp và tài liệu báo cáo `EVALUATION_SUMMARY.md`. | **[P1]** | `Pass` |

