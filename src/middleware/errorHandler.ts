import { Request, Response, NextFunction } from 'express';
import { PropertySearchError, ScrapingError } from '@/types';
import { logger } from '@/utils/logger';

export interface ErrorResponse {
  success: false;
  error: {
    message: string;
    code: string;
    statusCode: number;
    details?: any;
    timestamp: string;
    requestId?: string;
  };
}

export const errorHandler = (
  error: Error,
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  const requestId = req.headers['x-request-id'] as string;
  
  logger.error('Error occurred', {
    error: {
      name: error.name,
      message: error.message,
      stack: error.stack,
    },
    request: {
      method: req.method,
      url: req.url,
      headers: req.headers,
      body: req.body,
      params: req.params,
      query: req.query,
    },
    requestId,
  });

  let statusCode = 500;
  let code = 'INTERNAL_SERVER_ERROR';
  let message = 'An unexpected error occurred';
  let details: any = undefined;

  if (error instanceof PropertySearchError) {
    statusCode = error.statusCode;
    code = error.code;
    message = error.message;
    details = error.details;
  } else if (error instanceof ScrapingError) {
    statusCode = 500;
    code = 'SCRAPING_ERROR';
    message = error.message;
    details = {
      source: error.source,
      url: error.url,
      ...error.details,
    };
  } else if (error.name === 'ValidationError') {
    statusCode = 400;
    code = 'VALIDATION_ERROR';
    message = 'Invalid request data';
    details = error.message;
  } else if (error.name === 'CastError') {
    statusCode = 400;
    code = 'INVALID_ID';
    message = 'Invalid ID format';
  } else if (error.name === 'MongoTimeoutError') {
    statusCode = 503;
    code = 'DATABASE_TIMEOUT';
    message = 'Database operation timed out';
  } else if (error.name === 'RedisConnectionError') {
    statusCode = 503;
    code = 'CACHE_UNAVAILABLE';
    message = 'Cache service unavailable';
  }

  const errorResponse: ErrorResponse = {
    success: false,
    error: {
      message,
      code,
      statusCode,
      details,
      timestamp: new Date().toISOString(),
      requestId,
    },
  };

  res.status(statusCode).json(errorResponse);
};

export const notFoundHandler = (req: Request, res: Response): void => {
  const errorResponse: ErrorResponse = {
    success: false,
    error: {
      message: `Route ${req.method} ${req.path} not found`,
      code: 'NOT_FOUND',
      statusCode: 404,
      timestamp: new Date().toISOString(),
      requestId: req.headers['x-request-id'] as string,
    },
  };

  res.status(404).json(errorResponse);
};

export const asyncHandler = (fn: Function) => {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};