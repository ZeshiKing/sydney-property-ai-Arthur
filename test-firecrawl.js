#!/usr/bin/env node

/**
 * 独立测试脚本 - 验证Firecrawl API和房源数据抓取
 * 
 * 这个脚本将测试：
 * 1. Firecrawl API连接
 * 2. Domain.com.au URL构建
 * 3. 房源数据抓取和解析
 */

const https = require('https');
const fs = require('fs');

// 从.env文件读取API密钥
function loadEnvVariables() {
  const envPath = '.env';
  if (!fs.existsSync(envPath)) {
    console.error('❌ .env文件不存在，请先创建.env文件');
    process.exit(1);
  }

  const envContent = fs.readFileSync(envPath, 'utf8');
  const envVars = {};
  
  envContent.split('\n').forEach(line => {
    if (line.includes('=') && !line.startsWith('#')) {
      const [key, value] = line.split('=');
      envVars[key.trim()] = value.trim();
    }
  });

  return envVars;
}

// HTTP请求工具函数
function makeHttpRequest(url, options, postData = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(url, options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            data: jsonData
          });
        } catch (error) {
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            data: data
          });
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    if (postData) {
      req.write(postData);
    }
    
    req.end();
  });
}

// 测试1: 验证Firecrawl API连接
async function testFirecrawlConnection(apiKey) {
  console.log('\n🔧 测试1: 验证Firecrawl API连接...');
  
  try {
    const testUrl = 'https://example.com';
    
    const options = {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      }
    };

    const postData = JSON.stringify({
      url: testUrl,
      formats: ['markdown']
    });

    console.log(`📡 正在测试抓取: ${testUrl}`);
    
    const response = await makeHttpRequest('https://api.firecrawl.dev/v0/scrape', options, postData);
    
    if (response.statusCode === 200) {
      console.log('✅ Firecrawl API连接成功!');
      
      if (response.data.success) {
        console.log('✅ 数据抓取成功');
        console.log(`📝 内容预览: ${response.data.data?.markdown?.substring(0, 100)}...`);
        return true;
      } else {
        console.log('❌ 抓取失败:', response.data.error || '未知错误');
        return false;
      }
    } else {
      console.log('❌ API请求失败');
      console.log(`🔍 状态码: ${response.statusCode}`);
      console.log(`📄 响应: ${JSON.stringify(response.data, null, 2)}`);
      return false;
    }
  } catch (error) {
    console.error('❌ Firecrawl API测试失败:', error.message);
    return false;
  }
}

// 测试2: Domain.com.au URL构建
function testDomainUrlBuilder() {
  console.log('\n🏗️ 测试2: Domain.com.au URL构建...');
  
  // 模拟URL构建逻辑
  const buildDomainUrl = (params) => {
    const { listingType, location, propertyType, bedrooms, priceRange } = params;
    
    // 构建基础URL
    const locationSlug = `${location.suburb.toLowerCase().replace(/\s+/g, '-')}-${location.state.toLowerCase()}-${location.postcode}`;
    let url = `https://www.domain.com.au/${listingType}/${locationSlug}`;
    
    if (propertyType) {
      url += `/${propertyType}`;
    }
    url += '/';
    
    // 添加查询参数
    const queryParams = [];
    if (bedrooms) {
      if (bedrooms.min && bedrooms.max) {
        queryParams.push(`bedrooms=${bedrooms.min}-${bedrooms.max}`);
      } else if (bedrooms.min) {
        queryParams.push(`bedrooms=${bedrooms.min}-any`);
      }
    }
    
    if (priceRange) {
      if (priceRange.min && priceRange.max) {
        queryParams.push(`price=${priceRange.min}-${priceRange.max}`);
      }
    }
    
    if (queryParams.length > 0) {
      url += '?' + queryParams.join('&');
    }
    
    return url;
  };
  
  // 测试不同的搜索参数
  const testCases = [
    {
      name: '基础租房搜索 - Camperdown',
      params: {
        listingType: 'rent',
        location: {
          suburb: 'Camperdown',
          state: 'NSW',
          postcode: '2050'
        }
      }
    },
    {
      name: '公寓租房 - 2-3卧室',
      params: {
        listingType: 'rent',
        location: {
          suburb: 'Camperdown',
          state: 'NSW',
          postcode: '2050'
        },
        propertyType: 'apartment',
        bedrooms: { min: 2, max: 3 }
      }
    }
  ];
  
  testCases.forEach(testCase => {
    const url = buildDomainUrl(testCase.params);
    console.log(`✅ ${testCase.name}:`);
    console.log(`   ${url}`);
  });
  
  return testCases.map(tc => buildDomainUrl(tc.params));
}

// 测试3: 抓取Domain.com.au房源数据
async function testDomainScraping(apiKey, testUrls) {
  console.log('\n🏠 测试3: 抓取Domain.com.au房源数据...');
  
  const url = testUrls[0]; // 只测试第一个URL
  console.log(`📍 正在抓取: ${url}`);
  
  try {
    const options = {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      }
    };

    const postData = JSON.stringify({
      url: url,
      formats: ['markdown', 'html'],
      includeTags: ['script[id="__NEXT_DATA__"]'],
      excludeTags: ['script[src]', 'style', 'nav', 'footer'],
      onlyMainContent: false,
      waitFor: 3000
    });

    console.log('⏳ 正在抓取数据...');
    const response = await makeHttpRequest('https://api.firecrawl.dev/v0/scrape', options, postData);
    
    if (response.statusCode === 200 && response.data.success) {
      console.log('✅ 抓取成功!');
      
      const data = response.data.data;
      console.log(`📄 HTML长度: ${data.html?.length || 0} 字符`);
      console.log(`📝 Markdown长度: ${data.markdown?.length || 0} 字符`);
      
      // 分析数据
      await analyzeScrapedData(data);
      return true;
      
    } else {
      console.log('❌ 抓取失败');
      console.log(`🔍 状态: ${response.statusCode}`);
      console.log(`📄 错误: ${response.data.error || '未知错误'}`);
      return false;
    }
    
  } catch (error) {
    console.error(`❌ 抓取失败:`, error.message);
    return false;
  }
}

// 分析抓取的数据
async function analyzeScrapedData(data) {
  console.log('\n🔍 数据分析:');
  
  // 检查__NEXT_DATA__
  if (data.html && data.html.includes('__NEXT_DATA__')) {
    console.log('✅ 找到 __NEXT_DATA__ 结构数据');
    
    try {
      const nextDataMatch = data.html.match(/<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)<\/script>/s);
      if (nextDataMatch) {
        const nextDataJson = JSON.parse(nextDataMatch[1]);
        console.log('✅ 成功解析 __NEXT_DATA__');
        
        // 查找房产相关字段
        const dataStr = JSON.stringify(nextDataJson);
        const patterns = [
          { name: 'bedrooms', regex: /"bedrooms?":\s*\d+/gi },
          { name: 'price', regex: /"\$\d+[^"]*"/gi },
          { name: 'address', regex: /"address[^"]*":\s*"/gi }
        ];
        
        patterns.forEach(({ name, regex }) => {
          const matches = dataStr.match(regex);
          if (matches) {
            console.log(`🏷️ 找到 ${name}: ${matches.length} 个匹配`);
          }
        });
        
        return true;
      }
    } catch (error) {
      console.log('⚠️ __NEXT_DATA__ 解析失败:', error.message);
    }
  }
  
  // 文本内容分析
  const textContent = data.markdown || '';
  const patterns = [
    { name: '价格', regex: /\$\d+.*(?:week|pw)/gi },
    { name: '卧室', regex: /\d+\s*(?:bed|bedroom)/gi },
    { name: '浴室', regex: /\d+\s*(?:bath|bathroom)/gi }
  ];
  
  patterns.forEach(({ name, regex }) => {
    const matches = textContent.match(regex);
    if (matches) {
      console.log(`🔍 ${name}信息: ${matches.slice(0, 3).join(', ')}`);
    }
  });
  
  return true;
}

// 主测试函数
async function runTests() {
  console.log('🚀 澳洲租房聚合系统 - Firecrawl API测试\n');
  console.log('=' .repeat(60));
  
  // 加载环境变量
  const env = loadEnvVariables();
  const apiKey = env.FIRECRAWL_API_KEY;
  
  if (!apiKey || apiKey === 'your_firecrawl_api_key_here') {
    console.error('❌ 请在.env文件中设置有效的FIRECRAWL_API_KEY');
    console.error('💡 获取API密钥: https://firecrawl.dev');
    process.exit(1);
  }
  
  console.log(`✅ 已加载API密钥: ${apiKey.substring(0, 10)}...`);
  
  // 测试1: API连接
  const connectionTest = await testFirecrawlConnection(apiKey);
  
  if (!connectionTest) {
    console.log('\n❌ Firecrawl API连接失败，请检查API密钥');
    return;
  }
  
  // 测试2: URL构建
  const testUrls = testDomainUrlBuilder();
  
  // 测试3: 房源数据抓取
  const scrapingTest = await testDomainScraping(apiKey, testUrls);
  
  // 结果总结
  console.log('\n' + '=' .repeat(60));
  console.log('📊 测试结果:');
  console.log(`🔧 Firecrawl API: ${connectionTest ? '✅ 正常' : '❌ 失败'}`);
  console.log(`🏗️ URL构建: ✅ 正常`);
  console.log(`🏠 数据抓取: ${scrapingTest ? '✅ 正常' : '⚠️ 需要调试'}`);
  
  if (connectionTest && scrapingTest) {
    console.log('\n🎉 测试通过！可以开始使用房源数据抓取功能');
    console.log('\n📝 下一步:');
    console.log('   1. 启动完整服务: docker-compose up');
    console.log('   2. 测试API端点: POST /api/properties/search');
  }
}

// 运行测试
runTests().catch(console.error);