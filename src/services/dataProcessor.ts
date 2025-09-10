import * as cheerio from 'cheerio';
import { DomainProperty, StandardizedProperty, ScrapingError } from '@/types';
import { logger } from '@/utils/logger';

/**
 * Data Processing and Standardization Engine
 * 
 * Processes raw scraped data from various sources and converts them
 * into standardized property objects for consistent API responses.
 */
export class DataProcessor {
  
  /**
   * Process Domain.com.au scraped data into standardized format
   */
  public processDoaminData(scrapedData: any, sourceUrl: string): StandardizedProperty[] {
    try {
      logger.info('Processing Domain.com.au data', { sourceUrl });
      
      const properties: StandardizedProperty[] = [];
      
      // Extract data from __NEXT_DATA__ script tag
      if (scrapedData.structuredData?.nextData) {
        const nextData = scrapedData.structuredData.nextData;
        const domainProperties = this.extractPropertiesFromNextData(nextData);
        
        for (const domainProp of domainProperties) {
          const standardized = this.standardizeDomainProperty(domainProp, sourceUrl);
          if (standardized) {
            properties.push(standardized);
          }
        }
      }
      
      // Fallback: Parse HTML directly if __NEXT_DATA__ is not available
      if (properties.length === 0 && scrapedData.html) {
        const htmlProperties = this.extractPropertiesFromHTML(scrapedData.html, sourceUrl);
        properties.push(...htmlProperties);
      }
      
      logger.info('Domain.com.au data processing completed', {
        sourceUrl,
        propertiesCount: properties.length,
      });
      
      return properties;
    } catch (error) {
      logger.error('Failed to process Domain.com.au data', { sourceUrl, error });
      throw new ScrapingError(
        `Data processing failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        'domain',
        sourceUrl,
        { originalData: scrapedData }
      );
    }
  }

  /**
   * Extract properties from Domain's __NEXT_DATA__ structure
   */
  private extractPropertiesFromNextData(nextData: any): DomainProperty[] {
    const properties: DomainProperty[] = [];
    
    try {
      // Navigate the NextJS data structure to find property listings
      const props = nextData?.props;
      if (!props) return properties;
      
      // Check different possible data structures
      const possiblePaths = [
        props.pageProps?.componentProps?.results,
        props.pageProps?.results,
        props.pageProps?.data?.results,
        props.pageProps?.listingResults,
      ];
      
      for (const path of possiblePaths) {
        if (Array.isArray(path)) {
          for (const item of path) {
            const property = this.parseDomainPropertyData(item);
            if (property) {
              properties.push(property);
            }
          }
          break; // Found data, no need to check other paths
        }
      }
      
      logger.debug('Extracted properties from __NEXT_DATA__', {
        propertiesCount: properties.length,
        dataStructure: Object.keys(props.pageProps || {}),
      });
      
    } catch (error) {
      logger.warn('Failed to extract properties from __NEXT_DATA__', { error });
    }
    
    return properties;
  }

  /**
   * Parse individual Domain property data object
   */
  private parseDomainPropertyData(data: any): DomainProperty | null {
    try {
      if (!data || typeof data !== 'object') {
        return null;
      }
      
      // Extract property ID
      const id = data.id || data.listingId || data.propertyId;
      if (!id) {
        return null;
      }
      
      // Extract address information
      const address = {
        street: data.address?.street || data.streetAddress || '',
        suburb: data.address?.suburb || data.suburb || '',
        state: data.address?.state || data.state || '',
        postcode: data.address?.postcode || data.postcode || '',
        displayAddress: data.address?.displayAddress || data.displayAddress || '',
      };
      
      // Extract price information
      const price = {
        display: data.price?.display || data.priceText || data.displayPrice || '',
        value: this.extractPriceValue(data.price?.display || data.priceText),
        frequency: this.extractPriceFrequency(data.price?.display || data.priceText),
      };
      
      // Extract property features
      const bedrooms = data.bedrooms || data.bedroomCount || data.bed;
      const bathrooms = data.bathrooms || data.bathroomCount || data.bath;
      const parking = data.parking || data.carSpaces || data.carspaces;
      
      // Extract images
      const images = this.extractImages(data.media || data.images || []);
      
      // Extract description
      const description = data.description || data.headline || data.title || '';
      
      // Extract features
      const features = this.extractFeatures(data.features || data.propertyFeatures || []);
      
      // Extract agent information
      const agent = {
        name: data.agent?.name || data.advertiser?.name || '',
        phone: data.agent?.phone || data.advertiser?.phone || '',
        email: data.agent?.email || data.advertiser?.email || '',
        agency: data.agent?.agency || data.advertiser?.agency || data.agencyName || '',
      };
      
      // Extract dates
      const listingDate = data.listingDate || data.dateCreated || new Date().toISOString();
      const updatedDate = data.updatedDate || data.dateUpdated || listingDate;
      
      return {
        id: id.toString(),
        address,
        price,
        propertyType: data.propertyType || data.type || '',
        bedrooms: bedrooms ? parseInt(bedrooms) : undefined,
        bathrooms: bathrooms ? parseInt(bathrooms) : undefined,
        parking: parking ? parseInt(parking) : undefined,
        landSize: data.landSize || data.landArea || '',
        buildingSize: data.buildingSize || data.floorArea || '',
        images,
        description,
        features,
        agent,
        inspectionTimes: this.extractInspectionTimes(data.inspectionTimes || []),
        listingDate,
        updatedDate,
        url: data.url || data.seoUrl || '',
      };
    } catch (error) {
      logger.warn('Failed to parse Domain property data', { error, data });
      return null;
    }
  }

  /**
   * Extract properties from HTML when __NEXT_DATA__ is not available
   */
  private extractPropertiesFromHTML(html: string, sourceUrl: string): StandardizedProperty[] {
    const properties: StandardizedProperty[] = [];
    
    try {
      const $ = cheerio.load(html);
      
      // Look for property listing containers
      const propertySelectors = [
        '[data-testid="listing-card"]',
        '.property-card',
        '.listing-result',
        '.css-qrqvvq', // Domain-specific class
      ];
      
      for (const selector of propertySelectors) {
        const elements = $(selector);
        if (elements.length > 0) {
          logger.debug(`Found ${elements.length} properties using selector: ${selector}`);
          
          elements.each((index, element) => {
            const property = this.parsePropertyFromHTML($, $(element), sourceUrl);
            if (property) {
              properties.push(property);
            }
          });
          break; // Found properties, no need to try other selectors
        }
      }
      
      logger.info('HTML property extraction completed', {
        sourceUrl,
        propertiesFound: properties.length,
      });
      
    } catch (error) {
      logger.error('Failed to extract properties from HTML', { sourceUrl, error });
    }
    
    return properties;
  }

  /**
   * Parse property from HTML element
   */
  private parsePropertyFromHTML($: cheerio.CheerioAPI, element: cheerio.Cheerio, sourceUrl: string): StandardizedProperty | null {
    try {
      // Generate a unique ID if not available
      const id = element.attr('data-id') || 
                 element.find('[data-id]').attr('data-id') || 
                 `html_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Extract address
      const addressText = element.find('.address, [data-testid="address"]').text().trim();
      const address = this.parseAddressFromText(addressText);
      
      // Extract price
      const priceText = element.find('.price, [data-testid="price"]').text().trim();
      const price = {
        display: priceText,
        amount: this.extractPriceValue(priceText),
        frequency: this.extractPriceFrequency(priceText) as 'weekly' | 'monthly' | 'annually',
        currency: 'AUD' as const,
      };
      
      // Extract property details
      const bedroomText = element.find('[data-testid="bedrooms"], .bedrooms').text().trim();
      const bathroomText = element.find('[data-testid="bathrooms"], .bathrooms').text().trim();
      const parkingText = element.find('[data-testid="parking"], .parking').text().trim();
      
      const propertyDetails = {
        type: element.find('.property-type').text().trim() || 'Unknown',
        bedrooms: this.extractNumber(bedroomText),
        bathrooms: this.extractNumber(bathroomText),
        parking: this.extractNumber(parkingText),
      };
      
      // Extract images
      const images: string[] = [];
      element.find('img').each((_, img) => {
        const src = $(img).attr('src') || $(img).attr('data-src');
        if (src && this.isValidImageUrl(src)) {
          images.push(this.normalizeImageUrl(src));
        }
      });
      
      // Extract other details
      const description = element.find('.description, .summary').text().trim();
      const agentName = element.find('.agent-name, [data-testid="agent-name"]').text().trim();
      const agencyName = element.find('.agency-name, [data-testid="agency-name"]').text().trim();
      
      return {
        id,
        source: 'domain' as const,
        address,
        price,
        propertyDetails,
        media: {
          images,
        },
        description,
        features: [],
        contact: {
          agentName: agentName || 'Unknown',
          agencyName: agencyName || 'Unknown',
        },
        availability: {
          inspectionTimes: [],
        },
        metadata: {
          listingDate: new Date().toISOString(),
          lastUpdated: new Date().toISOString(),
          sourceUrl,
          scrapedAt: new Date().toISOString(),
        },
      };
    } catch (error) {
      logger.warn('Failed to parse property from HTML element', { error });
      return null;
    }
  }

  /**
   * Convert Domain property to standardized format
   */
  private standardizeDomainProperty(domainProp: DomainProperty, sourceUrl: string): StandardizedProperty | null {
    try {
      return {
        id: domainProp.id,
        source: 'domain' as const,
        address: {
          street: domainProp.address.street,
          suburb: domainProp.address.suburb,
          state: domainProp.address.state,
          postcode: domainProp.address.postcode,
          fullAddress: domainProp.address.displayAddress || 
                       `${domainProp.address.street}, ${domainProp.address.suburb} ${domainProp.address.state} ${domainProp.address.postcode}`,
        },
        price: {
          display: domainProp.price.display,
          amount: domainProp.price.value,
          frequency: domainProp.price.frequency || 'weekly',
          currency: 'AUD' as const,
        },
        propertyDetails: {
          type: domainProp.propertyType,
          bedrooms: domainProp.bedrooms,
          bathrooms: domainProp.bathrooms,
          parking: domainProp.parking,
          landSize: this.parseSize(domainProp.landSize),
          buildingSize: this.parseSize(domainProp.buildingSize),
        },
        media: {
          images: domainProp.images,
        },
        description: domainProp.description || '',
        features: domainProp.features,
        contact: {
          agentName: domainProp.agent.name,
          agencyName: domainProp.agent.agency,
          phone: domainProp.agent.phone,
          email: domainProp.agent.email,
        },
        availability: {
          inspectionTimes: domainProp.inspectionTimes || [],
        },
        metadata: {
          listingDate: domainProp.listingDate,
          lastUpdated: domainProp.updatedDate,
          sourceUrl: domainProp.url || sourceUrl,
          scrapedAt: new Date().toISOString(),
        },
      };
    } catch (error) {
      logger.warn('Failed to standardize Domain property', { domainProp, error });
      return null;
    }
  }

  /**
   * Helper methods
   */
  
  private extractPriceValue(priceText: string): number | undefined {
    if (!priceText) return undefined;
    
    // Remove currency symbols and non-numeric characters except decimal points
    const cleanPrice = priceText.replace(/[^\d.]/g, '');
    const price = parseFloat(cleanPrice);
    
    return isNaN(price) ? undefined : price;
  }

  private extractPriceFrequency(priceText: string): 'weekly' | 'monthly' | 'annually' {
    if (!priceText) return 'weekly';
    
    const lowerText = priceText.toLowerCase();
    if (lowerText.includes('month') || lowerText.includes('/m')) return 'monthly';
    if (lowerText.includes('year') || lowerText.includes('annual') || lowerText.includes('/y')) return 'annually';
    return 'weekly'; // Default for Australian rentals
  }

  private extractImages(media: any[]): string[] {
    const images: string[] = [];
    
    if (!Array.isArray(media)) return images;
    
    for (const item of media) {
      if (typeof item === 'string' && this.isValidImageUrl(item)) {
        images.push(this.normalizeImageUrl(item));
      } else if (item && typeof item === 'object') {
        const url = item.url || item.src || item.href;
        if (url && this.isValidImageUrl(url)) {
          images.push(this.normalizeImageUrl(url));
        }
      }
    }
    
    return images;
  }

  private extractFeatures(features: any[]): string[] {
    if (!Array.isArray(features)) return [];
    
    return features
      .map(feature => {
        if (typeof feature === 'string') return feature;
        if (feature && typeof feature === 'object') return feature.name || feature.title || feature.text;
        return null;
      })
      .filter(Boolean);
  }

  private extractInspectionTimes(inspections: any[]): Array<{ date: string; startTime: string; endTime: string }> {
    if (!Array.isArray(inspections)) return [];
    
    return inspections
      .map(inspection => {
        if (inspection && typeof inspection === 'object') {
          return {
            date: inspection.date || '',
            startTime: inspection.startTime || inspection.start || '',
            endTime: inspection.endTime || inspection.end || '',
          };
        }
        return null;
      })
      .filter(Boolean);
  }

  private parseAddressFromText(addressText: string): StandardizedProperty['address'] {
    const parts = addressText.split(',').map(part => part.trim());
    
    return {
      street: parts[0] || '',
      suburb: parts[1] || '',
      state: parts[2]?.split(' ')[0] || '',
      postcode: parts[2]?.split(' ')[1] || '',
      fullAddress: addressText,
    };
  }

  private extractNumber(text: string): number | undefined {
    if (!text) return undefined;
    
    const match = text.match(/\d+/);
    return match ? parseInt(match[0]) : undefined;
  }

  private parseSize(sizeText: string | undefined): number | undefined {
    if (!sizeText) return undefined;
    
    const match = sizeText.match(/[\d,]+/);
    if (!match) return undefined;
    
    return parseFloat(match[0].replace(',', ''));
  }

  private isValidImageUrl(url: string): boolean {
    if (!url || typeof url !== 'string') return false;
    
    // Check for image file extensions
    const imageExtensions = /\.(jpg|jpeg|png|gif|webp|svg)(\?|$)/i;
    if (imageExtensions.test(url)) return true;
    
    // Check for common image hosting patterns
    const imageHostPatterns = [
      /images\.domain\.com\.au/,
      /photos\.domain\.com\.au/,
      /bucket-api\.domain\.com\.au/,
    ];
    
    return imageHostPatterns.some(pattern => pattern.test(url));
  }

  private normalizeImageUrl(url: string): string {
    // Remove query parameters that might break the image
    try {
      const urlObj = new URL(url);
      // Keep only essential query parameters
      const keepParams = ['w', 'h', 'width', 'height', 'quality', 'format'];
      const newSearchParams = new URLSearchParams();
      
      keepParams.forEach(param => {
        if (urlObj.searchParams.has(param)) {
          newSearchParams.set(param, urlObj.searchParams.get(param)!);
        }
      });
      
      urlObj.search = newSearchParams.toString();
      return urlObj.toString();
    } catch {
      return url;
    }
  }
}

export default DataProcessor;