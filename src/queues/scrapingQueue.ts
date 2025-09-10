import Bull, { Job, Queue } from 'bull';
import { config } from '@/config';
import { ScrapingJob, ScrapingJobResult, PropertySearchParams, StandardizedProperty } from '@/types';
import { queueLogger as logger } from '@/utils/logger';
import FirecrawlService from '@/services/firecrawlService';
import { DomainUrlBuilder } from '@/services/domainUrlBuilder';
import DataProcessor from '@/services/dataProcessor';
import DatabaseService from '@/services/databaseService';
import CacheService from '@/services/cacheService';

/**
 * Scraping Queue System
 * 
 * Handles asynchronous property scraping jobs using Bull Queue.
 * Processes search requests, manages job priorities, and handles retries.
 */
export class ScrapingQueueManager {
  private queue: Queue;
  private firecrawlService: FirecrawlService;
  private urlBuilder: DomainUrlBuilder;
  private dataProcessor: DataProcessor;
  private databaseService: DatabaseService;
  private cacheService: CacheService;

  constructor(
    databaseService: DatabaseService,
    cacheService: CacheService
  ) {
    this.databaseService = databaseService;
    this.cacheService = cacheService;
    this.firecrawlService = new FirecrawlService();
    this.urlBuilder = new DomainUrlBuilder();
    this.dataProcessor = new DataProcessor();

    // Initialize Bull queue with Redis connection
    this.queue = new Bull('property-scraping', {
      redis: {
        host: config.redis.host,
        port: config.redis.port,
        password: config.redis.password,
      },
      defaultJobOptions: {
        removeOnComplete: 100, // Keep last 100 completed jobs
        removeOnFail: 50, // Keep last 50 failed jobs
        attempts: config.queue.retryAttempts,
        backoff: {
          type: 'exponential',
          delay: config.queue.retryDelay,
        },
      },
    });

    this.setupJobProcessors();
    this.setupEventHandlers();
  }

  /**
   * Add a property search job to the queue
   */
  public async addSearchJob(
    params: PropertySearchParams,
    priority: 'low' | 'normal' | 'high' | 'critical' = 'normal',
    userId?: string
  ): Promise<string> {
    const jobId = this.generateJobId();
    
    const job: ScrapingJob = {
      id: jobId,
      type: 'domain-search',
      params,
      priority,
      userId,
      createdAt: new Date(),
    };

    try {
      // Save job to database first
      await this.databaseService.saveScrapingJob(job);

      // Add to queue with appropriate priority
      const queuePriority = this.getPriorityValue(priority);
      
      await this.queue.add('domain-search', job, {
        priority: queuePriority,
        jobId,
      });

      logger.info('Search job added to queue', {
        jobId,
        priority,
        params: this.sanitizeParams(params),
      });

      return jobId;
    } catch (error) {
      logger.error('Failed to add search job to queue', { jobId, error });
      throw error;
    }
  }

  /**
   * Add a bulk property detail scraping job
   */
  public async addBulkDetailJob(
    propertyIds: string[],
    priority: 'low' | 'normal' | 'high' | 'critical' = 'normal',
    userId?: string
  ): Promise<string> {
    const jobId = this.generateJobId();
    
    const job: ScrapingJob = {
      id: jobId,
      type: 'bulk-scrape',
      params: { propertyIds },
      priority,
      userId,
      createdAt: new Date(),
    };

    try {
      await this.databaseService.saveScrapingJob(job);

      const queuePriority = this.getPriorityValue(priority);
      
      await this.queue.add('bulk-scrape', job, {
        priority: queuePriority,
        jobId,
      });

      logger.info('Bulk detail job added to queue', {
        jobId,
        priority,
        propertyCount: propertyIds.length,
      });

      return jobId;
    } catch (error) {
      logger.error('Failed to add bulk detail job to queue', { jobId, error });
      throw error;
    }
  }

  /**
   * Get job status
   */
  public async getJobStatus(jobId: string): Promise<any> {
    try {
      const job = await this.queue.getJob(jobId);
      
      if (!job) {
        return { status: 'not_found' };
      }

      const state = await job.getState();
      const progress = job.progress();
      const result = job.returnvalue;
      const failedReason = job.failedReason;

      return {
        id: jobId,
        status: state,
        progress,
        result,
        error: failedReason,
        createdAt: job.timestamp,
        processedAt: job.processedOn,
        finishedAt: job.finishedOn,
      };
    } catch (error) {
      logger.error('Failed to get job status', { jobId, error });
      return { status: 'error', error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  /**
   * Cancel a job
   */
  public async cancelJob(jobId: string): Promise<boolean> {
    try {
      const job = await this.queue.getJob(jobId);
      
      if (!job) {
        return false;
      }

      await job.remove();
      logger.info('Job cancelled', { jobId });
      return true;
    } catch (error) {
      logger.error('Failed to cancel job', { jobId, error });
      return false;
    }
  }

  /**
   * Get queue statistics
   */
  public async getQueueStats(): Promise<any> {
    try {
      const waiting = await this.queue.getWaiting();
      const active = await this.queue.getActive();
      const completed = await this.queue.getCompleted();
      const failed = await this.queue.getFailed();

      return {
        waiting: waiting.length,
        active: active.length,
        completed: completed.length,
        failed: failed.length,
        total: waiting.length + active.length + completed.length + failed.length,
      };
    } catch (error) {
      logger.error('Failed to get queue stats', { error });
      return null;
    }
  }

  /**
   * Clean old jobs from the queue
   */
  public async cleanQueue(): Promise<void> {
    try {
      await this.queue.clean(24 * 60 * 60 * 1000, 'completed'); // Clean completed jobs older than 24h
      await this.queue.clean(7 * 24 * 60 * 60 * 1000, 'failed'); // Clean failed jobs older than 7 days
      
      logger.info('Queue cleaned successfully');
    } catch (error) {
      logger.error('Failed to clean queue', { error });
    }
  }

  /**
   * Close the queue connection
   */
  public async close(): Promise<void> {
    try {
      await this.queue.close();
      logger.info('Scraping queue closed');
    } catch (error) {
      logger.error('Error closing scraping queue', { error });
    }
  }

  /**
   * Setup job processors
   */
  private setupJobProcessors(): void {
    // Process domain search jobs
    this.queue.process('domain-search', config.queue.concurrency, async (job: Job<ScrapingJob>) => {
      return this.processDomainSearchJob(job);
    });

    // Process bulk scraping jobs
    this.queue.process('bulk-scrape', Math.max(1, Math.floor(config.queue.concurrency / 2)), async (job: Job<ScrapingJob>) => {
      return this.processBulkScrapeJob(job);
    });

    // Process individual property detail jobs
    this.queue.process('property-detail', config.queue.concurrency, async (job: Job<ScrapingJob>) => {
      return this.processPropertyDetailJob(job);
    });
  }

  /**
   * Process domain search job
   */
  private async processDomainSearchJob(job: Job<ScrapingJob>): Promise<ScrapingJobResult> {
    const startTime = Date.now();
    const jobData = job.data;
    const params = jobData.params as PropertySearchParams;

    logger.info('Processing domain search job', {
      jobId: jobData.id,
      params: this.sanitizeParams(params),
    });

    try {
      job.progress(10);

      // Check cache first
      const cached = await this.cacheService.getCachedSearchResults(params);
      if (cached) {
        job.progress(100);
        
        const result: ScrapingJobResult = {
          jobId: jobData.id,
          status: 'completed',
          properties: cached.data,
          executionTime: Date.now() - startTime,
          completedAt: new Date(),
        };

        await this.databaseService.updateScrapingJobResult(result);
        
        logger.info('Domain search job completed from cache', {
          jobId: jobData.id,
          propertiesCount: cached.data.length,
        });

        return result;
      }

      job.progress(20);

      // Build URLs for scraping
      const urls = this.urlBuilder.buildMultipleSearchUrls(params);
      
      job.progress(30);

      // Scrape the URLs
      const scrapedData = await this.firecrawlService.scrapeUrls(urls);
      
      job.progress(60);

      // Process the scraped data
      const allProperties: StandardizedProperty[] = [];
      const errors: string[] = [];

      for (const data of scrapedData) {
        try {
          const properties = this.dataProcessor.processDoaminData(data, data.url);
          allProperties.push(...properties);
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown processing error';
          errors.push(`Failed to process ${data.url}: ${errorMessage}`);
          logger.warn('Failed to process scraped data', { url: data.url, error });
        }
      }

      job.progress(80);

      // Save properties to database
      if (allProperties.length > 0) {
        await this.databaseService.saveProperties(allProperties);
        
        // Cache the results
        await this.cacheService.cacheSearchResults(
          params,
          allProperties,
          { page: params.page || 1, totalPages: 1, totalProperties: allProperties.length }
        );
      }

      job.progress(100);

      const result: ScrapingJobResult = {
        jobId: jobData.id,
        status: allProperties.length > 0 ? 'completed' : 'partial',
        properties: allProperties,
        errors: errors.length > 0 ? errors : undefined,
        executionTime: Date.now() - startTime,
        completedAt: new Date(),
      };

      await this.databaseService.updateScrapingJobResult(result);

      logger.info('Domain search job completed', {
        jobId: jobData.id,
        propertiesCount: allProperties.length,
        errorsCount: errors.length,
        executionTime: result.executionTime,
      });

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      const result: ScrapingJobResult = {
        jobId: jobData.id,
        status: 'failed',
        properties: [],
        errors: [errorMessage],
        executionTime: Date.now() - startTime,
        completedAt: new Date(),
      };

      await this.databaseService.updateScrapingJobResult(result);

      logger.error('Domain search job failed', {
        jobId: jobData.id,
        error: errorMessage,
        executionTime: result.executionTime,
      });

      throw error;
    }
  }

  /**
   * Process bulk scraping job
   */
  private async processBulkScrapeJob(job: Job<ScrapingJob>): Promise<ScrapingJobResult> {
    const startTime = Date.now();
    const jobData = job.data;
    const { propertyIds } = jobData.params as { propertyIds: string[] };

    logger.info('Processing bulk scrape job', {
      jobId: jobData.id,
      propertyCount: propertyIds.length,
    });

    try {
      // This would implement bulk property detail scraping
      // For now, return a placeholder result
      const result: ScrapingJobResult = {
        jobId: jobData.id,
        status: 'completed',
        properties: [],
        executionTime: Date.now() - startTime,
        completedAt: new Date(),
      };

      await this.databaseService.updateScrapingJobResult(result);
      return result;
    } catch (error) {
      logger.error('Bulk scrape job failed', { jobId: jobData.id, error });
      throw error;
    }
  }

  /**
   * Process individual property detail job
   */
  private async processPropertyDetailJob(job: Job<ScrapingJob>): Promise<ScrapingJobResult> {
    const startTime = Date.now();
    const jobData = job.data;

    // Implementation for individual property detail scraping
    const result: ScrapingJobResult = {
      jobId: jobData.id,
      status: 'completed',
      properties: [],
      executionTime: Date.now() - startTime,
      completedAt: new Date(),
    };

    await this.databaseService.updateScrapingJobResult(result);
    return result;
  }

  /**
   * Setup event handlers
   */
  private setupEventHandlers(): void {
    this.queue.on('completed', (job, result) => {
      logger.info('Job completed', {
        jobId: job.id,
        type: job.data.type,
        executionTime: result.executionTime,
        propertiesCount: result.properties?.length || 0,
      });
    });

    this.queue.on('failed', (job, err) => {
      logger.error('Job failed', {
        jobId: job.id,
        type: job.data.type,
        error: err.message,
        attempts: job.attemptsMade,
      });
    });

    this.queue.on('stalled', (job) => {
      logger.warn('Job stalled', {
        jobId: job.id,
        type: job.data.type,
      });
    });

    this.queue.on('progress', (job, progress) => {
      logger.debug('Job progress', {
        jobId: job.id,
        progress,
      });
    });
  }

  /**
   * Helper methods
   */
  
  private generateJobId(): string {
    return `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private getPriorityValue(priority: string): number {
    const priorityMap = {
      'critical': 100,
      'high': 75,
      'normal': 50,
      'low': 25,
    };
    
    return priorityMap[priority as keyof typeof priorityMap] || 50;
  }

  private sanitizeParams(params: PropertySearchParams): any {
    return {
      listingType: params.listingType,
      location: params.location,
      propertyType: params.propertyType,
      bedrooms: params.bedrooms,
      priceRange: params.priceRange,
      // Remove potentially sensitive information
    };
  }
}

export default ScrapingQueueManager;