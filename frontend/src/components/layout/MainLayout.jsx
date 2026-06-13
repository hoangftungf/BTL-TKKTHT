import { Outlet } from 'react-router-dom';
import Header from './Header';
import Footer from './Footer';
import LoginModal from '../auth/LoginModal';
import CartDrawer from '../cart/CartDrawer';

const MainLayout = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-grow">
        <Outlet />
      </main>
      <Footer />
      <LoginModal />
      <CartDrawer />
    </div>
  );
};

export default MainLayout;
