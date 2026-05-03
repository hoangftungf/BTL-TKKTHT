# Yêu Cầu Tiểu Luận - Kiến Trúc và Thiết Kế Phần Mềm

## Thông Tin Chung
- **Đề tài:** Xây dựng Hệ thống E-Commerce theo Microservices và AI
- **GVHD:** Trần Đình Quế
- **Ngày:** 15 tháng 4 năm 2026

---

## Hạn Nộp

| Version | Hạn nộp | Tên file |
|---------|---------|----------|
| Version 01 | 23:30, Thứ Hai 27/04 | `tieuluan.v01_Lớp.nhóm_tenHosinhvien.PDF` |
| Version 02 | 23:30, Thứ Hai 11/05 | `tieuluan.v02_Lớp.nhóm_tenHosinhvien.PDF` |
| Final | 23:30, Trước ngày thi 1 ngày | `tieuluan.final_Lớp.nhóm_tenHosinhvien.PDF` |

**Lưu ý:** Sinh viên mang theo bản in khi đi thi. Bản in có viết tay/vẽ tay nhiều sẽ được điểm cộng.

---

## Chương 1: Từ Monolithic đến Microservices và DDD

### Nội dung cần trình bày:
- [ ] Giới thiệu Monolithic Architecture (khái niệm, cấu trúc, ưu/nhược điểm)
- [ ] Microservices Architecture (khái niệm, đặc điểm, so sánh với Monolithic)
- [ ] Domain Driven Design (DDD)
  - Entity, Value Object, Aggregate, Bounded Context
  - Context Map
- [ ] Case Study Healthcare (luyện phân rã hệ thống)

---

## Chương 2: Phát Triển Hệ E-Commerce Microservices

### 2.1 Functional Requirements
- [ ] Quản lý sản phẩm (đa domain: book, electronics, fashion)
- [ ] Quản lý người dùng (admin, staff, customer)
- [ ] Giỏ hàng (cart)
- [ ] Đặt hàng (order)
- [ ] Thanh toán (payment)
- [ ] Giao hàng (shipping)
- [ ] Tìm kiếm và gợi ý sản phẩm

### 2.2 Non-functional Requirements
- [ ] Scalability: scale từng service độc lập
- [ ] High Availability: hệ thống luôn sẵn sàng
- [ ] Security: JWT, authentication
- [ ] Maintainability: dễ bảo trì

### 2.3 Bounded Contexts (6 Services)
| Service | Database | Mô tả |
|---------|----------|-------|
| user-service | MySQL | Quản lý người dùng, phân quyền RBAC |
| product-service | PostgreSQL | Sản phẩm: Book, Electronics, Fashion |
| cart-service | - | Giỏ hàng |
| order-service | - | Đơn hàng |
| payment-service | - | Thanh toán (Pending/Success/Failed) |
| shipping-service | - | Giao hàng (Processing/Shipping/Delivered) |

### 2.4 Bài Tập Thực Hành
- [ ] Vẽ Class Diagram cho toàn bộ hệ thống bằng Visual Paradigm
- [ ] Mapping Class Diagram sang Database Schema
- [ ] Triển khai database bằng MySQL/PostgreSQL

### 2.5 Checklist Đánh Giá Chương 2
- [ ] Có sơ đồ class đúng UML
- [ ] Có mapping rõ ràng sang database
- [ ] Database tách riêng từng service
- [ ] Có sử dụng cả MySQL và PostgreSQL

---

## Chương 3: AI Service Cho Tư Vấn Sản Phẩm

### 3.1 Mục Tiêu
Xây dựng hệ thống AI gợi ý sản phẩm dựa trên:
- Hành vi người dùng (click, search, add-to-cart)
- Quan hệ sản phẩm (similarity)
- Ngữ cảnh truy vấn (chatbot)

### 3.2 Thành Phần AI Service
| Thành phần | Công nghệ | Mô tả |
|------------|-----------|-------|
| LSTM Model | PyTorch/TensorFlow | Dự đoán sản phẩm tiếp theo từ chuỗi hành vi |
| Knowledge Graph | Neo4j | Quan hệ User-Product (BUY, VIEW, SIMILAR) |
| RAG | FAISS/ChromaDB + LLM | Retrieval-Augmented Generation |
| Hybrid Model | - | Kết hợp: `final_score = w1*lstm + w2*graph + w3*rag` |

### 3.3 Hai Dạng AI Service
1. **Recommendation List**
   - API: `GET /recommend?user_id=1`
   - Output: `[101, 102, 205]`

2. **Chatbot Tư Vấn**
   - API: `POST /chatbot`
   - Pipeline: NLP hiểu intent → Retrieve sản phẩm → Generate response

### 3.4 Tech Stack AI Service
- PyTorch/TensorFlow (LSTM)
- Neo4j (Knowledge Graph)
- FAISS (Vector DB)
- FastAPI (service framework)

### 3.5 Bài Tập Thực Hành
- [ ] Xây dựng model LSTM đơn giản
- [ ] Tạo graph trong Neo4j
- [ ] Implement API recommendation
- [ ] Xây dựng chatbot cơ bản

### 3.6 Checklist Đánh Giá Chương 3
- [ ] Có pipeline AI rõ ràng
- [ ] Có model (LSTM)
- [ ] Có Graph và RAG
- [ ] Có API hoạt động

---

## Chương 4: Xây Dựng Hệ Thống Hoàn Chỉnh

### 4.1 Kiến Trúc Tổng Thể
```
ecom-final/
|-- gateway/
|   |-- nginx.conf          // API Gateway - Entry point
|-- user-service/           // staff, admin, customer
|-- product-service/        // 10 nhóm loại sản phẩm
|-- cart-service/
|-- order-service/
|-- payment-service/
|-- ai-service/
|-- infrastructure/
|   |-- docker-compose.yml
```

### 4.2 Nguyên Tắc Thiết Kế
- [ ] Mỗi service có database riêng
- [ ] Giao tiếp qua REST API
- [ ] Không truy cập DB của service khác
- [ ] Loose Coupling, High Cohesion
- [ ] Fault Isolation

### 4.3 Yêu Cầu Triển Khai
- [ ] API Gateway (Nginx) - routing, authentication
- [ ] JWT Authentication
- [ ] Docker hóa toàn bộ hệ thống
- [ ] Docker Compose cho development
- [ ] Kubernetes (Optional) cho production

### 4.4 Luồng Hệ Thống End-to-End (Use Case: Mua Hàng)
1. User login (user-service)
2. Xem sản phẩm (product-service)
3. Add to cart (cart-service)
4. Tạo order (order-service)
5. Thanh toán (payment-service)
6. Giao hàng (shipping-service)

### 4.5 Service Communication
- **Synchronous:** REST API over HTTP
- **Asynchronous:** Message queues (Redis, RabbitMQ) - event-driven

### 4.6 Security
- [ ] JWT-based authentication
- [ ] API Gateway validation
- [ ] Role-based access control (RBAC)

### 4.7 Logging & Monitoring (Optional)
- Logging: ELK stack
- Monitoring: Prometheus + Grafana

### 4.8 Bài Tập Thực Hành
- [ ] Triển khai các service bằng Django
- [ ] Kết nối qua API
- [ ] Docker hóa hệ thống
- [ ] Test full flow mua hàng + kết quả tư vấn

### 4.9 Checklist Đánh Giá Chương 4
- [ ] Có API Gateway
- [ ] Có JWT Auth
- [ ] Có Docker chạy được
- [ ] Có flow order → payment → shipping

---

## Tổng Hợp Checklist Toàn Bộ Dự Án

### Thiết Kế
- [ ] Class Diagram (Visual Paradigm) - export PNG/PDF
- [ ] Context Map (DDD)
- [ ] Database Schema cho từng service
- [ ] Sequence Diagram cho luồng mua hàng

### Backend Services (Django)
- [ ] user-service (RBAC: admin, staff, customer)
- [ ] product-service (Book, Electronics, Fashion)
- [ ] cart-service
- [ ] order-service
- [ ] payment-service
- [ ] shipping-service

### AI Service (FastAPI)
- [ ] LSTM recommendation model
- [ ] Neo4j Knowledge Graph
- [ ] RAG với Vector DB (FAISS/ChromaDB)
- [ ] Chatbot API

### Infrastructure
- [ ] Dockerfile cho mỗi service
- [ ] docker-compose.yml
- [ ] Nginx API Gateway config
- [ ] JWT Authentication

### Testing
- [ ] API hoạt động đúng
- [ ] Full flow mua hàng hoạt động
- [ ] AI recommendation hoạt động
- [ ] Chatbot hoạt động

---

## Kết Luận
- Microservices phù hợp hệ thống lớn
- DDD giúp thiết kế rõ ràng
- AI nâng cao trải nghiệm người dùng
