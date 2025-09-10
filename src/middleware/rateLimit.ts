import rateLimit from 'express-rate-limit';
import { Request, Response } from 'express';
import { config } from '@/config';
import { logger } from '@/utils/logger';

// Custom key generator for rate limiting
const keyGenerator = (req: Request): string => {
  // Use IP address as default
  let key = req.ip || 'unknown';
  
  // If user is authenticated, use user ID (when implemented)
  if (req.headers.authorization) {
    // This would be replaced with actual user ID extraction logic
    key = `user:${req.headers.authorization.substring(0, 10)}`;
  }
  
  return key;
};

// Custom handler for rate limit exceeded
const rateLimitHandler = (req: Request, res: Response): void => {
  logger.warn('Rate limit exceeded', {
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    path: req.path,
    method: req.method,
  });

  res.status(429).json({
    success: false,
    error: {
      message: 'Too many requests, please try again later',
      code: 'RATE_LIMIT_EXCEEDED',
      statusCode: 429,
      timestamp: new Date().toISOString(),
      retryAfter: Math.ceil(config.rateLimit.windowMs / 1000),
    },
  });
};

// Default rate limiter
export const defaultRateLimit = rateLimit({
  windowMs: config.rateLimit.windowMs,
  max: config.rateLimit.maxRequests,
  message: rateLimitHandler,
  keyGenerator,
  standardHeaders: true,
  legacyHeaders: false,
  skip: (req) => {
    // Skip rate limiting for health checks
    return req.path === '/health' || req.path === '/api/health';
  },
});

// Stricter rate limit for search endpoints
export const searchRateLimit = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 50, // Limit to 50 searches per 15 minutes
  message: rateLimitHandler,
  keyGenerator,
  standardHeaders: true,
  legacyHeaders: false,
});

// Very strict rate limit for resource-intensive operations
export const intensiveRateLimit = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 10, // Limit to 10 requests per hour
  message: rateLimitHandler,
  keyGenerator,
  standardHeaders: true,
  legacyHeaders: false,
});

// Lenient rate limit for static content
export const staticRateLimit = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000, // Limit to 1000 requests per 15 minutes
  message: rateLimitHandler,
  keyGenerator,
  standardHeaders: true,
  legacyHeaders: false,
});