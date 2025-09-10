import { config } from '@/config';

// Setup test environment
beforeAll(() => {
  // Set test environment
  process.env.NODE_ENV = 'test';
  
  // Mock external services during tests
  jest.mock('@/services/firecrawlService');
});

afterAll(() => {
  // Clean up after tests
  jest.restoreAllMocks();
});

// Global test timeout
jest.setTimeout(30000);