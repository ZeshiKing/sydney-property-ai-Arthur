import { Router, Request, Response } from 'express';
import { asyncHandler } from '@/middleware/errorHandler';
import { staticRateLimit } from '@/middleware/rateLimit';
import { config } from '@/config';
import { logger } from '@/utils/logger';

/**
 * Health Check Routes
 * 
 * Comprehensive health checking endpoints for monitoring
 * the application's health and dependencies.
 */
export function createHealthRoutes(): Router {
  const router = Router();

  /**
   * Basic health check
   * GET /health
   */
  router.get('/', staticRateLimit, asyncHandler(async (req: Request, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0',
      environment: config.server.env,
      uptime: process.uptime(),
      requestId,
    };

    logger.debug('Basic health check requested', { requestId });

    res.status(200).json(health);
  }));

  /**
   * Detailed health check
   * GET /health/detailed
   */
  router.get('/detailed', staticRateLimit, asyncHandler(async (req: Request, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    logger.debug('Detailed health check requested', { requestId });

    // TODO: Add actual health checks for dependencies
    const checks = {
      database: { status: 'healthy', responseTime: 0 },
      cache: { status: 'healthy', responseTime: 0 },
      queue: { status: 'healthy', responseTime: 0 },
      firecrawl: { status: 'healthy', responseTime: 0 },
    };

    const allHealthy = Object.values(checks).every(check => check.status === 'healthy');
    const overallStatus = allHealthy ? 'healthy' : 'unhealthy';
    
    const detailedHealth = {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0',
      environment: config.server.env,
      uptime: process.uptime(),
      system: {
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch,
        memory: {
          used: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
          total: Math.round(process.memoryUsage().heapTotal / 1024 / 1024),
          external: Math.round(process.memoryUsage().external / 1024 / 1024),
        },
        cpu: {
          loadAverage: process.platform !== 'win32' ? require('os').loadavg() : [0, 0, 0],
        },
      },
      dependencies: checks,
      requestId,
    };

    const statusCode = overallStatus === 'healthy' ? 200 : 503;
    res.status(statusCode).json(detailedHealth);
  }));

  /**
   * Readiness probe
   * GET /health/ready
   */
  router.get('/ready', staticRateLimit, asyncHandler(async (req: Request, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    logger.debug('Readiness probe requested', { requestId });

    // TODO: Add actual readiness checks
    const isReady = true; // Check if app is ready to serve traffic

    if (isReady) {
      res.status(200).json({
        status: 'ready',
        timestamp: new Date().toISOString(),
        requestId,
      });
    } else {
      res.status(503).json({
        status: 'not_ready',
        timestamp: new Date().toISOString(),
        requestId,
      });
    }
  }));

  /**
   * Liveness probe
   * GET /health/live
   */
  router.get('/live', staticRateLimit, asyncHandler(async (req: Request, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    logger.debug('Liveness probe requested', { requestId });

    // Simple liveness check - if this endpoint responds, the app is alive
    res.status(200).json({
      status: 'alive',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      requestId,
    });
  }));

  return router;
}

export default createHealthRoutes;