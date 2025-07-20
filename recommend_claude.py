import os
import anthropic
import pandas as pd
from typing import List, Dict, Any


def load_property_data() -> pd.DataFrame:
    """
    加载悉尼房源数据
    
    Returns:
        包含房源数据的 DataFrame
    """
    try:
        df = pd.read_csv('sydney_properties_working_final.csv')
        # 过滤掉价格为空的房源
        df = df[df['price_numeric'].notna()]
        return df
    except FileNotFoundError:
        raise FileNotFoundError("未找到 sydney_properties_working_final.csv 文件")
    except Exception as e:
        raise RuntimeError(f"加载数据文件失败: {str(e)}")


def filter_properties_flexible(df: pd.DataFrame, suburb: str = None, bedrooms: int = None, budget: float = None, 
                             geo_analysis: dict = None, intent_analysis: dict = None) -> pd.DataFrame:
    """
    灵活筛选房源 - 优先匹配所有条件，然后逐步放宽限制
    确保用户需求是推荐结果的子集
    
    Args:
        df: 房源数据
        suburb: 期望区域（可选）
        bedrooms: 卧室数量（可选）
        budget: 预算万澳币（可选）
        
    Returns:
        筛选后的房源数据
    """
    result_df = df.copy()
    
    # 转换预算为澳币
    budget_aud = budget * 10000 if budget else None
    
    # 1. 首先尝试完全匹配所有条件
    if suburb and bedrooms and budget_aud:
        exact_match = df[
            (df['suburb'].str.contains(suburb, case=False, na=False)) &
            (df['bedrooms'] == bedrooms) &
            (df['price_numeric'] <= budget_aud)
        ]
        if len(exact_match) >= 3:
            return exact_match.sort_values('price_numeric').head(10)
    
    # 2. 如果完全匹配结果少于3个，放宽预算限制（+50%）
    if suburb and bedrooms and budget_aud:
        relaxed_budget = budget_aud * 1.5
        budget_relaxed = df[
            (df['suburb'].str.contains(suburb, case=False, na=False)) &
            (df['bedrooms'] == bedrooms) &
            (df['price_numeric'] <= relaxed_budget)
        ]
        if len(budget_relaxed) >= 3:
            return budget_relaxed.sort_values('price_numeric').head(10)
    
    # 3. 只匹配区域和卧室
    if suburb and bedrooms:
        area_bedroom_match = df[
            (df['suburb'].str.contains(suburb, case=False, na=False)) &
            (df['bedrooms'] == bedrooms)
        ]
        if len(area_bedroom_match) >= 3:
            return area_bedroom_match.sort_values('price_numeric').head(10)
    
    # 4. 只匹配区域
    if suburb:
        area_match = df[
            df['suburb'].str.contains(suburb, case=False, na=False)
        ]
        if len(area_match) >= 3:
            return area_match.sort_values('price_numeric').head(10)
    
    # 5. 只匹配卧室数量
    if bedrooms:
        bedroom_match = df[df['bedrooms'] == bedrooms]
        if len(bedroom_match) >= 3:
            return bedroom_match.sort_values('price_numeric').head(10)
    
    # 6. 只匹配预算
    if budget_aud:
        budget_match = df[df['price_numeric'] <= budget_aud]
        if len(budget_match) >= 3:
            return budget_match.sort_values('price_numeric').head(10)
    
    # 7. 使用地理分析结果扩展搜索
    if geo_analysis and geo_analysis.get("location_analysis", {}).get("recommended_areas"):
        recommended_areas = geo_analysis["location_analysis"]["recommended_areas"]
        area_pattern = '|'.join(recommended_areas[:10])  # 使用前10个推荐区域
        geo_match = df[df['suburb'].str.contains(area_pattern, case=False, na=False)]
        
        # 如果有预算限制，应用预算筛选
        if budget_aud:
            geo_match = geo_match[geo_match['price_numeric'] <= budget_aud * 1.5]  # 放宽50%
        
        # 如果有卧室要求，应用卧室筛选
        if bedrooms:
            geo_match = geo_match[geo_match['bedrooms'] == bedrooms]
        
        if len(geo_match) >= 3:
            return geo_match.sort_values('price_numeric').head(10)
    
    # 8. 使用意图分析中的推测卧室数
    if intent_analysis and intent_analysis.get("size_analysis", {}).get("inferred_bedrooms"):
        inferred_bedrooms = intent_analysis["size_analysis"]["inferred_bedrooms"]
        inferred_match = df[df['bedrooms'] == inferred_bedrooms]
        
        if budget_aud:
            inferred_match = inferred_match[inferred_match['price_numeric'] <= budget_aud * 1.5]
        
        if len(inferred_match) >= 3:
            return inferred_match.sort_values('price_numeric').head(10)
    
    # 9. 如果所有条件都匹配不到足够结果，返回所有房源的前10个
    return df.sort_values('price_numeric').head(10)


def explain_recommendation_flexible(preference: str, suburb: str = None, bedrooms: int = None, budget: float = None, 
                                  api_key: str = None, geo_analysis: dict = None, intent_analysis: dict = None) -> List[str]:
    """
    基于悉尼房源数据灵活推荐，用户需求是推荐的子集
    
    Args:
        preference: 用户偏好描述
        suburb: 提取的区域信息
        bedrooms: 提取的卧室数量
        budget: 提取的预算
        api_key: Anthropic API key
        
    Returns:
        包含推荐文本的列表
    """
    # 从参数或环境变量获取 API key
    if not api_key:
        api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("请设置环境变量 ANTHROPIC_API_KEY 或提供 api_key 参数")
    
    # 如果没有提供提取的参数，尝试从preference中解析
    if not any([suburb, bedrooms, budget]):
        import re
        if not suburb:
            suburb_match = re.search(r'在(.+?)买|在(.+?)找|(.+?)区域|(.+?)附近', preference)
            if suburb_match:
                suburb = next(group for group in suburb_match.groups() if group)
        
        if not bedrooms:
            bedrooms_match = re.search(r'(\d+)室|(\d+)房|(\d+)个卧室', preference)
            if bedrooms_match:
                bedrooms = int(next(group for group in bedrooms_match.groups() if group))
        
        if not budget:
            budget_match = re.search(r'预算(\d+)万|(\d+)万以内|最多(\d+)万', preference)
            if budget_match:
                budget = float(next(group for group in budget_match.groups() if group))
    
    # 加载和筛选房源数据 - 使用灵活筛选
    df = load_property_data()
    filtered_properties = filter_properties_flexible(df, suburb, bedrooms, budget, geo_analysis, intent_analysis)
    
    # 构建用户需求描述
    user_requirements = []
    if suburb:
        user_requirements.append(f"区域：{suburb}")
    if bedrooms:
        user_requirements.append(f"卧室：{bedrooms}室")
    if budget:
        user_requirements.append(f"预算：{budget}万澳币以内")
    
    requirements_text = "、".join(user_requirements) if user_requirements else "任意条件"
    
    # 准备房源数据给 Claude
    properties_info = []
    for _, prop in filtered_properties.iterrows():
        properties_info.append(f"""
地址: {prop['address']}
价格: {prop['price']}
卧室: {prop['bedrooms']}室
浴室: {prop['bathrooms']}浴
停车: {prop['parking']}个车位
类型: {prop['property_type']}
链接: {prop['link']}
""")
    
    properties_text = "\n".join(properties_info)
    
    # 初始化 Claude 客户端
    client = anthropic.Anthropic(api_key=api_key)
    
    # 构建增强的提示词
    additional_context = ""
    
    # 添加地理分析结果
    if geo_analysis:
        location_analysis = geo_analysis.get("location_analysis", {})
        if location_analysis.get("distance_preference"):
            additional_context += f"\n📍 地理位置偏好：{location_analysis['distance_preference']}离市中心"
        if location_analysis.get("area_characteristics"):
            additional_context += f"\n🌟 区域特征偏好：{', '.join(location_analysis['area_characteristics'])}"
    
    # 添加意图分析结果
    if intent_analysis:
        size_analysis = intent_analysis.get("size_analysis", {})
        if size_analysis.get("size_preference"):
            additional_context += f"\n📐 房屋大小偏好：{size_analysis['size_preference']}"
        if size_analysis.get("inferred_bedrooms"):
            additional_context += f"\n🛏️ AI推测卧室需求：{size_analysis['inferred_bedrooms']}室"
    
    prompt = f"""你是一位专业的房产推荐顾问，请基于深度需求分析为用户提供个性化推荐。

用户原始需求：{preference}
提取的明确需求：{requirements_text}

🧠 AI深度分析结果：{additional_context}

🏠 匹配的悉尼房源数据（{len(filtered_properties)}套房源）：
{properties_text}

请基于以下原则提供推荐：

1. **智能匹配**：
   - 优先匹配用户明确需求
   - 考虑AI推测的隐含需求
   - 结合地理位置偏好和区域特征

2. **个性化推荐理由**：
   - 解释为什么这个房源适合用户
   - 结合用户的口语化表达（如"大一点的"、"离市区远"）
   - 说明房源如何满足用户的生活方式需求

3. **全面考虑**：
   - 如果用户要求"离市区远"，重点推荐外环区域的性价比房源
   - 如果用户要求"大一点的"，重点推荐空间较大的房源
   - 如果用户要求"安静"，重点推荐住宅区而非商业区

请提供3-5条推荐，格式：
推荐1：[具体房源地址 - 价格] - [个性化推荐理由，说明如何满足用户的具体需求]
推荐2：[具体房源地址 - 价格] - [个性化推荐理由，说明如何满足用户的具体需求]
推荐3：[具体房源地址 - 价格] - [个性化推荐理由，说明如何满足用户的具体需求]
（如有更多优质选择可继续）"""
    
    try:
        # 调用 Claude API
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # 解析响应文本
        content = response.content[0].text
        
        # 提取推荐内容
        recommendations = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('推荐1：'):
                recommendations.append(line[4:])
            elif line.startswith('推荐2：'):
                recommendations.append(line[4:])
            elif line.startswith('推荐3：'):
                recommendations.append(line[4:])
            elif line.startswith('推荐4：'):
                recommendations.append(line[4:])
            elif line.startswith('推荐5：'):
                recommendations.append(line[4:])
        
        # 返回推荐结果（3-5条）
        if len(recommendations) == 0:
            # 如果解析失败，返回原始内容的有效行
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            recommendations = lines[:5] if len(lines) >= 5 else lines
            
        return recommendations
        
    except Exception as e:
        raise RuntimeError(f"调用 Claude API 失败: {str(e)}")


if __name__ == "__main__":
    # 示例用法
    try:
        preference = "我喜欢安静的环境，预算在100万以内，希望找到靠近学校的房子"
        recommendations = explain_recommendation_flexible(preference)
        
        print("基于您的偏好，我们推荐：")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
            
    except Exception as e:
        print(f"错误: {e}")