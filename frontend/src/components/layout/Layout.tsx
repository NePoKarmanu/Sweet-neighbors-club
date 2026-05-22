import Header from './Header';
import PwaManager from '../PwaManager';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="app-container">
    <PwaManager />
    <Header />
    <main className="main-content">{children}</main>
  </div>
);

export default Layout;