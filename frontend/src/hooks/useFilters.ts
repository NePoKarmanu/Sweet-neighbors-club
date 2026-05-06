import { useState, useCallback } from 'react';
import type { ListingSearchDTO } from '../types';

export type FilterState = {
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
};

const initialFilterState: FilterState = {
  roomsMin: '', roomsMax: '',
  priceMin: '', priceMax: '',
  areaMin: '', areaMax: '',
  floorMin: '', floorMax: '',
  buildYearMin: '', buildYearMax: '',
  selectedPropertyTypes: [],
  selectedCreatorTypes: [],
  hasRepair: undefined,
  selectedLivingConditions: [],
};

export function useFilters() {
  const [filters, setFilters] = useState<FilterState>(initialFilterState);

  const updateFilter = useCallback((key: keyof FilterState, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(initialFilterState);
  }, []);

  const buildSearchDTO = useCallback((): ListingSearchDTO => {
    const result: ListingSearchDTO = {};

    if (filters.roomsMin || filters.roomsMax) {
      result.rooms = {
        min: filters.roomsMin ? parseInt(filters.roomsMin) : undefined,
        max: filters.roomsMax ? parseInt(filters.roomsMax) : undefined,
      };
    }
    if (filters.priceMin || filters.priceMax) {
      result.price = {
        min: filters.priceMin ? parseFloat(filters.priceMin) : undefined,
        max: filters.priceMax ? parseFloat(filters.priceMax) : undefined,
      };
    }
    if (filters.areaMin || filters.areaMax) {
      result.area = {
        min: filters.areaMin ? parseFloat(filters.areaMin) : undefined,
        max: filters.areaMax ? parseFloat(filters.areaMax) : undefined,
      };
    }
    if (filters.floorMin || filters.floorMax) {
      result.floor = {
        min: filters.floorMin ? parseInt(filters.floorMin) : undefined,
        max: filters.floorMax ? parseInt(filters.floorMax) : undefined,
      };
    }
    if (filters.buildYearMin || filters.buildYearMax) {
      result.build_year = {
        min: filters.buildYearMin ? parseInt(filters.buildYearMin) : undefined,
        max: filters.buildYearMax ? parseInt(filters.buildYearMax) : undefined,
      };
    }

    if (filters.selectedPropertyTypes.length > 0) {
      result.property_types = filters.selectedPropertyTypes;
    }
    if (filters.selectedCreatorTypes.length > 0) {
      result.creator_types = filters.selectedCreatorTypes as ('agency' | 'owner')[];
    }
    if (filters.selectedLivingConditions.length > 0) {
      result.living_conditions = filters.selectedLivingConditions;
    }

    if (filters.hasRepair !== undefined) {
      result.has_repair = filters.hasRepair;
    }

    return result;
  }, [filters]);

  const toggleArrayFilter = useCallback(
    (value: string, arrayKey: 'selectedPropertyTypes' | 'selectedCreatorTypes' | 'selectedLivingConditions') => {
      setFilters(prev => {
        const current = prev[arrayKey];
        const updated = current.includes(value)
          ? current.filter(v => v !== value)
          : [...current, value];
        return { ...prev, [arrayKey]: updated };
      });
    },
    []
  );

  return {
    filters,
    updateFilter,
    resetFilters,
    buildSearchDTO,
    toggleArrayFilter,
  };
}