// Core property search types
export interface PropertySearchParams {
  listingType: 'rent' | 'buy';
  location: {
    suburb: string;
    state: string;
    postcode: string;
  };
  propertyType?: 'apartment' | 'house' | 'townhouse' | 'unit' | 'villa';
  bedrooms?: {
    min?: number;
    max?: number;
  };
  bathrooms?: {
    min?: number;
    max?: number;
  };
  priceRange?: {
    min?: number;
    max?: number;
  };
  parking?: {
    min?: number;
  };
  features?: string[];
  sortBy?: 'price-asc' | 'price-desc' | 'date-desc' | 'date-asc';
  page?: number;
  limit?: number;
}

// Domain.com.au specific types
export interface DomainProperty {
  id: string;
  address: {
    street: string;
    suburb: string;
    state: string;
    postcode: string;
    displayAddress: string;
  };
  price: {
    display: string;
    value?: number;
    frequency?: 'weekly' | 'monthly' | 'annually';
  };
  propertyType: string;
  bedrooms?: number;
  bathrooms?: number;
  parking?: number;
  landSize?: string;
  buildingSize?: string;
  images: string[];
  description?: string;
  features: string[];
  agent: {
    name: string;
    phone?: string;
    email?: string;
    agency: string;
  };
  inspectionTimes?: Array<{
    date: string;
    startTime: string;
    endTime: string;
  }>;
  listingDate: string;
  updatedDate: string;
  url: string;
}

// Standardized property response
export interface StandardizedProperty {
  id: string;
  source: 'domain' | 'realestate' | 'other';
  address: {
    street: string;
    suburb: string;
    state: string;
    postcode: string;
    fullAddress: string;
    coordinates?: {
      lat: number;
      lng: number;
    };
  };
  price: {
    display: string;
    amount?: number;
    frequency: 'weekly' | 'monthly' | 'annually';
    currency: 'AUD';
  };
  propertyDetails: {
    type: string;
    bedrooms?: number;
    bathrooms?: number;
    parking?: number;
    landSize?: number;
    buildingSize?: number;
  };
  media: {
    images: string[];
    virtualTour?: string;
  };
  description: string;
  features: string[];
  contact: {
    agentName: string;
    agencyName: string;
    phone?: string;
    email?: string;
  };
  availability: {
    dateAvailable?: string;
    inspectionTimes: Array<{
      date: string;
      startTime: string;
      endTime: string;
    }>;
  };
  metadata: {
    listingDate: string;
    lastUpdated: string;
    sourceUrl: string;
    scrapedAt: string;
  };
}

// API Response types
export interface PropertySearchResponse {
  success: boolean;
  data: {
    properties: StandardizedProperty[];
    pagination: {
      currentPage: number;
      totalPages: number;
      totalProperties: number;
      hasNext: boolean;
      hasPrevious: boolean;
    };
    filters: {
      applied: PropertySearchParams;
      available: {
        suburbs: string[];
        propertyTypes: string[];
        priceRanges: Array<{
          min: number;
          max: number;
          count: number;
        }>;
      };
    };
    metadata: {
      searchId: string;
      executionTime: number;
      sourcesScrapped: string[];
      cacheHit: boolean;
    };
  };
  error?: string;
}

// Cache types
export interface CacheKey {
  type: 'search' | 'property' | 'location';
  identifier: string;
  params?: Record<string, any>;
}

export interface CachedSearchResult {
  data: StandardizedProperty[];
  pagination: any;
  timestamp: number;
  ttl: number;
}

// Queue job types
export interface ScrapingJob {
  id: string;
  type: 'domain-search' | 'property-detail' | 'bulk-scrape';
  params: PropertySearchParams | { propertyIds: string[] };
  priority: 'low' | 'normal' | 'high' | 'critical';
  userId?: string;
  createdAt: Date;
}

export interface ScrapingJobResult {
  jobId: string;
  status: 'completed' | 'failed' | 'partial';
  properties: StandardizedProperty[];
  errors?: string[];
  executionTime: number;
  completedAt: Date;
}

// Configuration types
export interface AppConfig {
  server: {
    port: number;
    host: string;
    env: 'development' | 'production' | 'test';
  };
  database: {
    url: string;
    host: string;
    port: number;
    name: string;
    user: string;
    password: string;
  };
  redis: {
    url: string;
    host: string;
    port: number;
    password?: string;
  };
  firecrawl: {
    apiKey: string;
    baseUrl: string;
  };
  cache: {
    ttl: number;
    prefix: string;
  };
  queue: {
    concurrency: number;
    retryAttempts: number;
    retryDelay: number;
  };
  scraping: {
    delay: number;
    maxConcurrent: number;
    timeout: number;
  };
  rateLimit: {
    windowMs: number;
    maxRequests: number;
  };
}

// Error types
export class PropertySearchError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public details?: any
  ) {
    super(message);
    this.name = 'PropertySearchError';
  }
}

export class ScrapingError extends Error {
  constructor(
    message: string,
    public source: string,
    public url?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ScrapingError';
  }
}