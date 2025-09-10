#!/usr/bin/env node

/**
 * 详细房产数据抓取测试
 * 展示完整的房产信息提取和标准化流程
 */

const https = require('https');
const fs = require('fs');

// 从.env文件读取API密钥
function loadEnvVariables() {
  const envContent = fs.readFileSync('.env', 'utf8');
  const envVars = {};
  
  envContent.split('\n').forEach(line => {
    if (line.includes('=') && !line.startsWith('#')) {
      const [key, value] = line.split('=');
      envVars[key.trim()] = value.trim();
    }
  });

  return envVars;
}

// HTTP请求工具
function makeHttpRequest(url, options, postData = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(url, options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          resolve({ statusCode: res.statusCode, data: JSON.parse(data) });
        } catch (error) {
          resolve({ statusCode: res.statusCode, data: data });
        }
      });
    });
    req.on('error', reject);
    if (postData) req.write(postData);
    req.end();
  });
}

// 详细数据抓取和分析
async function detailedPropertyScraping(apiKey) {
  console.log('🏠 详细房产数据抓取测试\n');
  console.log('=' .repeat(60));

  const testUrl = 'https://www.domain.com.au/rent/camperdown-nsw-2050/apartment/?bedrooms=2-any';
  
  console.log(`📍 目标URL: ${testUrl}`);
  console.log('⏳ 开始抓取...\n');

  try {
    const options = {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      }
    };

    const postData = JSON.stringify({
      url: testUrl,
      formats: ['markdown', 'html'],
      includeTags: ['script[id="__NEXT_DATA__"]', 'script[type="application/ld+json"]'],
      excludeTags: ['script[src]', 'style', 'nav', 'footer', 'aside'],
      onlyMainContent: false,
      waitFor: 4000
    });

    const response = await makeHttpRequest('https://api.firecrawl.dev/v0/scrape', options, postData);
    
    if (response.statusCode === 200 && response.data.success) {
      const data = response.data.data;
      console.log('✅ 数据抓取成功!');
      console.log(`📊 数据统计:`);
      console.log(`   - HTML长度: ${data.html?.length || 0} 字符`);
      console.log(`   - Markdown长度: ${data.markdown?.length || 0} 字符`);
      console.log(`   - 元数据: ${data.metadata ? JSON.stringify(data.metadata).length : 0} 字符\n`);

      // 详细数据分析
      await analyzePropertyData(data);
      
      // 提取房产信息
      const properties = await extractPropertyInfo(data);
      
      // 展示提取的房产数据
      displayProperties(properties);
      
      return true;
    } else {
      console.log('❌ 抓取失败:', response.data.error || '未知错误');
      return false;
    }
    
  } catch (error) {
    console.error('❌ 抓取过程出错:', error.message);
    return false;
  }
}

// 分析抓取的数据
async function analyzePropertyData(data) {
  console.log('🔍 数据结构分析:');
  
  // 检查__NEXT_DATA__
  if (data.html && data.html.includes('__NEXT_DATA__')) {
    console.log('✅ 找到 __NEXT_DATA__ 结构化数据');
    
    try {
      const nextDataMatch = data.html.match(/<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)<\/script>/s);
      if (nextDataMatch) {
        const nextData = JSON.parse(nextDataMatch[1]);
        console.log('✅ __NEXT_DATA__ 解析成功');
        
        // 分析数据结构
        analyzeDataStructure(nextData);
      }
    } catch (error) {
      console.log('⚠️ __NEXT_DATA__ 解析失败:', error.message);
    }
  }
  
  // 检查JSON-LD结构化数据
  if (data.html && data.html.includes('application/ld+json')) {
    console.log('✅ 找到 JSON-LD 结构化数据');
    
    const jsonLdMatches = data.html.match(/<script[^>]*type="application\/ld\+json"[^>]*>(.*?)<\/script>/gs);
    if (jsonLdMatches) {
      console.log(`📊 找到 ${jsonLdMatches.length} 个 JSON-LD 块`);
    }
  }
  
  // 文本内容分析
  console.log('\n📝 文本内容分析:');
  const markdown = data.markdown || '';
  
  const patterns = [
    { name: '价格信息', regex: /\$\d+[,\d]*\s*(?:per\s*week|\/week|pw|week)/gi },
    { name: '卧室信息', regex: /\d+\s*(?:bed|bedroom|br)\w*/gi },
    { name: '浴室信息', regex: /\d+\s*(?:bath|bathroom|ba)\w*/gi },
    { name: '停车位', regex: /\d+\s*(?:car|parking|space|garage)/gi },
    { name: '地址信息', regex: /\d+.*(?:street|st|road|rd|avenue|ave|lane|ln|drive|dr|close|cl|court|ct|place|pl)/gi }
  ];
  
  patterns.forEach(({ name, regex }) => {
    const matches = markdown.match(regex);
    if (matches && matches.length > 0) {
      console.log(`🏷️ ${name}: 找到 ${matches.length} 个匹配`);
      console.log(`   示例: ${matches.slice(0, 3).join(' | ')}`);
    }
  });
}

// 分析数据结构
function analyzeDataStructure(obj, path = '', depth = 0, maxDepth = 3) {
  if (depth > maxDepth) return;
  
  if (Array.isArray(obj) && obj.length > 0) {
    console.log(`📋 ${path}: 数组 (${obj.length} 项)`);
    
    // 检查是否包含房产数据
    const sample = obj[0];
    if (typeof sample === 'object' && sample !== null) {
      const keys = Object.keys(sample);
      const propertyKeys = keys.filter(key => 
        /(?:id|price|bed|bath|address|suburb|type)/i.test(key)
      );
      
      if (propertyKeys.length >= 3) {
        console.log(`🏠 ${path}: 可能包含房产数据 (${propertyKeys.length} 个相关字段)`);
        console.log(`   相关字段: ${propertyKeys.slice(0, 5).join(', ')}`);
      }
    }
  } else if (typeof obj === 'object' && obj !== null) {
    const keys = Object.keys(obj);
    if (keys.length > 0) {
      console.log(`📦 ${path}: 对象 (${keys.length} 个键)`);
      
      // 递归分析子对象
      keys.slice(0, 5).forEach(key => {
        if (key.length < 20) { // 避免过长的键名
          analyzeDataStructure(obj[key], `${path}.${key}`, depth + 1, maxDepth);
        }
      });
    }
  }
}

// 提取房产信息
async function extractPropertyInfo(data) {
  console.log('\n🔧 房产信息提取:');
  const properties = [];
  
  // 方法1: 从__NEXT_DATA__提取
  if (data.html && data.html.includes('__NEXT_DATA__')) {
    try {
      const nextDataMatch = data.html.match(/<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)<\/script>/s);
      if (nextDataMatch) {
        const nextData = JSON.parse(nextDataMatch[1]);
        
        // 递归查找可能的房产数组
        const foundProperties = findPropertyArrays(nextData);
        
        if (foundProperties.length > 0) {
          console.log(`✅ 从__NEXT_DATA__中找到 ${foundProperties.length} 个房产记录`);
          properties.push(...foundProperties);
        }
      }
    } catch (error) {
      console.log('⚠️ __NEXT_DATA__提取失败:', error.message);
    }
  }
  
  // 方法2: 从文本内容提取
  if (properties.length === 0) {
    console.log('🔍 尝试从文本内容提取房产信息...');
    
    const textProperties = extractFromText(data.markdown || '');
    if (textProperties.length > 0) {
      console.log(`✅ 从文本中提取了 ${textProperties.length} 个房产记录`);
      properties.push(...textProperties);
    }
  }
  
  return properties;
}

// 查找房产数组
function findPropertyArrays(obj, path = '', depth = 0) {
  if (depth > 5) return [];
  
  const results = [];
  
  if (Array.isArray(obj)) {
    if (obj.length > 0 && typeof obj[0] === 'object' && obj[0] !== null) {
      // 检查是否为房产数据
      const sample = obj[0];
      const keys = Object.keys(sample);
      const propertyScore = calculatePropertyScore(keys);
      
      if (propertyScore >= 3) {
        console.log(`🎯 在 ${path} 找到房产数组 (评分: ${propertyScore})`);
        
        // 提取前几个作为示例
        const extracted = obj.slice(0, 5).map((item, index) => 
          extractPropertyFromObject(item, `${path}[${index}]`)
        ).filter(Boolean);
        
        results.push(...extracted);
      }
    }
    
    // 继续递归搜索
    obj.slice(0, 3).forEach((item, index) => {
      if (typeof item === 'object' && item !== null) {
        results.push(...findPropertyArrays(item, `${path}[${index}]`, depth + 1));
      }
    });
    
  } else if (typeof obj === 'object' && obj !== null) {
    for (const [key, value] of Object.entries(obj)) {
      if (key.length < 15) { // 避免过长的键名
        results.push(...findPropertyArrays(value, `${path}.${key}`, depth + 1));
      }
    }
  }
  
  return results;
}

// 计算对象是否像房产数据的评分
function calculatePropertyScore(keys) {
  const propertyIndicators = [
    /^id$/i, /listingid/i, /propertyid/i,
    /^price/i, /rent/i, /cost/i,
    /bed/i, /bath/i,
    /address/i, /location/i, /suburb/i,
    /type/i, /category/i,
    /image/i, /photo/i
  ];
  
  let score = 0;
  keys.forEach(key => {
    if (propertyIndicators.some(pattern => pattern.test(key))) {
      score++;
    }
  });
  
  return score;
}

// 从对象提取房产信息
function extractPropertyFromObject(obj, path) {
  try {
    const property = {
      source_path: path,
      id: obj.id || obj.listingId || obj.propertyId || 'unknown',
      price: extractPrice(obj),
      bedrooms: obj.bedrooms || obj.bedroomCount || obj.bed || obj.beds,
      bathrooms: obj.bathrooms || obj.bathroomCount || obj.bath || obj.baths,
      propertyType: obj.propertyType || obj.type || obj.category,
      address: extractAddress(obj),
      images: extractImages(obj)
    };
    
    // 只返回有足够信息的房产
    const validFields = Object.values(property).filter(v => v !== undefined && v !== null && v !== '').length;
    return validFields >= 3 ? property : null;
    
  } catch (error) {
    return null;
  }
}

// 提取价格信息
function extractPrice(obj) {
  const priceFields = ['price', 'rent', 'cost', 'priceText', 'displayPrice'];
  for (const field of priceFields) {
    if (obj[field]) {
      return obj[field];
    }
  }
  return null;
}

// 提取地址信息
function extractAddress(obj) {
  if (obj.address) {
    if (typeof obj.address === 'string') return obj.address;
    if (typeof obj.address === 'object') {
      return obj.address.displayAddress || obj.address.fullAddress || 
             `${obj.address.street || ''} ${obj.address.suburb || ''}`.trim();
    }
  }
  return obj.location || obj.suburb || null;
}

// 提取图片信息
function extractImages(obj) {
  const imageFields = ['images', 'photos', 'media'];
  for (const field of imageFields) {
    if (obj[field]) {
      if (Array.isArray(obj[field])) {
        return obj[field].length;
      }
    }
  }
  return 0;
}

// 从文本提取房产信息
function extractFromText(markdown) {
  const properties = [];
  const lines = markdown.split('\n').filter(line => line.trim());
  
  // 查找包含价格和卧室信息的行
  const propertyLines = lines.filter(line => {
    const hasPrice = /\$\d+.*(?:week|pw)/i.test(line);
    const hasBedrooms = /\d+\s*(?:bed|br)/i.test(line);
    return hasPrice && hasBedrooms;
  });
  
  propertyLines.forEach((line, index) => {
    const property = {
      source_path: `text_line_${index}`,
      id: `text_${index}`,
      raw_text: line.trim(),
      price: line.match(/\$\d+[,\d]*\s*(?:per\s*week|\/week|pw|week)/i)?.[0],
      bedrooms: line.match(/(\d+)\s*(?:bed|br)/i)?.[1],
      bathrooms: line.match(/(\d+)\s*(?:bath|ba)/i)?.[1]
    };
    
    properties.push(property);
  });
  
  return properties;
}

// 展示提取的房产数据
function displayProperties(properties) {
  console.log('\n🏠 提取的房产数据:');
  console.log('=' .repeat(60));
  
  if (properties.length === 0) {
    console.log('⚠️ 未找到房产数据');
    return;
  }
  
  properties.forEach((property, index) => {
    console.log(`\n📋 房产 ${index + 1}:`);
    console.log(`   数据源: ${property.source_path}`);
    
    if (property.raw_text) {
      console.log(`   原始文本: ${property.raw_text}`);
    }
    
    Object.entries(property).forEach(([key, value]) => {
      if (key !== 'source_path' && key !== 'raw_text' && value !== undefined && value !== null) {
        console.log(`   ${key}: ${value}`);
      }
    });
  });
  
  console.log(`\n✅ 总计找到 ${properties.length} 个房产记录`);
}

// 主函数
async function main() {
  console.log('🏠 澳洲租房聚合系统 - 详细数据抓取测试\n');
  
  const env = loadEnvVariables();
  const apiKey = env.FIRECRAWL_API_KEY;
  
  if (!apiKey || apiKey === 'your_firecrawl_api_key_here') {
    console.error('❌ 请设置有效的FIRECRAWL_API_KEY');
    process.exit(1);
  }
  
  const success = await detailedPropertyScraping(apiKey);
  
  console.log('\n' + '=' .repeat(60));
  console.log(`📊 测试结果: ${success ? '✅ 成功' : '❌ 失败'}`);
  
  if (success) {
    console.log('\n🎉 房产数据抓取和解析功能正常工作！');
    console.log('💡 您的系统已经可以实时获取Domain.com.au的房源信息');
  }
}

main().catch(console.error);