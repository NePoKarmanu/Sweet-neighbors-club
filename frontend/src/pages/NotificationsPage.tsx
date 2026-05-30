import React, { useEffect, useState } from 'react';
import { createNotificationSettings, createPushSubscription } from '../api/notificationsApi';
import { useAuth } from '../context/AuthContext';


const PROPERTY_TYPES_OPTIONS = ['flat', 'room', 'house', 'townhouse', 'apartment'];
const CREATOR_TYPES_OPTIONS = ['agency', 'owner'];

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

interface NotificationSettings {
  city: string;
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
}

const NOTIFY_STORAGE_KEY = 'notification_settings';
const CITY_LABEL = 'Воронеж';
const CITY_BACKEND_VALUE = 'voronezh';

const PUSH_PUBLIC_KEY = import.meta.env.VITE_VAPID_PUBLIC_KEY;

const base64UrlToUint8Array = (base64Url: string): Uint8Array => {
  const padding = '='.repeat((4 - (base64Url.length % 4)) % 4);
  const base64 = (base64Url + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = window.atob(base64);
  return Uint8Array.from([...raw].map(char => char.charCodeAt(0)));
};

const NotificationsPage: React.FC = () => {
  const { user } = useAuth();

  const [message, setMessage] = useState('');
  const [city, setCity] = useState(CITY_BACKEND_VALUE);
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

  useEffect(() => {
    const saved = localStorage.getItem(NOTIFY_STORAGE_KEY);
    if (!saved) return;

    try {
      const settings: NotificationSettings = JSON.parse(saved);
      setCity(settings.city || CITY_BACKEND_VALUE);
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
    } catch {
      setCity(CITY_BACKEND_VALUE);
      setChannels([]);
    }
  }, []);

  const handleSave = async () => {
    const toSave: NotificationSettings = {
      city,
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
    };

    localStorage.setItem(NOTIFY_STORAGE_KEY, JSON.stringify(toSave));

    const parseRange = (min: string, max: string) => {
      const parsedMin = min.trim() === '' ? undefined : Number(min);
      const parsedMax = max.trim() === '' ? undefined : Number(max);
      if (parsedMin === undefined && parsedMax === undefined) return undefined;
      return { min: parsedMin, max: parsedMax };
    };

    try {
      await createNotificationSettings({
        city: CITY_BACKEND_VALUE,
        notify_email: channels.includes('email'),
        notify_push: channels.includes('push'),
        property_types: selectedPropertyTypes.length ? selectedPropertyTypes : undefined,
        creator_types: selectedCreatorTypes.length
          ? (selectedCreatorTypes as Array<'agency' | 'owner'>)
          : undefined,
        has_furniture: hasRepair,
        price: parseRange(priceMin, priceMax),
        area: parseRange(areaMin, areaMax),
        rooms: parseRange(roomsMin, roomsMax),
        floor: parseRange(floorMin, floorMax),
        build_year: parseRange(buildYearMin, buildYearMax),
      });
      setMessage('Настройки сохранены');
    } catch {
      setMessage('Не удалось сохранить настройки');
    }
  };

  const handleReset = () => {
    setCity(CITY_BACKEND_VALUE);
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
    localStorage.removeItem(NOTIFY_STORAGE_KEY);
    setMessage('Настройки сброшены');
  };

  const toggleArray = (
    value: string,
    array: string[],
    setter: React.Dispatch<React.SetStateAction<string[]>>,
  ) => {
    if (array.includes(value)) {
      setter(array.filter(v => v !== value));
    } else {
      setter([...array, value]);
    }
  };

  const handlePushToggle = async (checked: boolean) => {
    if (checked) {
      if (!('Notification' in window)) {
        alert('Браузер не поддерживает уведомления');
        return;
      }
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        alert('Push-уведомления не поддерживаются в этом браузере');
        return;
      }
      if (!PUSH_PUBLIC_KEY) {
        alert('VAPID public key не настроен');
        return;
      }

      if (!window.isSecureContext) {
        alert('Push-уведомления работают только в защищённом контексте (HTTPS или localhost)');
        return;
      }

      if (Notification.permission === 'denied') {
        alert('Разрешение на уведомления заблокировано в браузере. Разрешите уведомления в настройках сайта.');
        return;
      }

      const permission =
        Notification.permission === 'granted'
          ? 'granted'
          : await Notification.requestPermission();
      if (permission === 'granted') {
        try {
          const registration = await navigator.serviceWorker.register('/sw.js');
          const existingSubscription = await registration.pushManager.getSubscription();
          const pushSubscription = existingSubscription
            ? existingSubscription
            : await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: base64UrlToUint8Array(PUSH_PUBLIC_KEY) as BufferSource,
              });
          const key = pushSubscription.getKey('p256dh');
          const auth = pushSubscription.getKey('auth');
          if (!key || !auth) {
            alert('Не удалось получить push ключи подписки');
            return;
          }

          await createPushSubscription({
            endpoint: pushSubscription.endpoint,
            p256dh: btoa(String.fromCharCode(...new Uint8Array(key))),
            auth: btoa(String.fromCharCode(...new Uint8Array(auth))),
            user_agent: navigator.userAgent,
          });
        } catch {
          alert('Не удалось зарегистрировать push-подписку');
          return;
        }
        setChannels(prev => (prev.includes('push') ? prev : [...prev, 'push']));
      } else {
        alert('Не удалось получить разрешение на уведомления');
      }
      return;
    }

    setChannels(prev => prev.filter(c => c !== 'push'));
  };

  if (!user) {
    return <div className="form-page">Требуется авторизация</div>;
  }

  return (
    <div className="form-page" style={{ maxWidth: '500px', margin: '30px auto', padding: '20px' }}>
      <h1>Настройки уведомлений</h1>

      <section>
        <h2>Город</h2>
        <div className="filter-group">
          <label htmlFor="notifications-city">Выберите город</label>
          <select id="notifications-city" value={city} onChange={e => setCity(e.target.value)}>
            <option value={CITY_BACKEND_VALUE}>{CITY_LABEL}</option>
          </select>
        </div>
      </section>

      <section>
        <h2>Каналы доставки</h2>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={channels.includes('email')}
            onChange={e => {
              if (e.target.checked) setChannels(prev => [...prev, 'email']);
              else setChannels(prev => prev.filter(c => c !== 'email'));
            }}
          />
          Электронная почта
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={channels.includes('push')}
            onChange={e => handlePushToggle(e.target.checked)}
          />
          Push-уведомления
        </label>
      </section>

      <section>
        <h2>Критерии поиска</h2>
        <div className="filter-group">
          <label>Комнат</label>
          <div className="range-inputs">
            <input type="number" placeholder="от" value={roomsMin} onChange={e => setRoomsMin(e.target.value)} />
            <input type="number" placeholder="до" value={roomsMax} onChange={e => setRoomsMax(e.target.value)} />
          </div>
        </div>

        <div className="filter-group">
          <label>Цена, ₽</label>
          <div className="range-inputs">
            <input type="number" placeholder="от" value={priceMin} onChange={e => setPriceMin(e.target.value)} />
            <input type="number" placeholder="до" value={priceMax} onChange={e => setPriceMax(e.target.value)} />
          </div>
        </div>

        <div className="filter-group">
          <label>Площадь, м²</label>
          <div className="range-inputs">
            <input type="number" placeholder="от" value={areaMin} onChange={e => setAreaMin(e.target.value)} />
            <input type="number" placeholder="до" value={areaMax} onChange={e => setAreaMax(e.target.value)} />
          </div>
        </div>

        <div className="filter-group">
          <label>Этаж</label>
          <div className="range-inputs">
            <input type="number" placeholder="от" value={floorMin} onChange={e => setFloorMin(e.target.value)} />
            <input type="number" placeholder="до" value={floorMax} onChange={e => setFloorMax(e.target.value)} />
          </div>
        </div>

        <div className="filter-group">
          <label>Год постройки</label>
          <div className="range-inputs">
            <input type="number" placeholder="от" value={buildYearMin} onChange={e => setBuildYearMin(e.target.value)} />
            <input type="number" placeholder="до" value={buildYearMax} onChange={e => setBuildYearMax(e.target.value)} />
          </div>
        </div>

        <div className="filter-group">
          <label>Тип недвижимости</label>
          {PROPERTY_TYPES_OPTIONS.map(type => (
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
          {CREATOR_TYPES_OPTIONS.map(type => (
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
              <input type="radio" name="notify_repair" checked={hasRepair === undefined} onChange={() => setHasRepair(undefined)} />
              Любой
            </label>
            <label className="checkbox-label">
              <input type="radio" name="notify_repair" checked={hasRepair === true} onChange={() => setHasRepair(true)} />
              С ремонтом
            </label>
            <label className="checkbox-label">
              <input type="radio" name="notify_repair" checked={hasRepair === false} onChange={() => setHasRepair(false)} />
              Без ремонта
            </label>
          </div>
        </div>
      </section>

      <div style={{ marginTop: '20px' }}>
        <button className="btn-apply" onClick={handleSave}>Сохранить настройки</button>
        <button className="btn-reset" onClick={handleReset}>Сбросить</button>
      </div>

      {message && <p style={{ marginTop: '1rem', textAlign: 'center', color: '#2e7d32' }}>{message}</p>}
    </div>
  );
};

export default NotificationsPage;
