# Lộ trình & Tiến độ Xây dựng Admin Dashboard

Bản kế hoạch này theo dõi tiến độ thực tế khi xây dựng phân hệ Admin Dashboard tích hợp vào hệ thống E-commerce Microservice.

## Trạng thái Tổng quan
*   **Giai đoạn 1: Khung xương & Bảo mật (Layout & Route Guard):** ✅ Hoàn thành
*   **Giai đoạn 2: Quản lý Sản phẩm (Catalog Management):** ✅ Hoàn thành
*   **Giai đoạn 3: Quản lý Đơn hàng & Người dùng (Orders & Users):** ✅ Hoàn thành
*   **Giai đoạn 4: Tổng quan & AI Analytics (KPIs & Charts):** ✅ Hoàn thành
*   **Giai đoạn 5: Giám sát & Điều khiển AI (AI Monitoring):** ✅ Hoàn thành

---

## Chi tiết các Công việc

### Giai đoạn 1: Khung xương & Bảo mật (Layout & Route Guard)
Trạng thái: ✅ Hoàn thành
- [x] Cài đặt các thư viện bổ sung (`recharts`, `@heroicons/react` nếu chưa có).
- [x] Tạo component `AdminRoute` bảo vệ đường dẫn (Route Guard), kiểm tra JWT và `role` từ Auth Context / Redux Store.
- [x] Thiết kế Layout trang Admin (Sidebar cố định bên trái, Header chứa thông báo ở trên, Main Content ở giữa).
- [x] Thiết lập định tuyến trong React Router cho `/admin-dashboard/*`.
- [x] Tạo trang Dashboard trống và kiểm thử chuyển hướng trang khi truy cập với tài khoản không phải Admin.

### Giai đoạn 2: Quản lý Sản phẩm & Danh mục (Catalog Management)
Trạng thái: ✅ Hoàn thành
- [x] Xây dựng màn hình danh sách sản phẩm với bảng phân trang, tìm kiếm, lọc theo danh mục.
- [x] Phát triển Form CRUD thêm/sửa sản phẩm trực quan (tải ảnh lên, điền thông tin mô tả, chọn danh mục).
- [x] Xây dựng quản lý biến thể sản phẩm (Variant Management: chọn size, màu sắc, quản lý SKU biến thể và giá chênh lệch).
- [x] Xây dựng màn hình quản lý Danh mục sản phẩm (Category Tree) dưới dạng kéo thả hoặc danh sách lồng nhau.
- [x] Tích hợp API upload nhiều ảnh sản phẩm lên `product-service` media volume.

### Giai đoạn 3: Quản lý Đơn hàng & Người dùng (Orders & Users)
Trạng thái: ✅ Hoàn thành
- [x] Xây dựng danh sách đơn hàng lọc theo trạng thái (`Chờ xác nhận`, `Đang giao`, `Đã giao`, `Đã hủy`).
- [x] Tạo trang chi tiết đơn hàng hiển thị thông tin khách hàng, sản phẩm đã mua, tổng tiền, phương thức thanh toán.
- [x] Tích hợp cập nhật trạng thái đơn hàng và gửi tín hiệu vận chuyển qua `shipping-service`.
- [x] Tạo danh sách quản lý Người dùng (`user-service`) hiển thị thông tin user và role của họ.
- [x] Thao tác Admin: Khóa/Mở khóa tài khoản người dùng, đổi role người dùng (từ Customer lên Staff/Admin/Seller).

### Giai đoạn 4: Tổng quan & AI Analytics (KPIs & Charts)
Trạng thái: ✅ Hoàn thành
- [x] Thiết kế các thẻ thống kê nhanh (KPI Cards) ở trang chủ Admin (Doanh thu, Đơn hàng, Khách hàng mới).
- [x] Vẽ biểu đồ doanh thu theo tuần/tháng sử dụng `recharts` kết nối tới API của `ai-analytics`.
- [x] Hiển thị dữ liệu dự báo doanh thu 7 ngày tiếp theo được tính toán từ mô hình AI Analytics.
- [x] Tích hợp danh sách cảnh báo tồn kho thấp và gợi ý sản phẩm bán chạy nhất.

### Giai đoạn 5: Giám sát & Điều khiển AI (AI Monitoring)
Trạng thái: ✅ Hoàn thành
- [x] Tích hợp màn hình giám sát sức khỏe dịch vụ LLM Ollama và Neo4j database.
- [x] Tạo nút trigger yêu cầu hệ thống xây dựng lại cơ sở dữ liệu đồ thị tri thức (Rebuild Knowledge Graph trong Neo4j).
- [x] Hiển thị thống kê lịch sử chatbot: Số lượng câu hỏi của khách hàng, biểu đồ cảm xúc của các cuộc trò chuyện.
- [x] Hiển thị danh sách các câu hỏi chatbot chưa trả lời tốt để admin có thể cập nhật huấn luyện lại mô hình.
