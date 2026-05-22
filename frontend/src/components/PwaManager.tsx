import { useEffect, useMemo, useState } from 'react';
import { clearPrivatePwaCaches, registerPwa } from '../pwa';
import type { InstallPromptEvent } from '../pwa';

const PwaManager: React.FC = () => {
  const [needRefresh, setNeedRefresh] = useState(false);
  const [offlineReady, setOfflineReady] = useState(false);
  const [installPrompt, setInstallPrompt] = useState<InstallPromptEvent | null>(null);

  const updateServiceWorker = useMemo(
    () => registerPwa({ onNeedRefresh: () => setNeedRefresh(true), onOfflineReady: () => setOfflineReady(true) }),
    []
  );

  useEffect(() => {
    const handleBeforeInstallPrompt = (event: Event) => {
      event.preventDefault();
      setInstallPrompt(event as InstallPromptEvent);
    };

    const handleAppInstalled = () => {
      setInstallPrompt(null);
      console.info('PWA успешно установлено');
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  useEffect(() => {
    const onLogout = () => {
      void clearPrivatePwaCaches();
    };

    window.addEventListener('auth:logout', onLogout);
    return () => window.removeEventListener('auth:logout', onLogout);
  }, []);

  const handleInstall = async () => {
    if (!installPrompt) return;
    await installPrompt.prompt();
    await installPrompt.userChoice;
    setInstallPrompt(null);
  };

  return (
    <>
      {installPrompt && (
        <div className="pwa-banner" role="status">
          <span>Установите Sweet Neighbors Club как приложение.</span>
          <button onClick={handleInstall} type="button">Установить</button>
        </div>
      )}
      {needRefresh && (
        <div className="pwa-banner" role="status">
          <span>Доступна новая версия приложения.</span>
          <button onClick={() => updateServiceWorker(true)} type="button">Обновить</button>
        </div>
      )}
      {offlineReady && !needRefresh && (
        <div className="pwa-banner pwa-banner--success" role="status">
          <span>Офлайн-режим готов.</span>
          <button onClick={() => setOfflineReady(false)} type="button">Ок</button>
        </div>
      )}
    </>
  );
};

export default PwaManager;