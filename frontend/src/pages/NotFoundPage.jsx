import { Link } from 'react-router-dom';

const NotFoundPage = () => {
  return (
    <div className="min-h-[calc(100vh-300px)] flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-gray-200">404</h1>
        <h2 className="text-2xl font-bold text-gray-900 mt-4">Không tìm thấy trang</h2>
        <p className="text-gray-500 mt-2 mb-8">
          Trang bạn đang tìm kiếm không tồn tại hoặc đã bị di chuyển.
        </p>
        <Link to="/" className="btn-primary">
          Về trang chủ
        </Link>
      </div>
    </div>
  );
};

export default NotFoundPage;
