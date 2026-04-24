import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

const ProfilePage: React.FC = () => {
  const { user, updateProfile } = useAuth();

  const [email, setEmail] = useState(user?.email || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [newPassword, setNewPassword] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!currentPassword) {
      setError('Введите текущий пароль');
      return;
    }

    setIsLoading(true);
    try {
      await updateProfile(email, phone, newPassword, currentPassword);
      setSuccessMsg('Профиль успешно обновлён');
      setCurrentPassword('');
      setNewPassword('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка обновления профиля');
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) {
    return <div>Необходимо авторизоваться</div>;
  }

  return (
    <div className="form-page">
      <h1>Настройки профиля</h1>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="field">
          <label>Телефон</label>
          <input
            type="text"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            required
          />
        </div>

        <div className="field">
          <label>Новый пароль (оставьте пустым, если не меняете)</label>
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Новый пароль"
          />
        </div>

        <hr />

        <div className="field">
          <label>Текущий пароль (обязательно для сохранения)</label>
          <input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
          />
        </div>

        {error && <div className="server-error">{error}</div>}
        {successMsg && <div className="success-msg">{successMsg}</div>}

        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Сохранение...' : 'Сохранить изменения'}
        </button>
      </form>
    </div>
  );
};

export default ProfilePage;