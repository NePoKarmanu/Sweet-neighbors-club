import React, { useState, useEffect, useCallback } from 'react';
import { fetchListings } from '../api/listingsApi';
import type { ListingListResponse, ListingSearchDTO } from '../types';
import ListingCard from '../components/ListingCard';
import { useAuth } from '../context/AuthContext';

const LIMIT = 6;

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

const HomePage: React.FC = () => {
  const { user } = useAuth();

  const [data, setData] = useState<ListingListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [offset, setOffset] = useState(0);

  const [filters, setFilters] = useState<ListingSearchDTO>({});

  const [roomsMin, setRoomsMin] = useState<string>('');
  const [roomsMax, setRoomsMax] = useState<string>('');
  const [priceMin, setPriceMin] = useState<string>('');
  const [priceMax, setPriceMax] = useState<string>('');
  const [areaMin, setAreaMin] = useState<string>('');
  const [areaMax, setAreaMax] = useState<string>('');
  const [floorMin, setFloorMin] = useState<string>('');
  const [floorMax, setFloorMax] = useState<string>('');
  const [buildYearMin, setBuildYearMin] = useState<string>('');
  const [buildYearMax, setBuildYearMax] = useState<string>('');

  const [selectedPropertyTypes, setSelectedPropertyTypes] = useState<string[]>([]);
  const [selectedCreatorTypes, setSelectedCreatorTypes] = useState<string[]>([]);
  const [hasRepair, setHasRepair] = useState<boolean | undefined>(undefined);
  const [selectedLivingConditions, setSelectedLivingConditions] = useState<string[]>([]);

  const buildFilters = useCallback((): ListingSearchDTO => {
    const result: ListingSearchDTO = {};

    if (roomsMin || roomsMax) {
      result.rooms = {
        min: roomsMin ? parseInt(roomsMin) : undefined,
        max: roomsMax ? parseInt(roomsMax) : undefined,
      };
    }
    if (priceMin || priceMax) {
      result.price = {
        min: priceMin ? parseFloat(priceMin) : undefined,
        max: priceMax ? parseFloat(priceMax) : undefined,
      };
    }
    if (areaMin || areaMax) {
      result.area = {
        min: areaMin ? parseFloat(areaMin) : undefined,
        max: areaMax ? parseFloat(areaMax) : undefined,
      };
    }
    if (floorMin || floorMax) {
      result.floor = {
        min: floorMin ? parseInt(floorMin) : undefined,
        max: floorMax ? parseInt(floorMax) : undefined,
      };
    }
    if (buildYearMin || buildYearMax) {
      result.build_year = {
        min: buildYearMin ? parseInt(buildYearMin) : undefined,
        max: buildYearMax ? parseInt(buildYearMax) : undefined,
      };
    }

    if (selectedPropertyTypes.length > 0) {
      result.property_types = selectedPropertyTypes;
    }
    if (selectedCreatorTypes.length > 0) {
      result.creator_types = selectedCreatorTypes as ('agency' | 'owner')[];
    }
    if (selectedLivingConditions.length > 0) {
      result.living_conditions = selectedLivingConditions;
    }

    // Булево
    if (hasRepair !== undefined) {
      result.has_repair = hasRepair;
    }

    return result;
  }, [
    roomsMin, roomsMax, priceMin, priceMax, areaMin, areaMax,
    floorMin, floorMax, buildYearMin, buildYearMax,
    selectedPropertyTypes, selectedCreatorTypes,
    hasRepair, selectedLivingConditions,
  ]);

  // Загрузка данных
  const load = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError('');
    try {
      const search = buildFilters();
      const result = await fetchListings({
        limit: LIMIT,
        offset,
        search,
      });
      setData(result);
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Ошибка авторизации. Попробуйте войти заново.');
      } else {
        setError('Не удалось загрузить объявления');
      }
    } finally {
      setLoading(false);
    }
  }, [user, buildFilters, offset]);

  useEffect(() => {
    if (user) load();
  }, [load, user]);

  const applyFilters = () => {
    setFilters(buildFilters());
    setOffset(0);
  };

  const resetFilters = () => {
    setRoomsMin(''); setRoomsMax('');
    setPriceMin(''); setPriceMax('');
    setAreaMin(''); setAreaMax('');
    setFloorMin(''); setFloorMax('');
    setBuildYearMin(''); setBuildYearMax('');
    setSelectedPropertyTypes([]);
    setSelectedCreatorTypes([]);
    setHasRepair(undefined);
    setSelectedLivingConditions([]);
    setFilters({});
    setOffset(0);
  };

  // Обработчики пагинации
  const handlePrev = () => setOffset(prev => Math.max(0, prev - LIMIT));
  const handleNext = () => {
    if (data?.has_more) setOffset(prev => prev + LIMIT);
  };

  // Обработчик чекбоксов для массивов
  const toggleArrayFilter = (
    value: string,
    current: string[],
    setter: React.Dispatch<React.SetStateAction<string[]>>
  ) => {
    if (current.includes(value)) {
      setter(current.filter(v => v !== value));
    } else {
      setter([...current, value]);
    }
  };

  // для неавторизованных
  if (!user) {
    return (
      <div className="landing-page">
        <h1>Добро пожаловать в Sweet Neighbors Club!</h1>
        <p>
          Мы собираем самые свежие объявления с Циан, Авито и Домклик и присылаем вам только те,
          которые подходят под ваши критерии. Настройте фильтры, укажите желаемые параметры квартиры,
          и получайте уведомления на почту или прямо на телефон.
        </p>
        <ul>
          <li>Объявления с трех крупнейших площадок</li>
          <li>Мгновенные уведомления о новых объектах</li>
          <li>Гибкие фильтры по комнатам, цене, этажу</li>
          <li>Бесплатно и без лишних действий</li>
        </ul>
      </div>
    );

  }

  return (
    <div className="home-page">
      <aside className="filters-panel">
        <h3>Фильтры</h3>

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
          {PROPERTY_TYPES_OPTIONS.map(type => (
            <label key={type} className="checkbox-label">
              <input
                type="checkbox"
                checked={selectedPropertyTypes.includes(type)}
                onChange={() => toggleArrayFilter(type, selectedPropertyTypes, setSelectedPropertyTypes)}
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
                onChange={() => toggleArrayFilter(type, selectedCreatorTypes, setSelectedCreatorTypes)}
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
                name="has_repair"
                checked={hasRepair === undefined}
                onChange={() => setHasRepair(undefined)}
              />
              Любой
            </label>
            <label className="checkbox-label">
              <input
                type="radio"
                name="has_repair"
                checked={hasRepair === true}
                onChange={() => setHasRepair(true)}
              />
              С ремонтом
            </label>
            <label className="checkbox-label">
              <input
                type="radio"
                name="has_repair"
                checked={hasRepair === false}
                onChange={() => setHasRepair(false)}
              />
              Без ремонта
            </label>
          </div>
        </div>

        <div className="filter-group">
          <label>Условия</label>
          {LIVING_CONDITIONS_OPTIONS.map(cond => (
            <label key={cond} className="checkbox-label">
              <input
                type="checkbox"
                checked={selectedLivingConditions.includes(cond)}
                onChange={() => toggleArrayFilter(cond, selectedLivingConditions, setSelectedLivingConditions)}
              />
              {LIVING_CONDITIONS_LABELS[cond]}
            </label>
          ))}
        </div>

        <button className="btn-apply" onClick={applyFilters}>Применить</button>
        <button className="btn-reset" onClick={resetFilters}>Сбросить</button>
      </aside>

      <main className="listings-area">
        {loading && <div className="spinner">Загрузка...</div>}
        {error && <div className="error-message">{error}</div>}
        {!loading && data && (
          <>
            <div className="listings-grid">
              {data.items.map(item => (
                <ListingCard key={item.id} listing={item} />
              ))}
            </div>
            <div className="pagination">
              <button onClick={handlePrev} disabled={offset === 0}>
                ← Назад
              </button>
              <span>
                Показано {data.items.length} из {data.total}
              </span>
              <button onClick={handleNext} disabled={!data.has_more}>
                Вперед →
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default HomePage;