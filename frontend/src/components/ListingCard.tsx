import React from 'react';
import type { Listing } from '../types';

interface ListingCardProps {
  listing: Listing;
}

const ListingCard: React.FC<ListingCardProps> = ({ listing }) => {
  const {
    title,
    price,
    rooms,
    area,
    floor,
    url,
    data: { property_type, has_repair, build_year, creator_type, living_conditions },
  } = listing;

  const formattedPrice = price != null
    ? `${Math.round(price).toLocaleString('ru-RU')} ₽`
    : 'Цена не указана';

  const formattedArea = area != null ? `${area} м²` : null;
  const roomText = rooms != null ? `${rooms}-комн.` : null;
  const floorText = floor != null ? `Этаж ${floor}` : null;

  const specs = [roomText, formattedArea, floorText].filter(Boolean).join(' • ');

  const repairStatus = has_repair === true ? 'С ремонтом' : has_repair === false ? 'Без ремонта' : null;

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="listing-card"
    >
      <div className="listing-card-image">
        <img
          src="https://via.placeholder.com/300x200?text=Недвижимость"
          alt={title}
        />
      </div>
      <div className="listing-card-body">
        <h3 className="listing-card-title">{title}</h3>
        <div className="listing-card-price">{formattedPrice}</div>
        {specs && <div className="listing-card-specs">{specs}</div>}
        <div className="listing-card-meta">
          {creator_type && (
            <span className="badge">{creator_type === 'agency' ? 'Агентство' : 'Собственник'}</span>
          )}
          {property_type && <span className="badge">{property_type}</span>}
          {repairStatus && <span className="badge">{repairStatus}</span>}
          {build_year && <span className="badge">{build_year} г.</span>}
          {living_conditions.length > 0 && (
            <span className="badge">{living_conditions.join(', ')}</span>
          )}
        </div>
      </div>
    </a>
  );
};

export default ListingCard;