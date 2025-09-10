import { DomainUrlBuilder } from '@/services/domainUrlBuilder';
import { PropertySearchParams } from '@/types';

describe('DomainUrlBuilder', () => {
  let urlBuilder: DomainUrlBuilder;

  beforeEach(() => {
    urlBuilder = new DomainUrlBuilder();
  });

  describe('buildSearchUrl', () => {
    it('should build basic rental URL', () => {
      const params: PropertySearchParams = {
        listingType: 'rent',
        location: {
          suburb: 'Camperdown',
          state: 'NSW',
          postcode: '2050',
        },
      };

      const url = urlBuilder.buildSearchUrl(params);
      expect(url).toBe('https://www.domain.com.au/rent/camperdown-nsw-2050/');
    });

    it('should build URL with property type', () => {
      const params: PropertySearchParams = {
        listingType: 'rent',
        location: {
          suburb: 'Camperdown',
          state: 'NSW',
          postcode: '2050',
        },
        propertyType: 'apartment',
      };

      const url = urlBuilder.buildSearchUrl(params);
      expect(url).toBe('https://www.domain.com.au/rent/camperdown-nsw-2050/apartment/');
    });

    it('should build URL with bedroom filters', () => {
      const params: PropertySearchParams = {
        listingType: 'rent',
        location: {
          suburb: 'Camperdown',
          state: 'NSW',
          postcode: '2050',
        },
        bedrooms: {
          min: 2,
          max: 3,
        },
      };

      const url = urlBuilder.buildSearchUrl(params);
      expect(url).toBe('https://www.domain.com.au/rent/camperdown-nsw-2050/?bedrooms=2-3');
    });

    it('should build URL with multiple filters', () => {
      const params: PropertySearchParams = {
        listingType: 'rent',
        location: {
          suburb: 'Camperdown',
          state: 'NSW',
          postcode: '2050',
        },
        propertyType: 'apartment',
        bedrooms: {
          min: 2,
        },
        priceRange: {
          min: 400,
          max: 800,
        },
        sortBy: 'price-asc',
      };

      const url = urlBuilder.buildSearchUrl(params);
      expect(url).toContain('https://www.domain.com.au/rent/camperdown-nsw-2050/apartment/');
      expect(url).toContain('bedrooms=2-any');
      expect(url).toContain('price=400-800');
      expect(url).toContain('sort=price-asc');
    });

    it('should handle suburbs with spaces and special characters', () => {
      const params: PropertySearchParams = {
        listingType: 'rent',
        location: {
          suburb: 'St Kilda East',
          state: 'VIC',
          postcode: '3183',
        },
      };

      const url = urlBuilder.buildSearchUrl(params);
      expect(url).toBe('https://www.domain.com.au/rent/st-kilda-east-vic-3183/');
    });
  });

  describe('buildMultipleSearchUrls', () => {
    it('should return single URL when property type is specified', () => {
      const params: PropertySearchParams = {
        listingType: 'rent',
        location: {
          suburb: 'Camperdown',
          state: 'NSW',
          postcode: '2050',
        },
        propertyType: 'apartment',
      };

      const urls = urlBuilder.buildMultipleSearchUrls(params);
      expect(urls).toHaveLength(1);
      expect(urls[0]).toContain('/apartment/');
    });

    it('should return multiple URLs when property type is not specified', () => {
      const params: PropertySearchParams = {
        listingType: 'rent',
        location: {
          suburb: 'Camperdown',
          state: 'NSW',
          postcode: '2050',
        },
      };

      const urls = urlBuilder.buildMultipleSearchUrls(params);
      expect(urls.length).toBeGreaterThan(1);
      expect(urls.some(url => url.includes('/apartment/'))).toBe(true);
      expect(urls.some(url => url.includes('/house/'))).toBe(true);
      expect(urls.some(url => url.includes('/townhouse/'))).toBe(true);
    });
  });

  describe('parseSearchUrl', () => {
    it('should parse basic rental URL', () => {
      const url = 'https://www.domain.com.au/rent/camperdown-nsw-2050/';
      const params = urlBuilder.parseSearchUrl(url);

      expect(params).toEqual({
        listingType: 'rent',
        location: {
          suburb: 'Camperdown',
          state: 'NSW',
          postcode: '2050',
        },
      });
    });

    it('should parse URL with property type and filters', () => {
      const url = 'https://www.domain.com.au/rent/camperdown-nsw-2050/apartment/?bedrooms=2-any&price=400-800';
      const params = urlBuilder.parseSearchUrl(url);

      expect(params?.listingType).toBe('rent');
      expect(params?.location?.suburb).toBe('Camperdown');
      expect(params?.propertyType).toBe('apartment');
      expect(params?.bedrooms?.min).toBe(2);
      expect(params?.priceRange?.min).toBe(400);
      expect(params?.priceRange?.max).toBe(800);
    });

    it('should return null for invalid URLs', () => {
      const invalidUrls = [
        'https://example.com/invalid',
        'https://www.domain.com.au/invalid-path',
        'not-a-url',
      ];

      invalidUrls.forEach(url => {
        const params = urlBuilder.parseSearchUrl(url);
        expect(params).toBeNull();
      });
    });
  });

  describe('error handling', () => {
    it('should throw error for invalid location data', () => {
      const params = {
        listingType: 'rent' as const,
        location: {
          suburb: '',
          state: 'NSW',
          postcode: '2050',
        },
      };

      expect(() => urlBuilder.buildSearchUrl(params)).toThrow();
    });
  });
});