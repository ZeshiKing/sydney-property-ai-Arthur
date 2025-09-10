import axios, { AxiosInstance } from 'axios';
import { config } from '@/config';
import { ScrapingError } from '@/types';
import { scrapingLogger as logger } from '@/utils/logger';

/**
 * Firecrawl API Service
 * 
 * Handles web scraping using Firecrawl API with rate limiting,
 * error handling, and retry mechanisms.
 */
export class FirecrawlService {
  private readonly client: AxiosInstance;
  private readonly maxRetries = 3;
  private readonly retryDelay = 2000; // 2 seconds

  constructor() {
    this.client = axios.create({
      baseURL: config.firecrawl.baseUrl,
      headers: {
        'Authorization': `Bearer ${config.firecrawl.apiKey}`,
        'Content-Type': 'application/json',
      },
      timeout: config.scraping.timeout,
    });

    this.setupInterceptors();
  }

  /**
   * Scrape a single URL and return structured data
   */
  public async scrapeUrl(url: string, options?: ScrapeOptions): Promise<ScrapeResult> {
    try {
      logger.info('Starting scrape request', { url, options });
      
      const startTime = Date.now();
      const response = await this.makeRequest('/v0/scrape', {
        url,
        formats: ['markdown', 'html'],
        includeTags: ['script[id="__NEXT_DATA__"]', 'script[type="application/ld+json"]'],
        excludeTags: ['script[src]', 'style', 'nav', 'footer', 'aside'],
        onlyMainContent: true,
        waitFor: 2000, // Wait for dynamic content
        ...options,
      });

      const executionTime = Date.now() - startTime;
      
      logger.info('Scrape request completed', {
        url,
        executionTime,
        success: response.success,
      });

      if (!response.success) {
        throw new ScrapingError(
          `Scraping failed: ${response.error}`,
          'firecrawl',
          url,
          response
        );
      }

      return {
        url,
        markdown: response.data?.markdown || '',
        html: response.data?.html || '',
        metadata: response.data?.metadata || {},
        structuredData: this.extractStructuredData(response.data),
        executionTime,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      logger.error('Scrape request failed', { url, error });
      
      if (axios.isAxiosError(error)) {
        throw new ScrapingError(
          `HTTP error: ${error.response?.status} ${error.response?.statusText}`,
          'firecrawl',
          url,
          {
            status: error.response?.status,
            data: error.response?.data,
          }
        );
      }
      
      throw new ScrapingError(
        error instanceof Error ? error.message : 'Unknown scraping error',
        'firecrawl',
        url
      );
    }
  }

  /**
   * Scrape multiple URLs concurrently with rate limiting
   */
  public async scrapeUrls(urls: string[], options?: ScrapeOptions): Promise<ScrapeResult[]> {
    logger.info('Starting batch scrape', { urlCount: urls.length, options });
    
    const results: ScrapeResult[] = [];
    const errors: Array<{ url: string; error: string }> = [];
    
    // Process URLs in batches to respect rate limits
    const batchSize = config.scraping.maxConcurrent;
    
    for (let i = 0; i < urls.length; i += batchSize) {
      const batch = urls.slice(i, i + batchSize);
      
      const batchPromises = batch.map(async (url) => {
        try {
          // Add delay between requests to prevent rate limiting
          if (i > 0) {
            await this.delay(config.scraping.delay);
          }
          
          return await this.scrapeUrl(url, options);
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          errors.push({ url, error: errorMessage });
          logger.warn('Failed to scrape URL in batch', { url, error: errorMessage });
          return null;
        }
      });
      
      const batchResults = await Promise.all(batchPromises);
      
      // Filter out failed requests
      const successfulResults = batchResults.filter(result => result !== null) as ScrapeResult[];
      results.push(...successfulResults);
      
      logger.info('Batch completed', {
        batchIndex: Math.floor(i / batchSize) + 1,
        totalBatches: Math.ceil(urls.length / batchSize),
        successCount: successfulResults.length,
        errorCount: batch.length - successfulResults.length,
      });
    }
    
    logger.info('Batch scraping completed', {
      totalUrls: urls.length,
      successCount: results.length,
      errorCount: errors.length,
      errors: errors.slice(0, 5), // Log first 5 errors
    });
    
    return results;
  }

  /**
   * Search the web and scrape results
   */
  public async searchAndScrape(query: string, options?: SearchOptions): Promise<SearchResult> {
    try {
      logger.info('Starting search request', { query, options });
      
      const response = await this.makeRequest('/v0/search', {
        query,
        limit: options?.limit || 10,
        scrapeOptions: {
          formats: ['markdown'],
          onlyMainContent: true,
          ...options?.scrapeOptions,
        },
      });

      if (!response.success) {
        throw new ScrapingError(
          `Search failed: ${response.error}`,
          'firecrawl',
          undefined,
          response
        );
      }

      return {
        query,
        results: response.data || [],
        metadata: {
          totalResults: response.data?.length || 0,
          timestamp: new Date().toISOString(),
        },
      };
    } catch (error) {
      logger.error('Search request failed', { query, error });
      throw error;
    }
  }

  /**
   * Get crawling status for async operations
   */
  public async getCrawlStatus(jobId: string): Promise<CrawlStatus> {
    try {
      const response = await this.makeRequest(`/v0/crawl/status/${jobId}`, {}, 'GET');
      
      return {
        jobId,
        status: response.status,
        current: response.current,
        total: response.total,
        data: response.data || [],
        partial_data: response.partial_data || [],
      };
    } catch (error) {
      logger.error('Failed to get crawl status', { jobId, error });
      throw error;
    }
  }

  /**
   * Extract structured data from scraped content
   */
  private extractStructuredData(data: any): any {
    const structuredData: any = {};
    
    try {
      // Extract JSON-LD structured data
      if (data.html) {
        const jsonLdMatches = data.html.match(/<script[^>]*type="application\/ld\+json"[^>]*>(.*?)<\/script>/gs);
        if (jsonLdMatches) {
          structuredData.jsonLd = jsonLdMatches.map((match: string) => {
            const jsonContent = match.replace(/<script[^>]*>/, '').replace(/<\/script>/, '');
            try {
              return JSON.parse(jsonContent);
            } catch {
              return null;
            }
          }).filter(Boolean);
        }
      }
      
      // Extract __NEXT_DATA__ for Domain.com.au
      if (data.html) {
        const nextDataMatch = data.html.match(/<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)<\/script>/s);
        if (nextDataMatch) {
          try {
            structuredData.nextData = JSON.parse(nextDataMatch[1]);
          } catch (error) {
            logger.warn('Failed to parse __NEXT_DATA__', { error });
          }
        }
      }
      
      // Extract metadata
      if (data.metadata) {
        structuredData.metadata = {
          title: data.metadata.title,
          description: data.metadata.description,
          ogTitle: data.metadata.ogTitle,
          ogDescription: data.metadata.ogDescription,
          ogImage: data.metadata.ogImage,
          keywords: data.metadata.keywords,
        };
      }
    } catch (error) {
      logger.warn('Failed to extract structured data', { error });
    }
    
    return structuredData;
  }

  /**
   * Setup axios interceptors for logging and retry logic
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        logger.debug('Firecrawl API request', {
          method: config.method,
          url: config.url,
          params: config.params,
        });
        return config;
      },
      (error) => {
        logger.error('Firecrawl API request error', { error });
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        logger.debug('Firecrawl API response', {
          status: response.status,
          url: response.config.url,
        });
        return response;
      },
      (error) => {
        logger.error('Firecrawl API response error', {
          status: error.response?.status,
          url: error.config?.url,
          error: error.response?.data,
        });
        return Promise.reject(error);
      }
    );
  }

  /**
   * Make HTTP request with retry logic
   */
  private async makeRequest(
    endpoint: string,
    data: any,
    method: 'GET' | 'POST' = 'POST'
  ): Promise<any> {
    let lastError: any;
    
    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        const response = method === 'GET' 
          ? await this.client.get(endpoint, { params: data })
          : await this.client.post(endpoint, data);
        
        return response.data;
      } catch (error) {
        lastError = error;
        
        if (axios.isAxiosError(error)) {
          const status = error.response?.status;
          
          // Don't retry on 4xx errors (except 429)
          if (status && status >= 400 && status < 500 && status !== 429) {
            break;
          }
        }
        
        if (attempt < this.maxRetries) {
          logger.warn(`Retrying request (attempt ${attempt + 1}/${this.maxRetries})`, {
            endpoint,
            error: error instanceof Error ? error.message : 'Unknown error',
          });
          
          await this.delay(this.retryDelay * attempt); // Exponential backoff
        }
      }
    }
    
    throw lastError;
  }

  /**
   * Delay helper function
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Types for Firecrawl service
export interface ScrapeOptions {
  formats?: string[];
  includeTags?: string[];
  excludeTags?: string[];
  onlyMainContent?: boolean;
  waitFor?: number;
  timeout?: number;
}

export interface ScrapeResult {
  url: string;
  markdown: string;
  html: string;
  metadata: any;
  structuredData: any;
  executionTime: number;
  timestamp: string;
}

export interface SearchOptions {
  limit?: number;
  scrapeOptions?: ScrapeOptions;
}

export interface SearchResult {
  query: string;
  results: any[];
  metadata: {
    totalResults: number;
    timestamp: string;
  };
}

export interface CrawlStatus {
  jobId: string;
  status: 'scraping' | 'completed' | 'failed';
  current: number;
  total: number;
  data: any[];
  partial_data: any[];
}

export default FirecrawlService;