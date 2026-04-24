import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useState } from 'react';

const Header = () => {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    setMenuOpen(false);
    navigate('/');
  };

  return (
    <header className="header">
      <Link to="/" className="logo">Sweet Neighbors</Link>
      <nav>
        {user ? (
          <div className="user-menu">
            <button onClick={() => setMenuOpen(!menuOpen)} className="user-button">
              {user.email}
            </button>
            {menuOpen && (
              <ul className="dropdown">
                <li><Link to="/notifications">Уведомления</Link></li>
                <li><Link to="/profile">Настройки</Link></li>
                <li><button onClick={handleLogout}>Выход</button></li>
              </ul>
            )}
          </div>
        ) : (
          <Link to="/signin">Войти</Link>
        )}
      </nav>
    </header>
  );
};

export default Header; 