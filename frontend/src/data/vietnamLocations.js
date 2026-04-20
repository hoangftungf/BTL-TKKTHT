// Dữ liệu địa chỉ hành chính Việt Nam (sau sáp nhập)
// Cấu trúc: Tỉnh/Thành phố -> Quận/Huyện -> Phường/Xã

const vietnamLocations = {
  "Hà Nội": {
    "Ba Đình": ["Phúc Xá", "Trúc Bạch", "Vĩnh Phúc", "Cống Vị", "Liễu Giai", "Nguyễn Trung Trực", "Quán Thánh", "Ngọc Hà", "Điện Biên", "Đội Cấn", "Ngọc Khánh", "Kim Mã", "Giảng Võ", "Thành Công"],
    "Hoàn Kiếm": ["Phúc Tân", "Đồng Xuân", "Hàng Mã", "Hàng Buồm", "Hàng Đào", "Hàng Bồ", "Cửa Đông", "Lý Thái Tổ", "Hàng Bạc", "Hàng Gai", "Chương Dương", "Hàng Trống", "Cửa Nam", "Hàng Bông", "Tràng Tiền", "Trần Hưng Đạo", "Phan Chu Trinh", "Hàng Bài"],
    "Đống Đa": ["Cát Linh", "Văn Miếu", "Quốc Tử Giám", "Hàng Bột", "Láng Thượng", "Ô Chợ Dừa", "Văn Chương", "Trung Liệt", "Khâm Thiên", "Thổ Quan", "Nam Đồng", "Trung Phụng", "Quang Trung", "Trung Tự", "Kim Liên", "Phương Liên", "Thịnh Quang", "Láng Hạ", "Khương Thượng", "Ngã Tư Sở", "Phương Mai"],
    "Hai Bà Trưng": ["Nguyễn Du", "Bạch Đằng", "Phạm Đình Hổ", "Lê Đại Hành", "Đồng Nhân", "Phố Huế", "Đống Mác", "Thanh Lương", "Thanh Nhàn", "Cầu Dền", "Bách Khoa", "Đồng Tâm", "Vĩnh Tuy", "Bạch Mai", "Quỳnh Mai", "Quỳnh Lôi", "Minh Khai", "Trương Định"],
    "Cầu Giấy": ["Nghĩa Đô", "Nghĩa Tân", "Mai Dịch", "Dịch Vọng", "Dịch Vọng Hậu", "Quan Hoa", "Yên Hòa", "Trung Hòa"],
    "Thanh Xuân": ["Thanh Xuân Bắc", "Thanh Xuân Nam", "Thanh Xuân Trung", "Hạ Đình", "Khương Trung", "Khương Mai", "Khương Đình", "Nhân Chính", "Phương Liệt", "Kim Giang"],
    "Hoàng Mai": ["Thanh Trì", "Vĩnh Hưng", "Định Công", "Mai Động", "Tương Mai", "Đại Kim", "Tân Mai", "Hoàng Văn Thụ", "Giáp Bát", "Lĩnh Nam", "Thịnh Liệt", "Trần Phú", "Hoàng Liệt", "Yên Sở"],
    "Long Biên": ["Thượng Thanh", "Ngọc Thụy", "Giang Biên", "Đức Giang", "Việt Hưng", "Gia Thụy", "Ngọc Lâm", "Phúc Lợi", "Bồ Đề", "Sài Đồng", "Long Biên", "Thạch Bàn", "Phúc Đồng", "Cự Khối"],
    "Tây Hồ": ["Phú Thượng", "Nhật Tân", "Tứ Liên", "Quảng An", "Xuân La", "Yên Phụ", "Bưởi", "Thụy Khuê"],
    "Bắc Từ Liêm": ["Thượng Cát", "Liên Mạc", "Đông Ngạc", "Đức Thắng", "Thụy Phương", "Tây Tựu", "Xuân Đỉnh", "Xuân Tảo", "Minh Khai", "Cổ Nhuế 1", "Cổ Nhuế 2", "Phú Diễn", "Phúc Diễn"],
    "Nam Từ Liêm": ["Cầu Diễn", "Xuân Phương", "Phương Canh", "Mỹ Đình 1", "Mỹ Đình 2", "Tây Mỗ", "Mễ Trì", "Phú Đô", "Đại Mỗ", "Trung Văn"],
    "Hà Đông": ["Nguyễn Trãi", "Mộ Lao", "Văn Quán", "Vạn Phúc", "Yết Kiêu", "Quang Trung", "La Khê", "Phú La", "Phúc La", "Hà Cầu", "Yên Nghĩa", "Kiến Hưng", "Phú Lãm", "Phú Lương", "Dương Nội", "Đồng Mai", "Biên Giang"],
    "Sơn Tây": ["Lê Lợi", "Phú Thịnh", "Quang Trung", "Sơn Lộc", "Xuân Khanh", "Đường Lâm", "Viên Sơn", "Xuân Sơn", "Trung Hưng", "Trung Sơn Trầm", "Kim Sơn", "Sơn Đông", "Cổ Đông", "Thanh Mỹ", "Đông Sơn"],
    "Đan Phượng": ["Đan Phượng", "Đồng Tháp", "Song Phượng", "Phượng Cách", "Liên Hà", "Liên Hồng", "Liên Trung", "Tân Hội", "Tân Lập", "Thọ An", "Thọ Xuân", "Thượng Mỗ", "Hạ Mỗ", "Hồng Hà", "Trung Châu"],
    "Hoài Đức": ["Trạm Trôi", "Đức Thượng", "Minh Khai", "Dương Liễu", "Di Trạch", "Đức Giang", "Cát Quế", "Kim Chung", "Yên Sở", "Sơn Đồng", "Vân Canh", "Đắc Sở", "Tiền Yên", "Song Phương", "An Khánh", "An Thượng", "Vân Côn", "La Phù", "Đông La", "Lại Yên"],
    "Thanh Oai": ["Kim Bài", "Bích Hòa", "Cự Khê", "Phương Trung", "Thanh Cao", "Bình Minh", "Cao Viên", "Thanh Văn", "Thanh Mai", "Xuân Dương", "Hồng Dương", "Tam Hưng", "Kim Thư", "Phú Lương", "Mỹ Hưng", "Cao Dương", "Tân Ước", "Dân Hòa", "Liên Châu", "Rộng Thượng"],
    "Gia Lâm": ["Trâu Quỳ", "Đa Tốn", "Kiêu Kỵ", "Dương Xá", "Đặng Xá", "Đông Dư", "Bát Tràng", "Kim Lan", "Văn Đức", "Cổ Bi", "Đình Xuyên", "Phù Đổng", "Lệ Chi", "Kim Sơn", "Phú Thị", "Yên Viên", "Yên Thường", "Ninh Hiệp", "Dương Hà", "Dương Quang", "Đa Tốn"],
    "Đông Anh": ["Đông Anh", "Nam Hồng", "Bắc Hồng", "Nguyên Khê", "Xuân Nộn", "Thụy Lâm", "Liên Hà", "Vân Hà", "Uy Nỗ", "Việt Hùng", "Tiên Dương", "Vân Nội", "Dục Tú", "Đại Mạch", "Võng La", "Cổ Loa", "Hải Bối", "Xuân Canh", "Vĩnh Ngọc", "Mai Lâm", "Đông Hội", "Kim Nỗ", "Kim Chung", "Tàm Xá"],
    "Sóc Sơn": ["Sóc Sơn", "Bắc Sơn", "Minh Trí", "Hồng Kỳ", "Nam Sơn", "Trung Giã", "Tân Hưng", "Minh Phú", "Phù Linh", "Bắc Phú", "Tân Minh", "Quang Tiến", "Hiền Ninh", "Tân Dân", "Tiên Dược", "Việt Long", "Xuân Giang", "Mai Đình", "Đức Hòa", "Thanh Xuân", "Đông Xuân", "Kim Lũ", "Phú Cường", "Phú Minh", "Phù Lỗ", "Xuân Thu"],
    "Mê Linh": ["Chi Đông", "Đại Thịnh", "Kim Hoa", "Thạch Đà", "Tiến Thắng", "Tự Lập", "Quang Minh", "Thanh Lâm", "Tam Đồng", "Liên Mạc", "Vạn Yên", "Chu Phan", "Tiến Thịnh", "Mê Linh", "Văn Khê", "Hoàng Kim", "Tráng Việt", "Tiền Phong"],
    "Chương Mỹ": ["Chúc Sơn", "Xuân Mai", "Phụng Châu", "Tiên Phương", "Đông Phương Yên", "Đông Sơn", "Thủy Xuân Tiên", "Thanh Bình", "Trần Phú", "Văn Võ", "Hòa Chính", "Phú Nam An", "Hợp Đồng", "Lam Điền", "Tân Tiến", "Đại Yên", "Thụy Hương", "Trường Yên", "Ngọc Hòa", "Thượng Vực", "Quảng Bị", "Mỹ Lương", "Hồng Phong", "Đồng Phú", "Trung Hòa", "Hoàng Văn Thụ", "Hoàng Diệu", "Hữu Văn", "Quang Húc", "Nam Phương Tiến", "Tốt Động"],
    "Thường Tín": ["Thường Tín", "Ninh Sở", "Nhị Khê", "Duyên Thái", "Khánh Hà", "Hòa Bình", "Văn Bình", "Hiền Giang", "Hồng Vân", "Vân Tảo", "Liên Phương", "Văn Phú", "Tự Nhiên", "Tiền Phong", "Hà Hồi", "Thư Phú", "Nguyễn Trãi", "Quất Động", "Chương Dương", "Tân Minh", "Lê Lợi", "Thống Nhất", "Nghiêm Xuyên", "Tô Hiệu", "Thắng Lợi", "Dũng Tiến", "Minh Cường", "Vạn Điểm"],
    "Phú Xuyên": ["Phú Xuyên", "Phú Minh", "Văn Hoàng", "Hồng Minh", "Phượng Dực", "Nam Triều", "Bạch Hạ", "Quang Trung", "Châu Can", "Hoàng Long", "Minh Tân", "Tri Trung", "Văn Nhân", "Thụy Phú", "Tri Thủy", "Sơn Hà", "Đại Thắng", "Tân Dân", "Khai Thái", "Phúc Tiến", "Chuyên Mỹ", "Vân Từ", "Hồng Thái", "Đại Xuyên", "Phú Túc", "Văn Từ", "Quang Lãng"],
    "Ứng Hòa": ["Vân Đình", "Viên An", "Viên Nội", "Hòa Lâm", "Hòa Xá", "Trường Thịnh", "Cao Thành", "Liên Bạt", "Sơn Công", "Đồng Tiến", "Phương Tú", "Trung Tú", "Đông Lỗ", "Kim Đường", "Hòa Nam", "Hòa Phú", "Đại Hưng", "Đại Cường", "Đông Phương", "Tảo Dương Văn", "Trầm Lộng", "Minh Đức", "Hồng Quang", "Phù Lưu", "Lưu Hoàng", "Quảng Phú Cầu"],
    "Mỹ Đức": ["Đại Nghĩa", "Phúc Lâm", "Mỹ Đức", "Phù Lưu Tế", "An Tiến", "Hồng Sơn", "Lê Thanh", "Xuy Xá", "An Mỹ", "Phùng Xá", "Hương Sơn", "Hùng Tiến", "Đại Hưng", "Vạn Kim", "Đốc Tín", "An Phú", "Thượng Lâm", "Tuy Lai", "Hợp Thanh", "Hợp Tiến", "Bột Xuyên", "Đồng Tâm"],
    "Thanh Trì": ["Tứ Hiệp", "Tân Triều", "Thanh Liệt", "Tả Thanh Oai", "Hữu Hòa", "Vạn Phúc", "Đại Áng", "Liên Ninh", "Đông Mỹ", "Ngọc Hồi", "Duyên Hà", "Ngũ Hiệp", "Vĩnh Quỳnh", "Tam Hiệp", "Yên Mỹ", "Tứ Hiệp"],
    "Ba Vì": ["Tây Đằng", "Phú Cường", "Cẩm Lĩnh", "Sơn Đà", "Đông Quang", "Phú Châu", "Phú Phương", "Phú Đông", "Tòng Bạt", "Cổ Đô", "Tiên Phong", "Vạn Thắng", "Chu Minh", "Minh Châu", "Minh Quang", "Ba Trại", "Ba Vì", "Khánh Thượng", "Yên Bài", "Thuần Mỹ", "Tản Lĩnh", "Thái Hòa", "Vật Lại", "Cam Thượng", "Châu Sơn", "Phong Vân", "Thụy An", "Đông Phú", "Phú Cường", "Phú Sơn", "Sơn Đà", "Tản Hồng"]
  },
  "Hồ Chí Minh": {
    "Quận 1": ["Bến Nghé", "Bến Thành", "Cầu Kho", "Cầu Ông Lãnh", "Cô Giang", "Đa Kao", "Nguyễn Cư Trinh", "Nguyễn Thái Bình", "Phạm Ngũ Lão", "Tân Định"],
    "Quận 3": ["Phường 1", "Phường 2", "Phường 3", "Phường 4", "Phường 5", "Phường 6", "Phường 7", "Phường 8", "Phường 9", "Phường 10", "Phường 11", "Phường 12", "Phường 13", "Phường 14", "Võ Thị Sáu"],
    "Quận 4": ["Phường 1", "Phường 2", "Phường 3", "Phường 4", "Phường 5", "Phường 6", "Phường 8", "Phường 9", "Phường 10", "Phường 12", "Phường 13", "Phường 14", "Phường 15", "Phường 16", "Phường 18"],
    "Quận 5": ["Phường 1", "Phường 2", "Phường 3", "Phường 4", "Phường 5", "Phường 6", "Phường 7", "Phường 8", "Phường 9", "Phường 10", "Phường 11", "Phường 12", "Phường 13", "Phường 14", "Phường 15"],
    "Quận 6": ["Phường 1", "Phường 2", "Phường 3", "Phường 4", "Phường 5", "Phường 6", "Phường 7", "Phường 8", "Phường 9", "Phường 10", "Phường 11", "Phường 12", "Phường 13", "Phường 14"],
    "Quận 7": ["Bình Thuận", "Phú Mỹ", "Phú Thuận", "Tân Hưng", "Tân Kiểng", "Tân Phong", "Tân Phú", "Tân Quy", "Tân Thuận Đông", "Tân Thuận Tây"],
    "Quận 8": ["Phường 1", "Phường 2", "Phường 3", "Phường 4", "Phường 5", "Phường 6", "Phường 7", "Phường 8", "Phường 9", "Phường 10", "Phường 11", "Phường 12", "Phường 13", "Phường 14", "Phường 15", "Phường 16"],
    "Quận 10": ["Phường 1", "Phường 2", "Phường 3", "Phường 4", "Phường 5", "Phường 6", "Phường 7", "Phường 8", "Phường 9", "Phường 10", "Phường 11", "Phường 12", "Phường 13", "Phường 14", "Phường 15"],
    "Quận 11": ["Phường 1", "Phường 2", "Phường 3", "Phường 4", "Phường 5", "Phường 6", "Phường 7", "Phường 8", "Phường 9", "Phường 10", "Phường 11", "Phường 12", "Phường 13", "Phường 14", "Phường 15", "Phường 16"],
    "Quận 12": ["An Phú Đông", "Đông Hưng Thuận", "Hiệp Thành", "Tân Chánh Hiệp", "Tân Hưng Thuận", "Tân Thới Hiệp", "Tân Thới Nhất", "Thạnh Lộc", "Thạnh Xuân", "Thới An", "Trung Mỹ Tây"],
    "Quận Bình Tân": ["An Lạc", "An Lạc A", "Bình Hưng Hòa", "Bình Hưng Hòa A", "Bình Hưng Hòa B", "Bình Trị Đông", "Bình Trị Đông A", "Bình Trị Đông B", "Tân Tạo", "Tân Tạo A"],
    "Quận Bình Thạnh": ["Phường 1", "Phường 2", "Phường 3", "Phường 5", "Phường 6", "Phường 7", "Phường 11", "Phường 12", "Phường 13", "Phường 14", "Phường 15", "Phường 17", "Phường 19", "Phường 21", "Phường 22", "Phường 24", "Phường 25", "Phường 26", "Phường 27", "Phường 28"],
    "Quận Gò Vấp": ["Phường 1", "Phường 3", "Phường 4", "Phường 5", "Phường 6", "Phường 7", "Phường 8", "Phường 9", "Phường 10", "Phường 11", "Phường 12", "Phường 13", "Phường 14", "Phường 15", "Phường 16", "Phường 17"],
    "Quận Phú Nhuận": ["Phường 1", "Phường 2", "Phường 3", "Phường 4", "Phường 5", "Phường 7", "Phường 8", "Phường 9", "Phường 10", "Phường 11", "Phường 12", "Phường 13", "Phường 14", "Phường 15", "Phường 17"],
    "Quận Tân Bình": ["Phường 1", "Phường 2", "Phường 3", "Phường 4", "Phường 5", "Phường 6", "Phường 7", "Phường 8", "Phường 9", "Phường 10", "Phường 11", "Phường 12", "Phường 13", "Phường 14", "Phường 15"],
    "Quận Tân Phú": ["Hiệp Tân", "Hòa Thạnh", "Phú Thạnh", "Phú Thọ Hòa", "Phú Trung", "Sơn Kỳ", "Tân Quý", "Tân Sơn Nhì", "Tân Thành", "Tân Thới Hòa", "Tây Thạnh"],
    "Thủ Đức": ["An Khánh", "An Lợi Đông", "An Phú", "Bình Chiểu", "Bình Thọ", "Bình Trưng Đông", "Bình Trưng Tây", "Cát Lái", "Hiệp Bình Chánh", "Hiệp Bình Phước", "Hiệp Phú", "Linh Chiểu", "Linh Đông", "Linh Tây", "Linh Trung", "Linh Xuân", "Long Bình", "Long Phước", "Long Thạnh Mỹ", "Long Trường", "Phú Hữu", "Phước Bình", "Phước Long A", "Phước Long B", "Tam Bình", "Tam Phú", "Tân Phú", "Tăng Nhơn Phú A", "Tăng Nhơn Phú B", "Thạnh Mỹ Lợi", "Thảo Điền", "Thủ Thiêm", "Trường Thạnh", "Trường Thọ"],
    "Bình Chánh": ["An Phú Tây", "Bình Chánh", "Bình Hưng", "Bình Lợi", "Đa Phước", "Hưng Long", "Lê Minh Xuân", "Phạm Văn Hai", "Phong Phú", "Quy Đức", "Tân Kiên", "Tân Nhựt", "Tân Quý Tây", "Tân Túc", "Vĩnh Lộc A", "Vĩnh Lộc B"],
    "Cần Giờ": ["An Thới Đông", "Bình Khánh", "Cần Thạnh", "Long Hòa", "Lý Nhơn", "Tam Thôn Hiệp", "Thạnh An"],
    "Củ Chi": ["An Nhơn Tây", "An Phú", "Bình Mỹ", "Củ Chi", "Hòa Phú", "Nhuận Đức", "Phạm Văn Cội", "Phú Hòa Đông", "Phú Mỹ Hưng", "Phước Hiệp", "Phước Thạnh", "Phước Vĩnh An", "Tân An Hội", "Tân Phú Trung", "Tân Thạnh Đông", "Tân Thạnh Tây", "Tân Thông Hội", "Thái Mỹ", "Trung An", "Trung Lập Hạ", "Trung Lập Thượng"],
    "Hóc Môn": ["Bà Điểm", "Đông Thạnh", "Nhị Bình", "Tân Hiệp", "Tân Thới Nhì", "Tân Xuân", "Thới Tam Thôn", "Trung Chánh", "Xuân Thới Đông", "Xuân Thới Sơn", "Xuân Thới Thượng"],
    "Nhà Bè": ["Hiệp Phước", "Long Thới", "Nhà Bè", "Nhơn Đức", "Phú Xuân", "Phước Kiển", "Phước Lộc"]
  },
  "Đà Nẵng": {
    "Hải Châu": ["Hải Châu 1", "Hải Châu 2", "Thạch Thang", "Thanh Bình", "Thuận Phước", "Phước Ninh", "Hòa Thuận Tây", "Hòa Thuận Đông", "Nam Dương", "Bình Hiên", "Bình Thuận", "Hòa Cường Bắc", "Hòa Cường Nam"],
    "Thanh Khê": ["Tam Thuận", "Thanh Khê Tây", "Thanh Khê Đông", "Xuân Hà", "Tân Chính", "Chính Gián", "Vĩnh Trung", "Thạc Gián", "An Khê", "Hòa Khê"],
    "Sơn Trà": ["An Hải Bắc", "An Hải Đông", "An Hải Tây", "Mân Thái", "Nại Hiên Đông", "Phước Mỹ", "Thọ Quang"],
    "Ngũ Hành Sơn": ["Hòa Hải", "Hòa Quý", "Khuê Mỹ", "Mỹ An"],
    "Liên Chiểu": ["Hòa Hiệp Bắc", "Hòa Hiệp Nam", "Hòa Khánh Bắc", "Hòa Khánh Nam", "Hòa Minh"],
    "Cẩm Lệ": ["Hòa An", "Hòa Phát", "Hòa Thọ Đông", "Hòa Thọ Tây", "Hòa Xuân", "Khuê Trung"],
    "Hòa Vang": ["Hòa Bắc", "Hòa Châu", "Hòa Khương", "Hòa Liên", "Hòa Nhơn", "Hòa Ninh", "Hòa Phong", "Hòa Phú", "Hòa Sơn", "Hòa Tiến"],
    "Hoàng Sa": ["Hoàng Sa"]
  },
  "Hải Phòng": {
    "Hồng Bàng": ["Hoàng Văn Thụ", "Minh Khai", "Phan Bội Châu", "Quán Toan", "Sở Dầu", "Thượng Lý", "Trại Chuối", "Hạ Lý"],
    "Ngô Quyền": ["Cầu Đất", "Cầu Tre", "Đằng Giang", "Đông Khê", "Lạc Viên", "Lạch Tray", "Lê Lợi", "Máy Chai", "Máy Tơ", "Vạn Mỹ", "Gia Viên", "Đổng Quốc Bình"],
    "Lê Chân": ["An Biên", "An Dương", "Cát Dài", "Đông Hải 1", "Đông Hải 2", "Dư Hàng", "Dư Hàng Kênh", "Hàng Kênh", "Hồ Nam", "Nghĩa Xá", "Niệm Nghĩa", "Trần Nguyên Hãn", "Vĩnh Niệm"],
    "Hải An": ["Đông Hải 1", "Đông Hải 2", "Đằng Hải", "Đằng Lâm", "Nam Hải", "Tràng Cát", "Cát Bi"],
    "Kiến An": ["Bắc Sơn", "Đồng Hòa", "Nam Sơn", "Ngọc Sơn", "Phù Liễn", "Quán Trữ", "Tân Dương", "Tràng Minh", "Trần Thành Ngọ"],
    "Đồ Sơn": ["Bàng La", "Hợp Đức", "Minh Đức", "Ngọc Hải", "Ngọc Xuyên", "Vạn Hương", "Vạn Sơn"],
    "Dương Kinh": ["Anh Dũng", "Đa Phúc", "Hải Thành", "Hòa Nghĩa", "Hưng Đạo", "Tân Thành"],
    "Thủy Nguyên": ["Núi Đèo", "Minh Đức", "An Lư", "Cao Nhân", "Chính Mỹ", "Dương Quan", "Gia Đức", "Gia Minh", "Hoa Động", "Hoàng Động", "Hợp Thành", "Kênh Giang", "Kiền Bái", "Lại Xuân", "Lâm Động", "Liên Khê", "Lưu Kiếm", "Lưu Kỳ", "Mỹ Đồng", "Ngũ Lão", "Phả Lễ", "Phục Lễ", "Phù Ninh", "Quảng Thanh", "Tam Hưng", "Tân Dương", "Thiên Hương", "Thủy Đường", "Thủy Sơn", "Thủy Triều", "Trung Hà"],
    "An Dương": ["An Đồng", "An Dương", "An Hoà", "An Hồng", "An Hưng", "Bắc Sơn", "Đại Bản", "Đặng Cương", "Đồng Thái", "Hồng Phong", "Hồng Thái", "Lê Lợi", "Lê Thiện", "Nam Sơn", "Quốc Tuấn", "Tân Tiến"],
    "An Lão": ["An Lão", "An Thái", "An Thắng", "An Thọ", "An Tiến", "Bát Trang", "Chiến Thắng", "Mỹ Đức", "Quang Hưng", "Quang Trung", "Quốc Tuấn", "Thái Sơn", "Trường Sơn", "Trường Thành", "Tân Dân", "Tân Viên"],
    "Kiến Thụy": ["Kiến Quốc", "Ngũ Phúc", "Du Lễ", "Đại Đồng", "Đại Hà", "Đại Hợp", "Đoàn Xá", "Hữu Bằng", "Minh Tân", "Ngũ Đoan", "Tân Phong", "Tân Trào", "Thanh Sơn", "Thụy Hương", "Thuận Thiên", "Tú Sơn"],
    "Tiên Lãng": ["Tiên Lãng", "Bắc Hưng", "Cấp Tiến", "Đại Thắng", "Đoàn Lập", "Đông Hưng", "Hùng Thắng", "Kiến Thiết", "Nam Hưng", "Quyết Tiến", "Tây Hưng", "Tiên Cường", "Tiên Minh", "Tiên Thanh", "Tiên Thắng", "Toàn Thắng", "Tự Cường", "Vinh Quang"],
    "Vĩnh Bảo": ["Vĩnh Bảo", "An Hòa", "Cao Minh", "Cộng Hiền", "Cổ Am", "Đồng Minh", "Dũng Tiến", "Giang Biên", "Hiệp Hòa", "Hòa Bình", "Hùng Tiến", "Liên Am", "Nhân Hòa", "Tam Đa", "Tam Cường", "Tân Hưng", "Tân Liên", "Thắng Thủy", "Tiền Phong", "Thanh Lương", "Trấn Dương", "Trung Lập", "Việt Tiến", "Vĩnh An", "Vĩnh Long", "Vĩnh Phong", "Vĩnh Tiến"],
    "Cát Hải": ["Cát Bà", "Cát Hải", "Đồng Bài", "Gia Luận", "Hiền Hào", "Hoàng Châu", "Nghĩa Lộ", "Phù Long", "Trân Châu", "Văn Phong", "Xuân Đám"],
    "Bạch Long Vĩ": ["Bạch Long Vĩ"]
  },
  "Cần Thơ": {
    "Ninh Kiều": ["An Bình", "An Cư", "An Hòa", "An Khánh", "An Nghiệp", "An Phú", "Cái Khế", "Hưng Lợi", "Tân An", "Thới Bình", "Xuân Khánh"],
    "Cái Răng": ["Ba Láng", "Hưng Phú", "Hưng Thạnh", "Lê Bình", "Phú Thứ", "Tân Phú", "Thường Thạnh"],
    "Bình Thủy": ["An Thới", "Bình Thủy", "Bùi Hữu Nghĩa", "Long Hòa", "Long Tuyền", "Thới An Đông", "Trà An", "Trà Nóc"],
    "Ô Môn": ["Châu Văn Liêm", "Long Hưng", "Phước Thới", "Thới An", "Thới Hòa", "Thới Long", "Trường Lạc"],
    "Thốt Nốt": ["Tân Hưng", "Tân Lộc", "Thạnh Hòa", "Thuận An", "Thuận Hưng", "Thốt Nốt", "Thới Thuận", "Trung Kiên", "Trung Nhứt"],
    "Phong Điền": ["Giai Xuân", "Mỹ Khánh", "Nhơn Ái", "Nhơn Nghĩa", "Tân Thới", "Trường Long"],
    "Cờ Đỏ": ["Đông Hiệp", "Đông Thắng", "Thạnh Phú", "Thới Đông", "Thới Hưng", "Thới Xuân", "Trung An", "Trung Hưng", "Trung Thạnh"],
    "Vĩnh Thạnh": ["Thạnh An", "Thạnh Lộc", "Thạnh Lợi", "Thạnh Mỹ", "Thạnh Qưới", "Thạnh Thắng", "Thạnh Tiến", "Vĩnh Bình", "Vĩnh Trinh"]
  },
  "Bình Dương": {
    "Thủ Dầu Một": ["Chánh Mỹ", "Chánh Nghĩa", "Định Hòa", "Hiệp An", "Hiệp Thành", "Hòa Phú", "Phú Cường", "Phú Hòa", "Phú Lợi", "Phú Mỹ", "Phú Tân", "Phú Thọ", "Tân An", "Tương Bình Hiệp"],
    "Thuận An": ["An Phú", "An Sơn", "An Thạnh", "Bình Chuẩn", "Bình Hòa", "Bình Nhâm", "Hưng Định", "Lái Thiêu", "Thuận Giao", "Vĩnh Phú"],
    "Dĩ An": ["An Bình", "Bình An", "Bình Thắng", "Dĩ An", "Đông Hòa", "Tân Bình", "Tân Đông Hiệp"],
    "Bến Cát": ["Chánh Phú Hòa", "Hòa Lợi", "Mỹ Phước", "Tân Định", "Thới Hòa", "An Điền", "An Tây", "Phú An", "Cây Trường II", "Lai Uyên", "Long Nguyên", "Tân Hưng"],
    "Tân Uyên": ["Hội Nghĩa", "Khánh Bình", "Phú Chánh", "Tân Hiệp", "Tân Phước Khánh", "Tân Vĩnh Hiệp", "Thái Hòa", "Thạnh Hội", "Thạnh Phước", "Uyên Hưng", "Vĩnh Tân", "Bạch Đằng", "Đất Cuốc", "Hiếu Liêm", "Lạc An", "Tân Bình", "Tân Định", "Tân Lập", "Tân Mỹ", "Tân Thành", "Thường Tân"],
    "Bàu Bàng": ["Cây Trường", "Hưng Hòa", "Lai Hưng", "Lai Uyên", "Long Nguyên", "Tân Hưng", "Trừ Văn Thố"],
    "Phú Giáo": ["An Bình", "An Linh", "An Long", "An Thái", "Phước Hòa", "Phước Sang", "Tam Lập", "Tân Hiệp", "Tân Long", "Vĩnh Hòa"],
    "Dầu Tiếng": ["An Lập", "Định An", "Định Hiệp", "Định Thành", "Dầu Tiếng", "Long Hòa", "Long Tân", "Minh Hòa", "Minh Tân", "Minh Thạnh", "Thanh An", "Thanh Tuyền"],
    "Bắc Tân Uyên": ["Bình Mỹ", "Đất Cuốc", "Hiếu Liêm", "Lạc An", "Tân Bình", "Tân Định", "Tân Lập", "Tân Mỹ", "Tân Thành", "Thường Tân"]
  },
  "Đồng Nai": {
    "Biên Hòa": ["An Bình", "An Hòa", "Bình Đa", "Bửu Hòa", "Bửu Long", "Hòa An", "Hòa Bình", "Hố Nai", "Long Bình", "Long Bình Tân", "Phước Tân", "Quyết Thắng", "Tam Hiệp", "Tam Hòa", "Tân Biên", "Tân Hạnh", "Tân Hiệp", "Tân Hòa", "Tân Mai", "Tân Phong", "Tân Tiến", "Tân Vạn", "Thanh Bình", "Thống Nhất", "Trảng Dài", "Trung Dũng", "An Hòa", "Hiệp Hòa", "Hóa An", "Phước Hưng", "Long Hưng"],
    "Long Khánh": ["Bảo Quang", "Bảo Vinh", "Bàu Sen", "Bàu Trâm", "Hàng Gòn", "Phú Bình", "Suối Tre", "Xuân An", "Xuân Bình", "Xuân Hòa", "Xuân Lập", "Xuân Tân", "Xuân Thanh", "Xuân Trung"],
    "Nhơn Trạch": ["Đại Phước", "Hiệp Phước", "Long Tân", "Long Thọ", "Phú Đông", "Phú Hội", "Phú Hữu", "Phú Thạnh", "Phước An", "Phước Khánh", "Phước Thiền", "Vĩnh Thanh"],
    "Long Thành": ["Long Thành", "An Phước", "Bàu Cạn", "Bình An", "Bình Sơn", "Cẩm Đường", "Long An", "Long Đức", "Long Hưng", "Long Phước", "Lộc An", "Phước Bình", "Phước Thái", "Suối Trầu", "Tam An", "Tam Phước", "Tân Hiệp"],
    "Trảng Bom": ["Trảng Bom", "An Viễn", "Bàu Hàm", "Bắc Sơn", "Bình Minh", "Cây Gáo", "Đông Hòa", "Đồi 61", "Giang Điền", "Hố Nai 3", "Hưng Thịnh", "Quảng Tiến", "Sông Thao", "Sông Trầu", "Tây Hòa", "Thanh Bình", "Trung Hòa"],
    "Thống Nhất": ["Bàu Hàm 2", "Gia Kiệm", "Gia Tân 1", "Gia Tân 2", "Gia Tân 3", "Hưng Lộc", "Lộ 25", "Quang Trung", "Xuân Thạnh", "Xuân Thiện"],
    "Vĩnh Cửu": ["Vĩnh An", "Bình Hòa", "Bình Lợi", "Hiếu Liêm", "Mã Đà", "Phú Lý", "Tân An", "Tân Bình", "Thạnh Phú", "Thiện Tân", "Trị An", "Vĩnh Tân"],
    "Tân Phú": ["Tân Phú", "Đắk Lua", "Nam Cát Tiên", "Núi Tượng", "Phú An", "Phú Bình", "Phú Điền", "Phú Lâm", "Phú Lập", "Phú Lộc", "Phú Sơn", "Phú Thanh", "Phú Thịnh", "Phú Trung", "Phú Xuân", "Tà Lài", "Thanh Sơn", "Trà Cổ"],
    "Định Quán": ["Định Quán", "Gia Canh", "La Ngà", "Ngọc Định", "Phú Cường", "Phú Hòa", "Phú Lợi", "Phú Ngọc", "Phú Tân", "Phú Túc", "Phú Vinh", "Suối Nho", "Thanh Sơn", "Túc Trưng"],
    "Xuân Lộc": ["Gia Ray", "Lang Minh", "Suối Cao", "Suối Cát", "Xuân Bắc", "Xuân Định", "Xuân Hiệp", "Xuân Hòa", "Xuân Hưng", "Xuân Phú", "Xuân Tâm", "Xuân Thành", "Xuân Thọ", "Xuân Trường"],
    "Cẩm Mỹ": ["Bảo Bình", "Lâm San", "Long Giao", "Nhân Nghĩa", "Sông Nhạn", "Sông Ray", "Thừa Đức", "Xuân Bảo", "Xuân Đông", "Xuân Đường", "Xuân Mỹ", "Xuân Quế", "Xuân Tây"]
  }
};

// Lấy danh sách tỉnh/thành
export const getProvinces = () => {
  return Object.keys(vietnamLocations).sort();
};

// Lấy danh sách quận/huyện theo tỉnh
export const getDistricts = (province) => {
  if (!province || !vietnamLocations[province]) return [];
  return Object.keys(vietnamLocations[province]).sort();
};

// Lấy danh sách phường/xã theo quận/huyện
export const getWards = (province, district) => {
  if (!province || !district || !vietnamLocations[province] || !vietnamLocations[province][district]) return [];
  return vietnamLocations[province][district].sort();
};

export default vietnamLocations;
