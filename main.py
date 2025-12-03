import os
import json
import re
import feedparser
import google.generativeai as genai
from datetime import datetime

# ================= 配置区 =================
api_key = os.environ.get("GOOGLE_API_KEY")

# ================= 1. 动态获取模型 =================
def get_best_model():
    if not api_key: return None
    genai.configure(api_key=api_key)
    try:
        model_list = list(genai.list_models())
        supported_models = [m.name for m in model_list if 'generateContent' in m.supported_generation_methods]
        for name in supported_models:
            if 'flash' in name.lower(): return genai.GenerativeModel(name)
        for name in supported_models:
            if 'pro' in name.lower(): return genai.GenerativeModel(name)
        if supported_models: return genai.GenerativeModel(supported_models[0])
    except: return None
    return None

# ================= 2. 深度数据采集 =================
def get_data():
    print("🚀 开始全网情报挖掘...")
    data_list = [] # 这一次我们用列表存储，方便处理
    
    # 1. Google Trends
    try:
        feed = feedparser.parse("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US")
        print(f"📊 Google Trends 抓取到 {len(feed.entries)} 条")
        for entry in feed.entries[:12]:
            traffic = getattr(entry, 'ht_approx_traffic', 'N/A')
            # 构造原始数据块
            data_list.append({
                "source": "Google Trends",
                "title": entry.title,
                "link": getattr(entry, 'link', '#'),
                "raw_content": f"Traffic: {traffic}\nNews Snippet: {entry.description}"
            })
    except Exception as e:
        print(f"⚠️ Google 跳过: {e}")

    # 2. Reddit
    reddit_feeds = [
        ("r/Entrepreneur", "https://www.reddit.com/r/Entrepreneur/top/.rss?t=day"), 
        ("r/SideProject", "https://www.reddit.com/r/SideProject/top/.rss?t=day"),   
        ("r/technology", "https://www.reddit.com/r/technology/top/.rss?t=day"),     
        ("r/popular", "https://www.reddit.com/r/popular/top/.rss?t=day"),           
    ]

    for source_name, url in reddit_feeds:
        try:
            print(f"💎 正在挖掘 {source_name}...")
            feed = feedparser.parse(url, agent="Mozilla/5.0")
            for entry in feed.entries[:6]: 
                # 提取正文
                raw_txt = "No text content."
                if hasattr(entry, 'content'):
                    raw_txt = entry.content[0].value[:1500] # 抓更多
                elif hasattr(entry, 'summary'):
                    raw_txt = entry.summary[:1500]
                
                # 清洗 HTML 标签，只留纯文本，防止破坏 JSON 结构
                clean_txt = re.sub('<[^<]+?>', ' ', raw_txt)
                clean_txt = clean_txt.replace('"', "'").replace('\n', ' ') # 替换掉可能破坏JSON的字符
                
                data_list.append({
                    "source": source_name,
                    "title": entry.title,
                    "link": entry.link,
                    "raw_content": clean_txt[:800] + "..." # 截断一下防止过长
                })
        except Exception as e:
            print(f"⚠️ {source_name} 跳过")
            
    return data_list

# ================= 3. AI 分析 (只负责输出 JSON) =================
def analyze_data(data_list):
    model = get_best_model()
    if not model: return []

    print(f"🧠 AI 正在分析 {len(data_list)} 条数据...")
    
    # 将数据列表转为字符串喂给 AI
    data_str = json.dumps(data_list, ensure_ascii=False, indent=1)
    
    prompt = f"""
    You are a Business Intelligence Analyst. 
    Analyze the following raw data list and identify **15 most valuable insights**.

    【Input Data】
    {data_str}

    【Task】
    Return a **JSON Array** of objects. Do not output Markdown or HTML. Just raw JSON.
    Each object in the array must have these exact keys:
    1. "category": (String) Choose one: "Business Opportunity", "Viral Trend", "Tech Signal".
    2. "source_tag": (String) e.g., "Google Trends", "r/Entrepreneur".
    3. "title_en": (String) Catchy English title.
    4. "title_cn": (String) Chinese title.
    5. "insight_en": (String) English analysis (Why it matters).
    6. "insight_cn": (String) Chinese analysis.
    7. "original_content": (String) **COPY verbatim** the "raw_content" from the input data corresponding to this item. Do not summarize it.

    【Format Example】
    [
      {{
        "category": "Business Opportunity",
        "source_tag": "r/SideProject",
        "title_en": "AI Tool Demand",
        "title_cn": "AI工具需求",
        "insight_en": "Users are looking for...",
        "insight_cn": "用户正在寻找...",
        "original_content": "I built this app because..."
      }}
    ]
    """

    try:
        response = model.generate_content(prompt)
        # 清洗 AI 返回的可能包含 ```json 的标记
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        # 解析 JSON
        analyzed_list = json.loads(clean_json)
        return analyzed_list
    except Exception as e:
        print(f"❌ AI 分析 JSON 失败: {e}")
        # 如果出错，打印原始内容方便调试
        print(response.text[:500]) 
        return []

# ================= 4. Python 渲染 HTML (强制生成按钮) =================
def render_html(analyzed_data):
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 这里的 CSS 是写死的，保证一定美观
    css = """
    <style>
        :root { --bg: #0f172a; --card: #1e293b; --text: #e2e8f0; --accent: #38bdf8; }
        body { font-family: sans-serif; background: var(--bg); color: var(--text); padding: 20px; margin: 0; }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        
        /* 瀑布流网格 */
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 24px; max-width: 1400px; margin: 0 auto; }
        
        /* 卡片 */
        .card { background: var(--card); padding: 24px; border-radius: 16px; border: 1px solid #334155; display: flex; flex-direction: column; }
        .tags { margin-bottom: 15px; }
        .tag { font-size: 12px; padding: 4px 8px; border-radius: 4px; background: #334155; margin-right: 5px; color: #94a3b8; }
        .tag.biz { color: #facc15; border: 1px solid #713f12; background: #422006; }
        .tag.trend { color: #f472b6; border: 1px solid #831843; background: #500724; }
        
        h2 { font-size: 18px; margin: 0 0 5px 0; color: #fff; }
        h3 { font-size: 14px; margin: 0 0 15px 0; color: #94a3b8; font-weight: normal; }
        
        .insight { background: #0f172a; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 3px solid var(--accent); }
        .insight p { margin: 5px 0; font-size: 14px; }
        .en { color: #cbd5e1; }
        .cn { color: #94a3b8; }
        
        /* 强制显示的原文区域 */
        details { margin-top: auto; border-top: 1px solid #334155; padding-top: 10px; }
        summary { cursor: pointer; color: var(--accent); font-size: 14px; font-weight: bold; }
        .raw { background: #000; color: #4ade80; padding: 15px; border-radius: 6px; font-family: monospace; font-size: 12px; margin-top: 10px; white-space: pre-wrap; word-break: break-word; max-height: 250px; overflow-y: auto; }
    </style>
    """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Business Intelligence {date_str}</title>
        {css}
    </head>
    <body>
        <div class="header">
            <h1>🇺🇸 Global Business Intelligence / 全球商业情报</h1>
            <p>{date_str} • Powered by Gemini 1.5 Flash</p>
        </div>
        <div class="grid">
    """
    
    # Python 循环生成卡片 (这是关键！由代码控制结构，而不是 AI)
    for item in analyzed_data:
        # 根据分类给 Tag 换颜色
        tag_class = "tag"
        if "Business" in item.get('category', ''): tag_class = "tag biz"
        if "Viral" in item.get('category', ''): tag_class = "tag trend"
        
        html_content += f"""
        <div class="card">
            <div class="tags">
                <span class="{tag_class}">{item.get('category', 'General')}</span>
                <span class="tag">{item.get('source_tag', 'Web')}</span>
            </div>
            <h2>{item.get('title_en', 'No Title')}</h2>
            <h3>{item.get('title_cn', '无标题')}</h3>
            
            <div class="insight">
                <p class="en">💡 {item.get('insight_en', 'No analysis')}</p>
                <p class="cn">🔍 {item.get('insight_cn', '无分析')}</p>
            </div>
            
            <details>
                <summary>▶ Click to View Raw Content / 查看原文详情</summary>
                <div class="raw">
{item.get('original_content', 'No content available.')}
                </div>
            </details>
        </div>
        """
        
    html_content += """
        </div>
    </body>
    </html>
    """
    return html_content

# ================= 主程序 =================
if __name__ == "__main__":
    # 1. 获取原始数据
    raw_data_list = get_data()
    
    if not raw_data_list:
        print("❌ 没有抓取到数据")
        exit()
        
    # 2. AI 分析 (返回 JSON 对象)
    analyzed_data = analyze_data(raw_data_list)
    
    # 3. 如果 AI 解析失败，生成一个空的 HTML 防止报错
    if not analyzed_data:
        print("❌ AI 返回的数据格式有误")
        analyzed_data = []

    # 4. Python 渲染 HTML
    html_page = render_html(analyzed_data)
    
    # 5. 保存
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_page)
    
    print("✅ 强制结构化网页生成完成")
