import { Pool, PoolClient, QueryResult } from 'pg';
import { config } from '@/config';
import { StandardizedProperty, PropertySearchParams, ScrapingJob, ScrapingJobResult } from '@/types';
import { dbLogger as logger } from '@/utils/logger';

/**
 * PostgreSQL Database Service
 * 
 * Handles database connections, queries, and data persistence
 * for search history, property data, and job tracking.
 */
export class DatabaseService {
  private pool: Pool;
  private isConnected = false;

  constructor() {
    this.pool = new Pool({
      connectionString: config.database.url,
      host: config.database.host,
      port: config.database.port,
      database: config.database.name,
      user: config.database.user,
      password: config.database.password,
      max: 20, // Maximum number of clients in the pool
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 5000,
      ssl: config.server.env === 'production' ? { rejectUnauthorized: false } : false,
    });

    this.setupEventHandlers();
  }

  /**
   * Initialize database connection and create tables if needed
   */
  public async connect(): Promise<void> {
    try {
      // Test the connection
      const client = await this.pool.connect();
      await client.query('SELECT NOW()');
      client.release();

      this.isConnected = true;
      logger.info('Database service connected successfully');

      // Create tables if they don't exist
      await this.createTables();
    } catch (error) {
      logger.error('Failed to connect to database', { error });
      throw error;
    }
  }

  /**
   * Close database connection
   */
  public async disconnect(): Promise<void> {
    try {
      if (this.isConnected) {
        await this.pool.end();
        this.isConnected = false;
        logger.info('Database service disconnected');
      }
    } catch (error) {
      logger.error('Error disconnecting from database', { error });
    }
  }

  /**
   * Execute a query
   */
  public async query(text: string, params?: any[]): Promise<QueryResult> {
    const start = Date.now();
    
    try {
      const result = await this.pool.query(text, params);
      const duration = Date.now() - start;
      
      logger.debug('Database query executed', {
        query: text.substring(0, 100) + (text.length > 100 ? '...' : ''),
        duration,
        rows: result.rowCount,
      });
      
      return result;
    } catch (error) {
      const duration = Date.now() - start;
      logger.error('Database query failed', {
        query: text.substring(0, 100) + (text.length > 100 ? '...' : ''),
        params,
        duration,
        error,
      });
      throw error;
    }
  }

  /**
   * Save search parameters and results for analytics
   */
  public async saveSearchRecord(
    searchId: string,
    params: PropertySearchParams,
    resultCount: number,
    executionTime: number,
    sourcesScrapped: string[],
    userIp?: string
  ): Promise<void> {
    try {
      const query = `
        INSERT INTO search_history 
        (search_id, search_params, result_count, execution_time, sources_scrapped, user_ip, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, NOW())
      `;
      
      await this.query(query, [
        searchId,
        JSON.stringify(params),
        resultCount,
        executionTime,
        JSON.stringify(sourcesScrapped),
        userIp,
      ]);

      logger.debug('Search record saved', { searchId, resultCount });
    } catch (error) {
      logger.error('Failed to save search record', { searchId, error });
      // Don't throw error as this is not critical for the main functionality
    }
  }

  /**
   * Save scraped property data
   */
  public async saveProperty(property: StandardizedProperty): Promise<void> {
    try {
      const query = `
        INSERT INTO properties 
        (property_id, source, address_data, price_data, property_details, media_data, 
         description, features, contact_data, availability_data, metadata, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
        ON CONFLICT (property_id, source) 
        DO UPDATE SET
          address_data = EXCLUDED.address_data,
          price_data = EXCLUDED.price_data,
          property_details = EXCLUDED.property_details,
          media_data = EXCLUDED.media_data,
          description = EXCLUDED.description,
          features = EXCLUDED.features,
          contact_data = EXCLUDED.contact_data,
          availability_data = EXCLUDED.availability_data,
          metadata = EXCLUDED.metadata,
          updated_at = NOW()
      `;

      await this.query(query, [
        property.id,
        property.source,
        JSON.stringify(property.address),
        JSON.stringify(property.price),
        JSON.stringify(property.propertyDetails),
        JSON.stringify(property.media),
        property.description,
        JSON.stringify(property.features),
        JSON.stringify(property.contact),
        JSON.stringify(property.availability),
        JSON.stringify(property.metadata),
      ]);

      logger.debug('Property saved to database', { propertyId: property.id, source: property.source });
    } catch (error) {
      logger.error('Failed to save property', { propertyId: property.id, error });
    }
  }

  /**
   * Save multiple properties in a batch
   */
  public async saveProperties(properties: StandardizedProperty[]): Promise<void> {
    if (properties.length === 0) return;

    const client = await this.pool.connect();
    
    try {
      await client.query('BEGIN');

      for (const property of properties) {
        const query = `
          INSERT INTO properties 
          (property_id, source, address_data, price_data, property_details, media_data, 
           description, features, contact_data, availability_data, metadata, created_at, updated_at)
          VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
          ON CONFLICT (property_id, source) 
          DO UPDATE SET
            address_data = EXCLUDED.address_data,
            price_data = EXCLUDED.price_data,
            property_details = EXCLUDED.property_details,
            media_data = EXCLUDED.media_data,
            description = EXCLUDED.description,
            features = EXCLUDED.features,
            contact_data = EXCLUDED.contact_data,
            availability_data = EXCLUDED.availability_data,
            metadata = EXCLUDED.metadata,
            updated_at = NOW()
        `;

        await client.query(query, [
          property.id,
          property.source,
          JSON.stringify(property.address),
          JSON.stringify(property.price),
          JSON.stringify(property.propertyDetails),
          JSON.stringify(property.media),
          property.description,
          JSON.stringify(property.features),
          JSON.stringify(property.contact),
          JSON.stringify(property.availability),
          JSON.stringify(property.metadata),
        ]);
      }

      await client.query('COMMIT');
      logger.info('Batch properties saved to database', { count: properties.length });
    } catch (error) {
      await client.query('ROLLBACK');
      logger.error('Failed to save properties batch', { count: properties.length, error });
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Get property by ID
   */
  public async getProperty(propertyId: string, source: string): Promise<StandardizedProperty | null> {
    try {
      const query = 'SELECT * FROM properties WHERE property_id = $1 AND source = $2';
      const result = await this.query(query, [propertyId, source]);

      if (result.rows.length === 0) {
        return null;
      }

      const row = result.rows[0];
      return this.mapRowToProperty(row);
    } catch (error) {
      logger.error('Failed to get property', { propertyId, source, error });
      return null;
    }
  }

  /**
   * Search properties in database
   */
  public async searchProperties(
    params: PropertySearchParams,
    offset: number = 0,
    limit: number = 20
  ): Promise<{ properties: StandardizedProperty[]; total: number }> {
    try {
      const whereConditions: string[] = [];
      const queryParams: any[] = [];
      let paramIndex = 1;

      // Location filter
      if (params.location) {
        whereConditions.push(`address_data->>'suburb' ILIKE $${paramIndex}`);
        queryParams.push(`%${params.location.suburb}%`);
        paramIndex++;

        if (params.location.state) {
          whereConditions.push(`address_data->>'state' = $${paramIndex}`);
          queryParams.push(params.location.state);
          paramIndex++;
        }

        if (params.location.postcode) {
          whereConditions.push(`address_data->>'postcode' = $${paramIndex}`);
          queryParams.push(params.location.postcode);
          paramIndex++;
        }
      }

      // Property type filter
      if (params.propertyType) {
        whereConditions.push(`property_details->>'type' ILIKE $${paramIndex}`);
        queryParams.push(`%${params.propertyType}%`);
        paramIndex++;
      }

      // Bedrooms filter
      if (params.bedrooms) {
        if (params.bedrooms.min !== undefined) {
          whereConditions.push(`(property_details->>'bedrooms')::integer >= $${paramIndex}`);
          queryParams.push(params.bedrooms.min);
          paramIndex++;
        }
        if (params.bedrooms.max !== undefined) {
          whereConditions.push(`(property_details->>'bedrooms')::integer <= $${paramIndex}`);
          queryParams.push(params.bedrooms.max);
          paramIndex++;
        }
      }

      // Price range filter
      if (params.priceRange) {
        if (params.priceRange.min !== undefined) {
          whereConditions.push(`(price_data->>'amount')::numeric >= $${paramIndex}`);
          queryParams.push(params.priceRange.min);
          paramIndex++;
        }
        if (params.priceRange.max !== undefined) {
          whereConditions.push(`(price_data->>'amount')::numeric <= $${paramIndex}`);
          queryParams.push(params.priceRange.max);
          paramIndex++;
        }
      }

      const whereClause = whereConditions.length > 0 
        ? `WHERE ${whereConditions.join(' AND ')}`
        : '';

      // Count total results
      const countQuery = `SELECT COUNT(*) FROM properties ${whereClause}`;
      const countResult = await this.query(countQuery, queryParams);
      const total = parseInt(countResult.rows[0].count);

      // Get paginated results
      const orderBy = this.buildOrderBy(params.sortBy);
      const dataQuery = `
        SELECT * FROM properties 
        ${whereClause}
        ${orderBy}
        LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
      `;

      queryParams.push(limit, offset);
      const dataResult = await this.query(dataQuery, queryParams);

      const properties = dataResult.rows.map(row => this.mapRowToProperty(row));

      logger.debug('Database search completed', {
        params,
        total,
        returned: properties.length,
      });

      return { properties, total };
    } catch (error) {
      logger.error('Failed to search properties in database', { params, error });
      throw error;
    }
  }

  /**
   * Save scraping job
   */
  public async saveScrapingJob(job: ScrapingJob): Promise<void> {
    try {
      const query = `
        INSERT INTO scraping_jobs 
        (job_id, job_type, job_params, priority, user_id, created_at, status)
        VALUES ($1, $2, $3, $4, $5, $6, 'pending')
      `;

      await this.query(query, [
        job.id,
        job.type,
        JSON.stringify(job.params),
        job.priority,
        job.userId,
        job.createdAt,
      ]);

      logger.debug('Scraping job saved', { jobId: job.id, type: job.type });
    } catch (error) {
      logger.error('Failed to save scraping job', { jobId: job.id, error });
    }
  }

  /**
   * Update scraping job result
   */
  public async updateScrapingJobResult(result: ScrapingJobResult): Promise<void> {
    try {
      const query = `
        UPDATE scraping_jobs 
        SET status = $2, result_data = $3, execution_time = $4, completed_at = $5, errors = $6
        WHERE job_id = $1
      `;

      await this.query(query, [
        result.jobId,
        result.status,
        JSON.stringify(result.properties),
        result.executionTime,
        result.completedAt,
        JSON.stringify(result.errors || []),
      ]);

      logger.debug('Scraping job result updated', { jobId: result.jobId, status: result.status });
    } catch (error) {
      logger.error('Failed to update scraping job result', { jobId: result.jobId, error });
    }
  }

  /**
   * Get search analytics
   */
  public async getSearchAnalytics(days: number = 7): Promise<any> {
    try {
      const query = `
        SELECT 
          DATE(created_at) as date,
          COUNT(*) as search_count,
          AVG(result_count) as avg_results,
          AVG(execution_time) as avg_execution_time,
          ARRAY_AGG(DISTINCT sources_scrapped::text) as sources_used
        FROM search_history 
        WHERE created_at >= NOW() - INTERVAL '${days} days'
        GROUP BY DATE(created_at)
        ORDER BY date DESC
      `;

      const result = await this.query(query);
      return result.rows;
    } catch (error) {
      logger.error('Failed to get search analytics', { error });
      return [];
    }
  }

  /**
   * Create database tables
   */
  private async createTables(): Promise<void> {
    const client = await this.pool.connect();
    
    try {
      // Search history table
      await client.query(`
        CREATE TABLE IF NOT EXISTS search_history (
          id SERIAL PRIMARY KEY,
          search_id VARCHAR(255) UNIQUE NOT NULL,
          search_params JSONB NOT NULL,
          result_count INTEGER NOT NULL,
          execution_time INTEGER NOT NULL,
          sources_scrapped JSONB NOT NULL,
          user_ip INET,
          created_at TIMESTAMP WITH TIME ZONE NOT NULL
        )
      `);

      // Properties table
      await client.query(`
        CREATE TABLE IF NOT EXISTS properties (
          id SERIAL PRIMARY KEY,
          property_id VARCHAR(255) NOT NULL,
          source VARCHAR(50) NOT NULL,
          address_data JSONB NOT NULL,
          price_data JSONB NOT NULL,
          property_details JSONB NOT NULL,
          media_data JSONB NOT NULL,
          description TEXT,
          features JSONB NOT NULL,
          contact_data JSONB NOT NULL,
          availability_data JSONB NOT NULL,
          metadata JSONB NOT NULL,
          created_at TIMESTAMP WITH TIME ZONE NOT NULL,
          updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
          UNIQUE(property_id, source)
        )
      `);

      // Scraping jobs table
      await client.query(`
        CREATE TABLE IF NOT EXISTS scraping_jobs (
          id SERIAL PRIMARY KEY,
          job_id VARCHAR(255) UNIQUE NOT NULL,
          job_type VARCHAR(100) NOT NULL,
          job_params JSONB NOT NULL,
          priority VARCHAR(20) NOT NULL,
          user_id VARCHAR(255),
          status VARCHAR(20) NOT NULL DEFAULT 'pending',
          result_data JSONB,
          execution_time INTEGER,
          errors JSONB,
          created_at TIMESTAMP WITH TIME ZONE NOT NULL,
          completed_at TIMESTAMP WITH TIME ZONE
        )
      `);

      // Create indexes for better performance
      await client.query(`CREATE INDEX IF NOT EXISTS idx_search_history_created_at ON search_history(created_at)`);
      await client.query(`CREATE INDEX IF NOT EXISTS idx_properties_location ON properties USING GIN ((address_data->>'suburb'), (address_data->>'state'))`);
      await client.query(`CREATE INDEX IF NOT EXISTS idx_properties_price ON properties USING BTREE (((price_data->>'amount')::numeric))`);
      await client.query(`CREATE INDEX IF NOT EXISTS idx_properties_bedrooms ON properties USING BTREE (((property_details->>'bedrooms')::integer))`);
      await client.query(`CREATE INDEX IF NOT EXISTS idx_scraping_jobs_status ON scraping_jobs(status, created_at)`);

      logger.info('Database tables created/verified successfully');
    } catch (error) {
      logger.error('Failed to create database tables', { error });
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Set up database event handlers
   */
  private setupEventHandlers(): void {
    this.pool.on('error', (err) => {
      logger.error('Database pool error', { error: err });
    });

    this.pool.on('connect', () => {
      logger.debug('Database client connected');
    });

    this.pool.on('remove', () => {
      logger.debug('Database client removed');
    });
  }

  /**
   * Map database row to StandardizedProperty
   */
  private mapRowToProperty(row: any): StandardizedProperty {
    return {
      id: row.property_id,
      source: row.source,
      address: row.address_data,
      price: row.price_data,
      propertyDetails: row.property_details,
      media: row.media_data,
      description: row.description || '',
      features: row.features,
      contact: row.contact_data,
      availability: row.availability_data,
      metadata: row.metadata,
    };
  }

  /**
   * Build ORDER BY clause based on sort parameter
   */
  private buildOrderBy(sortBy?: string): string {
    switch (sortBy) {
      case 'price-asc':
        return 'ORDER BY (price_data->>\'amount\')::numeric ASC';
      case 'price-desc':
        return 'ORDER BY (price_data->>\'amount\')::numeric DESC';
      case 'date-desc':
        return 'ORDER BY created_at DESC';
      case 'date-asc':
        return 'ORDER BY created_at ASC';
      default:
        return 'ORDER BY updated_at DESC';
    }
  }

  /**
   * Health check for database service
   */
  public async healthCheck(): Promise<{ status: string; details?: any }> {
    try {
      const start = Date.now();
      const result = await this.query('SELECT 1 as health_check');
      const duration = Date.now() - start;

      if (result.rows[0].health_check === 1) {
        return {
          status: 'healthy',
          details: {
            connected: this.isConnected,
            responseTime: duration,
            poolSize: this.pool.totalCount,
            idleClients: this.pool.idleCount,
            waitingClients: this.pool.waitingCount,
          },
        };
      } else {
        return { status: 'unhealthy' };
      }
    } catch (error) {
      return {
        status: 'error',
        details: { error: error instanceof Error ? error.message : 'Unknown error' },
      };
    }
  }
}

export default DatabaseService;