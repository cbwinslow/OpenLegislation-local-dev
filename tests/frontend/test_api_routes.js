/**
 * Tests for Next.js API routes.
 *
 * This module tests API endpoints including:
 * - Data API routes
 * - Ingestion API routes
 * - Logs API routes
 * - Error handling
 * - Authentication
 * - Rate limiting
 */

import { jest } from '@jest/globals';

// Mock Next.js request/response objects
const createMockRequest = (method = 'GET', body = null, headers = {}) => ({
  method,
  json: async () => body,
  headers: {
    get: (key) => headers[key],
    ...headers
  },
  url: 'http://localhost:3000/api/test',
  nextUrl: { pathname: '/api/test' }
});

const createMockResponse = () => {
  const res = {
    status: jest.fn().mockReturnThis(),
    json: jest.fn().mockReturnThis(),
    send: jest.fn().mockReturnThis(),
    setHeader: jest.fn().mockReturnThis(),
    getHeader: jest.fn(),
    headers: new Map()
  };
  return res;
};

describe('Data API Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('GET /api/data returns legislation data', async () => {
    // Mock the data route handler
    const mockData = {
      bills: { count: 150, lastUpdated: '2025-01-15T10:30:00Z' },
      members: { count: 535, lastUpdated: '2025-01-14T15:45:00Z' },
      votes: { count: 2340, lastUpdated: '2025-01-15T09:15:00Z' }
    };

    // Mock database or external API call
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    // Import and test the route handler
    const { GET } = require('../api/data/route');

    const req = createMockRequest('GET');
    const res = createMockResponse();

    await GET(req);

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/legislation/data'),
      expect.any(Object)
    );
  });

  test('GET /api/data handles errors gracefully', async () => {
    // Mock failed API call
    global.fetch = jest.fn().mockRejectedValueOnce(new Error('Database connection failed'));

    const { GET } = require('../api/data/route');

    const req = createMockRequest('GET');
    const res = createMockResponse();

    await GET(req);

    expect(res.status).toHaveBeenCalledWith(500);
    expect(res.json).toHaveBeenCalledWith(
      expect.objectContaining({
        error: expect.stringContaining('Failed to fetch data')
      })
    );
  });

  test('POST /api/data validates input', async () => {
    const { POST } = require('../api/data/route');

    // Test with invalid data
    const invalidData = { invalidField: 'value' };
    const req = createMockRequest('POST', invalidData);
    const res = createMockResponse();

    await POST(req);

    expect(res.status).toHaveBeenCalledWith(400);
    expect(res.json).toHaveBeenCalledWith(
      expect.objectContaining({
        error: expect.stringContaining('Invalid input')
      })
    );
  });

  test('POST /api/data processes valid data', async () => {
    const validData = {
      billId: 'S.123',
      title: 'Test Bill',
      status: 'introduced'
    };

    // Mock successful data processing
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: '123', ...validData })
    });

    const { POST } = require('../api/data/route');

    const req = createMockRequest('POST', validData);
    const res = createMockResponse();

    await POST(req);

    expect(res.status).toHaveBeenCalledWith(201);
    expect(res.json).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        data: expect.objectContaining(validData)
      })
    );
  });
});

describe('Ingestion API Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('POST /api/ingest/start triggers ingestion process', async () => {
    const ingestionRequest = {
      dataType: 'bills',
      source: 'govinfo',
      dateRange: {
        start: '2025-01-01',
        end: '2025-01-31'
      }
    };

    // Mock ingestion service
    const mockIngestionResult = {
      jobId: 'ingest_12345',
      status: 'started',
      estimatedDuration: '30 minutes'
    };

    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockIngestionResult
    });

    const { POST } = require('../api/ingest/route');

    const req = createMockRequest('POST', ingestionRequest);
    const res = createMockResponse();

    await POST(req);

    expect(res.status).toHaveBeenCalledWith(202); // Accepted
    expect(res.json).toHaveBeenCalledWith(
      expect.objectContaining({
        jobId: 'ingest_12345',
        status: 'started'
      })
    );
  });

  test('GET /api/ingest/status returns ingestion progress', async () => {
    const mockStatus = {
      jobId: 'ingest_12345',
      status: 'running',
      progress: 65,
      currentTask: 'Processing bill metadata',
      eta: '15 minutes',
      startTime: '2025-01-15T10:30:00Z'
    };

    // Mock status retrieval
    const mockQueueStatus = { ...mockStatus };

    const { GET } = require('../api/ingest/route');

    const req = createMockRequest('GET', null, { 'x-job-id': 'ingest_12345' });
    const res = createMockResponse();

    // Mock the queue manager or status service
    jest.doMock('../../../queue_manager', () => ({
      getJobStatus: jest.fn().mockResolvedValue(mockQueueStatus)
    }));

    await GET(req);

    expect(res.status).toHaveBeenCalledWith(200);
    expect(res.json).toHaveBeenCalledWith(
      expect.objectContaining({
        status: 'running',
        progress: 65
      })
    );
  });

  test('POST /api/ingest/start validates required fields', async () => {
    const invalidRequest = {
      // Missing required dataType
      source: 'govinfo'
    };

    const { POST } = require('../api/ingest/route');

    const req = createMockRequest('POST', invalidRequest);
    const res = createMockResponse();

    await POST(req);

    expect(res.status).toHaveBeenCalledWith(400);
    expect(res.json).toHaveBeenCalledWith(
      expect.objectContaining({
        error: expect.stringContaining('dataType')
      })
    );
  });

  test('DELETE /api/ingest cancels running ingestion', async () => {
    const { DELETE } = require('../api/ingest/route');

    const req = createMockRequest('DELETE', null, { 'x-job-id': 'ingest_12345' });
    const res = createMockResponse();

    // Mock cancellation service
    jest.doMock('../../../queue_manager', () => ({
      cancelJob: jest.fn().mockResolvedValue({ cancelled: true })
    }));

    await DELETE(req);

    expect(res.status).toHaveBeenCalledWith(200);
    expect(res.json).toHaveBeenCalledWith(
      expect.objectContaining({
        cancelled: true
      })
    );
  });
});

describe('Logs API Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('GET /api/logs returns application logs', async () => {
    const mockLogs = [
      {
        timestamp: '2025-01-15T10:30:00Z',
        level: 'INFO',
        message: 'Ingestion started for bills',
        source: 'ingestion-service'
      },
      {
        timestamp: '2025-01-15T10:35:00Z',
        level: 'ERROR',
        message: 'Failed to process bill S.123',
        source: 'data-processor',
        error: 'Invalid XML format'
      }
    ];

    // Mock log retrieval
    jest.doMock('../../../observability_setup', () => ({
      getLogs: jest.fn().mockResolvedValue(mockLogs)
    }));

    const { GET } = require('../api/logs/route');

    const req = createMockRequest('GET', null, {
      'x-limit': '50',
      'x-level': 'ERROR'
    });
    const res = createMockResponse();

    await GET(req);

    expect(res.status).toHaveBeenCalledWith(200);
    expect(res.json).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({
          level: expect.any(String),
          message: expect.any(String),
          timestamp: expect.any(String)
        })
      ])
    );
  });

  test('GET /api/logs supports filtering by level', async () => {
    const errorLogs = [
      {
        timestamp: '2025-01-15T10:35:00Z',
        level: 'ERROR',
        message: 'Database connection failed',
        source: 'db-service'
      }
    ];

    jest.doMock('../../../observability_setup', () => ({
      getLogs: jest.fn().mockImplementation((options) => {
        if (options.level === 'ERROR') {
          return Promise.resolve(errorLogs);
        }
        return Promise.resolve([]);
      })
    }));

    const { GET } = require('../api/logs/route');

    const req = createMockRequest('GET', null, { 'x-level': 'ERROR' });
    const res = createMockResponse();

    await GET(req);

    expect(res.json).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ level: 'ERROR' })
      ])
    );
  });

  test('POST /api/logs adds new log entry', async () => {
    const newLogEntry = {
      level: 'WARN',
      message: 'High memory usage detected',
      source: 'monitoring-service',
      metadata: { memoryUsage: '85%' }
    };

    jest.doMock('../../../observability_setup', () => ({
      addLog: jest.fn().mockResolvedValue({
        id: 'log_123',
        ...newLogEntry,
        timestamp: '2025-01-15T11:00:00Z'
      })
    }));

    const { POST } = require('../api/logs/route');

    const req = createMockRequest('POST', newLogEntry);
    const res = createMockResponse();

    await POST(req);

    expect(res.status).toHaveBeenCalledWith(201);
    expect(res.json).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'log_123',
        level: 'WARN',
        message: 'High memory usage detected'
      })
    );
  });
});

describe('API Authentication', () => {
  test('validates API key authentication', async () => {
    const authMiddleware = (req) => {
      const apiKey = req.headers.get('x-api-key');
      if (!apiKey || apiKey !== process.env.API_KEY) {
        throw new Error('Unauthorized');
      }
      return true;
    };

    // Mock environment variable
    process.env.API_KEY = 'test-api-key-123';

    const req = createMockRequest('GET', null, { 'x-api-key': 'test-api-key-123' });

    expect(() => authMiddleware(req)).not.toThrow();

    const invalidReq = createMockRequest('GET', null, { 'x-api-key': 'wrong-key' });
    expect(() => authMiddleware(invalidReq)).toThrow('Unauthorized');
  });

  test('handles JWT token authentication', async () => {
    const jwtAuth = (req) => {
      const token = req.headers.get('authorization')?.replace('Bearer ', '');
      if (!token) {
        throw new Error('No token provided');
      }

      // Mock JWT verification
      if (token === 'valid.jwt.token') {
        return { userId: '123', role: 'admin' };
      }
      throw new Error('Invalid token');
    };

    const req = createMockRequest('GET', null, {
      'authorization': 'Bearer valid.jwt.token'
    });

    const user = jwtAuth(req);
    expect(user).toEqual({ userId: '123', role: 'admin' });

    const invalidReq = createMockRequest('GET', null, {
      'authorization': 'Bearer invalid.token'
    });
    expect(() => jwtAuth(invalidReq)).toThrow('Invalid token');
  });
});

describe('API Rate Limiting', () => {
  test('enforces rate limits', async () => {
    let requestCount = 0;
    const rateLimit = 5; // 5 requests per minute

    const rateLimitMiddleware = (req) => {
      requestCount++;
      if (requestCount > rateLimit) {
        const error = new Error('Rate limit exceeded');
        error.statusCode = 429;
        throw error;
      }
      return true;
    };

    // First 5 requests should succeed
    for (let i = 1; i <= rateLimit; i++) {
      const req = createMockRequest('GET');
      expect(() => rateLimitMiddleware(req)).not.toThrow();
    }

    // 6th request should fail
    const req = createMockRequest('GET');
    expect(() => rateLimitMiddleware(req)).toThrow();
    expect(() => rateLimitMiddleware(req)).toThrow();
  });

  test('includes rate limit headers in response', async () => {
    const rateLimitHeaders = (res, remaining, resetTime) => {
      res.setHeader('X-RateLimit-Remaining', remaining);
      res.setHeader('X-RateLimit-Reset', resetTime);
      res.setHeader('X-RateLimit-Limit', 100);
    };

    const res = createMockResponse();

    rateLimitHeaders(res, 95, '1640995200');

    expect(res.setHeader).toHaveBeenCalledWith('X-RateLimit-Remaining', 95);
    expect(res.setHeader).toHaveBeenCalledWith('X-RateLimit-Reset', '1640995200');
    expect(res.setHeader).toHaveBeenCalledWith('X-RateLimit-Limit', 100);
  });
});

describe('API Error Handling', () => {
  test('handles validation errors', async () => {
    const validateInput = (data) => {
      const errors = [];

      if (!data.title) errors.push('Title is required');
      if (!data.description) errors.push('Description is required');
      if (data.priority && !['low', 'medium', 'high'].includes(data.priority)) {
        errors.push('Invalid priority value');
      }

      if (errors.length > 0) {
        const error = new Error('Validation failed');
        error.statusCode = 400;
        error.details = errors;
        throw error;
      }

      return data;
    };

    expect(() => validateInput({})).toThrow();
    expect(() => validateInput({})).toThrow();

    const validData = {
      title: 'Valid Title',
      description: 'Valid Description',
      priority: 'high'
    };

    expect(validateInput(validData)).toEqual(validData);
  });

  test('handles database errors', async () => {
    const databaseOperation = async (operation) => {
      try {
        if (operation === 'fail') {
          throw new Error('Connection timeout');
        }
        return { success: true };
      } catch (error) {
        const dbError = new Error('Database operation failed');
        dbError.statusCode = 500;
        dbError.originalError = error;
        throw dbError;
      }
    };

    await expect(databaseOperation('success')).resolves.toEqual({ success: true });

    await expect(databaseOperation('fail')).rejects.toThrow('Database operation failed');
    await expect(databaseOperation('fail')).rejects.toMatchObject({
      statusCode: 500,
      originalError: expect.any(Error)
    });
  });

  test('handles external API failures', async () => {
    const externalApiCall = async (shouldFail) => {
      if (shouldFail) {
        const response = await fetch('https://api.example.com/fail');
        if (!response.ok) {
          throw new Error(`External API error: ${response.status}`);
        }
      }
      return { data: 'success' };
    };

    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: false,
        status: 503,
        statusText: 'Service Unavailable'
      });

    await expect(externalApiCall(true)).rejects.toThrow('External API error: 503');
  });
});

describe('API Response Formatting', () => {
  test('formats successful responses consistently', () => {
    const formatSuccessResponse = (data, meta = {}) => ({
      success: true,
      data,
      meta: {
        timestamp: new Date().toISOString(),
        version: '1.0',
        ...meta
      }
    });

    const response = formatSuccessResponse(
      { bills: 150 },
      { requestId: 'req_123' }
    );

    expect(response).toEqual({
      success: true,
      data: { bills: 150 },
      meta: expect.objectContaining({
        timestamp: expect.any(String),
        version: '1.0',
        requestId: 'req_123'
      })
    });
  });

  test('formats error responses consistently', () => {
    const formatErrorResponse = (error, statusCode = 500) => ({
      success: false,
      error: {
        message: error.message,
        code: statusCode,
        details: error.details || null
      },
      meta: {
        timestamp: new Date().toISOString(),
        version: '1.0'
      }
    });

    const error = new Error('Validation failed');
    error.details = ['Field X is required'];

    const response = formatErrorResponse(error, 400);

    expect(response).toEqual({
      success: false,
      error: {
        message: 'Validation failed',
        code: 400,
        details: ['Field X is required']
      },
      meta: expect.objectContaining({
        timestamp: expect.any(String),
        version: '1.0'
      })
    });
  });

  test('handles pagination metadata', () => {
    const formatPaginatedResponse = (data, pagination) => ({
      success: true,
      data,
      meta: {
        pagination: {
          page: pagination.page,
          limit: pagination.limit,
          total: pagination.total,
          totalPages: Math.ceil(pagination.total / pagination.limit)
        },
        timestamp: new Date().toISOString(),
        version: '1.0'
      }
    });

    const response = formatPaginatedResponse(
      [{ id: 1 }, { id: 2 }],
      { page: 1, limit: 10, total: 25 }
    );

    expect(response.meta.pagination).toEqual({
      page: 1,
      limit: 10,
      total: 25,
      totalPages: 3
    });
  });
});