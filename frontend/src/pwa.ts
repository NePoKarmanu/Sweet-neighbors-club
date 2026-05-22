import { registerSW } from 'virtual:pwa-register';

export type InstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
};

type PwaEvents = {
  onNeedRefresh: () => void;
  onOfflineReady: () => void;
};

async function cleanupServiceWorkersAndCaches(): Promise<void> {
  if ('serviceWorker' in navigator) {
    const registrations = await navigator.serviceWorker.getRegistrations();
    await Promise.all(registrations.map((registration) => registration.unregister()));
  }

  if ('caches' in window) {
    const cacheKeys = await caches.keys();
    await Promise.all(cacheKeys.map((key) => caches.delete(key)));
  }
}

export const registerPwa = ({ onNeedRefresh, onOfflineReady }: PwaEvents) => {
  if (import.meta.env.DEV) {
    void cleanupServiceWorkersAndCaches();
    return () => {
      // no-op in dev
    };
  }

  return registerSW({
    immediate: true,
    onNeedRefresh,
    onOfflineReady,
    onRegisteredSW(swUrl: string, registration: ServiceWorkerRegistration | undefined) {
      console.info('Service worker зарегистрирован:', swUrl, registration);
    }
  });
};

export async function clearPrivatePwaCaches(): Promise<void> {
  if (!('caches' in window)) return;

  const keys = await caches.keys();
  const privateCaches = keys.filter((key) => key.includes('api-runtime'));
  await Promise.all(privateCaches.map((key) => caches.delete(key)));
}
