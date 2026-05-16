import React from 'react';
import type { Listing } from '../types';

const PROPERTY_LABELS: Record<string, string> = {
  flat: 'Квартира',
  room: 'Комната',
  house: 'Дом',
  townhouse: 'Таунхаус',
  apartment: 'Апартаменты',
};

const LIVING_CONDITIONS_LABELS: Record<string, string> = {
  mortgage: 'Ипотека',
  maternal_capital: 'Маткапитал',
  bargain: 'Торг',
  exchange: 'Обмен',
};

interface ListingCardProps {
  listing: Listing;
}

const ListingCard: React.FC<ListingCardProps> = ({ listing }) => {
  const {
    title, price, rooms, area, floor, url, image_url,
    data: { property_type, has_repair, build_year, creator_type, living_conditions },
  } = listing;

  const formattedPrice = price != null ? `${Math.round(price).toLocaleString('ru-RU')} ₽` : 'Цена не указана';
  const formattedArea = area != null ? `${area} м²` : null;
  const roomText = rooms != null ? `${rooms}-комн.` : null;
  const floorText = floor != null ? `Этаж ${floor}` : null;
  const specs = [roomText, formattedArea, floorText].filter(Boolean).join(' • ');

  const repairStatus = has_repair === true ? 'С ремонтом' : has_repair === false ? 'Без ремонта' : null;
  const propertyDisplay = property_type ? PROPERTY_LABELS[property_type] || property_type : null;
  const livingDisplay = living_conditions
    ? living_conditions.map(c => LIVING_CONDITIONS_LABELS[c] || c).join(', ')
    : null;

  return (
    <a href={url} target="_blank" rel="noopener noreferrer" className="listing-card">
      <div className="listing-card-image">
        <img src={image_url ?? "https://via.placeholder.com/300x200?text=Недвижимость"} alt={title} />
      </div>
      <div className="listing-card-body">
        <h3 className="listing-card-title">{title}</h3>
        <div className="listing-card-price">{formattedPrice}</div>
        {specs && <div className="listing-card-specs">{specs}</div>}
        <div className="listing-card-meta">
          {creator_type && (
            <span className="badge">{creator_type === 'agency' ? 'Агентство' : 'Собственник'}</span>
          )}
          {propertyDisplay && <span className="badge">{propertyDisplay}</span>}
          {repairStatus && <span className="badge">{repairStatus}</span>}
          {build_year && <span className="badge">{build_year} г.</span>}
          {livingDisplay && <span className="badge">{livingDisplay}</span>}
        </div>
      </div>
    </a>
  );
};

export default ListingCard;