# Nền Tảng AI-Ecommerce (FORTE_X)

Nền tảng thương mại điện tử tích hợp trợ lý AI thông minh, được xây dựng theo kiến trúc **Microservices** sử dụng **Django REST Framework** cho backend và **React** cho frontend.

---

## 1. Tổng Quan Kiến Trúc

Hệ thống được thiết kế theo nguyên lý **Database per Service** (mỗi service sử dụng một database riêng biệt) và giao tiếp qua hai giao thức chính:
- **Đồng bộ (Synchronous):** REST API qua HTTP thông qua API Gateway.
- **Bất đồng bộ (Asynchronous):** Hàng đợi tin nhắn RabbitMQ / Redis (Event-driven) cho các tác vụ như gửi thông báo, đồng bộ dữ liệu.

```
                               ┌─────────────────────────┐
                               │     FRONTEND (React)    │
                               │        Cổng: 3000       │
                               └─────────────────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │   API GATEWAY (Django)  │
                               │        Cổng: 8000       │
                               └─────────────────────────┘
                                            │
      ┌──────────────┬───────────────┬──────┴────────┬──────────────┬──────────────┐
      ▼              ▼               ▼               ▼              ▼              ▼
┌───────────┐  ┌───────────┐   ┌───────────┐   ┌───────────┐  ┌───────────┐  ┌───────────┐
│ Xác thực  │  │Người dùng │   │ Sản phẩm  │   │ Đơn hàng  │  │ Dịch vụ AI│  │  Chatbot  │
│  Service  │  │  Service  │   │  Service  │   │  Service  │  │ Gợi ý (Rec)│  │  Service  │
│   :8001   │  │   :8002   │   │   :8003   │   │   :8005   │  │   :8010   │  │   :8012   │
└───────────┘  └───────────┘   └───────────┘   └───────────┘  └───────────┘  └───────────┘
      │              │               │               │              │              │
      ▼              ▼               ▼               ▼              ▼              ▼
┌───────────┐  ┌───────────┐   ┌───────────┐   ┌───────────┐  ┌───────────┐  ┌───────────┐
│PostgreSQL │  │PostgreSQL │   │PostgreSQL │   │PostgreSQL │  │   Neo4j   │  │ FAISS DB  │
│  auth_db  │  │  user_db  │   │product_db │   │ order_db  │  │(Knowledge)│  │(Embeddings│
└───────────┘  └───────────┘   └───────────┘   └───────────┘  └───────────┘  └───────────┘
```

---

## 2. Danh Sách Services & Cổng Kết Nối

| Nhóm | Service | Cổng | Cơ sở dữ liệu | Vai trò / Tính năng chính |
| :--- | :--- | :---: | :--- | :--- |
| **Cốt lõi** | `api-gateway` | 8000 | Redis | Định tuyến tập trung, Giới hạn tốc độ, Kiểm tra JWT |
| | `auth-service` | 8001 | PostgreSQL (`auth_db`) | Xác thực JWT (Đăng ký, Đăng nhập, Vô hiệu hóa) |
| | `user-service` | 8002 | PostgreSQL (`user_db`) | Quản lý Hồ sơ người dùng, Địa chỉ, Quyền (RBAC) |
| | `product-service` | 8003 | PostgreSQL (`product_db`) | Quản lý sản phẩm đa ngành (Book, Electronics, Fashion) |
| | `cart-service` | 8004 | PostgreSQL (`cart_db`) | Lưu trữ giỏ hàng tạm thời và đồng bộ |
| | `order-service` | 8005 | PostgreSQL (`order_db`) | Xử lý quy trình đặt hàng, cập nhật kho (State Machine) |
| | `payment-service` | 8006 | PostgreSQL (`payment_db`) | Thanh toán sandbox MoMo, VNPay, COD |
| | `shipping-service` | 8007 | PostgreSQL (`shipping_db`) | Vận chuyển và cập nhật mã theo dõi vận đơn |
| | `review-service` | 8008 | PostgreSQL (`review_db`) | Đánh giá & xếp hạng sản phẩm (1-5 sao kèm ảnh) |
| | `notification-service`| 8009 | PostgreSQL (`notification_db`)| Thông báo Email, SMS, Web Push qua hàng đợi RabbitMQ |
| **Hệ thống AI** | `ai-recommendation`| 8010 | Neo4j Graph + Redis | Gợi ý Hybrid: LSTM + Knowledge Graph + RAG |
| | `ai-search` | 8011 | Elasticsearch | Tìm kiếm ngữ nghĩa, gợi ý từ khóa |
| | `ai-chatbot` | 8012 | FAISS Vector DB + Ollama | Chatbot hỗ trợ: NLP Intent, NER, Cypher, Fallback |
| | `ai-analytics` | 8013 | PostgreSQL | Dự đoán doanh số bán hàng, phân tích xu hướng |
| **Client** | `frontend` | 3000 | - | Giao diện React SPA + Tailwind CSS |

---

## 3. Công Nghệ Sử Dụng

- **Backend:** Python 3.11+, Django 5.0, Django REST Framework, SimpleJWT.
- **Frontend:** React 18, Redux Toolkit, Tailwind CSS, Axios, Playwright (Scraper).
- **Cơ sở dữ liệu & Caching:** PostgreSQL 16, Redis 7 (Cache & Queue), Neo4j (Knowledge Graph).
- **AI/ML Engine:** 
  - **Mô hình ngôn ngữ lớn (LLM):** Ollama (chạy `llama3.2:3b`, `qwen2.5:7b`, `gemma2:9b`).
  - **Gợi ý chuỗi:** PyTorch (Mô hình BiLSTM kết hợp cơ chế Attention).
  - **Vector Database:** FAISS (sử dụng mô hình embedding `nomic-embed-text`).
- **DevOps:** Docker, Docker Compose, Nginx (Gateway Proxy), Prometheus + Grafana (Giám sát).

---

## 4. Hướng Dẫn Bắt Đầu Nhanh

### 4.1 Yêu cầu phần cứng tối thiểu
- **CPU:** 4 Cores+
- **RAM:** 16GB RAM (khuyến nghị có GPU rời nếu chạy các dòng model LLM 7B/9B cục bộ).
- **Hệ điều hành:** Windows/Linux/macOS đã cài Docker & Docker Compose v2+.

### 4.2 Thiết lập ban đầu
1. Sao chép cấu hình môi trường:
   ```bash
   cp .env.example .env
   ```
2. Khởi động toàn bộ cụm dịch vụ qua Docker Compose:
   ```bash
   docker-compose up --build -d
   ```
3. Chạy cơ chế di cư cơ sở dữ liệu (Database Migrations):
   ```bash
   docker-compose exec product-service python manage.py migrate
   docker-compose exec api-gateway python manage.py migrate
   # Áp dụng tương tự cho các service core khác
   ```

### 4.3 Cài đặt & cấu hình Mô hình LLM (Ollama)
Tải các mô hình phục vụ cho RAG và Chatbot:
```bash
# Tải mô hình embedding văn bản
docker-compose exec ollama ollama pull nomic-embed-text

# Tải các mô hình ngôn ngữ lớn
docker-compose exec ollama ollama pull llama3.2:3b
docker-compose exec ollama ollama pull qwen2.5:7b
```

---

## 5. Đồng Bộ Chỉ Mục AI & Đồ Thị Tri Thức

Để chatbot và hệ thống gợi ý hoạt động đúng, dữ liệu sản phẩm trong PostgreSQL cần được đồng bộ sang Neo4j và chỉ mục hóa sang FAISS.

### 5.1 Đồng bộ sang Neo4j Knowledge Graph
Chạy lệnh quản lý trong service `ai-recommendation` để xây dựng đồ thị quan hệ:
```bash
docker-compose exec ai-recommendation python manage.py sync_to_neo4j --rebuild
```
*Lệnh này sẽ tạo các nút `(:User)`, `(:Product)`, `(:Category)` và liên kết `[:CHILD_OF]`, `[:BUY]`, `[:VIEW]` tương ứng.*

### 5.2 Xây dựng chỉ mục vector FAISS
Chạy lệnh quản lý trong service `ai-chatbot` để tạo cơ sở dữ liệu tìm kiếm ngữ nghĩa:
```bash
docker-compose exec ai-chatbot python manage.py build_ai_index
```
*Sau khi chạy thành công, tệp chỉ mục `chatbot.index` và siêu dữ liệu `meta.json` sẽ được lưu xuống ổ đĩa.*

---

## 6. Luồng Nghiệp Vụ & Pipeline AI

### 6.1 Gợi ý kết hợp (Hybrid Recommendation Pipeline)
Hệ thống sử dụng công thức tính điểm hỗn hợp cho mỗi sản phẩm để tối ưu hóa khả năng gợi ý cá nhân hóa:
$$\text{Final Score} = w_1 \times \text{LSTM} + w_2 \times \text{Graph} + w_3 \times \text{RAG}$$
- **LSTM:** Dự đoán dựa trên chuỗi hành vi mua sắm gần đây (BiLSTM + Attention).
- **Graph:** Khai thác các sản phẩm tương tự mà người dùng cùng nhóm đã mua qua Neo4j.
- **RAG:** Đo độ tương đồng ngữ nghĩa của mô tả sản phẩm.

### 6.2 Xử lý của Chatbot thông minh
1. **Trích xuất thông tin (Query Parser):** Trích xuất danh mục, khoảng giá, thương hiệu từ câu hỏi tiếng Việt của khách hàng (NER).
2. **Cypher Guard:** Tạo truy vấn Neo4j an toàn, kiểm tra chặt chẽ giá (`toInteger(p.price)`) để tránh đưa ra sản phẩm vượt ngân sách.
3. **Semantic Fallback:** Nếu đồ thị không có kết quả, chatbot tự động truy vấn chỉ mục FAISS để tìm sản phẩm mô tả tương đồng.
4. **Anti-Hallucination:** Ngăn chặn ảo tưởng của LLM bằng việc bắt buộc trích dẫn mã `[ID: xxx]` và chặn các câu hỏi bẫy về sản phẩm không tồn tại.

---

## 7. Pipeline Đánh Giá & Kiểm Thử Tự Động

### 7.1 Chạy Test Suite Tích Hợp (Automated QA)
Hệ thống đi kèm bộ kiểm thử hồi quy tự động kiểm soát chất lượng phản hồi AI, Tracing và độ trễ:
```bash
# Chạy toàn bộ test suite
pytest tests/test_ai_system.py -v

# Chạy test theo nhóm nhãn (marker)
pytest tests/test_ai_system.py -v -m grounding   # Kiểm tra chống ảo tưởng dữ liệu
pytest tests/test_ai_system.py -v -m tracing     # Kiểm tra truyền dẫn X-Trace-Id
pytest tests/test_ai_system.py -v -m performance # Kiểm tra tốc độ phản hồi SLA
pytest tests/test_ai_system.py -v -m hybrid      # Kiểm tra tìm kiếm hỗn hợp
```

### 7.2 Đánh Giá Mô Hình (LLM-as-a-Judge)
Pipeline đánh giá tự động so sánh hiệu năng các mô hình LLM trên 4 bộ dữ liệu (synthetic & real data):
```bash
python scripts/evaluation/evaluate_models.py
```
*Script sẽ tự động giải phóng VRAM bằng cách dọn dẹp bộ nhớ đệm Ollama sau mỗi lượt chạy của mô hình. Kết quả tổng hợp sẽ được ghi vào `results/evaluation_all_models.csv` và các biểu đồ so sánh xuất ra thư mục `results/charts/`.*

---

## 8. Địa Chỉ Truy Cập Dịch Vụ (Local)

- **Giao diện Client:** `http://localhost:3000`
- **Cổng API Gateway:** `http://localhost:8000`
- **Tài liệu API (Swagger):** `http://localhost:8000/api/docs/`
- **Trang Quản Trị (Admin Panel):** `http://localhost:8000/admin/`
- **Giao diện Giám sát Grafana:** `http://localhost:3001`
- **Giao diện quản lý hàng đợi RabbitMQ:** `http://localhost:15672` (Tài khoản: `guest`/`guest`)
