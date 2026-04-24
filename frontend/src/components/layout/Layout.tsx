import Header from './Header';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="app-container">
    <Header />
    <main className="main-content">{children}</main>
  </div>
);

export default Layout;