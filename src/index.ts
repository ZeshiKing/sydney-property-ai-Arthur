import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import { config } from '@/config';
import { logger, apiLogger } from '@/utils/logger';
import { errorHandler, notFoundHandler } from '@/middleware/errorHandler';
import { defaultRateLimit } from '@/middleware/rateLimit';

// Import routes
import { createPropertyRoutes, createLocationRoutes, createAdminRoutes } from '@/routes/propertyRoutes';
import createHealthRoutes from '@/routes/healthRoutes';
import PropertyController from '@/controllers/propertyController';
import PropertyService from '@/services/propertyService';
import DatabaseService from '@/services/databaseService';
import CacheService from '@/services/cacheService';
import ScrapingQueueManager from '@/queues/scrapingQueue';

const app = express();

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID'],
  exposedHeaders: ['X-Request-ID'],
}));

// Request parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(compression());

// Rate limiting
app.use(defaultRateLimit);

// Request ID middleware
app.use((req, res, next) => {
  const requestId = req.headers['x-request-id'] as string || 
    Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  
  req.headers['x-request-id'] = requestId;
  res.setHeader('X-Request-ID', requestId);
  next();
});

// Request logging
app.use((req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    apiLogger.info('HTTP Request', {
      method: req.method,
      url: req.url,
      statusCode: res.statusCode,
      duration,
      userAgent: req.get('User-Agent'),
      ip: req.ip,
      requestId: req.headers['x-request-id'],
    });
  });
  
  next();
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0',
    environment: config.server.env,
    uptime: process.uptime(),
  });
});

// Initialize services
async function initializeServices() {
  try {
    // Initialize database service
    const databaseService = new DatabaseService();
    await databaseService.connect();

    // Initialize cache service
    const cacheService = new CacheService();
    await cacheService.connect();

    // Initialize queue manager
    const queueManager = new ScrapingQueueManager(databaseService, cacheService);

    // Initialize property service
    const propertyService = new PropertyService(databaseService, cacheService, queueManager);

    // Initialize controller
    const propertyController = new PropertyController(propertyService);

    return {
      databaseService,
      cacheService,
      queueManager,
      propertyService,
      propertyController,
    };
  } catch (error) {
    logger.error('Failed to initialize services', { error });
    throw error;
  }
}

// Initialize services and setup routes
initializeServices().then((services) => {
  // Setup API routes
  app.use('/api/properties', createPropertyRoutes(services.propertyController));
  app.use('/api/locations', createLocationRoutes(services.propertyController));
  app.use('/api/admin', createAdminRoutes(services.propertyController));
  app.use('/health', createHealthRoutes());

  // API root endpoint
  app.use('/api', (req, res) => {
    res.json({
      message: 'Rental Aggregator API',
      version: '1.0.0',
      status: 'operational',
      endpoints: {
        health: '/health',
        properties: {
          search: 'POST /api/properties/search',
          getById: 'GET /api/properties/:id',
          health: 'GET /api/properties/health',
        },
        locations: {
          suggest: 'GET /api/locations/suggest?query=<location>',
        },
        admin: {
          analytics: 'GET /api/admin/analytics/search',
          queue: 'GET /api/admin/queue/status',
          cache: 'POST /api/admin/cache/invalidate',
        },
      },
    });
  });

  logger.info('API routes initialized successfully');
}).catch((error) => {
  logger.error('Failed to initialize services and routes', { error });
  process.exit(1);
});

// 404 handler
app.use(notFoundHandler);

// Error handler (must be last)
app.use(errorHandler);

// Graceful shutdown handling
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection at:', { promise, reason });
  process.exit(1);
});

process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception:', { error });
  process.exit(1);
});

// Start server
const server = app.listen(config.server.port, config.server.host, () => {
  logger.info(`Server started on ${config.server.host}:${config.server.port}`, {
    environment: config.server.env,
    nodeVersion: process.version,
    pid: process.pid,
  });
});

export default app;