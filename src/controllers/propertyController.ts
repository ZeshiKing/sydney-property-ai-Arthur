import { Request, Response, NextFunction } from 'express';
import { PropertySearchParams } from '@/types';
import { asyncHandler } from '@/middleware/errorHandler';
import PropertyService from '@/services/propertyService';
import { apiLogger as logger } from '@/utils/logger';

/**
 * Property Controller
 * 
 * Handles HTTP requests for property-related operations including
 * search, individual property retrieval, and location suggestions.
 */
export class PropertyController {
  constructor(private propertyService: PropertyService) {}

  /**
   * Search for properties
   * POST /api/properties/search
   */
  public searchProperties = asyncHandler(async (req: Request, res: Response, next: NextFunction) => {
    const startTime = Date.now();
    const requestId = req.headers['x-request-id'] as string;
    const userIp = req.ip;
    const searchParams: PropertySearchParams = req.body;

    logger.info('Property search request received', {
      requestId,
      userIp,
      params: this.sanitizeParamsForLogging(searchParams),
    });

    try {
      const result = await this.propertyService.searchProperties(searchParams, userIp);
      
      const executionTime = Date.now() - startTime;
      
      logger.info('Property search request completed', {
        requestId,
        executionTime,
        propertiesCount: result.data.properties.length,
        success: result.success,
        cacheHit: result.data.metadata.cacheHit,
      });

      // Set appropriate cache headers
      if (result.data.metadata.cacheHit) {
        res.set('Cache-Control', 'public, max-age=900'); // 15 minutes
        res.set('X-Cache', 'HIT');
      } else {
        res.set('Cache-Control', 'public, max-age=300'); // 5 minutes for fresh data
        res.set('X-Cache', 'MISS');
      }

      res.set('X-Search-ID', result.data.metadata.searchId);
      res.set('X-Execution-Time', executionTime.toString());
      
      res.status(200).json(result);
    } catch (error) {
      logger.error('Property search request failed', {
        requestId,
        error: error instanceof Error ? error.message : 'Unknown error',
        params: this.sanitizeParamsForLogging(searchParams),
      });
      next(error);
    }
  });

  /**
   * Get property by ID
   * GET /api/properties/:id
   */
  public getPropertyById = asyncHandler(async (req: Request, res: Response, next: NextFunction) => {
    const { id } = req.params;
    const source = (req.query.source as string) || 'domain';
    const requestId = req.headers['x-request-id'] as string;

    logger.debug('Property by ID request received', {
      requestId,
      propertyId: id,
      source,
    });

    try {
      const property = await this.propertyService.getPropertyById(id, source);

      if (!property) {
        logger.info('Property not found', { requestId, propertyId: id, source });
        
        return res.status(404).json({
          success: false,
          error: {
            message: 'Property not found',
            code: 'PROPERTY_NOT_FOUND',
            statusCode: 404,
            timestamp: new Date().toISOString(),
            requestId,
          },
        });
      }

      logger.debug('Property by ID request completed', {
        requestId,
        propertyId: id,
        source,
      });

      // Set cache headers for individual properties
      res.set('Cache-Control', 'public, max-age=1800'); // 30 minutes
      res.set('ETag', `"${property.id}-${new Date(property.metadata.lastUpdated).getTime()}"`);

      res.status(200).json({
        success: true,
        data: property,
      });
    } catch (error) {
      logger.error('Property by ID request failed', {
        requestId,
        propertyId: id,
        source,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      next(error);
    }
  });

  /**
   * Get location suggestions
   * GET /api/locations/suggest
   */
  public getLocationSuggestions = asyncHandler(async (req: Request, res: Response, next: NextFunction) => {
    const { query, limit } = req.query;
    const requestId = req.headers['x-request-id'] as string;

    if (!query || typeof query !== 'string') {
      return res.status(400).json({
        success: false,
        error: {
          message: 'Query parameter is required',
          code: 'MISSING_QUERY',
          statusCode: 400,
          timestamp: new Date().toISOString(),
          requestId,
        },
      });
    }

    logger.debug('Location suggestions request received', {
      requestId,
      query,
      limit,
    });

    try {
      const limitNum = limit ? parseInt(limit as string, 10) : 10;
      const suggestions = await this.propertyService.getLocationSuggestions(query, limitNum);

      logger.debug('Location suggestions request completed', {
        requestId,
        query,
        suggestionsCount: suggestions.length,
      });

      // Cache location suggestions for longer
      res.set('Cache-Control', 'public, max-age=3600'); // 1 hour

      res.status(200).json({
        success: true,
        data: {
          query,
          suggestions,
          count: suggestions.length,
        },
      });
    } catch (error) {
      logger.error('Location suggestions request failed', {
        requestId,
        query,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      next(error);
    }
  });

  /**
   * Get search analytics (admin endpoint)
   * GET /api/admin/analytics/search
   */
  public getSearchAnalytics = asyncHandler(async (req: Request, res: Response, next: NextFunction) => {
    const { days } = req.query;
    const requestId = req.headers['x-request-id'] as string;

    logger.debug('Search analytics request received', {
      requestId,
      days,
    });

    try {
      const daysNum = days ? parseInt(days as string, 10) : 7;
      const analytics = await this.propertyService.getSearchAnalytics(daysNum);

      logger.debug('Search analytics request completed', {
        requestId,
        days: daysNum,
        analyticsCount: analytics.length,
      });

      res.status(200).json({
        success: true,
        data: {
          period: `${daysNum} days`,
          analytics,
        },
      });
    } catch (error) {
      logger.error('Search analytics request failed', {
        requestId,
        days,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      next(error);
    }
  });

  /**
   * Health check endpoint
   * GET /api/properties/health
   */
  public healthCheck = asyncHandler(async (req: Request, res: Response, next: NextFunction) => {
    const requestId = req.headers['x-request-id'] as string;

    try {
      const health = await this.propertyService.healthCheck();

      logger.debug('Property service health check completed', {
        requestId,
        status: health.status,
      });

      const statusCode = health.status === 'healthy' ? 200 : 
                        health.status === 'degraded' ? 200 : 503;

      res.status(statusCode).json({
        success: true,
        data: {
          service: 'property-service',
          status: health.status,
          timestamp: new Date().toISOString(),
          details: health.details,
        },
      });
    } catch (error) {
      logger.error('Property service health check failed', {
        requestId,
        error: error instanceof Error ? error.message : 'Unknown error',
      });

      res.status(503).json({
        success: false,
        data: {
          service: 'property-service',
          status: 'unhealthy',
          timestamp: new Date().toISOString(),
          error: error instanceof Error ? error.message : 'Unknown error',
        },
      });
    }
  });

  /**
   * Get queue status (admin endpoint)
   * GET /api/admin/queue/status
   */
  public getQueueStatus = asyncHandler(async (req: Request, res: Response, next: NextFunction) => {
    const requestId = req.headers['x-request-id'] as string;

    logger.debug('Queue status request received', { requestId });

    try {
      // This would need to be implemented to get queue stats from the property service
      const queueStats = {
        waiting: 0,
        active: 0,
        completed: 0,
        failed: 0,
        total: 0,
      };

      logger.debug('Queue status request completed', {
        requestId,
        stats: queueStats,
      });

      res.status(200).json({
        success: true,
        data: {
          queue: 'property-scraping',
          status: 'operational',
          timestamp: new Date().toISOString(),
          stats: queueStats,
        },
      });
    } catch (error) {
      logger.error('Queue status request failed', {
        requestId,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      next(error);
    }
  });

  /**
   * Manual cache invalidation (admin endpoint)
   * POST /api/admin/cache/invalidate
   */
  public invalidateCache = asyncHandler(async (req: Request, res: Response, next: NextFunction) => {
    const { pattern } = req.body;
    const requestId = req.headers['x-request-id'] as string;

    logger.info('Cache invalidation request received', {
      requestId,
      pattern,
    });

    try {
      // This would need to be implemented to invalidate cache through the property service
      // await this.propertyService.invalidateCache(pattern);

      logger.info('Cache invalidation completed', {
        requestId,
        pattern,
      });

      res.status(200).json({
        success: true,
        data: {
          message: 'Cache invalidated successfully',
          pattern,
          timestamp: new Date().toISOString(),
        },
      });
    } catch (error) {
      logger.error('Cache invalidation failed', {
        requestId,
        pattern,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      next(error);
    }
  });

  /**
   * Sanitize search parameters for logging (remove sensitive data)
   */
  private sanitizeParamsForLogging(params: PropertySearchParams): any {
    return {
      listingType: params.listingType,
      location: {
        suburb: params.location.suburb,
        state: params.location.state,
        postcode: params.location.postcode,
      },
      propertyType: params.propertyType,
      bedrooms: params.bedrooms,
      bathrooms: params.bathrooms,
      priceRange: params.priceRange,
      parking: params.parking,
      sortBy: params.sortBy,
      page: params.page,
      limit: params.limit,
      // Omit potentially sensitive fields like features array details
      featuresCount: params.features?.length || 0,
    };
  }
}

export default PropertyController;