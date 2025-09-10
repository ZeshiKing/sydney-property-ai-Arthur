import { createClient, RedisClientType } from 'redis';
import { config } from '@/config';
import { CacheKey, CachedSearchResult, PropertySearchParams } from '@/types';
import { cacheLogger as logger } from '@/utils/logger';

/**
 * Redis Cache Service
 * 
 * Handles caching of search results, property data, and other 
 * frequently accessed information to improve performance.
 */
export class CacheService {
  private client: RedisClientType;
  private isConnected = false;

  constructor() {
    this.client = createClient({
      url: config.redis.url,
      password: config.redis.password,
    });

    this.setupEventHandlers();
  }

  /**
   * Initialize the Redis connection
   */
  public async connect(): Promise<void> {
    try {
      await this.client.connect();
      this.isConnected = true;
      logger.info('Redis cache service connected successfully');
    } catch (error) {
      logger.error('Failed to connect to Redis cache service', { error });
      throw error;
    }
  }

  /**
   * Close the Redis connection
   */
  public async disconnect(): Promise<void> {
    try {
      if (this.isConnected) {
        await this.client.quit();
        this.isConnected = false;
        logger.info('Redis cache service disconnected');
      }
    } catch (error) {
      logger.error('Error disconnecting from Redis', { error });
    }
  }

  /**
   * Cache search results
   */
  public async cacheSearchResults(
    params: PropertySearchParams,
    results: any[],
    pagination: any,
    ttl?: number
  ): Promise<void> {
    if (!this.isConnected) {
      logger.warn('Cache service not connected, skipping cache operation');
      return;
    }

    try {
      const key = this.generateSearchCacheKey(params);
      const cacheData: CachedSearchResult = {
        data: results,
        pagination,
        timestamp: Date.now(),
        ttl: ttl || config.cache.ttl,
      };

      await this.client.setEx(
        key,
        ttl || config.cache.ttl,
        JSON.stringify(cacheData)
      );

      logger.debug('Search results cached', {
        key,
        resultsCount: results.length,
        ttl: ttl || config.cache.ttl,
      });
    } catch (error) {
      logger.error('Failed to cache search results', { params, error });
    }
  }

  /**
   * Get cached search results
   */
  public async getCachedSearchResults(
    params: PropertySearchParams
  ): Promise<CachedSearchResult | null> {
    if (!this.isConnected) {
      return null;
    }

    try {
      const key = this.generateSearchCacheKey(params);
      const cached = await this.client.get(key);

      if (!cached) {
        logger.debug('Cache miss for search', { key });
        return null;
      }

      const cacheData: CachedSearchResult = JSON.parse(cached);
      
      // Check if cache has expired (additional validation)
      const now = Date.now();
      if (now - cacheData.timestamp > cacheData.ttl * 1000) {
        logger.debug('Cache expired for search', { key });
        await this.client.del(key); // Clean up expired cache
        return null;
      }

      logger.debug('Cache hit for search', {
        key,
        resultsCount: cacheData.data.length,
        age: now - cacheData.timestamp,
      });

      return cacheData;
    } catch (error) {
      logger.error('Failed to get cached search results', { params, error });
      return null;
    }
  }

  /**
   * Cache individual property data
   */
  public async cacheProperty(propertyId: string, propertyData: any, ttl?: number): Promise<void> {
    if (!this.isConnected) return;

    try {
      const key = this.generatePropertyCacheKey(propertyId);
      
      await this.client.setEx(
        key,
        ttl || config.cache.ttl,
        JSON.stringify({
          data: propertyData,
          timestamp: Date.now(),
        })
      );

      logger.debug('Property cached', { propertyId, key });
    } catch (error) {
      logger.error('Failed to cache property', { propertyId, error });
    }
  }

  /**
   * Get cached property data
   */
  public async getCachedProperty(propertyId: string): Promise<any | null> {
    if (!this.isConnected) return null;

    try {
      const key = this.generatePropertyCacheKey(propertyId);
      const cached = await this.client.get(key);

      if (!cached) {
        logger.debug('Cache miss for property', { propertyId, key });
        return null;
      }

      const cacheData = JSON.parse(cached);
      logger.debug('Cache hit for property', { propertyId, key });

      return cacheData.data;
    } catch (error) {
      logger.error('Failed to get cached property', { propertyId, error });
      return null;
    }
  }

  /**
   * Cache location suggestions
   */
  public async cacheLocationSuggestions(
    query: string,
    suggestions: any[],
    ttl?: number
  ): Promise<void> {
    if (!this.isConnected) return;

    try {
      const key = this.generateLocationCacheKey(query);
      
      await this.client.setEx(
        key,
        ttl || config.cache.ttl * 24, // Locations change less frequently
        JSON.stringify({
          data: suggestions,
          timestamp: Date.now(),
        })
      );

      logger.debug('Location suggestions cached', { query, key, count: suggestions.length });
    } catch (error) {
      logger.error('Failed to cache location suggestions', { query, error });
    }
  }

  /**
   * Get cached location suggestions
   */
  public async getCachedLocationSuggestions(query: string): Promise<any[] | null> {
    if (!this.isConnected) return null;

    try {
      const key = this.generateLocationCacheKey(query);
      const cached = await this.client.get(key);

      if (!cached) {
        logger.debug('Cache miss for location suggestions', { query, key });
        return null;
      }

      const cacheData = JSON.parse(cached);
      logger.debug('Cache hit for location suggestions', { query, key });

      return cacheData.data;
    } catch (error) {
      logger.error('Failed to get cached location suggestions', { query, error });
      return null;
    }
  }

  /**
   * Invalidate cache by pattern
   */
  public async invalidatePattern(pattern: string): Promise<void> {
    if (!this.isConnected) return;

    try {
      const keys = await this.client.keys(`${config.cache.prefix}${pattern}`);
      
      if (keys.length > 0) {
        await this.client.del(keys);
        logger.info('Cache invalidated by pattern', { pattern, keysDeleted: keys.length });
      }
    } catch (error) {
      logger.error('Failed to invalidate cache by pattern', { pattern, error });
    }
  }

  /**
   * Clear all cache
   */
  public async clearAll(): Promise<void> {
    if (!this.isConnected) return;

    try {
      const keys = await this.client.keys(`${config.cache.prefix}*`);
      
      if (keys.length > 0) {
        await this.client.del(keys);
        logger.info('All cache cleared', { keysDeleted: keys.length });
      }
    } catch (error) {
      logger.error('Failed to clear all cache', { error });
    }
  }

  /**
   * Get cache statistics
   */
  public async getStats(): Promise<any> {
    if (!this.isConnected) return null;

    try {
      const info = await this.client.info('memory');
      const keys = await this.client.keys(`${config.cache.prefix}*`);
      
      return {
        isConnected: this.isConnected,
        totalKeys: keys.length,
        memoryInfo: this.parseRedisInfo(info),
        prefix: config.cache.prefix,
      };
    } catch (error) {
      logger.error('Failed to get cache stats', { error });
      return null;
    }
  }

  /**
   * Set up Redis event handlers
   */
  private setupEventHandlers(): void {
    this.client.on('error', (error) => {
      logger.error('Redis client error', { error });
      this.isConnected = false;
    });

    this.client.on('connect', () => {
      logger.info('Redis client connected');
    });

    this.client.on('reconnecting', () => {
      logger.warn('Redis client reconnecting');
    });

    this.client.on('end', () => {
      logger.info('Redis client connection ended');
      this.isConnected = false;
    });
  }

  /**
   * Generate cache key for search results
   */
  private generateSearchCacheKey(params: PropertySearchParams): string {
    // Create a deterministic hash of search parameters
    const keyData = {
      listingType: params.listingType,
      location: params.location,
      propertyType: params.propertyType,
      bedrooms: params.bedrooms,
      bathrooms: params.bathrooms,
      priceRange: params.priceRange,
      parking: params.parking,
      sortBy: params.sortBy,
      page: params.page || 1,
      limit: params.limit || 20,
    };

    const keyString = JSON.stringify(keyData);
    const hash = this.generateHash(keyString);
    
    return `${config.cache.prefix}search:${hash}`;
  }

  /**
   * Generate cache key for individual property
   */
  private generatePropertyCacheKey(propertyId: string): string {
    return `${config.cache.prefix}property:${propertyId}`;
  }

  /**
   * Generate cache key for location suggestions
   */
  private generateLocationCacheKey(query: string): string {
    const normalizedQuery = query.toLowerCase().trim().replace(/\s+/g, '_');
    return `${config.cache.prefix}location:${normalizedQuery}`;
  }

  /**
   * Generate a simple hash for cache keys
   */
  private generateHash(input: string): string {
    let hash = 0;
    for (let i = 0; i < input.length; i++) {
      const char = input.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36);
  }

  /**
   * Parse Redis INFO response
   */
  private parseRedisInfo(info: string): any {
    const lines = info.split('\r\n');
    const result: any = {};
    
    for (const line of lines) {
      if (line.includes(':')) {
        const [key, value] = line.split(':');
        result[key] = value;
      }
    }
    
    return result;
  }

  /**
   * Health check for cache service
   */
  public async healthCheck(): Promise<{ status: string; details?: any }> {
    try {
      if (!this.isConnected) {
        return { status: 'disconnected' };
      }

      const pingResult = await this.client.ping();
      
      if (pingResult === 'PONG') {
        const stats = await this.getStats();
        return {
          status: 'healthy',
          details: {
            ping: pingResult,
            totalKeys: stats?.totalKeys || 0,
            memoryUsed: stats?.memoryInfo?.used_memory || 'unknown',
          },
        };
      } else {
        return { status: 'unhealthy', details: { ping: pingResult } };
      }
    } catch (error) {
      return {
        status: 'error',
        details: { error: error instanceof Error ? error.message : 'Unknown error' },
      };
    }
  }
}

export default CacheService;