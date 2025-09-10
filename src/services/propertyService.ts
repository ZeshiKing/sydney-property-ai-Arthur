import { PropertySearchParams, PropertySearchResponse, StandardizedProperty } from '@/types';
import { logger } from '@/utils/logger';
import DatabaseService from './databaseService';
import CacheService from './cacheService';
import ScrapingQueueManager from '../queues/scrapingQueue';

/**
 * Property Service
 * 
 * Main business logic service that orchestrates property searches,
 * manages cache, database operations, and coordinates with scraping queue.
 */
export class PropertyService {
  constructor(
    private databaseService: DatabaseService,
    private cacheService: CacheService,
    private queueManager: ScrapingQueueManager
  ) {}

  /**
   * Search for properties with caching and async scraping
   */
  public async searchProperties(
    params: PropertySearchParams,
    userIp?: string
  ): Promise<PropertySearchResponse> {
    const searchId = this.generateSearchId();
    const startTime = Date.now();

    logger.info('Property search initiated', {
      searchId,
      params: this.sanitizeParams(params),
    });

    try {
      // First, check cache for existing results
      const cached = await this.cacheService.getCachedSearchResults(params);
      if (cached) {
        const executionTime = Date.now() - startTime;
        
        logger.info('Property search served from cache', {
          searchId,
          propertiesCount: cached.data.length,
          executionTime,
        });

        return this.buildSuccessResponse(
          cached.data,
          cached.pagination,
          params,
          searchId,
          executionTime,
          ['cache'],
          true
        );
      }

      // Check database for recent results
      const dbResults = await this.databaseService.searchProperties(
        params,
        ((params.page || 1) - 1) * (params.limit || 20),
        params.limit || 20
      );

      let properties = dbResults.properties;
      let totalProperties = dbResults.total;
      let sourcesScrapped = ['database'];

      // If no results or results are old, trigger async scraping
      const shouldScrape = this.shouldTriggerScraping(properties);
      
      if (shouldScrape) {
        // Add to scraping queue for fresh data
        const jobId = await this.queueManager.addSearchJob(params, 'normal');
        
        logger.info('Async scraping job queued', {
          searchId,
          jobId,
          reason: properties.length === 0 ? 'no_results' : 'stale_data',
        });

        sourcesScrapped.push('queue');
      }

      // If we have some results, return them while scraping happens in background
      if (properties.length > 0) {
        const pagination = this.buildPagination(params, totalProperties);
        const executionTime = Date.now() - startTime;

        // Save search record
        await this.databaseService.saveSearchRecord(
          searchId,
          params,
          properties.length,
          executionTime,
          sourcesScrapped,
          userIp
        );

        // Cache the results
        await this.cacheService.cacheSearchResults(
          params,
          properties,
          pagination
        );

        logger.info('Property search completed from database', {
          searchId,
          propertiesCount: properties.length,
          executionTime,
          asyncScrapingTriggered: shouldScrape,
        });

        return this.buildSuccessResponse(
          properties,
          pagination,
          params,
          searchId,
          executionTime,
          sourcesScrapped,
          false
        );
      }

      // No cached or database results, return empty response
      // (scraping job is already queued for future requests)
      const executionTime = Date.now() - startTime;
      
      await this.databaseService.saveSearchRecord(
        searchId,
        params,
        0,
        executionTime,
        sourcesScrapped,
        userIp
      );

      logger.info('Property search returned empty results', {
        searchId,
        executionTime,
        asyncScrapingTriggered: shouldScrape,
      });

      return this.buildSuccessResponse(
        [],
        this.buildPagination(params, 0),
        params,
        searchId,
        executionTime,
        sourcesScrapped,
        false
      );

    } catch (error) {
      const executionTime = Date.now() - startTime;
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';

      logger.error('Property search failed', {
        searchId,
        error: errorMessage,
        executionTime,
      });

      return {
        success: false,
        data: {
          properties: [],
          pagination: this.buildPagination(params, 0),
          filters: {
            applied: params,
            available: {
              suburbs: [],
              propertyTypes: [],
              priceRanges: [],
            },
          },
          metadata: {
            searchId,
            executionTime,
            sourcesScrapped: [],
            cacheHit: false,
          },
        },
        error: errorMessage,
      };
    }
  }

  /**
   * Get property by ID
   */
  public async getPropertyById(propertyId: string, source: string = 'domain'): Promise<StandardizedProperty | null> {
    try {
      logger.debug('Getting property by ID', { propertyId, source });

      // Check cache first
      const cached = await this.cacheService.getCachedProperty(propertyId);
      if (cached) {
        logger.debug('Property served from cache', { propertyId });
        return cached;
      }

      // Check database
      const property = await this.databaseService.getProperty(propertyId, source);
      
      if (property) {
        // Cache the property
        await this.cacheService.cacheProperty(propertyId, property);
        logger.debug('Property served from database and cached', { propertyId });
        return property;
      }

      logger.debug('Property not found', { propertyId, source });
      return null;
    } catch (error) {
      logger.error('Failed to get property by ID', { propertyId, source, error });
      return null;
    }
  }

  /**
   * Get available locations for search suggestions
   */
  public async getLocationSuggestions(query: string, limit: number = 10): Promise<any[]> {
    try {
      logger.debug('Getting location suggestions', { query, limit });

      // Check cache first
      const cached = await this.cacheService.getCachedLocationSuggestions(query);
      if (cached) {
        return cached.slice(0, limit);
      }

      // For now, return some mock data
      // In a real implementation, this would query a locations database or API
      const mockLocations = [
        { suburb: 'Camperdown', state: 'NSW', postcode: '2050' },
        { suburb: 'Camperdown', state: 'VIC', postcode: '3260' },
        { suburb: 'Campbelltown', state: 'NSW', postcode: '2560' },
        { suburb: 'Camden', state: 'NSW', postcode: '2570' },
        { suburb: 'Campbell', state: 'ACT', postcode: '2612' },
      ].filter(location => 
        location.suburb.toLowerCase().includes(query.toLowerCase())
      ).slice(0, limit);

      // Cache the results
      await this.cacheService.cacheLocationSuggestions(query, mockLocations);

      logger.debug('Location suggestions returned', { query, count: mockLocations.length });
      return mockLocations;
    } catch (error) {
      logger.error('Failed to get location suggestions', { query, error });
      return [];
    }
  }

  /**
   * Get search analytics
   */
  public async getSearchAnalytics(days: number = 7): Promise<any> {
    try {
      return await this.databaseService.getSearchAnalytics(days);
    } catch (error) {
      logger.error('Failed to get search analytics', { days, error });
      return [];
    }
  }

  /**
   * Health check for property service
   */
  public async healthCheck(): Promise<{ status: string; details?: any }> {
    try {
      const cacheHealth = await this.cacheService.healthCheck();
      const dbHealth = await this.databaseService.healthCheck();
      const queueStats = await this.queueManager.getQueueStats();

      const allHealthy = cacheHealth.status === 'healthy' && 
                        dbHealth.status === 'healthy';

      return {
        status: allHealthy ? 'healthy' : 'degraded',
        details: {
          cache: cacheHealth,
          database: dbHealth,
          queue: queueStats,
        },
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        details: {
          error: error instanceof Error ? error.message : 'Unknown error',
        },
      };
    }
  }

  /**
   * Private helper methods
   */
  
  private generateSearchId(): string {
    return `search_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private shouldTriggerScraping(properties: StandardizedProperty[]): boolean {
    // Trigger scraping if no results
    if (properties.length === 0) {
      return true;
    }

    // Check if results are stale (older than cache TTL)
    const cacheThreshold = Date.now() - (15 * 60 * 1000); // 15 minutes
    const hasStaleData = properties.some(property => {
      const scrapedAt = new Date(property.metadata.scrapedAt).getTime();
      return scrapedAt < cacheThreshold;
    });

    return hasStaleData;
  }

  private buildPagination(params: PropertySearchParams, totalProperties: number): any {
    const page = params.page || 1;
    const limit = params.limit || 20;
    const totalPages = Math.ceil(totalProperties / limit);

    return {
      currentPage: page,
      totalPages,
      totalProperties,
      hasNext: page < totalPages,
      hasPrevious: page > 1,
    };
  }

  private buildSuccessResponse(
    properties: StandardizedProperty[],
    pagination: any,
    params: PropertySearchParams,
    searchId: string,
    executionTime: number,
    sourcesScrapped: string[],
    cacheHit: boolean
  ): PropertySearchResponse {
    return {
      success: true,
      data: {
        properties,
        pagination,
        filters: {
          applied: params,
          available: {
            suburbs: this.extractUniqueSuburbs(properties),
            propertyTypes: this.extractUniquePropertyTypes(properties),
            priceRanges: this.generatePriceRanges(properties),
          },
        },
        metadata: {
          searchId,
          executionTime,
          sourcesScrapped,
          cacheHit,
        },
      },
    };
  }

  private extractUniqueSuburbs(properties: StandardizedProperty[]): string[] {
    const suburbs = new Set<string>();
    properties.forEach(property => {
      if (property.address.suburb) {
        suburbs.add(property.address.suburb);
      }
    });
    return Array.from(suburbs).sort();
  }

  private extractUniquePropertyTypes(properties: StandardizedProperty[]): string[] {
    const types = new Set<string>();
    properties.forEach(property => {
      if (property.propertyDetails.type) {
        types.add(property.propertyDetails.type);
      }
    });
    return Array.from(types).sort();
  }

  private generatePriceRanges(properties: StandardizedProperty[]): Array<{ min: number; max: number; count: number }> {
    const prices = properties
      .map(p => p.price.amount)
      .filter(price => price !== undefined) as number[];

    if (prices.length === 0) {
      return [];
    }

    // Create price ranges
    const ranges = [
      { min: 0, max: 300, count: 0 },
      { min: 300, max: 500, count: 0 },
      { min: 500, max: 750, count: 0 },
      { min: 750, max: 1000, count: 0 },
      { min: 1000, max: 1500, count: 0 },
      { min: 1500, max: 2000, count: 0 },
      { min: 2000, max: 999999, count: 0 },
    ];

    prices.forEach(price => {
      const range = ranges.find(r => price >= r.min && price < r.max);
      if (range) {
        range.count++;
      }
    });

    return ranges.filter(range => range.count > 0);
  }

  private sanitizeParams(params: PropertySearchParams): any {
    return {
      listingType: params.listingType,
      location: params.location,
      propertyType: params.propertyType,
      bedrooms: params.bedrooms,
      priceRange: params.priceRange,
      page: params.page,
      limit: params.limit,
      // Omit potentially sensitive information
    };
  }
}

export default PropertyService;