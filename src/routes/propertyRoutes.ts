import { Router } from 'express';
import PropertyController from '@/controllers/propertyController';
import { 
  validatePropertySearch, 
  validatePropertyId, 
  validateLocationSearch,
  validatePagination 
} from '@/middleware/validation';
import { searchRateLimit, intensiveRateLimit, staticRateLimit } from '@/middleware/rateLimit';

/**
 * Property Routes
 * 
 * Defines all property-related API endpoints with appropriate
 * validation, rate limiting, and middleware.
 */
export function createPropertyRoutes(propertyController: PropertyController): Router {
  const router = Router();

  // Search properties
  router.post('/search', 
    searchRateLimit,
    validatePropertySearch,
    propertyController.searchProperties
  );

  // Get property by ID
  router.get('/:id',
    staticRateLimit,
    validatePropertyId,
    propertyController.getPropertyById
  );

  // Health check
  router.get('/health',
    staticRateLimit,
    propertyController.healthCheck
  );

  return router;
}

/**
 * Location Routes
 * 
 * Location-related endpoints for suggestions and autocomplete.
 */
export function createLocationRoutes(propertyController: PropertyController): Router {
  const router = Router();

  // Location suggestions
  router.get('/suggest',
    staticRateLimit,
    validateLocationSearch,
    propertyController.getLocationSuggestions
  );

  return router;
}

/**
 * Admin Routes
 * 
 * Administrative endpoints for monitoring and management.
 */
export function createAdminRoutes(propertyController: PropertyController): Router {
  const router = Router();

  // TODO: Add authentication middleware for admin routes
  // router.use(authenticate, authorize(['admin']));

  // Search analytics
  router.get('/analytics/search',
    intensiveRateLimit,
    validatePagination,
    propertyController.getSearchAnalytics
  );

  // Queue status
  router.get('/queue/status',
    staticRateLimit,
    propertyController.getQueueStatus
  );

  // Cache invalidation
  router.post('/cache/invalidate',
    intensiveRateLimit,
    propertyController.invalidateCache
  );

  return router;
}

export default { createPropertyRoutes, createLocationRoutes, createAdminRoutes };