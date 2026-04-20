# Nền Tảng AI-Ecommerce

Nền tảng thương mại điện tử tích hợp AI, được xây dựng theo kiến trúc microservices sử dụng Django REST Framework.

## Tổng Quan Kiến Trúc

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                                │
│                              Cổng: 3000                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY (Django)                               │
│                    Cổng: 8000 | Xác thực JWT + Giới hạn tốc độ               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────┬───────────────┼───────────────┬─────────────┐
        ▼             ▼               ▼               ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Xác thực  │ │  Người dùng │ │  Sản phẩm   │ │  Đơn hàng   │ │   Dịch vụ   │
│   Service   │ │   Service   │ │   Service   │ │   Service   │ │     AI      │
│   :8001     │ │   :8002     │ │   :8003     │ │   :8004     │ │ :8010-8013  │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
        │             │               │               │             │
        ▼             ▼               ▼               ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ PostgreSQL  │ │ PostgreSQL  │ │ PostgreSQL  │ │ PostgreSQL  │ │   Ollama    │
│   auth_db   │ │   user_db   │ │ product_db  │ │  order_db   │ │   + Redis   │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

## Danh Sách Services

| Service | Cổng | Mô tả |
|---------|------|-------|
| API Gateway | 8000 | Định tuyến, Xác thực JWT, Giới hạn tốc độ |
| Auth Service | 8001 | Xác thực người dùng với JWT (đăng nhập, đăng ký, làm mới token) |
| User Service | 8002 | Hồ sơ người dùng, địa chỉ, tùy chọn |
| Product Service | 8003 | Danh mục sản phẩm, phân loại, tồn kho |
| Cart Service | 8004 | Quản lý giỏ hàng |
| Order Service | 8005 | Xử lý & quản lý đơn hàng |
| Payment Service | 8006 | Thanh toán MoMo, VNPay, COD |
| Shipping Service | 8007 | Vận chuyển & theo dõi giao hàng |
| Review Service | 8008 | Đánh giá & xếp hạng sản phẩm |
| Notification Service | 8009 | Thông báo Email, SMS, Push |
| AI Recommendation | 8010 | Gợi ý sản phẩm (lọc cộng tác) |
| AI Search | 8011 | Tìm kiếm thông minh với NLP |
| AI Chatbot | 8012 | Chatbot hỗ trợ khách hàng (Ollama) |
| AI Analytics | 8013 | Dự đoán doanh số & phân tích |
| Frontend | 3000 | Ứng dụng React |

## Công Nghệ Sử Dụng

### Backend
- **Framework:** Django 5.0 + Django REST Framework
- **Cơ sở dữ liệu:** PostgreSQL 16 (mỗi service một database)
- **Cache:** Redis 7
- **Hàng đợi tin nhắn:** RabbitMQ (giao tiếp bất đồng bộ)
- **Xác thực:** JWT (SimpleJWT)

### Frontend
- **Framework:** React 18
- **CSS:** Tailwind CSS
- **Quản lý state:** Redux Toolkit
- **HTTP Client:** Axios

### AI/ML
- **LLM:** Ollama (llama3.2:3b, mistral)
- **Gợi ý sản phẩm:** Scikit-learn, Surprise
- **Tìm kiếm:** Elasticsearch + sentence-transformers
- **Phân tích:** Pandas, Prophet

### Hạ tầng
- **Container hóa:** Docker & Docker Compose
- **Reverse Proxy:** Nginx
- **Giám sát:** Prometheus + Grafana

## Bắt Đầu Nhanh

### Yêu Cầu Hệ Thống

- Docker & Docker Compose v2+
- Git
- RAM tối thiểu 8GB (cho các dịch vụ AI)

### Cài Đặt

```bash
# Clone repository
git clone https://github.com/your-repo/ai-ecommerce.git
cd ai-ecommerce

# Sao chép file môi trường
cp .env.example .env

# Khởi động tất cả services
docker-compose up --build -d

# Đợi services khởi động hoàn tất (2-3 phút)
docker-compose ps

# Chạy database migrations
docker-compose exec api-gateway python manage.py migrate
```

### Tải Model AI

```bash
# Tải model Ollama cho chatbot
docker-compose exec ollama ollama pull llama3.2:3b
docker-compose exec ollama ollama pull nomic-embed-text
```

### Truy Cập Ứng Dụng

| Dịch vụ | URL |
|---------|-----|
| Giao diện người dùng | http://localhost:3000 |
| API Gateway | http://localhost:8000 |
| Tài liệu API (Swagger) | http://localhost:8000/api/docs/ |
| Trang quản trị | http://localhost:8000/admin/ |
| Grafana | http://localhost:3001 |

### Tài Khoản Mặc Định

- **Quản trị viên:** admin@example.com / admin123
- **Người dùng test:** user@example.com / user123

## Cấu Trúc Dự Án

```
ai-ecommerce/
├── docker-compose.yml
├── .env.example
├── README.md
│
├── services/
│   ├── api-gateway/          # Dịch vụ API Gateway
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── manage.py
│   │   └── gateway/
│   │       ├── settings.py
│   │       ├── urls.py
│   │       └── middleware/
│   │
│   ├── auth-service/         # Dịch vụ xác thực
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── auth_app/
│   │       ├── models.py
│   │       ├── views.py
│   │       ├── serializers.py
│   │       └── urls.py
│   │
│   ├── user-service/         # Quản lý người dùng
│   ├── product-service/      # Danh mục sản phẩm
│   ├── cart-service/         # Giỏ hàng
│   ├── order-service/        # Quản lý đơn hàng
│   ├── payment-service/      # Xử lý thanh toán
│   ├── shipping-service/     # Vận chuyển & giao hàng
│   ├── review-service/       # Đánh giá & xếp hạng
│   ├── notification-service/ # Thông báo
│   │
│   ├── ai-recommendation/    # Gợi ý sản phẩm AI
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── recommender/
│   │       ├── models.py
│   │       ├── engine.py     # Engine gợi ý ML
│   │       └── views.py
│   │
│   ├── ai-search/            # Tìm kiếm AI
│   ├── ai-chatbot/           # Chatbot hỗ trợ khách hàng
│   └── ai-analytics/         # Phân tích & dự đoán doanh số
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── store/
│   │   ├── services/
│   │   └── App.jsx
│   └── public/
│
├── nginx/
│   └── nginx.conf
│
└── scripts/
    ├── init-db.sh
    ├── run-tests.sh
    └── seed-data.py
```

## API Endpoints

### Xác thực (`/api/auth/`)
| Phương thức | Endpoint | Mô tả |
|-------------|----------|-------|
| POST | `/register/` | Đăng ký người dùng mới |
| POST | `/login/` | Đăng nhập & lấy token |
| POST | `/refresh/` | Làm mới access token |
| POST | `/logout/` | Đăng xuất & vô hiệu hóa token |
| GET | `/me/` | Lấy thông tin người dùng hiện tại |

### Người dùng (`/api/users/`)
| Phương thức | Endpoint | Mô tả |
|-------------|----------|-------|
| GET | `/profile/` | Lấy hồ sơ người dùng |
| PUT | `/profile/` | Cập nhật hồ sơ |
| GET | `/addresses/` | Danh sách địa chỉ |
| POST | `/addresses/` | Thêm địa chỉ mới |

### Sản phẩm (`/api/products/`)
| Phương thức | Endpoint | Mô tả |
|-------------|----------|-------|
| GET | `/` | Danh sách sản phẩm (có bộ lọc) |
| GET | `/{id}/` | Chi tiết sản phẩm |
| GET | `/categories/` | Danh sách danh mục |
| GET | `/search/?q=` | Tìm kiếm sản phẩm |
| POST | `/` | Tạo sản phẩm (Admin) |
| PUT | `/{id}/` | Cập nhật sản phẩm (Admin) |

### Giỏ hàng (`/api/cart/`)
| Phương thức | Endpoint | Mô tả |
|-------------|----------|-------|
| GET | `/` | Xem giỏ hàng |
| POST | `/items/` | Thêm vào giỏ hàng |
| PUT | `/items/{id}/` | Cập nhật số lượng |
| DELETE | `/items/{id}/` | Xóa sản phẩm |
| DELETE | `/clear/` | Xóa toàn bộ giỏ hàng |

### Đơn hàng (`/api/orders/`)
| Phương thức | Endpoint | Mô tả |
|-------------|----------|-------|
| POST | `/` | Tạo đơn hàng |
| GET | `/` | Danh sách đơn hàng |
| GET | `/{id}/` | Chi tiết đơn hàng |
| PUT | `/{id}/cancel/` | Hủy đơn hàng |
| GET | `/{id}/track/` | Theo dõi vận chuyển |

### Thanh toán (`/api/payments/`)
| Phương thức | Endpoint | Mô tả |
|-------------|----------|-------|
| POST | `/momo/` | Tạo thanh toán MoMo |
| POST | `/vnpay/` | Tạo thanh toán VNPay |
| POST | `/cod/` | Tạo đơn hàng COD |
| GET | `/{order_id}/status/` | Trạng thái thanh toán |
| POST | `/webhook/momo/` | Callback IPN MoMo |

### Đánh giá (`/api/reviews/`)
| Phương thức | Endpoint | Mô tả |
|-------------|----------|-------|
| GET | `/product/{id}/` | Đánh giá sản phẩm |
| POST | `/` | Tạo đánh giá |
| PUT | `/{id}/` | Cập nhật đánh giá |
| DELETE | `/{id}/` | Xóa đánh giá |
| GET | `/product/{id}/stats/` | Thống kê xếp hạng |

### Dịch vụ AI (`/api/ai/`)
| Phương thức | Endpoint | Mô tả |
|-------------|----------|-------|
| GET | `/recommend/product/{id}/` | Sản phẩm tương tự |
| GET | `/recommend/user/` | Gợi ý cá nhân hóa |
| GET | `/recommend/trending/` | Sản phẩm xu hướng |
| POST | `/search/` | Tìm kiếm AI |
| POST | `/chat/` | Trò chuyện với chatbot |
| GET | `/analytics/sales/` | Dự đoán doanh số |

## Biến Môi Trường

### Chung
| Biến | Mô tả | Mặc định |
|------|-------|----------|
| `DEBUG` | Bật chế độ debug | `False` |
| `SECRET_KEY` | Khóa bí mật Django | - |
| `JWT_SECRET` | Khóa ký JWT | - |
| `ALLOWED_HOSTS` | Các host được phép | `localhost` |

### Cơ sở dữ liệu
| Biến | Mô tả | Mặc định |
|------|-------|----------|
| `DATABASE_URL` | Kết nối PostgreSQL | - |
| `REDIS_URL` | Kết nối Redis | `redis://redis:6379/0` |

### Thanh toán
| Biến | Mô tả |
|------|-------|
| `MOMO_PARTNER_CODE` | Mã đối tác MoMo |
| `MOMO_ACCESS_KEY` | Khóa truy cập MoMo |
| `MOMO_SECRET_KEY` | Khóa bí mật MoMo |
| `VNPAY_TMN_CODE` | Mã terminal VNPay |
| `VNPAY_HASH_SECRET` | Khóa hash VNPay |

### Dịch vụ AI
| Biến | Mô tả | Mặc định |
|------|-------|----------|
| `OLLAMA_HOST` | URL server Ollama | `http://ollama:11434` |
| `OLLAMA_MODEL` | Model LLM mặc định | `llama3.2:3b` |
| `ELASTICSEARCH_URL` | URL Elasticsearch | `http://elasticsearch:9200` |

## Phát Triển

### Chạy Service Riêng Lẻ

```bash
cd services/product-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8003
```

### Chạy Tests

```bash
# Tất cả services
./scripts/run-tests.sh

# Một service
cd services/auth-service
python manage.py test

# Với coverage
pytest --cov=. --cov-report=html
```

### Database Migrations

```bash
# Tạo migrations
docker-compose exec product-service python manage.py makemigrations

# Áp dụng migrations
docker-compose exec product-service python manage.py migrate

# Tạo dữ liệu mẫu
docker-compose exec api-gateway python scripts/seed-data.py
```

## Luồng Demo

### 1. Đăng Ký & Đăng Nhập
- Đăng ký tại `/register`
- Đăng nhập để nhận JWT tokens
- Hồ sơ được tạo tự động

### 2. Duyệt Sản Phẩm
- Xem sản phẩm tại `/products`
- Lọc theo danh mục, giá, đánh giá
- Tìm kiếm AI với ngôn ngữ tự nhiên

### 3. Thêm Vào Giỏ Hàng
- Nhấn "Thêm vào giỏ" trên sản phẩm
- Điều chỉnh số lượng trong giỏ
- Xem gợi ý sản phẩm AI

### 4. Thanh Toán
- Tiến hành thanh toán
- Chọn địa chỉ giao hàng
- Chọn phương thức thanh toán

### 5. Thanh Toán
- **MoMo:** Chuyển hướng đến sandbox MoMo
- **VNPay:** Chuyển hướng đến sandbox VNPay
- **COD:** Đơn hàng được xác nhận ngay

### 6. Theo Dõi Đơn Hàng
- Xem trạng thái đơn hàng
- Theo dõi vận chuyển thời gian thực
- Nhận thông báo

### 7. Đánh Giá Sản Phẩm
- Viết đánh giá sau khi nhận hàng
- Xếp hạng 1-5 sao
- Tải lên hình ảnh

### 8. Tính Năng AI
- Nhận gợi ý sản phẩm cá nhân hóa
- Sử dụng chatbot AI để hỗ trợ
- Tìm kiếm sản phẩm bằng ngôn ngữ tự nhiên

## Giám Sát

### Kiểm Tra Sức Khỏe

```bash
# Kiểm tra tất cả services
curl http://localhost:8000/health/

# Kiểm tra service cụ thể
curl http://localhost:8001/health/
```

### Logs

```bash
# Tất cả services
docker-compose logs -f

# Service cụ thể
docker-compose logs -f product-service
```

### Metrics

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

## Triển Khai

### Checklist Production

- [ ] Đặt `DEBUG=False`
- [ ] Sử dụng `SECRET_KEY` và `JWT_SECRET` mạnh
- [ ] Cấu hình HTTPS (chứng chỉ SSL)
- [ ] Thiết lập `ALLOWED_HOSTS` đúng
- [ ] Cấu hình database production
- [ ] Thiết lập Redis cluster
- [ ] Cấu hình CDN cho static files
- [ ] Thiết lập log aggregation
- [ ] Cấu hình cảnh báo giám sát

### Docker Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Đóng Góp

1. Fork repository
2. Tạo nhánh tính năng (`git checkout -b feature/tinh-nang-moi`)
3. Commit thay đổi (`git commit -m 'Thêm tính năng mới'`)
4. Push lên nhánh (`git push origin feature/tinh-nang-moi`)
5. Mở Pull Request

## Giấy Phép

MIT License - xem file [LICENSE](LICENSE) để biết chi tiết.

## Hỗ Trợ

- Issues: [GitHub Issues](https://github.com/your-repo/ai-ecommerce/issues)
- Tài liệu: [Wiki](https://github.com/your-repo/ai-ecommerce/wiki)
