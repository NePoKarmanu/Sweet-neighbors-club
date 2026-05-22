import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { createNotificationSettings, createPushSubscription } from '../api/notificationsApi';

const PROPERTY_TYPES_OPTIONS = ['flat', 'room', 'house', 'townhouse', 'apartment'];
const CREATOR_TYPES_OPTIONS = ['agency', 'owner'];
const LIVING_CONDITIONS_OPTIONS = ['mortgage', 'maternal_capital', 'bargain', 'exchange'];

const PROPERTY_LABELS: Record<string, string> = {
  flat: 'Квартира',
  room: 'Комната',
  house: 'Дом',
  townhouse: 'Таунхаус',
  apartment: 'Апартаменты',
};

const CREATOR_LABELS: Record<string, string> = {
  agency: 'Агентство',
  owner: 'Собственник',
};

const LIVING_CONDITIONS_LABELS: Record<string, string> = {
  mortgage: 'Ипотека',
  maternal_capital: 'Маткапитал',
  bargain: 'Торг',
  exchange: 'Обмен',
};

interface NotificationSettings {
  channels: string[];
  roomsMin: string;
  roomsMax: string;
  priceMin: string;
  priceMax: string;
  areaMin: string;
  areaMax: string;
  floorMin: string;
  floorMax: string;
  buildYearMin: string;
  buildYearMax: string;
  selectedPropertyTypes: string[];
  selectedCreatorTypes: string[];
  hasRepair: boolean | undefined;
  selectedLivingConditions: string[];
}

const NOTIFY_STORAGE_KEY = 'notification_settings';

const urlBase64ToUint8Array = (base64String: string): Uint8Array => {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
};

const NotificationsPage: React.FC = () => {
  const { user } = useAuth();

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [channels, setChannels] = useState<string[]>([]);
  const [roomsMin, setRoomsMin] = useState('');
  const [roomsMax, setRoomsMax] = useState('');
  const [priceMin, setPriceMin] = useState('');
  const [priceMax, setPriceMax] = useState('');
  const [areaMin, setAreaMin] = useState('');
  const [areaMax, setAreaMax] = useState('');
  const [floorMin, setFloorMin] = useState('');
  const [floorMax, setFloorMax] = useState('');
  const [buildYearMin, setBuildYearMin] = useState('');
  const [buildYearMax, setBuildYearMax] = useState('');
  const [selectedPropertyTypes, setSelectedPropertyTypes] = useState<string[]>([]);
  const [selectedCreatorTypes, setSelectedCreatorTypes] = useState<string[]>([]);
  const [hasRepair, setHasRepair] = useState<boolean | undefined>(undefined);
  const [selectedLivingConditions, setSelectedLivingConditions] = useState<string[]>([]);

  useEffect(() => {
    const saved = localStorage.getItem(NOTIFY_STORAGE_KEY);
    if (!saved) return;

    try {
      const settings: NotificationSettings = JSON.parse(saved);
      setChannels(settings.channels || []);
      setRoomsMin(settings.roomsMin || '');
      setRoomsMax(settings.roomsMax || '');
      setPriceMin(settings.priceMin || '');
      setPriceMax(settings.priceMax || '');
      setAreaMin(settings.areaMin || '');
      setAreaMax(settings.areaMax || '');
      setFloorMin(settings.floorMin || '');
      setFloorMax(settings.floorMax || '');
      setBuildYearMin(settings.buildYearMin || '');
      setBuildYearMax(settings.buildYearMax || '');
      setSelectedPropertyTypes(settings.selectedPropertyTypes || []);
      setSelectedCreatorTypes(settings.selectedCreatorTypes || []);
      setHasRepair(settings.hasRepair);
      setSelectedLivingConditions(settings.selectedLivingConditions || []);
    } catch {
      localStorage.removeItem(NOTIFY_STORAGE_KEY);
    }
  }, []);
  const subscribePushIfNeeded = async (): Promise<void> => {
    if (!channels.includes('push')) return;

    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      throw new Error('Push не поддерживается этим браузером');
    }

    const registration = await navigator.serviceWorker.ready;
    const vapidPublicKey = import.meta.env.VITE_VAPID_PUBLIC_KEY as string | undefined;
    if (!vapidPublicKey) {
      throw new Error('Отсутствует VITE_VAPID_PUBLIC_KEY');
    }

    const existingSubscription = await registration.pushManager.getSubscription();
    const pushSubscription =
      existingSubscription ??
      (await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublicKey) as unknown as BufferSource,
      }));

    const subscriptionJson = pushSubscription.toJSON();
    const p256dh = subscriptionJson.keys?.p256dh;
    const auth = subscriptionJson.keys?.auth;

    if (!subscriptionJson.endpoint || !p256dh || !auth) {
      throw new Error('Не удалось получить данные push-подписки');
    }

    await createPushSubscription({
      endpoint: subscriptionJson.endpoint,
      p256dh,
      auth,
      user_agent: navigator.userAgent,
    });
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError('');
    setMessage('');

    const toSave: NotificationSettings = {
      channels,
      roomsMin,
      roomsMax,
      priceMin,
      priceMax,
      areaMin,
      areaMax,
      floorMin,
      floorMax,
      buildYearMin,
      buildYearMax,
      selectedPropertyTypes,
      selectedCreatorTypes,
      hasRepair,
      selectedLivingConditions,
    };
    try {
      localStorage.setItem(NOTIFY_STORAGE_KEY, JSON.stringify(toSave));

      await createNotificationSettings({
        city: 'Москва',
        notify_email: channels.includes('email'),
        notify_push: channels.includes('push'),
      });

      await subscribePushIfNeeded();
      setMessage('Настройки сохранены');
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Не удалось сохранить настройки');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setChannels([]);
    setRoomsMin('');
    setRoomsMax('');
    setPriceMin('');
    setPriceMax('');
    setAreaMin('');
    setAreaMax('');
    setFloorMin('');
    setFloorMax('');
    setBuildYearMin('');
    setBuildYearMax('');
    setSelectedPropertyTypes([]);
    setSelectedCreatorTypes([]);
    setHasRepair(undefined);
    setSelectedLivingConditions([]);

    localStorage.removeItem(NOTIFY_STORAGE_KEY);
    setMessage('Настройки сброшены');
    setError('');
  };
  const toggleArray = (
    value: string,
    array: string[],
    setter: React.Dispatch<React.SetStateAction<string[]>>,
  ) => {
    if (array.includes(value)) {
      setter(array.filter((v) => v !== value));
      return;
    }

    setter([...array, value]);
  };

  if (!user) {
    return <div className="form-page">Требуется авторизация</div>;
  }

  return (
    <div className="form-page notifications-page">
      <h1>Настройки уведомлений</h1>

      <section>
        <h2>Каналы доставки</h2>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={channels.includes('email')}
            onChange={(e) => {
              if (e.target.checked) setChannels((prev) => [...prev, 'email']);
              else setChannels((prev) => prev.filter((c) => c !== 'email'));
            }}
          />
          Электронная почта
        </label>

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={channels.includes('push')}
            onChange={(e) => {
              if (e.target.checked) setChannels((prev) => [...prev, 'push']);
              else setChannels((prev) => prev.filter((c) => c !== 'push'));
            }}
          />
          Push-уведомления
        </label>
      </section>

      <section>
        <h2>Критерии поиска</h2>
        <div className="filter-group">
          <label>Комнат</label>
          <div className="range-inputs">
            <input type="number" placeholder="от" value={roomsMin} onChange={(e) => setRoomsMin(e.target.value)} />
            <input type="number" placeholder="до" value={roomsMax} onChange={(e) => setRoomsMax(e.target.value)} />
          </div>
        </div>

        <div className="filter-group">
          <label>Цена, ₽</label>
          <div className="range-inputs">
            <input type="number" placeholder="от" value={priceMin} onChange={(e) => setPriceMin(e.target.value)} />
            <input type="number" placeholder="до" value={priceMax} onChange={(e) => setPriceMax(e.target.value)} />
          </div>
        </div>

        <div className="filter-group">
          <label>Площадь, м²</label>
          <div className="range-inputs">
            <input type="number" placeholder="от" value={areaMin} onChange={(e) => setAreaMin(e.target.value)} />
            <input type="number" placeholder="до" value={areaMax} onChange={(e) => setAreaMax(e.target.value)} />
          </div>
        </div>

        <div className="filter-group">
          <label>Этаж</label>
          <div className="range-inputs">
            <input type="number" placeholder="от" value={floorMin} onChange={(e) => setFloorMin(e.target.value)} />
            <input type="number" placeholder="до" value={floorMax} onChange={(e) => setFloorMax(e.target.value)} />
          </div>
        </div>

        <div className="filter-group">
          <label>Год постройки</label>
          <div className="range-inputs">
            <input type="number" placeholder="от" value={buildYearMin} onChange={(e) => setBuildYearMin(e.target.value)} />
            <input type="number" placeholder="до" value={buildYearMax} onChange={(e) => setBuildYearMax(e.target.value)} />
          </div>
        </div>

        <div className="filter-group">
          <label>Тип недвижимости</label>
            {PROPERTY_TYPES_OPTIONS.map((type) => (
            <label key={type} className="checkbox-label">
              <input
                type="checkbox"
                checked={selectedPropertyTypes.includes(type)}
                onChange={() => toggleArray(type, selectedPropertyTypes, setSelectedPropertyTypes)}
              />
              {PROPERTY_LABELS[type]}
            </label>
          ))}
        </div>

        <div className="filter-group">
          <label>Продавец</label>
           {CREATOR_TYPES_OPTIONS.map((type) => (
            <label key={type} className="checkbox-label">
              <input
                type="checkbox"
                checked={selectedCreatorTypes.includes(type)}
                onChange={() => toggleArray(type, selectedCreatorTypes, setSelectedCreatorTypes)}
              />
              {CREATOR_LABELS[type]}
            </label>
          ))}
        </div>

        <div className="filter-group">
          <label>Ремонт</label>
          <div className="radio-group">
            <label className="checkbox-label">
          <input
                type="radio"
                name="notify_repair"
                checked={hasRepair === undefined}
                onChange={() => setHasRepair(undefined)}
              />
              Любой
            </label>
            <label className="checkbox-label">
          <input
                type="radio"
                name="notify_repair"
                checked={hasRepair === true}
                onChange={() => setHasRepair(true)}
              />
              С ремонтом
            </label>
            <label className="checkbox-label">
          <input
                type="radio"
                name="notify_repair"
                checked={hasRepair === false}
                onChange={() => setHasRepair(false)}
              />
              Без ремонта
            </label>
          </div>
        </div>

        <div className="filter-group">
          <label>Условия</label>
          {LIVING_CONDITIONS_OPTIONS.map((cond) => (
            <label key={cond} className="checkbox-label">
              <input
                type="checkbox"
                checked={selectedLivingConditions.includes(cond)}
                onChange={() => toggleArray(cond, selectedLivingConditions, setSelectedLivingConditions)}
              />
              {LIVING_CONDITIONS_LABELS[cond]}
            </label>
          ))}
        </div>
      </section>

      <div style={{ marginTop: '20px' }}>
          <button className="btn-apply" onClick={handleSave} disabled={isSaving}>
          {isSaving ? 'Сохранение...' : 'Сохранить настройки'}
        </button>
        <button className="btn-reset" onClick={handleReset} disabled={isSaving}>
          Сбросить
        </button>
      </div>

      {error && <p style={{ marginTop: '1rem', textAlign: 'center', color: '#d32f2f' }}>{error}</p>}
      {message && <p style={{ marginTop: '1rem', textAlign: 'center', color: '#2e7d32' }}>{message}</p>}
    </div>
  );
};

export default NotificationsPage;