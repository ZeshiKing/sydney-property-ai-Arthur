import Joi from 'joi';
import { Request, Response, NextFunction } from 'express';
import { PropertySearchError } from '@/types';

// Property search validation schema
export const propertySearchSchema = Joi.object({
  listingType: Joi.string().valid('rent', 'buy').required(),
  location: Joi.object({
    suburb: Joi.string().min(2).max(100).required(),
    state: Joi.string().valid('NSW', 'VIC', 'QLD', 'WA', 'SA', 'TAS', 'ACT', 'NT').required(),
    postcode: Joi.string().pattern(/^\d{4}$/).required(),
  }).required(),
  propertyType: Joi.string().valid('apartment', 'house', 'townhouse', 'unit', 'villa').optional(),
  bedrooms: Joi.object({
    min: Joi.number().integer().min(0).max(10).optional(),
    max: Joi.number().integer().min(0).max(10).optional(),
  }).optional(),
  bathrooms: Joi.object({
    min: Joi.number().integer().min(0).max(10).optional(),
    max: Joi.number().integer().min(0).max(10).optional(),
  }).optional(),
  priceRange: Joi.object({
    min: Joi.number().integer().min(0).optional(),
    max: Joi.number().integer().min(0).optional(),
  }).optional(),
  parking: Joi.object({
    min: Joi.number().integer().min(0).max(10).optional(),
  }).optional(),
  features: Joi.array().items(Joi.string()).optional(),
  sortBy: Joi.string().valid('price-asc', 'price-desc', 'date-desc', 'date-asc').optional(),
  page: Joi.number().integer().min(1).max(100).default(1),
  limit: Joi.number().integer().min(1).max(100).default(20),
}).custom((value, helpers) => {
  // Validate price range
  if (value.priceRange && value.priceRange.min && value.priceRange.max) {
    if (value.priceRange.min >= value.priceRange.max) {
      return helpers.error('custom.priceRange');
    }
  }
  
  // Validate bedroom range
  if (value.bedrooms && value.bedrooms.min && value.bedrooms.max) {
    if (value.bedrooms.min > value.bedrooms.max) {
      return helpers.error('custom.bedroomRange');
    }
  }
  
  // Validate bathroom range
  if (value.bathrooms && value.bathrooms.min && value.bathrooms.max) {
    if (value.bathrooms.min > value.bathrooms.max) {
      return helpers.error('custom.bathroomRange');
    }
  }
  
  return value;
}, 'Custom validation').messages({
  'custom.priceRange': 'Price minimum must be less than maximum',
  'custom.bedroomRange': 'Bedroom minimum must be less than or equal to maximum',
  'custom.bathroomRange': 'Bathroom minimum must be less than or equal to maximum',
});

// Generic validation middleware factory
export const validateSchema = (schema: Joi.ObjectSchema) => {
  return (req: Request, res: Response, next: NextFunction) => {
    const { error, value } = schema.validate(req.body, {
      abortEarly: false,
      stripUnknown: true,
    });

    if (error) {
      const details = error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message,
      }));

      throw new PropertySearchError(
        'Validation failed',
        'VALIDATION_ERROR',
        400,
        details
      );
    }

    req.body = value;
    next();
  };
};

// Query parameter validation
export const validateQuery = (schema: Joi.ObjectSchema) => {
  return (req: Request, res: Response, next: NextFunction) => {
    const { error, value } = schema.validate(req.query, {
      abortEarly: false,
      stripUnknown: true,
    });

    if (error) {
      const details = error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message,
      }));

      throw new PropertySearchError(
        'Query validation failed',
        'QUERY_VALIDATION_ERROR',
        400,
        details
      );
    }

    req.query = value;
    next();
  };
};

// Property ID validation
export const propertyIdSchema = Joi.object({
  id: Joi.string().alphanum().min(10).max(50).required(),
});

// Pagination query schema
export const paginationSchema = Joi.object({
  page: Joi.number().integer().min(1).max(100).default(1),
  limit: Joi.number().integer().min(1).max(100).default(20),
});

// Location search schema
export const locationSearchSchema = Joi.object({
  query: Joi.string().min(2).max(100).required(),
  state: Joi.string().valid('NSW', 'VIC', 'QLD', 'WA', 'SA', 'TAS', 'ACT', 'NT').optional(),
  limit: Joi.number().integer().min(1).max(50).default(10),
});

// Export validation middleware functions
export const validatePropertySearch = validateSchema(propertySearchSchema);
export const validatePropertyId = validateSchema(propertyIdSchema);
export const validatePagination = validateQuery(paginationSchema);
export const validateLocationSearch = validateQuery(locationSearchSchema);