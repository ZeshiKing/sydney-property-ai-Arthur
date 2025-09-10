import dotenv from 'dotenv';
import { AppConfig } from '@/types';

// Load environment variables
dotenv.config();

const getEnvVar = (name: string, defaultValue?: string): string => {
  const value = process.env[name];
  if (value === undefined && defaultValue === undefined) {
    throw new Error(`Environment variable ${name} is required`);
  }
  return value || defaultValue!;
};

const getEnvNumber = (name: string, defaultValue: number): number => {
  const value = process.env[name];
  if (value === undefined) return defaultValue;
  const parsed = parseInt(value, 10);
  if (isNaN(parsed)) {
    throw new Error(`Environment variable ${name} must be a valid number`);
  }
  return parsed;
};

const getEnvBoolean = (name: string, defaultValue: boolean): boolean => {
  const value = process.env[name];
  if (value === undefined) return defaultValue;
  return value.toLowerCase() === 'true';
};

export const config: AppConfig = {
  server: {
    port: getEnvNumber('PORT', 3000),
    host: getEnvVar('HOST', 'localhost'),
    env: (getEnvVar('NODE_ENV', 'development') as 'development' | 'production' | 'test'),
  },
  
  database: {
    url: getEnvVar('DATABASE_URL'),
    host: getEnvVar('DB_HOST', 'localhost'),
    port: getEnvNumber('DB_PORT', 5432),
    name: getEnvVar('DB_NAME', 'rental_aggregator'),
    user: getEnvVar('DB_USER', 'postgres'),
    password: getEnvVar('DB_PASSWORD', ''),
  },
  
  redis: {
    url: getEnvVar('REDIS_URL', 'redis://localhost:6379'),
    host: getEnvVar('REDIS_HOST', 'localhost'),
    port: getEnvNumber('REDIS_PORT', 6379),
    password: process.env.REDIS_PASSWORD,
  },
  
  firecrawl: {
    apiKey: getEnvVar('FIRECRAWL_API_KEY'),
    baseUrl: getEnvVar('FIRECRAWL_BASE_URL', 'https://api.firecrawl.dev'),
  },
  
  cache: {
    ttl: getEnvNumber('CACHE_TTL_SECONDS', 900), // 15 minutes
    prefix: getEnvVar('CACHE_PREFIX', 'rental_agg:'),
  },
  
  queue: {
    concurrency: getEnvNumber('QUEUE_CONCURRENCY', 5),
    retryAttempts: getEnvNumber('QUEUE_RETRY_ATTEMPTS', 3),
    retryDelay: getEnvNumber('QUEUE_RETRY_DELAY', 5000),
  },
  
  scraping: {
    delay: getEnvNumber('SCRAPING_DELAY_MS', 1000),
    maxConcurrent: getEnvNumber('MAX_CONCURRENT_REQUESTS', 3),
    timeout: getEnvNumber('SCRAPING_TIMEOUT_MS', 30000),
  },
  
  rateLimit: {
    windowMs: getEnvNumber('RATE_LIMIT_WINDOW_MS', 900000), // 15 minutes
    maxRequests: getEnvNumber('RATE_LIMIT_MAX_REQUESTS', 100),
  },
};

export const isDevelopment = config.server.env === 'development';
export const isProduction = config.server.env === 'production';
export const isTest = config.server.env === 'test';

export default config;