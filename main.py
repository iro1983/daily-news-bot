import os
import feedparser
import google.generativeai as genai
from datetime import datetime
import time

# ================= 配置区 =================
api_key = os.environ.get("GOOGLE_API_KEY")

# ================= 1. 动态获取模型 =================
def get_best_model():
    if not api_key: return None
    genai.configure(api_key=api_key)
    try:
        model_list = list(genai.list_models())
        supported_models = [m.name for m in model_list if 'generateContent' in m.supported_generation_methods]
        
        # 优先 Flash (速度快)
        for name in supported_models:
            if 'flash' in name.lower(): return genai.GenerativeModel(name)
        # 其次 Pro
        for name in supported_models:
            if 'pro' in name.lower(): return genai.GenerativeModel(name)
        # 保底
        if supported_models: return genai.GenerativeModel(supported_models[0])
    except: return None
    return None

# ================= 2. 深度采集 (抓取长文本) =================
def get_data():
    print("🚀 开始全网情报挖掘...")
    data_text = ""
    
    # 1. Google Trends
    try:
        feed = feedparser.parse("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US")
        data_text += "\n【Google Trends】:\n"
        for entry in feed.entries[:15]:
            traffic = getattr(entry, 'ht_approx_traffic', 'N/A')
            data_text += f"- Keyword: {entry.title} (Traffic: {traffic})\n  Raw Context: {entry.description}\n"
    except Exception as e:
        print(f"⚠️ Google 跳过: {e}")

    # 2. Reddit 多板块
    reddit_feeds = [
        ("r/Entrepreneur", "https://www.reddit.com/r/Entrepreneur/top/.rss?t=day"), 
        ("r/SideProject", "https://www.reddit.com/r/SideProject/top/.rss?t=day"),   
        ("r/technology", "https://www.reddit.com/r/technology/top/.rss?t=day"),     
        ("r/popular", "https://www.reddit.com/r/popular/top/.rss?t=day"),           
        ("r/marketing", "https://www.reddit.com/r/marketing/top/.rss?t=day")        
    ]

    for source_name, url in reddit_feeds:
        try:
            print(f"💎 正在挖掘 {source_name}...")
            feed = feedparser.parse(url, agent="Mozilla/5.0")
            if feed.entries:
                data_text += f"\n【Source: {source_name}】:\n"
                for entry in feed.entries[:6]: 
                    # 抓取正文
                    raw_content = "Link post / No text content."
                    if hasattr(entry, 'content'):
                        raw_content = entry.content[0].value[:1200]
                    elif hasattr(entry, 'summary'):
                        raw_content = entry.summary[:1200]
                    
                    # 清洗
                    raw_content = raw_content.replace("<p>", "").replace("</p>", "\n\n").replace("<br>", "\n")
                    
                    data_text += f"--- Post ---\nTitle: {entry.title}\nLink: {entry.link}\nRaw Content: {raw_content}\n"
        except Exception as e:
            print(f"⚠️ {source_name} 跳过")
            
    return data_text

# ================= 3. AI 设计师 (内置专业 CSS) =================
def analyze_to_html(text_data):
    model = get_best_model()
    if not model: return "<h1>AI 配置失败</h1>"

    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"🧠 AI 正在构建高颜值仪表盘...")
    
    # --- 这里是核心：直接把写好的 CSS 喂给 AI，不让它乱写 ---
    css_template = """
    <style>
        :root { --bg: #0f172a; --card-bg: #1e293b; --text-main: #e2e8f0; --text-dim: #94a3b8; --accent: #38bdf8; --border: #334155; }
        body { font-family: 'Segoe UI', Roboto, Helvetica, sans-serif; background-color: var(--bg); color: var(--text-main); margin: 0; padding: 20px; line-height: 1.6; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 40px; padding: 20px; border-bottom: 1px solid var(--border); }
        .header h1 { font-size: 2.5rem; background: linear-gradient(90deg, #60a5fa, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
        
        /* 瀑布流/网格布局 */
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 24px; }
        
        /* 卡片样式 */
        .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 24px; transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; }
        .card:hover { transform: translateY(-4px); box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3); border-color: var(--accent); }
        
        /* 标签 */
        .tags { margin-bottom: 16px; display: flex; gap: 8px; flex-wrap: wrap; }
        .tag { font-size: 0.75rem; padding: 4px 10px; border-radius: 20px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
        .tag-source { background: #334155; color: #cbd5e1; }
        .tag-biz { background: #451a03; color: #fbbf24; border: 1px solid #78350f; }
        .tag-tech { background: #0f172a; color: #38bdf8; border: 1px solid #0c4a6e; }
        .tag-trend { background: #3f0e40; color: #f472b6; border: 1px solid #831843; }

        /* 标题与内容 */
        .card h2 { font-size: 1.25rem; margin: 0 0 8px 0; color: #fff; line-height: 1.3; }
        .card h3 { font-size: 1rem; color: var(--text-dim); margin: 0 0 16px 0; font-weight: 400; }
        .analysis-box { background: #0f172a; padding: 16px; border-radius: 8px; border-left: 4px solid var(--accent); margin-bottom: 16px; }
        .analysis-en { margin-bottom: 8px; color: #e2e8f0; font-weight: 500; }
        .analysis-cn { color: #94a3b8; font-size: 0.95rem; }
        
        /* 重点：原文折叠按钮 */
        details { margin-top: auto; border-top: 1px solid var(--border); padding-top: 12px; }
        summary { cursor: pointer; color: var(--accent); font-weight: 600; font-size: 0.9rem; user-select: none; transition: color 0.2s; list-style: none; display: flex; align-items: center; }
        summary:hover { color: #7dd3fc; }
        summary::before { content: "📄"; margin-right: 8px; }
        details[open] summary { margin-bottom: 12px; }
        
        /* 原文内容区域 */
        .raw-content { background: #000; color: #22c55e; padding: 16px; border-radius: 8px; font-family: 'Cons
