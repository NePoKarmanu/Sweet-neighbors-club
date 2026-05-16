// pages/HomePage.tsx
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
  flat: 'Квартира', room: 'Комната', house: 'Дом', townhouse: 'Таунхаус', apartment: 'Апартаменты',
};
const CREATOR_LABELS: Record<string, string> = {
  agency: 'Агентство', owner: 'Собственник',
};
const LIVING_CONDITIONS_LABELS: Record<string, string> = {
  mortgage: 'Ипотека', maternal_capital: 'Маткапитал', bargain: 'Торг', exchange: 'Обмен',
};

const HomePage: React.FC = () => {
  const { user } = useAuth();

  const [data, setData] = useState<ListingListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [offset, setOffset] = useState(0);

  // Фильтры
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

  const buildFilters = (): ListingSearchDTO => {
    const result: ListingSearchDTO = {};
    if (roomsMin || roomsMax) {
      result.rooms = { min: roomsMin ? parseInt(roomsMin) : undefined, max: roomsMax ? parseInt(roomsMax) : undefined };
    }
    if (priceMin || priceMax) {
      result.price = { min: priceMin ? parseFloat(priceMin) : undefined, max: priceMax ? parseFloat(priceMax) : undefined };
    }
    if (areaMin || areaMax) {
      result.area = { min: areaMin ? parseFloat(areaMin) : undefined, max: areaMax ? parseFloat(areaMax) : undefined };
    }
    if (floorMin || floorMax) {
      result.floor = { min: floorMin ? parseInt(floorMin) : undefined, max: floorMax ? parseInt(floorMax) : undefined };
    }
    if (buildYearMin || buildYearMax) {
      result.build_year = { min: buildYearMin ? parseInt(buildYearMin) : undefined, max: buildYearMax ? parseInt(buildYearMax) : undefined };
    }
    if (selectedPropertyTypes.length) result.property_types = selectedPropertyTypes;
    if (selectedCreatorTypes.length) result.creator_types = selectedCreatorTypes as ('agency' | 'owner')[];
    if (selectedLivingConditions.length) result.living_conditions = selectedLivingConditions;
    if (hasRepair !== undefined) result.has_repair = hasRepair;
    return result;
  };

  // Функция загрузки
  const load = useCallback(async (currentOffset: number) => {
    if (!user) return;
    setLoading(true);
    setError('');
    try {
      const search = buildFilters();
      const result = await fetchListings({ limit: LIMIT, offset: currentOffset, search });
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
  }, [user, roomsMin, roomsMax, priceMin, priceMax, areaMin, areaMax, floorMin, floorMax, buildYearMin, buildYearMax, selectedPropertyTypes, selectedCreatorTypes, hasRepair, selectedLivingConditions]);

  useEffect(() => {
    if (user) load(0);
  }, [user]);

  const applyFilters = () => {
    setOffset(0);
    load(0);
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
    setOffset(0);
    load(0);
  };

  const handlePrev = () => {
    const newOffset = Math.max(0, offset - LIMIT);
    setOffset(newOffset);
    load(newOffset);
  };

  const handleNext = () => {
    if (!data?.has_more) return;
    const newOffset = offset + LIMIT;
    setOffset(newOffset);
    load(newOffset);
  };

  const toggleArrayFilter = (value: string, array: string[], setter: React.Dispatch<React.SetStateAction<string[]>>) => {
    if (array.includes(value)) setter(array.filter(v => v !== value));
    else setter([...array, value]);
  };

  return (
    <div className="home-page">
      <aside className="filters-panel">
        <h3>Фильтры</h3>
        {/* Диапазоны */}
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
        {/* Чекбоксы */}
        <div className="filter-group">
          <label>Тип недвижимости</label>
          {PROPERTY_TYPES_OPTIONS.map(type => (
            <label key={type} className="checkbox-label">
              <input type="checkbox" checked={selectedPropertyTypes.includes(type)}
                onChange={() => toggleArrayFilter(type, selectedPropertyTypes, setSelectedPropertyTypes)} />
              {PROPERTY_LABELS[type]}
            </label>
          ))}
        </div>
        <div className="filter-group">
          <label>Продавец</label>
          {CREATOR_TYPES_OPTIONS.map(type => (
            <label key={type} className="checkbox-label">
              <input type="checkbox" checked={selectedCreatorTypes.includes(type)}
                onChange={() => toggleArrayFilter(type, selectedCreatorTypes, setSelectedCreatorTypes)} />
              {CREATOR_LABELS[type]}
            </label>
          ))}
        </div>
        <div className="filter-group">
          <label>Ремонт</label>
          <div className="radio-group">
            <label className="checkbox-label">
              <input type="radio" name="repair" checked={hasRepair === undefined} onChange={() => setHasRepair(undefined)} />
              Любой
            </label>
            <label className="checkbox-label">
              <input type="radio" name="repair" checked={hasRepair === true} onChange={() => setHasRepair(true)} />
              С ремонтом
            </label>
            <label className="checkbox-label">
              <input type="radio" name="repair" checked={hasRepair === false} onChange={() => setHasRepair(false)} />
              Без ремонта
            </label>
          </div>
        </div>
        <div className="filter-group">
          <label>Условия</label>
          {LIVING_CONDITIONS_OPTIONS.map(cond => (
            <label key={cond} className="checkbox-label">
              <input type="checkbox" checked={selectedLivingConditions.includes(cond)}
                onChange={() => toggleArrayFilter(cond, selectedLivingConditions, setSelectedLivingConditions)} />
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
              {data.items.map(item => <ListingCard key={item.id} listing={item} />)}
            </div>
            <div className="pagination">
              <button onClick={handlePrev} disabled={offset === 0}>← Назад</button>
              <span>Показано {data.items.length} из {data.total}</span>
              <button onClick={handleNext} disabled={!data.has_more}>Вперед →</button>
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default HomePage;