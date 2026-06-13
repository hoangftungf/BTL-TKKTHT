# Đánh giá Frontend — AI E-commerce

## Tổng quan kiến trúc

Frontend sử dụng **React 18 + Redux Toolkit + React Router v6 + Tailwind CSS + Ant Design**,
mô phỏng giao diện **Tiki.vn** với các trang: Home, Product Listing, Product Detail, Cart, Checkout, Profile, Search, và Admin Panel.

## Điểm mạnh

### 1. UI/UX mượt, bám sát Tiki
- Header có đầy đủ: promo ribbon, search với suggestions, hot keywords, cart badge, user dropdown → **trải nghiệm giống Tiki thật**.
- HeroSection dùng Ant Design Carousel + grid 10 icon quick links.
- Product Card: hiển thị rating, đã bán, giá gốc, compare price, badges "Chính hãng", "Giao nhanh 2h".
- ProductDetail dạng 2 cột, gallery + thumbnail + variant selector + quantity + accordion tabs → **rất chi tiết và chuyên nghiệp**.

### 2. Responsive tốt
- Header responsive: desktop full, mobile có search thu gọn, hamburger menu drawer.
- ProductGrid: `grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5` — responsive đẹp.
- Cart page có layout 2 cột (lg:grid-cols-3), chuyển sang 1 cột trên mobile.
- Admin Layout có sidebar mobile drawer + backdrop.

### 3. State management tốt
- Redux Slice chia rõ ràng: auth, cart, product, order, ui, wishlist.
- Dùng `createAsyncThunk` cho async actions, quản lý pending/fulfilled/rejected.
- `serializableCheck: false` cho phép linh hoạt, tránh warning không cần thiết.

### 4. Xử lý lỗi hình ảnh cẩn thận
- ProductCard: dùng `useState` + `useCallback` cho image error fallback → tránh re-render loop.
- ProductDetail: `mainImgFailed` + `failedThumbnails` state riêng cho từng thumbnail.
- CartItem: `onError` fallback về `/placeholder.png`.

### 5. AI tích hợp sâu
- SearchPage gọi `searchService.search()` (hybrid search AI).
- ProductRecommendations: 3 loại — similar, personalized, trending.
- Chatbot: gọi chatbot API, hiển thị sản phẩm + bought_together, có variant modal.
- AdminAIPage: health check 3 services, Neo4j stats, action buttons sync/train.
- AdminDashboard: AreaChart doanh thu + dự đoán ML, PieChart phân khúc RFM.

### 6. Code chất lượng
- `ProductRecommendations` dùng `React.memo` + `useRef(isMountedRef)` → tránh memory leak.
- CartDrawer dùng `useRef` + `handleClickOutside` để đóng drawer.
- Header debounce search 300ms.
- ProductDetail `toggleTab` cho accordion description/specs/shipping.
- `format.js` xử lý VND currency, date, status mapping.

### 7. UX nhỏ nhưng tinh tế
- Cart page auto-select newly added items.
- Checkout tự động chọn địa chỉ mặc định.
- LoginModal redirect sau khi đăng nhập thành công.
- Toast notification cho mọi action (thêm giỏ, xóa, lỗi...).
- Empty states có thiết kế riêng (SearchPage có SfVG illustration + tips).

---

## Điểm yếu & Cần cải thiện

### 1. Thiếu kiểm soát dependency trong useEffect
**File**: `ProductRecommendations.jsx` (dòng 81)
```jsx
// eslint-disable-next-line react-hooks/exhaustive-deps
}, [productId, userId, type, limit]);
```
Bỏ qua lint warning — thiếu `fetchRecommendations` trong dependency array.
Nếu `fetchRecommendations` thay đổi (mounted lại), behavior không predict được.

### 2. Mock data fallback trong Admin Panel
**File**: `AdminDashboardPage.jsx` (dòng 130-177), `AdminAIPage.jsx` (dòng 60-70, 108-117, 154-162)
- Dashboard fallback về mock data khi API lỗi → gây hiểu lầm "số liệu thật".
- AdminAI mock graph stats, conversations, messages → có thể gây nhầm lẫn khi debug.
- **Recommendation**: Nên có indicator rõ ràng hơn (đã có badge "Dữ liệu Demo" nhưng dễ bỏ qua).

### 3. Thiếu loading/skeleton ở một số chỗ
- `LoginPage`, `LoginModal`: button chỉ hiển thị text "Đang đăng nhập..." thay vì spinner.
- `ProfilePage`: chỉ hiển thị "Đang tải..." text thuần, không skeleton.
- Một số trang không có `ErrorBoundary` bao bọc.

### 4. Auth flow còn điểm yếu
- `localStorage` lưu token thuần (dễ bị XSS).
- `checkAuth` chỉ kiểm tra token ở `App.jsx` — không refresh token định kỳ.
- Logout không clear Redux state (cart, wishlist, order) — nếu user A login, user B login sau, data cũ vẫn còn trong cache.

### 5. Không có ErrorBoundary component
Toàn bộ app không có `ErrorBoundary` wrapper → nếu một component con crash, toàn bộ trang sẽ white screen (React 18 behavior).

### 6. Thiếu unit test
Không có file test nào (`*.test.js`, `*.spec.js`) trong `frontend/src/`.
`react-scripts test` không có test suite.

### 7. Code duplicate
- `getAttributeLabel` function được định nghĩa giống hệt nhau ở **3 nơi**:
  - `ProductDetailPage.jsx` (dòng 130-140)
  - `Chatbot.jsx` (dòng 30-39)
  - `CartItem.jsx` (dòng 25-35)
  → Nên đưa vào `utils/format.js` hoặc `utils/product.js`.

- `getCategoryIcon` function duplicate giữa `HomePage.jsx` và `ProductsPage.jsx`.

- Xử lý error message (object → string) duplicate giữa `LoginPage.jsx` và `LoginModal.jsx`.

### 8. Thiếu PropTypes/TypeScript
Không có TypeScript, không có PropTypes validation cho component props.
Component như `ProductRecommendations`, `CartItem`, `ProductCard` nhận nhiều props phức tạp mà không có type checking.

### 9. Hard-coded strings
- Shipping fee 30,000 VND hard-coded trong `CheckoutPage.jsx` (dòng 133).
- Hot keywords hard-coded trong `Header.jsx` (dòng 96).
- Thông tin vận chuyển/bảo hành hard-coded trong `ProductDetailPage.jsx` (dòng 490-507).

### 10. SEO chưa tối ưu
- Chỉ có `index.html` với meta tags cơ bản.
- Không có SSR, không có react-helmet cho dynamic meta tags (title, description theo từng product).
- Ảnh product thiếu `loading="lazy"` (chỉ có ở HeroSection banners).

### 11. Accessibility (a11y) còn thiếu
- Một số button thiếu `aria-label` (VD: search button, cart toggle, quantity buttons).
- Form inputs thiếu `aria-describedby` cho error messages.
- Màu sắc: `text-slate-400` trên nền trắng có contrast ratio thấp (~3.0:1, không đạt WCAG AA).

### 12. AdminPanel injection từ URL
```jsx
// AdminAIPage.jsx line 220-230
<span className="text-[10px] text-slate-500 font-mono">Port 11434 (llama3.2:3b)</span>
```
Thông tin port và model hard-code → nếu config thay đổi, admin panel không reflect.

---

## Tổng kết

### Điểm: 7/10

| Tiêu chí | Đánh giá |
|----------|----------|
| UI/UX | 9/10 — Rất đẹp, bám sát Tiki, responsive tốt |
| State management | 8/10 — Redux tốt, nhưng thiếu cleanup khi logout |
| AI Integration | 9/10 — Tích hợp sâu, chatbot + recommend + search |
| Code quality | 6/10 — Nhiều duplicate, thiếu TypeScript, thiếu test |
| Performance | 7/10 — Image fallback tốt nhưng thiếu lazy loading, skeleton |
| Accessibility | 4/10 — Còn nhiều vấn đề a11y |
| Maintainability | 6/10 — Cần refactor utils chung, xóa mock data |

### Ưu tiên cải thiện
1. **Tách utils chung** (getAttributeLabel, getCategoryIcon, error parser).
2. **Thêm ErrorBoundary** cho toàn app.
3. **Clear Redux state khi logout**.
4. **Thêm PropTypes** hoặc TypeScript cho component chính.
5. **Xóa mock data fallback** hoặc tách ra file riêng, có flag rõ ràng.

---

*Review tạo ngày 13/06/2026 bởi Claude Code dựa trên phân tích mã nguồn frontend.*
