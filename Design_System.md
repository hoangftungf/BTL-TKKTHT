# Design System - BTL TKKTHT E-commerce AI Platform

## Mục lục

1. [Tổng quan hệ thống](#1-tổng-quan-hệ-thống)
2. [Kiến trúc tổng thể](#2-kiến-trúc-tổng-thể)
3. [Luồng nghiệp vụ chính](#3-luồng-nghiệp-vụ-chính)
4. [Backend Services](#4-backend-services)
5. [API Endpoints](#5-api-endpoints)
6. [Frontend](#6-frontend)
7. [AI Services](#7-ai-services)
8. [Cơ sở dữ liệu](#8-cơ-sở-dữ-liệu)
9. [Giao tiếp liên service](#9-giao-tiếp-liên-service)
10. [Triển khai](#10-triển-khai)

---

## 1. Tổng quan hệ thống

**Tên dự án:** Hệ thống Thương mại điện tử tích hợp AI (E-commerce AI Platform)

**Công nghệ chính:**
- **Backend:** Django, Django REST Framework (13 microservices)
- **Frontend:** React 18, Redux Toolkit, TailwindCSS
- **AI:** Ollama (Llama3/Qwen2.5/Gemma2), Neo4j Knowledge Graph, FAISS Vector Store
- **Database:** PostgreSQL 16 (multi-database), Redis 7, Neo4j 5
- **Message Queue:** RabbitMQ + Celery
- **Gateway:** Nginx + API Gateway (Django)
- **Container:** Docker Compose (17 containers)

**Mục tiêu:** Đồ án tốt nghiệp - Đánh giá 3 mô hình LLM (Llama3, Qwen2.5, Gemma2) trên 3 tập dữ liệu (synthetic_small, synthetic_large, real_tiki).

---

## 2. Kiến trúc tổng thể

### 2.1 Sơ đồ kiến trúc

```
┌──────────────┐     ┌─────────────────────────────────────────────┐
│   Browser    │────▶│              Nginx (80/443)                 │
│  (React SPA) │     │  Reverse Proxy + Rate Limit + SSL           │
└──────────────┘     └──────────┬──────────────────────────┬───────┘
                                │                          │
                        ┌───────▼────────┐          ┌──────▼──────┐
                        │  /api/*        │          │  /*         │
                        │                │          │             │
                  ┌─────▼──────────────┐  │    ┌─────▼─────────┐  │
                  │   API Gateway      │◀─┘    │  Frontend     │  │
                  │   (Port 8000)      │       │  (Port 3000)  │  │
                  └─────┬──────────────┘       └───────────────┘  │
                        │                                          │
        ┌───────────────┼───────────────────┬──────────────┐      │
        ▼               ▼                   ▼              ▼       │
┌───────────────┐ ┌───────────┐ ┌───────────────────┐ ┌──────────┐│
│ Core Services │ │ Business  │ │   AI Services     │ │Infra     ││
│               │ │ Services  │ │                   │ │          ││
│ Auth    8001  │ │ Payment   │ │ Recommendation8010│ │Postgres  ││
│ User    8002  │ │   8006    │ │                   │ │  5432    ││
│ Product 8003  │ │ Shipping  │ │ Search     8011   │ │          ││
│ Cart    8004  │ │   8007    │ │                   │ │Redis     ││
│ Order   8005  │ │ Review    │ │ Chatbot    8012   │ │  6379    ││
│               │ │   8008    │ │                   │ │          ││
│               │ │Notificatio│ │ Analytics  8013   │ │RabbitMQ  ││
│               │ │   8009    │ │                   │ │  5672    ││
└───────────────┘ └───────────┘ └───────────────────┘ │Neo4j     ││
                                                      │7474/7687 ││
                                                      │Ollama    ││
                                                      │ 11434    ││
                                                      └──────────┘│
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Danh sách containers (17 services)

| Service | Image | Port | Database |
|---------|-------|------|----------|
| `postgres` | postgres:16-alpine | 5432 | 13 databases |
| `redis` | redis:7-alpine | 6379 | - |
| `rabbitmq` | rabbitmq:3-management-alpine | 5672, 15672 | - |
| `api-gateway` | custom | 8000 | - |
| `auth-service` | custom | 8001 | auth_db |
| `user-service` | custom | 8002 | user_db |
| `product-service` | custom | 8003 | product_db |
| `cart-service` | custom | 8004 | cart_db |
| `order-service` | custom | 8005 | order_db |
| `payment-service` | custom | 8006 | payment_db |
| `shipping-service` | custom | 8007 | shipping_db |
| `review-service` | custom | 8008 | review_db |
| `notification-service` | custom | 8009 | notification_db |
| `ai-recommendation` | custom | 8010 | recommendation_db |
| `ai-search` | custom | 8011 | search_db |
| `ai-chatbot` | custom | 8012 | chatbot_db |
| `ai-analytics` | custom | 8013 | analytics_db |
| `ollama` | ollama/ollama | 11434 | - |
| `neo4j` | neo4j:5-community | 7474, 7687 | - |
| `frontend` | custom (node:18) | 3000 | - |
| `nginx` | nginx:alpine | 80, 443 | - |

### 2.3 Network

- **Docker Network:** `ecommerce-network` (bridge)
- **Nginx Rate Limit:** 10 requests/second per IP (burst 20)
- **Gzip:** Enabled cho JSON, JS, CSS, HTML

---

## 3. Luồng nghiệp vụ chính

### 3.1 Luồng xác thực (Authentication Flow)

```
┌─────────┐     ┌────────────┐     ┌──────────────┐     ┌──────────────┐
│  User   │     │  Frontend  │     │ API Gateway  │     │ Auth Service │
│         │     │  (React)   │     │  (Port 8000) │     │  (Port 8001) │
└────┬────┘     └──────┬─────┘     └──────┬───────┘     └──────┬───────┘
     │                  │                  │                     │
     │ 1. POST /login   │                  │                     │
     │─────────────────▶│                  │                     │
     │                  │ 2. POST /api/auth/login/               │
     │                  │─────────────────▶│                     │
     │                  │                  │ 3. POST /login/     │
     │                  │                  │────────────────────▶│
     │                  │                  │                     │
     │                  │                  │◀────────────────────│
     │                  │                  │   {access, refresh} │
     │                  │◀────────────────│                     │
     │ 4. Lưu tokens    │                  │                     │
     │    localStorage  │                  │                     │
     │◀────────────────│                  │                     │
     │                  │                  │                     │
     │ 5. Gọi API       │                  │                     │
     │    (có Bearer)   │                  │                     │
     │─────────────────▶│ 6. Axios interceptor thêm Bearer token │
     │                  │─────────────────▶│ 7. Proxy request    │
     │                  │                  │────▶ Service ──────▶│
     │                  │                  │                     │
     │                  │                  │◀─── Service ───────│
     │                  │◀────────────────│                     │
     │◀────────────────│                  │                     │
     │                  │                  │                     │
```

**Chi tiết:**
1. User gửi email/password → `POST /api/auth/login/`
2. Auth service xác thực, trả về JWT access token (15 phút) + refresh token (7 ngày)
3. Frontend lưu tokens vào localStorage
4. Mọi request sau đó đều có header `Authorization: Bearer <access_token>`
5. Axios interceptor tự động refresh token khi 401:
   - Gọi `POST /api/auth/refresh/` với refresh token
   - Lưu access token mới, retry request gốc
   - Nếu refresh thất bại → redirect `/login`

### 3.2 Luồng mua hàng (Checkout Flow)

```
┌──────┐  ┌────────┐  ┌──────────┐  ┌───────┐  ┌────────┐  ┌──────────┐  ┌──────────────┐
│ User │  │ Cart   │  │ Order    │  │Payment│  │Ship   │  │Notifi-  │  │Recommend    │
│      │  │Service │  │Service   │  │Service│  │Service│  │cation   │  │Service       │
└──┬───┘  └───┬────┘  └────┬─────┘  └───┬───┘  └───┬───┘  └──┬──────┘  └──────┬───────┘
   │          │            │             │         │         │                │
   │1. POST /cart/items/   │             │         │         │                │
   │─────────▶│            │             │         │         │                │
   │          │2. Validate stock qua product-service                      │
   │          │◀───────────│─────────────│─────────│─────────│──────────────│
   │◀─────────│            │             │         │         │                │
   │          │            │             │         │         │                │
   │3. POST /orders/       │             │         │         │                │
   │────────────────────────────────────▶│         │         │                │
   │          │            │             │         │         │                │
   │          │4. Lấy cart từ cart-service│         │         │                │
   │          │◀───────────│             │         │         │                │
   │          │5. Kiểm tra stock         │         │         │                │
   │          │◀───────────│─────────────│─────────│─────────│────────────────│
   │          │            │6. Tạo đơn +  │         │         │                │
   │          │            │   items     │         │         │                │
   │          │            │7. Xóa cart  │         │         │                │
   │          │◀───────────│             │         │         │                │
   │          │            │8. Gửi notification                    │
   │          │            │──────────────────────────────────────▶│
   │          │            │9. Track purchase behavior             │
   │          │            │───────────────────────────────────────────────────▶│
   │◀─────────│────────────│             │         │         │                │
   │          │            │             │         │         │                │
   │10. POST /payments/cod/│             │         │         │                │
   │─────────────────────────────────────────────▶│         │                │
   │          │            │             │◀────────│         │                │
   │          │            │             │         │         │                │
   │          │            │11. Tạo shipment       │         │                │
   │          │            │────────────────────────────────▶│                │
   │          │            │             │         │         │                │
```

**Chi tiết luồng:**

1. **Thêm giỏ hàng:** User thêm sản phẩm → Cart service validate stock qua Product service
2. **Tạo đơn hàng:** User ấn "Đặt hàng" → Order service:
   - Lấy cart từ Cart service
   - Kiểm tra stock còn không
   - Tạo Order + OrderItems
   - Clear cart
   - Gửi notification cho user và admin
   - Track `purchase` behavior
3. **Thanh toán:** User chọn phương thức (COD/MoMo/VNPay)
4. **Vận chuyển:** Tạo shipment record
5. **Xác nhận:** User ấn "Đã nhận được hàng" → Đơn hoàn thành

### 3.3 Luồng đánh giá sản phẩm (Review Flow)

```
┌────────┐  ┌──────────┐  ┌──────────────┐  ┌────────────┐
│  User  │  │  Review  │  │ Order Service│  │  Product   │
│        │  │  Service │  │              │  │  Service   │
└───┬────┘  └────┬─────┘  └──────┬───────┘  └─────┬──────┘
    │            │                │                 │
    │ POST /reviews/             │                 │
    │───────────▶│               │                 │
    │            │ Kiểm tra order│                 │
    │            │ completed     │                 │
    │            │──────────────▶│                 │
    │            │◀──────────────│                 │
    │            │               │                 │
    │            │ Gửi notify    │                 │
    │            │ cho admin     │                 │
    │            │───▶ (notification-service)      │
    │◀───────────│               │                 │
    │            │               │                 │
    │            │ GET /product/:id/stats/         │
    │            │               │                 │
    │            │               │  Cập nhật       │
    │            │               │  rating_avg     │
    │            │               │  rating_count   │
    │            │◀──────────────│────────────────▶│
```

**Ràng buộc:**
- Mỗi user chỉ được review 1 lần cho 1 sản phẩm (unique_together: product_id + user_id)
- Chỉ user đã mua hàng (order completed) mới được review
- Admin có thể ẩn/hiện review

### 3.4 Luồng Chatbot AI

```
┌────────┐  ┌────────────┐  ┌───────────┐  ┌────────────┐  ┌────────┐  ┌─────────┐
│  User  │  │  Chatbot   │  │  Redis    │  │  Neo4j KG  │  │Ollama  │  │Product  │
│        │  │  Service   │  │  Cache    │  │            │  │LLM     │  │Service  │
└───┬────┘  └─────┬──────┘  └─────┬─────┘  └──────┬─────┘  └───┬────┘  └────┬────┘
    │             │                │                │            │            │
    │ POST /chat/ │                │                │            │            │
    │────────────▶│                │                │            │            │
    │             │1. Check cache  │                │            │            │
    │             │───────────────▶│                │            │            │
    │             │ Cache miss     │                │            │            │
    │             │◀───────────────│                │            │            │
    │             │                │                │            │            │
    │             │2. Detect intent│                │            │            │
    │             │ (pattern match)│                │            │            │
    │             │                │                │            │            │
    │             │3. Query KG     │                │            │            │
    │             │────────────────────────────────▶│            │            │
    │             │  Products/RAG  │                │            │            │
    │             │◀────────────────────────────────│            │            │
    │             │                │                │            │            │
    │             │4. Build prompt │                │            │            │
    │             │ (context + query)               │            │            │
    │             │─────────────────────────────────────────────▶│            │
    │             │  LLM Response  │                │            │            │
    │             │◀─────────────────────────────────────────────│            │
    │             │                │                │            │            │
    │             │5. Guardrails   │                │            │            │
    │             │ Filter output  │                │            │            │
    │             │                │                │            │            │
    │             │6. Cache result │                │            │            │
    │             │───────────────▶│                │            │            │
    │◀────────────│                │                │            │            │
    │             │                │                │            │            │
```

**Xử lý đặc biệt:**
- **Semantic Cache:** Lưu embedding query + response, threshold cosine similarity 0.92
- **Guardrails:** Chặn nhắc đến đối thủ cạnh tranh, bắt buộc trích dẫn sản phẩm
- **Fallback:** Nếu KG không có kết quả → hỏi lại user hoặc trả lời chung

### 3.5 Luồng cập nhật sản phẩm lên Knowledge Graph

Khi sản phẩm được tạo/cập nhật (Product service signal):
1. Signal `product_saved` / `product_deleted` được kích hoạt
2. Gửi request đến `POST /api/chatbot/update-product/`
3. Chatbot service tạo Celery task `update_product_knowledge_base_async`
4. Task này đồng bộ dữ liệu sản phẩm (kèm variants, images) lên Neo4j

### 3.6 Luồng Tracking hành vi người dùng

```
┌──────────┐  ┌──────────────┐  ┌───────────────┐  ┌───────────┐  ┌──────────┐
│ Any      │  │ Shared       │  │Recommendation │  │  Neo4j    │  │  FAISS   │
│ Service  │  │ Tracking     │  │  Service      │  │  KG       │  │  Vector  │
│          │  │ Client       │  │               │  │           │  │  Store   │
└────┬─────┘  └──────┬───────┘  └──────┬────────┘  └─────┬─────┘  └────┬─────┘
     │               │                  │                  │             │
     │ track(action, │                  │                  │             │
     │  user, product)                  │                  │             │
     │──────────────▶│                  │                  │             │
     │               │ POST /track/     │                  │             │
     │               │─────────────────▶│                  │             │
     │               │                  │                  │             │
     │               │                  │ 1. Lưu UserBehavior            │
     │               │                  │    (PostgreSQL)                │
     │               │                  │                  │             │
     │               │                  │ 2. Tạo/lấy User                │
     │               │                  │    node trong Neo4j            │
     │               │                  │─────────────────▶              │
     │               │                  │ 3. Tạo/lấy Product             │
     │               │                  │    node trong Neo4j            │
     │               │                  │─────────────────▶              │
     │               │                  │ 4. Tạo RELATIONSHIP            │
     │               │                  │    (VIEWED/PURCHASED/...)      │
     │               │                  │─────────────────▶              │
     │               │                  │                  │             │
     │               │                  │ 5. Nếu view: tạo               │
     │               │                  │    embedding → FAISS           │
     │               │                  │──────────────────────────────▶│
```

**8 action types được track:** view_product, click_product, add_to_cart, remove_from_cart, purchase, add_to_wishlist, search, view_category

**Score weights cho Collaborative Filtering:**
| Action | Weight |
|--------|--------|
| view_product | 1.0 |
| click_product | 1.5 |
| add_to_cart | 3.0 |
| remove_from_cart | -1.0 |
| add_to_wishlist | 2.5 |
| purchase | 5.0 |
| search | 0.5 |
| view_category | 0.5 |

---

## 4. Backend Services

### 4.1 API Gateway

- **Port:** 8000
- **Framework:** Django REST Framework
- **Chức năng:** Proxy tất cả request tới microservices tương ứng

**Middleware:**
- `RateLimitMiddleware` - Redis-based rate limiting (100 req/60s per IP, exempt /admin/ và /health/)
- CORS headers
- Standard Django middlewares

**Proxy views (BaseProxyView pattern):**
- Tất cả các proxy view kế thừa từ `BaseProxyView`
- Hỗ trợ GET, POST, PUT, PATCH, DELETE
- Timeout 30s, trả về 503 nếu service unavailable, 504 nếu timeout

### 4.2 Auth Service

- **Port:** 8001
- **DB:** auth_db
- **Model:** `User` (custom AbstractBaseUser)
- **Auth:** JWT (SimpleJWT), email-based

**User Model Fields:**
| Field | Type | Description |
|-------|------|-------------|
| id | UUID (PK) | Primary key |
| email | EmailField (unique) | Đăng nhập bằng email |
| phone | CharField(15) | Số điện thoại |
| role | CharField(20) | customer / seller / admin |
| is_active | BooleanField | Kích hoạt |
| is_staff | BooleanField | Staff status |
| is_verified | BooleanField | Đã xác minh |
| last_login_ip | GenericIPAddressField | IP cuối |

### 4.3 User Service

- **Port:** 8002
- **DB:** user_db

**Models:**
- `Profile` - full_name, avatar, gender, date_of_birth (1-1 với user_id)
- `Address` - recipient_name, phone, address_type (home/office/other), province/district/ward/street_address, is_default
- `Wishlist` - user_id + product_id (unique together)

### 4.4 Product Service

- **Port:** 8003
- **DB:** product_db
- **Search:** PostgreSQL full-text search (SearchVector/ SearchQuery)

**Models:**
- `Category` - name, slug, parent (self-FK), level (auto-calc), is_active, display_order
- `Product` - name, slug, sku, price, compare_price, category, brand, status (draft/active/inactive/out_of_stock), stock, specifications (JSON), is_featured, rating_avg, rating_count
- `ProductImage` - product (FK), image, is_primary, display_order
- `ProductVariant` - product (FK), name, sku, price, stock, attributes (JSON)

**Caching:** Redis cache 5 phút cho product list/detail, 15 phút cho categories

### 4.5 Cart Service

- **Port:** 8004
- **DB:** cart_db

**Models:**
- `Cart` - user_id (unique 1-1), total_items (property), total_amount (property)
- `CartItem` - cart (FK), product_id, variant_id, product_name, product_image, price, quantity, subtotal (property)

**Self-healing:** Tự động fetch product image từ product-service nếu bị thiếu

### 4.6 Order Service

- **Port:** 8005
- **DB:** order_db

**Models:**
- `Order` - order_number (auto ORD+datetime+uuid), user_id, recipient info, shipping address, subtotal/shipping_fee/discount/total, status (8 states), payment_status, payment_method, cancel_reason, timestamps
- `OrderItem` - order (FK), product_id, variant_id, product_name, product_image, sku, price, quantity, subtotal
- `OrderStatusHistory` - order (FK), status, note, created_by

**Order status flow:**
```
pending → confirmed → processing → shipping → delivered → completed
    ↓          ↓
 cancelled   cancelled
    ↓
 refunded
```

### 4.7 Payment Service

- **Port:** 8006
- **DB:** payment_db

**Models:**
- `Payment` - order_id, transaction_id (unique), method (momo/vnpay/cod/bank_transfer), amount, status, provider_transaction_id, provider_response (JSON), payment_url
- `Refund` - payment (FK), refund_id, amount, reason, status

**Tích hợp:**
- **MoMo:** partner_code, access_key, secret_key, endpoint
- **VNPay:** tmn_code, hash_secret, url

### 4.8 Shipping Service

- **Port:** 8007
- **DB:** shipping_db

**Models:**
- `Shipment` - order_id, tracking_number, carrier, status (7 states), weight, shipping_fee, estimated_delivery, actual_delivery
- `TrackingEvent` - shipment (FK), status, location, description

### 4.9 Review Service

- **Port:** 8008
- **DB:** review_db

**Models:**
- `Review` - product_id, user_id, order_id, rating (1-5), title, content, is_verified (auto via order check), is_visible, helpful_count
- `ReviewImage` - review (FK), image
- `ReviewReply` - review (FK), user_id, content, is_seller

**Ràng buộc:** unique_together = [product_id, user_id]

### 4.10 Notification Service

- **Port:** 8009
- **DB:** notification_db

**Models:**
- `Notification` - user_id, type (order/payment/shipping/promotion/system), channel (in_app/email/sms/push), title, message, data (JSON), is_read, read_at
- `NotificationTemplate` - code (unique), type, title_template, message_template, is_active

---


## 5. API Endpoints

### 5.1 Auth (`/api/auth/`)


| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| POST | `/api/auth/register/` | - | Đăng ký tài khoản |
| POST | `/api/auth/login/` | - | Đăng nhập, trả về JWT |
| POST | `/api/auth/refresh/` | - | Refresh access token |
| POST | `/api/auth/logout/` | Bearer | Đăng xuất (blacklist refresh) |
| GET | `/api/auth/me/` | Bearer | Lấy thông tin user hiện tại |
| PUT | `/api/auth/me/` | Bearer | Cập nhật thông tin user |
| GET | `/api/auth/users/` | Admin | Danh sách users (admin) |
| PUT | `/api/auth/users/<id>/` | Admin | Cập nhật user (admin) |

### 5.2 User (`/api/users/`)

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/users/profile/` | Bearer | Lấy profile |
| PUT | `/api/users/profile/` | Bearer | Cập nhật profile |
| GET | `/api/users/addresses/` | Bearer | Danh sách địa chỉ |
| POST | `/api/users/addresses/` | Bearer | Thêm địa chỉ |
| GET | `/api/users/addresses/<id>/` | Bearer | Chi tiết địa chỉ |
| PUT | `/api/users/addresses/<id>/` | Bearer | Sửa địa chỉ |
| DELETE | `/api/users/addresses/<id>/` | Bearer | Xóa địa chỉ |
| GET | `/api/users/wishlist/` | Bearer | Danh sách yêu thích |
| POST | `/api/users/wishlist/` | Bearer | Thêm yêu thích |
| DELETE | `/api/users/wishlist/` | Bearer | Xóa yêu thích (theo product_id) |

### 5.3 Product (`/api/products/`)

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/products/` | - | Danh sách sản phẩm (filter: category, brand, price, featured, ordering, page) |
| POST | `/api/products/` | - | Tạo sản phẩm |
| GET | `/api/products/<id>/` | - | Chi tiết sản phẩm |
| PUT | `/api/products/<id>/` | - | Cập nhật sản phẩm |
| DELETE | `/api/products/<id>/` | - | Xóa sản phẩm |
| GET | `/api/products/search/?q=` | - | Full-text search |
| GET | `/api/products/suggest/?q=` | - | Gợi ý autocomplete |
| GET | `/api/products/categories/` | - | Danh mục gốc (cached 15ph) |
| POST | `/api/products/categories/` | - | Tạo danh mục |
| GET | `/api/products/category/<id>/` | - | Sản phẩm theo danh mục |
| POST | `/api/products/track/click/` | - | Track click sản phẩm |

### 5.4 Cart (`/api/cart/`)

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/cart/` | Bearer | Lấy giỏ hàng (tự động tạo nếu chưa có) |
| POST | `/api/cart/items/` | Bearer | Thêm item (validate stock) |
| PUT | `/api/cart/items/<id>/` | Bearer | Sửa số lượng (0 = xóa) |
| DELETE | `/api/cart/items/<id>/` | Bearer | Xóa item |
| DELETE | `/api/cart/clear/` | Bearer | Xóa toàn bộ giỏ |

### 5.5 Order (`/api/orders/`)

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/orders/` | Bearer | Danh sách đơn hàng |
| POST | `/api/orders/` | Bearer | Tạo đơn từ cart |
| GET | `/api/orders/<id>/` | Bearer | Chi tiết đơn + lịch sử |
| PUT | `/api/orders/<id>/cancel/` | Bearer | Hủy đơn (đang pending/confirmed) |
| GET | `/api/orders/<id>/track/` | Bearer | Tracking đơn hàng |
| PUT | `/api/orders/<id>/status/` | Admin | Cập nhật trạng thái |
| PUT | `/api/orders/<id>/confirm-received/` | Bearer | Xác nhận đã nhận hàng |

### 5.6 Payment (`/api/payments/`)

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| POST | `/api/payments/momo/` | Bearer | Tạo thanh toán MoMo |
| POST | `/api/payments/vnpay/` | Bearer | Tạo thanh toán VNPay |
| POST | `/api/payments/cod/` | Bearer | Tạo thanh toán COD |
| GET | `/api/payments/<order_id>/status/` | Bearer | Kiểm tra trạng thái |
| POST | `/api/payments/webhook/momo/` | - | MoMo webhook callback |
| GET | `/api/payments/vnpay/return/` | - | VNPay return URL |

### 5.7 Shipping (`/api/shipping/`)

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/shipping/` | Bearer | Danh sách shipments |
| GET | `/api/shipping/<id>/` | Bearer | Chi tiết shipment |
| GET | `/api/shipping/track/<code>/` | - | Tra cứu vận đơn |
| POST | `/api/shipping/rates/` | - | Tính phí vận chuyển |

### 5.8 Review (`/api/reviews/`)

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/reviews/` | - | Danh sách reviews |
| POST | `/api/reviews/` | Bearer | Tạo review (cần order completed) |
| GET | `/api/reviews/<id>/` | - | Chi tiết review |
| PUT | `/api/reviews/<id>/` | Bearer | Sửa review (owner) |
| DELETE | `/api/reviews/<id>/` | Bearer | Xóa review (owner) |
| GET | `/api/reviews/product/<id>/` | - | Reviews theo sản phẩm |
| GET | `/api/reviews/product/<id>/stats/` | - | Thống kê đánh giá |
| POST | `/api/reviews/replies/<review_id>/` | Bearer | Trả lời review |
| GET | `/api/reviews/admin-reviews/` | Admin | Danh sách all reviews |
| PATCH | `/api/reviews/admin-reviews/<id>/visibility/` | Admin | Ẩn/hiện review |

### 5.9 Notification (`/api/notifications/`)

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/notifications/` | Bearer | Danh sách (unread_count, filter type/is_read) |
| GET | `/api/notifications/<id>/` | Bearer | Chi tiết (auto mark read) |
| DELETE | `/api/notifications/<id>/` | Bearer | Xóa notification |
| POST | `/api/notifications/mark-read/` | Bearer | Đánh dấu đã đọc |
| POST | `/api/notifications/send/` | Admin | Gửi notification |

### 5.10 AI - Recommendation (`/api/recommendations/`)

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/recommendations/product/<id>/` | - | Similar products (CF) |
| GET | `/api/recommendations/user/` | Bearer | Personalized recommendations |
| GET | `/api/recommendations/trending/` | - | Trending products |
| GET | `/api/recommendations/frequently-bought/<id>/` | - | Mua cùng nhau |
| POST | `/api/recommendations/train/` | - | Train CF model |
| POST | `/api/recommendations/interaction/` | Bearer | Record interaction |
| POST | `/api/recommendations/track/` | - | Universal behavior tracking |
| GET | `/api/recommendations/hybrid/` | - | Hybrid recommendations |
| POST | `/api/recommendations/hybrid/chatbot/` | - | Hybrid chatbot |
| GET | `/api/recommendations/lstm/predict/` | Bearer | LSTM predictions |
| POST | `/api/recommendations/lstm/train/` | - | Train LSTM |
| GET | `/api/recommendations/graph/recommend/` | Bearer | KG recommendations |
| GET | `/api/recommendations/graph/similar/<id>/` | - | KG similar products |
| POST | `/api/recommendations/graph/sync/` | - | Sync Django → Neo4j |
| GET | `/api/recommendations/graph/stats/` | - | KG statistics |
| GET | `/api/recommendations/rag/search/` | - | Semantic search |
| POST | `/api/recommendations/rag/index/` | - | Index products |
| POST | `/api/recommendations/seed/` | - | Seed sample data |

### 5.11 AI - Search (`/api/search/`)

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/search/?q=` | - | Smart search |
| POST | `/api/search/` | - | Search with filters |
| GET | `/api/search/autocomplete/?q=` | - | Autocomplete suggestions |
| POST | `/api/search/index/` | - | Reindex products |

### 5.12 AI - Chatbot (`/api/chatbot/`)

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| POST | `/api/chatbot/chat/` | - | Chat (sync) |
| POST | `/api/chatbot/chat/stream/` | - | Chat (SSE streaming) |
| POST | `/api/chatbot/messages/<id>/rate/` | - | Đánh giá câu trả lời |
| POST | `/api/chatbot/update-product/` | - | Webhook cập nhật product KG |
| GET | `/api/chatbot/audit-quality/` | - | Audit chất lượng |
| GET | `/api/chatbot/conversations/` | - | Danh sách conversations |
| GET | `/api/chatbot/conversations/<id>/` | - | Chi tiết conversation |
| DELETE | `/api/chatbot/conversations/<id>/` | - | Xóa conversation |
| GET | `/api/chatbot/faqs/` | - | Danh sách FAQs |
| POST | `/api/chatbot/faqs/` | - | Tạo FAQ |

### 5.13 AI - Analytics (`/api/analytics/`)

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| GET | `/api/analytics/dashboard/` | - | Dashboard metrics |
| GET | `/api/analytics/sales/` | - | Sales report |
| GET | `/api/analytics/products/` | - | Product analytics |
| GET | `/api/analytics/predictions/` | - | Sales predictions |
| GET | `/api/analytics/customers/segments/` | - | Customer segments |
| GET | `/api/analytics/trends/` | - | Trend analysis |

### 5.14 System

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/health/` | Health check tất cả services |

---

## 6. Frontend

### 6.1 Tech Stack
- **Framework:** React 18 (Create React App)
- **State Management:** Redux Toolkit (6 slices)
- **Routing:** React Router v6
- **Styling:** TailwindCSS
- **HTTP Client:** Axios (interceptor: JWT + auto-refresh)

### 6.2 Redux Store

| Slice | State | Actions |
|-------|-------|---------|
| `authSlice` | user, tokens, isAuthenticated | login, register, logout, checkAuth, updateUser |
| `cartSlice` | items, totalItems, totalAmount | fetchCart, addItem, updateQuantity, removeItem, clearCart |
| `productSlice` | products, categories, featuredProducts, loading | fetchProducts, fetchCategories, fetchFeatured, fetchProductById |
| `orderSlice` | orders, currentOrder | fetchOrders, createOrder, cancelOrder, confirmReceived |
| `uiSlice` | sidebarOpen, modalOpen, notification | toggleSidebar, openModal, closeModal |
| `wishlistSlice` | items, productIds | fetchWishlist, addToWishlist, removeFromWishlist |

### 6.3 Routes

| Route | Component | Layout | Auth |
|-------|-----------|--------|------|
| `/` | HomePage | MainLayout | - |
| `/products` | ProductsPage | MainLayout | - |
| `/products/:id` | ProductDetailPage | MainLayout | - |
| `/search` | SearchPage | MainLayout | - |
| `/login` | LoginPage | MainLayout | - |
| `/register` | RegisterPage | MainLayout | - |
| `/cart` | CartPage | MainLayout | - |
| `/checkout` | CheckoutPage | MainLayout | Bearer |
| `/profile` | ProfilePage | MainLayout | Bearer |
| `/orders` | OrdersPage | MainLayout | Bearer |
| `/orders/:id` | OrderDetailPage | MainLayout | Bearer |
| `/admin-dashboard` | AdminDashboardPage | AdminLayout | Admin |
| `/admin-dashboard/products` | AdminProductsPage | AdminLayout | Admin |
| `/admin-dashboard/orders` | AdminOrdersPage | AdminLayout | Admin |
| `/admin-dashboard/reviews` | AdminReviewsPage | AdminLayout | Admin |
| `/admin-dashboard/users` | AdminUsersPage | AdminLayout | Admin |
| `/admin-dashboard/ai` | AdminAIPage | AdminLayout | Admin |
| `*` | NotFoundPage | MainLayout | - |

### 6.4 Components chính

| Component | Chức năng |
|-----------|-----------|
| `Chatbot` | Floating AI chatbot widget (global) |
| `Header` | Navigation + search + cart badge + user menu |
| `Footer` | Site footer |
| `CartDrawer` | Slide-in cart sidebar |
| `CartItem` | Cart item với quantity control |
| `ProductCard` | Product card cho grid |
| `ProductGrid` | Product grid layout |
| `ProductRecommendations` | AI-powered recommendations |
| `NotificationDropdown` | Bell icon + notification list |
| `AddressForm` | Form nhập địa chỉ |
| `LoginModal` | Login dialog |
| `ProtectedRoute` | Auth guard (redirect nếu chưa login) |
| `AdminRoute` | Admin guard (redirect nếu không phải admin) |

### 6.5 Services (API clients)

| Service File | Base URL | Methods |
|-------------|----------|---------|
| `api.js` | `http://localhost:8000/api` | Axios instance + interceptors |
| `authService.js` | `/auth/` | register, login, logout, refresh, getMe, updateMe |
| `productService.js` | `/products/` | getProducts, getProduct, getCategories, searchProducts, suggestProducts |
| `cartService.js` | `/cart/` | getCart, addItem, updateQuantity, removeItem, clearCart |
| `orderService.js` | `/orders/` | getOrders, createOrder, cancelOrder, confirmReceived, trackOrder |
| `paymentService.js` | `/payments/` | createMomo, createVNPay, createCOD, checkStatus |
| `reviewService.js` | `/reviews/` | getReviews, createReview, getProductReviews, getProductStats |
| `notificationService.js` | `/notifications/` | getNotifications, markRead, markAllRead |
| `userService.js` | `/users/` | getProfile, updateProfile, getAddresses, manageWishlist |
| `aiService.js` | `/recommendations/`, `/search/`, `/chatbot/` | recommend, search, chat |

---

## 7. AI Services

### 7.1 Recommendation Service

**Vị trí:** `services/ai-recommendation/`
**Port:** 8010

#### 5 Engines:

| Engine | File | Kỹ thuật | Input | Output |
|--------|------|----------|-------|--------|
| **Collaborative Filtering** | `engine.py` | User-Item matrix + cosine similarity | user_id, product_id | similar_products, recommendations |
| **Knowledge Graph** | `knowledge_graph.py` | Neo4j Cypher queries | user_id, product_id | KG recommendations |
| **RAG** | `rag_engine.py` | FAISS + sentence-transformers | text query | semantic search results |
| **LSTM** | `lstm_model.py` | TensorFlow/Keras sequence model | user behavior sequence | next purchase prediction |
| **Hybrid** | `hybrid_engine.py` | Weighted combination of all 4 | user_id, product_id | combined recommendations |

**Knowledge Graph Schema (Neo4j):**
```
Nodes: User, Product, Category, Brand
Relationships:
  (User)-[:VIEWED]->(Product)
  (User)-[:PURCHASED]->(Product)
  (User)-[:ADDED_TO_CART]->(Product)
  (User)-[:WISHLISTED]->(Product)
  (Product)-[:BELONGS_TO]->(Category)
  (Product)-[:MADE_BY]->(Brand)
  (Product)-[:SIMILAR]->(Product)
```

**Cold-start strategy:**
1. Content-based (same category)
2. Trending products
3. Featured products

### 7.2 Search Service

**Vị trí:** `services/ai-search/`
**Port:** 8011

**Kỹ thuật:**
- Vietnamese text normalization (Unicode → ASCII)
- Tokenization + stopword removal
- Keyword extraction
- TF-IDF + cosine similarity
- Synonym dictionary (30+ groups: "giay the thao" ↔ "sneaker", "dien thoai" ↔ "smartphone")
- Fuzzy matching (difflib)
- Category-aware + price filter

### 7.3 Chatbot Service

**Vị trí:** `services/ai-chatbot/`
**Port:** 8012
**Async:** Celery + RabbitMQ

**Components:**

| Component | Chức năng |
|-----------|-----------|
| **Redis Semantic Cache** | Embedding + response cache, cosine threshold 0.92, TTL 1 ngày |
| **Neo4j KG** | Product lookup, category search, price comparison |
| **Intent Detection** | Pattern matching + keyword extraction |
| **Ollama LLM** | llama3.2:3b (configurable), streaming |
| **Guardrails** | Chặn competitor brands, enforce citations, block hallucination |
| **RAG Hybrid Search** | KG results + product data as context |

**Models:**
- `Conversation` - user_id, session_id, context (JSON)
- `Message` - conversation (FK), role (user/assistant/system), content, metadata (JSON)
- `Intent` - name (unique), patterns (JSON), responses (JSON), action
- `FAQ` - question, answer, category, keywords, view_count

### 7.4 Analytics Service

**Vị trí:** `services/ai-analytics/`
**Port:** 8013

**Models:**
- `DailySales` - date, total_orders, total_revenue, total_items, avg_order_value, new_customers, returning_customers
- `ProductAnalytics` - product_id, date, views, add_to_carts, purchases, revenue, conversion_rate
- `CategoryAnalytics` - category, date, total_views, total_sales, total_revenue
- `SalesPrediction` - date, predicted_revenue, predicted_orders, confidence, model_version
- `CustomerSegment` - user_id, segment (vip/loyal/regular/new/at_risk/churned), rfm_score

### 7.5 Kết quả đánh giá mô hình

| Model | Latency | Faithfulness | Relevance | Overall |
|-------|---------|--------------|-----------|---------|
| `llama3.2:3b` | 11.1s | 81% | 67% | 0.70 |
| `qwen2.5:7b` | 6.7s | 81% | 67% | 0.74 |
| `gemma2:9b` ⭐ | **4.4s** | 81% | 67% | **0.77** |

---

## 8. Cơ sở dữ liệu

### 8.1 PostgreSQL Schema (13 databases)

| Database | Tables |
|----------|--------|
| `auth_db` | users |
| `user_db` | profiles, addresses, wishlists |
| `product_db` | categories, products, product_images, product_variants |
| `cart_db` | carts, cart_items |
| `order_db` | orders, order_items, order_status_history |
| `payment_db` | payments, refunds |
| `shipping_db` | shipments, tracking_events |
| `review_db` | reviews, review_images, review_replies |
| `notification_db` | notifications, notification_templates |
| `recommendation_db` | user_behaviors, user_interactions, product_similarities, user_recommendations |
| `search_db` | (in-memory TF-IDF index) |
| `chatbot_db` | conversations, messages, intents, faqs |
| `analytics_db` | daily_sales, product_analytics, category_analytics, sales_predictions, customer_segments |

### 8.2 Redis Usage

| Service | Redis DB | Usage |
|---------|----------|-------|
| API Gateway | default | Rate limiting |
| Product Service | default | Cache product list (5ph), product detail (5ph), categories (15ph) |
| AI Search | 4 | Cache search queries (5ph), autocomplete (10ph) |
| AI Chatbot | 5 | Semantic cache (1 ngày) |
| AI Recommendation | 3 | Cache recommendations (30-60ph) |

### 8.3 Neo4j Schema

```
Nodes: ~Product, ~Category, ~Brand, ~User (from behavior tracking)
Edge types: VIEWED, PURCHASED, ADDED_TO_CART, WISHLISTED, BELONGS_TO, MADE_BY, SIMILAR
Plugin: APOC
```

---

## 9. Giao tiếp liên service

### 9.1 Synchronous (HTTP)

| Service gọi | Service đích | Mục đích |
|-------------|-------------|----------|
| Cart | Product | Validate stock, lấy product info |
| Order | Cart | Lấy cart để tạo order |
| Order | Product | Validate stock khi tạo order |
| Order | Notification | Gửi notification khi tạo/cập nhật order |
| Review | Order | Xác thực user đã mua hàng |
| API Gateway | Tất cả | Proxy requests |

### 9.2 Async (Background threads)

| Service gọi | Service đích | Hành động |
|-------------|-------------|-----------|
| Product | Recommendation | Track view_product, click_product |
| Cart | Recommendation | Track add_to_cart, remove_from_cart |
| Order | Recommendation | Track purchase |
| User | Recommendation | Track add_to_wishlist |
| Search | Recommendation | Track search |
| Order | Notification | Gửi in-app notification |

### 9.3 Async (Celery + RabbitMQ)

| Task | Schedule | Mô tả |
|------|----------|-------|
| `update_product_knowledge_base_async` | On demand (webhook) | Đồng bộ sản phẩm lên Neo4j |
| Train recommendation models | On demand (API) | Train CF/LSTM models |

---

## 10. Triển khai

### 10.1 Yêu cầu hệ thống
- Docker & Docker Compose
- NVIDIA GPU (cho Ollama)
- RAM tối thiểu: 16GB (khuyến nghị 32GB)
- Disk: 20GB+ cho models + data

### 10.2 Environment variables

| Variable | Mô tả | Default |
|----------|-------|---------|
| `POSTGRES_USER` | PostgreSQL user | postgres |
| `POSTGRES_PASSWORD` | PostgreSQL password | postgres123 |
| `SECRET_KEY` | Django secret key | - |
| `JWT_SECRET` | JWT signing key | - |
| `REDIS_URL` | Redis connection | redis://redis:6379/0 |
| `RABBITMQ_URL` | RabbitMQ connection | - |
| `OLLAMA_MODEL` | LLM model name | llama3.2:3b |
| `MOMO_*` | MoMo payment config | - |
| `VNPAY_*` | VNPay payment config | - |

### 10.3 Docker commands

```bash
# Khởi động tất cả services
docker compose up -d

# Khởi động specific service
docker compose up -d api-gateway auth-service

# Xem logs
docker compose logs -f ai-chatbot

# Build lại service
docker compose build ai-chatbot

# Dừng tất cả
docker compose down

# Dừng và xóa volumes
docker compose down -v
```

### 10.4 Nginx config

```
/api/*    → api-gateway:8000  (rate limit: 10r/s, burst 20)
/admin/*  → api-gateway:8000  (no rate limit)
/*        → frontend:3000
```

### 10.5 Scripts hữu ích

| Script | Mô tả |
|--------|-------|
| `scripts/run_pipeline.py --all` | Chạy toàn bộ pipeline |
| `scripts/load_knowledge_graph.py` | Load data lên Neo4j |
| `scripts/rebuild_graph_schema.py` | Rebuild Neo4j schema |
| `scripts/evaluation/evaluate_models.py` | Đánh giá mô hình LLM |
| `scripts/evaluation/generate_charts.py` | Tạo biểu đồ kết quả |
| `scripts/data/import_to_django.py` | Import data vào Django |
| `scripts/data/generate_synthetic_large.py` | Generate synthetic data |
| `scripts/scrapers/tiki_scraper.py` | Scrape Tiki products |
| `scripts/seed-data.py` | Seed product data |

---

## Phụ lục

### A. Quy tắc đặt tên

- **Models:** Tiếng Anh, PascalCase (`Product`, `OrderItem`)
- **Fields:** snake_case (`created_at`, `payment_method`)
- **URLs:** snake_case (`/api/orders/<id>/cancel/`)
- **verbose_name:** Tiếng Việt có dấu
- **db_table:** số nhiều, snake_case (`order_items`, `product_images`)

### B. Quy ước response

**Success:**
```json
{
  "id": "uuid",
  "name": "...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error:**
```json
{
  "error": "Mô tả lỗi"
}
```

**Paginated list:**
```json
{
  "count": 100,
  "next": "http://.../?page=2",
  "previous": null,
  "results": [...]
}
```

### C. Authentication token format

- **Access token:** JWT, expires 15 phút
- **Refresh token:** JWT, expires 7 ngày
- **Header:** `Authorization: Bearer <access_token>`
- **Refresh:** `POST /api/auth/refresh/` with body `{"refresh": "<refresh_token>"}`
