import { PropertySearchParams } from '@/types';
import { logger } from '@/utils/logger';

/**
 * Domain.com.au URL Builder Service
 * 
 * Constructs search URLs for Domain.com.au based on user search parameters.
 * Handles property type mapping, location formatting, and filter parameters.
 */
export class DomainUrlBuilder {
  private readonly baseUrl = 'https://www.domain.com.au';
  
  /**
   * Map generic property types to Domain.com.au specific types
   */
  private readonly propertyTypeMap: Record<string, string> = {
    'apartment': 'apartment',
    'house': 'house',
    'townhouse': 'townhouse',
    'unit': 'apartment',
    'villa': 'house',
  };

  /**
   * Map sort options to Domain.com.au sort parameters
   */
  private readonly sortMap: Record<string, string> = {
    'price-asc': 'price-asc',
    'price-desc': 'price-desc',
    'date-desc': 'latest',
    'date-asc': 'oldest',
  };

  /**
   * Build a Domain.com.au search URL from search parameters
   */
  public buildSearchUrl(params: PropertySearchParams): string {
    try {
      const { listingType, location, propertyType } = params;
      
      // Build base path: /{listingType}/{suburb-state-postcode}/{propertyType}/
      const locationSlug = this.buildLocationSlug(location);
      const propertyTypeSlug = propertyType ? this.mapPropertyType(propertyType) : '';
      
      let path = `/${listingType}/${locationSlug}`;
      if (propertyTypeSlug) {
        path += `/${propertyTypeSlug}`;
      }
      path += '/';
      
      // Build query parameters
      const queryParams = this.buildQueryParams(params);
      const queryString = queryParams.length > 0 ? `?${queryParams.join('&')}` : '';
      
      const fullUrl = `${this.baseUrl}${path}${queryString}`;
      
      logger.debug('Built Domain URL', {
        params: this.sanitizeParams(params),
        url: fullUrl,
      });
      
      return fullUrl;
    } catch (error) {
      logger.error('Failed to build Domain URL', { params, error });
      throw new Error(`Failed to build Domain URL: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Build multiple URLs for different property types (when type is not specified)
   */
  public buildMultipleSearchUrls(params: PropertySearchParams): string[] {
    if (params.propertyType) {
      return [this.buildSearchUrl(params)];
    }

    const propertyTypes: Array<PropertySearchParams['propertyType']> = [
      'apartment',
      'house',
      'townhouse',
    ];

    return propertyTypes.map(type => 
      this.buildSearchUrl({ ...params, propertyType: type })
    );
  }

  /**
   * Extract search parameters from a Domain URL (reverse engineering)
   */
  public parseSearchUrl(url: string): Partial<PropertySearchParams> | null {
    try {
      const urlObj = new URL(url);
      const pathParts = urlObj.pathname.split('/').filter(Boolean);
      
      if (pathParts.length < 2) {
        return null;
      }

      const [listingType, locationPart, propertyTypePart] = pathParts;
      
      if (!['rent', 'buy'].includes(listingType)) {
        return null;
      }

      const location = this.parseLocationSlug(locationPart);
      if (!location) {
        return null;
      }

      const params: Partial<PropertySearchParams> = {
        listingType: listingType as 'rent' | 'buy',
        location,
      };

      // Parse property type if present
      if (propertyTypePart && this.isValidPropertyType(propertyTypePart)) {
        params.propertyType = this.reverseMapPropertyType(propertyTypePart);
      }

      // Parse query parameters
      const queryParams = Object.fromEntries(urlObj.searchParams.entries());
      this.parseQueryParams(queryParams, params);

      return params;
    } catch (error) {
      logger.warn('Failed to parse Domain URL', { url, error });
      return null;
    }
  }

  /**
   * Build location slug from location object
   * Format: suburb-state-postcode (e.g., camperdown-nsw-2050)
   */
  private buildLocationSlug(location: PropertySearchParams['location']): string {
    const { suburb, state, postcode } = location;
    return `${this.slugify(suburb)}-${state.toLowerCase()}-${postcode}`;
  }

  /**
   * Parse location slug back to location object
   */
  private parseLocationSlug(locationSlug: string): PropertySearchParams['location'] | null {
    const parts = locationSlug.split('-');
    
    if (parts.length < 3) {
      return null;
    }

    const postcode = parts.pop()!;
    const state = parts.pop()!.toUpperCase();
    const suburb = parts.join('-');

    // Validate state
    const validStates = ['NSW', 'VIC', 'QLD', 'WA', 'SA', 'TAS', 'ACT', 'NT'];
    if (!validStates.includes(state)) {
      return null;
    }

    // Validate postcode
    if (!/^\d{4}$/.test(postcode)) {
      return null;
    }

    return {
      suburb: this.unslugify(suburb),
      state: state as PropertySearchParams['location']['state'],
      postcode,
    };
  }

  /**
   * Map generic property type to Domain.com.au property type
   */
  private mapPropertyType(propertyType: string): string {
    return this.propertyTypeMap[propertyType] || propertyType;
  }

  /**
   * Reverse map Domain property type to generic type
   */
  private reverseMapPropertyType(domainType: string): PropertySearchParams['propertyType'] {
    const reverseMap = Object.fromEntries(
      Object.entries(this.propertyTypeMap).map(([k, v]) => [v, k])
    );
    return reverseMap[domainType] as PropertySearchParams['propertyType'] || domainType as any;
  }

  /**
   * Check if property type is valid for Domain
   */
  private isValidPropertyType(propertyType: string): boolean {
    const validTypes = Object.values(this.propertyTypeMap);
    return validTypes.includes(propertyType);
  }

  /**
   * Build query parameters array
   */
  private buildQueryParams(params: PropertySearchParams): string[] {
    const queryParams: string[] = [];

    // Bedrooms
    if (params.bedrooms) {
      const { min, max } = params.bedrooms;
      if (min !== undefined && max !== undefined) {
        queryParams.push(`bedrooms=${min}-${max}`);
      } else if (min !== undefined) {
        queryParams.push(`bedrooms=${min}-any`);
      } else if (max !== undefined) {
        queryParams.push(`bedrooms=0-${max}`);
      }
    }

    // Bathrooms
    if (params.bathrooms) {
      const { min, max } = params.bathrooms;
      if (min !== undefined && max !== undefined) {
        queryParams.push(`bathrooms=${min}-${max}`);
      } else if (min !== undefined) {
        queryParams.push(`bathrooms=${min}-any`);
      }
    }

    // Price range
    if (params.priceRange) {
      const { min, max } = params.priceRange;
      if (min !== undefined && max !== undefined) {
        queryParams.push(`price=${min}-${max}`);
      } else if (min !== undefined) {
        queryParams.push(`price=${min}-any`);
      } else if (max !== undefined) {
        queryParams.push(`price=0-${max}`);
      }
    }

    // Parking
    if (params.parking?.min !== undefined) {
      queryParams.push(`parking=${params.parking.min}`);
    }

    // Sort
    if (params.sortBy) {
      const sortParam = this.sortMap[params.sortBy];
      if (sortParam) {
        queryParams.push(`sort=${sortParam}`);
      }
    }

    // Pagination
    if (params.page && params.page > 1) {
      queryParams.push(`page=${params.page}`);
    }

    // Features (if supported by Domain)
    if (params.features && params.features.length > 0) {
      params.features.forEach(feature => {
        queryParams.push(`features=${encodeURIComponent(feature)}`);
      });
    }

    return queryParams;
  }

  /**
   * Parse query parameters into search params
   */
  private parseQueryParams(
    queryParams: Record<string, string>, 
    params: Partial<PropertySearchParams>
  ): void {
    // Parse bedrooms
    if (queryParams.bedrooms) {
      const bedroomMatch = queryParams.bedrooms.match(/^(\d+)-(\d+|any)$/);
      if (bedroomMatch) {
        params.bedrooms = {
          min: parseInt(bedroomMatch[1]),
          max: bedroomMatch[2] === 'any' ? undefined : parseInt(bedroomMatch[2]),
        };
      }
    }

    // Parse bathrooms
    if (queryParams.bathrooms) {
      const bathroomMatch = queryParams.bathrooms.match(/^(\d+)-(\d+|any)$/);
      if (bathroomMatch) {
        params.bathrooms = {
          min: parseInt(bathroomMatch[1]),
          max: bathroomMatch[2] === 'any' ? undefined : parseInt(bathroomMatch[2]),
        };
      }
    }

    // Parse price
    if (queryParams.price) {
      const priceMatch = queryParams.price.match(/^(\d+)-(\d+|any)$/);
      if (priceMatch) {
        params.priceRange = {
          min: parseInt(priceMatch[1]),
          max: priceMatch[2] === 'any' ? undefined : parseInt(priceMatch[2]),
        };
      }
    }

    // Parse parking
    if (queryParams.parking) {
      const parking = parseInt(queryParams.parking);
      if (!isNaN(parking)) {
        params.parking = { min: parking };
      }
    }

    // Parse sort
    if (queryParams.sort) {
      const reverseSort = Object.fromEntries(
        Object.entries(this.sortMap).map(([k, v]) => [v, k])
      );
      params.sortBy = reverseSort[queryParams.sort] as PropertySearchParams['sortBy'];
    }

    // Parse page
    if (queryParams.page) {
      const page = parseInt(queryParams.page);
      if (!isNaN(page) && page > 0) {
        params.page = page;
      }
    }
  }

  /**
   * Convert string to URL-friendly slug
   */
  private slugify(text: string): string {
    return text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  /**
   * Convert slug back to readable text
   */
  private unslugify(slug: string): string {
    return slug
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  /**
   * Remove sensitive information from params for logging
   */
  private sanitizeParams(params: PropertySearchParams): any {
    return {
      ...params,
      // Add any sensitive field sanitization here if needed
    };
  }
}