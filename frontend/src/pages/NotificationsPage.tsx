import { useState } from 'react';

const NotificationsPage = () => {
  // Временное хранение настроек, пока нет API для их сохранения
  const storedEmail = localStorage.getItem('notify_email') === 'true';
  const storedPush = localStorage.getItem('notify_push') === 'true';

  const [emailEnabled, setEmailEnabled] = useState(storedEmail);
  const [pushEnabled, setPushEnabled] = useState(storedPush);
  const [message, setMessage] = useState('');

  const handleRequestPushPermission = async () => {
    if (!('Notification' in window)) {
      alert('Ваш браузер не поддерживает уведомления');
      return;
    }
    const permission = await Notification.requestPermission();
    if (permission === 'granted') {
      setPushEnabled(true);
      localStorage.setItem('notify_push', 'true');
      setMessage('Push-уведомления разрешены');
    } else {
      setMessage('Разрешение на push-уведомления не получено');
    }
  };

  const handleSave = () => {
    localStorage.setItem('notify_email', String(emailEnabled));
    localStorage.setItem('notify_push', String(pushEnabled));
    setMessage('Настройки уведомлений сохранены локально');
  };

  return (
    <div className="form-page">
      <h1>Настройки уведомлений</h1>

      <div className="field">
        <label>
          <input
            type="checkbox"
            checked={emailEnabled}
            onChange={(e) => setEmailEnabled(e.target.checked)}
          />
          {' '}Уведомления по Email
        </label>
      </div>

      <div className="field">
        <label>
          <input
            type="checkbox"
            checked={pushEnabled}
            onChange={async (e) => {
              if (e.target.checked) {
                await handleRequestPushPermission();
              } else {
                setPushEnabled(false);
                localStorage.setItem('notify_push', 'false');
              }
            }}
          />
          {' '}Push-уведомления (PWA)
        </label>
      </div>

      {/* Блок для будущих критериев поиска */}
      <div style={{ marginTop: '1rem', padding: '1rem', background: '#f9f9f9', borderRadius: '8px' }}>
        <p><em>Критерии поиска (будут добавлены позже)</em></p>
        <label>Количество комнат: <input disabled placeholder="от студии до 4+" style={{ width: '100%', marginTop: '0.5rem' }} /></label>
        <label style={{ display: 'block', marginTop: '0.5rem' }}>Цена от: <input disabled placeholder="0" style={{ width: '100%', marginTop: '0.5rem' }} /></label>
      </div>

      <button onClick={handleSave} style={{ marginTop: '1.5rem', width: '100%' }}>
        Сохранить настройки
      </button>

      {message && <p style={{ marginTop: '1rem', textAlign: 'center', color: '#2e7d32' }}>{message}</p>}
    </div>
  );
};

export default NotificationsPage;
