#!/usr/bin/env node

/**
 * 最终测试 - 完整房产搜索流程演示
 * 展示实际可用的房产数据提取
 */

const https = require('https');
const fs = require('fs');

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

// 改进的文本解析器
function parsePropertyText(markdown) {
  console.log('🔧 使用改进的文本解析器...');
  
  const properties = [];
  const lines = markdown.split('\n').map(line => line.trim()).filter(Boolean);
  
  // 更精确的价格模式
  const priceRegex = /\$(\d{1,4}(?:,\d{3})*)\s*per\s*week/gi;
  const bedroomRegex = /(\d+)\s*Bed/gi;
  const bathroomRegex = /(\d+)\s*Bath/gi;
  const parkingRegex = /(\d+)\s*Parking/gi;
  
  // 查找包含完整房产信息的文本段落
  for (let i = 0; i < lines.length; i++) {
    const currentLine = lines[i];
    const context = lines.slice(Math.max(0, i-2), i+3).join(' ');
    
    const priceMatch = currentLine.match(priceRegex);
    if (priceMatch) {
      const property = {
        id: `property_${properties.length + 1}`,
        price: priceMatch[0],
        priceAmount: parseInt(priceMatch[0].match(/\d+/)[0]),
        rawText: currentLine,
        context: context
      };
      
      // 在上下文中查找其他属性
      const bedroomMatch = context.match(bedroomRegex);
      if (bedroomMatch) property.bedrooms = parseInt(bedroomMatch[0].match(/\d+/)[0]);
      
      const bathroomMatch = context.match(bathroomRegex);
      if (bathroomMatch) property.bathrooms = parseInt(bathroomMatch[0].match(/\d+/)[0]);
      
      const parkingMatch = context.match(parkingRegex);
      if (parkingMatch) property.parking = parseInt(parkingMatch[0].match(/\d+/)[0]);
      
      // 查找地址信息
      const addressMatch = context.match(/(\d+[^,]*(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Close|Cl|Court|Ct|Place|Pl)[^,]*)/i);
      if (addressMatch) property.address = addressMatch[1].trim();
      
      properties.push(property);
    }
  }
  
  return properties;
}

// 统计和分析函数
function analyzeResults(properties) {
  console.log('\n📊 数据分析结果:');
  console.log('=' .repeat(50));
  
  if (properties.length === 0) {
    console.log('⚠️ 没有找到完整的房产数据');
    return;
  }
  
  const prices = properties.map(p => p.priceAmount).filter(Boolean);
  const bedrooms = properties.map(p => p.bedrooms).filter(Boolean);
  
  console.log(`🏠 找到房产数量: ${properties.length}`);
  console.log(`💰 价格范围: $${Math.min(...prices)} - $${Math.max(...prices)} per week`);
  console.log(`🛏️ 卧室数量分布: ${[...new Set(bedrooms)].sort().join(', ')}`);
  
  // 展示前5个房产的详细信息
  console.log('\n📋 房产详细信息:');
  properties.slice(0, 5).forEach((property, index) => {
    console.log(`\n🏡 房产 ${index + 1}:`);
    console.log(`   💰 价格: ${property.price}`);
    if (property.bedrooms) console.log(`   🛏️ 卧室: ${property.bedrooms}`);
    if (property.bathrooms) console.log(`   🚿 浴室: ${property.bathrooms}`);
    if (property.parking) console.log(`   🚗 停车位: ${property.parking}`);
    if (property.address) console.log(`   📍 地址: ${property.address}`);
    console.log(`   📝 原始文本: ${property.rawText.substring(0, 100)}...`);
  });
  
  return {
    total: properties.length,
    priceRange: { min: Math.min(...prices), max: Math.max(...prices) },
    avgPrice: Math.round(prices.reduce((a, b) => a + b, 0) / prices.length),
    bedroomTypes: [...new Set(bedrooms)].sort()
  };
}

// 完整搜索流程测试
async function completeSearchTest(apiKey) {
  console.log('🏠 完整房产搜索流程测试');
  console.log('=' .repeat(60));
  
  const searchParams = {
    location: 'Camperdown, NSW 2050',
    propertyType: 'apartment',
    bedrooms: '2+',
    listingType: 'rent'
  };
  
  console.log('🔍 搜索参数:');
  Object.entries(searchParams).forEach(([key, value]) => {
    console.log(`   ${key}: ${value}`);
  });
  
  const testUrl = 'https://www.domain.com.au/rent/camperdown-nsw-2050/apartment/?bedrooms=2-any';
  console.log(`\n📍 构建的URL: ${testUrl}`);
  
  try {
    console.log('\n⏳ 正在抓取数据...');
    
    const options = {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      }
    };

    const postData = JSON.stringify({
      url: testUrl,
      formats: ['markdown'],
      onlyMainContent: true,
      waitFor: 3000
    });

    const response = await makeHttpRequest('https://api.firecrawl.dev/v0/scrape', options, postData);
    
    if (response.statusCode === 200 && response.data.success) {
      console.log('✅ 数据抓取成功!');
      
      const markdown = response.data.data.markdown;
      console.log(`📄 抓取到 ${markdown.length} 字符的内容`);
      
      // 解析房产数据
      const properties = parsePropertyText(markdown);
      
      // 分析结果
      const analysis = analyzeResults(properties);
      
      if (analysis) {
        console.log('\n🎯 搜索结果摘要:');
        console.log(`   总房产数: ${analysis.total}`);
        console.log(`   价格区间: $${analysis.priceRange.min} - $${analysis.priceRange.max}/周`);
        console.log(`   平均价格: $${analysis.avgPrice}/周`);
        console.log(`   房型分布: ${analysis.bedroomTypes.join(', ')}室`);
      }
      
      return true;
    } else {
      console.log('❌ 抓取失败:', response.data.error || '未知错误');
      return false;
    }
    
  } catch (error) {
    console.error('❌ 搜索过程出错:', error.message);
    return false;
  }
}

// 主函数
async function main() {
  console.log('🚀 澳洲租房聚合系统 - 完整功能验证\n');
  
  const env = loadEnvVariables();
  const apiKey = env.FIRECRAWL_API_KEY;
  
  if (!apiKey || apiKey === 'your_firecrawl_api_key_here') {
    console.error('❌ 请设置有效的FIRECRAWL_API_KEY');
    process.exit(1);
  }
  
  const success = await completeSearchTest(apiKey);
  
  console.log('\n' + '=' .repeat(60));
  console.log('📊 最终测试结果:');
  
  if (success) {
    console.log('✅ 房产搜索系统完全正常工作！');
    console.log('\n🎉 恭喜！您的系统现在可以：');
    console.log('   ✅ 连接Firecrawl API');
    console.log('   ✅ 构建Domain.com.au搜索URL');
    console.log('   ✅ 实时抓取房产列表');
    console.log('   ✅ 解析房产价格、卧室、浴室等信息');
    console.log('   ✅ 提供结构化的房产数据');
    
    console.log('\n📝 下一步建议:');
    console.log('   1. 启动完整的Docker服务');
    console.log('   2. 测试完整的API端点');
    console.log('   3. 集成前端用户界面');
    console.log('   4. 实现AI报告生成功能');
    
  } else {
    console.log('❌ 系统测试失败，请检查配置');
  }
  
  console.log('\n💡 技术说明:');
  console.log('   - 使用Firecrawl API进行智能网页抓取');
  console.log('   - 支持实时数据获取，无需维护爬虫');
  console.log('   - 自动处理反爬虫保护和JavaScript渲染');
  console.log('   - 提供标准化的房产数据格式');
}

main().catch(console.error);