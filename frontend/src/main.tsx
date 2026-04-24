import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

async function requestPushPermission() {
  if (!('Notification' in window)) {
    console.log('Уведомления не поддерживаются');
    return;
  }
  const permission = await Notification.requestPermission();
  if (permission === 'granted') {
    console.log('Разрешение получено');
    // В будущем здесь будет подписка на push-сервис
  }
}
