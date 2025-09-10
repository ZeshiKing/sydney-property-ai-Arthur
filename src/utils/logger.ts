import winston from 'winston';
import { config } from '@/config';

const logFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

const developmentFormat = winston.format.combine(
  winston.format.colorize(),
  winston.format.timestamp({ format: 'HH:mm:ss' }),
  winston.format.printf(({ timestamp, level, message, service, ...meta }) => {
    let metaStr = '';
    if (Object.keys(meta).length > 0) {
      metaStr = JSON.stringify(meta, null, 2);
    }
    return `${timestamp} [${level}] ${service ? `[${service}] ` : ''}${message}${metaStr ? `\n${metaStr}` : ''}`;
  })
);

const transports: winston.transport[] = [
  new winston.transports.Console({
    level: config.server.env === 'development' ? 'debug' : 'info',
    format: config.server.env === 'development' ? developmentFormat : logFormat,
  }),
];

// Add file transport for production
if (config.server.env === 'production') {
  transports.push(
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error',
      format: logFormat,
      maxsize: 5242880, // 5MB
      maxFiles: 5,
    }),
    new winston.transports.File({
      filename: 'logs/combined.log',
      format: logFormat,
      maxsize: 5242880, // 5MB
      maxFiles: 5,
    })
  );
}

export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: logFormat,
  defaultMeta: { service: 'rental-aggregator' },
  transports,
  exitOnError: false,
});

// Create specialized loggers for different services
export const createLogger = (service: string) => {
  return logger.child({ service });
};

// Export service-specific loggers
export const scrapingLogger = createLogger('scraping');
export const cacheLogger = createLogger('cache');
export const queueLogger = createLogger('queue');
export const dbLogger = createLogger('database');
export const apiLogger = createLogger('api');

export default logger;