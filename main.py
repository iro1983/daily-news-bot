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
        
        # 优先 Flash (长文本处理快)
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
            # 抓取新闻片段作为原文
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
                    # 抓取正文 (Selftext)
                    raw_content = "Link post / No text content."
                    if hasattr(entry, 'content'):
                        raw_content = entry.content[0].value[:1000] # 抓取1000字，保留更多细节
                    elif hasattr(entry, 'summary'):
                        raw_content = entry.summary[:1000]
                    
                    # 简单的 HTML 清洗，保留换行
                    raw_content = raw_content.replace("<p>", "").replace("</p>", "\n").replace("<br>", "\n").replace("&nbsp;", " ")
                    
                    data_text += f"--- Post ---\nTitle: {entry.title}\nLink: {entry.link}\nRaw Content: {raw_content}\n"
        except Exception as e:
            print(f"⚠️ {source_name} 跳过")
            
    return data_text

# ================= 3. AI 设计师 (网格布局 + 折叠原文) =================
def analyze_to_html(text_data):
    model = get_best_model()
    if not model: return "<h1>AI 配置失败</h1>"

    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"🧠 AI 正在构建可视化仪表盘...")
    
    prompt = f"""
    You are a UI/UX Designer and Business Analyst. Today is {date_str}.
    
    【Goal】
    Transform the raw data into a **High-Density Business Intelligence Dashboard**.
    
    【UI Layout Requirements】
    1. **Masonry Grid Layout**: Use a 3-column grid for desktop (horizontal display), collapsing to 1 column on mobile.
    2. **Collapsible Raw Content**: 
       - Inside each card, use the HTML `<details>` and `<summary>` tags.
       - The summary should say "🔍 Read Original Post / 查看原文详情".
       - Inside the details, put the **Raw Content** (user's full complaint, story, or news snippet) verbatim.
    3. **Visual Hierarchy**: 
       - Title (Bold)
       - Tags (Colored badges)
       - Analysis (Bilingual)
       - **Hidden Raw Content** (Bottom)

    【Content Requirements (15+ Items)】
    Generate 3 Sections (Business, Trends, Tech). At least 5 cards per section.
    
    **Card Content Structure**:
    1. **Header**: English Title + 中文标题
    2. **Tags**: [Source] [Category]
    3. **Insight (Bilingual)**: 
       - **Opportunity/Analysis**: Deep dive into the "Why".
       - **Action**: One sentence tip.
    4. **The Raw Content (Hidden)**:
       - Quote the user's post body or news description inside the `<details>` tag. This is CRITICAL.

    【Design & CSS Rules】
    - Body Background: #121212 (Deep Dark).
    - Grid Container: `display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px;`
    - Card Style: Background #1e1e1e; Border-radius 12px; Padding 20px; Border: 1px solid #333.
    - Text: White (#eee) for main text, Gray (#aaa) for secondary.
    - "Details" Section: Background #000; Padding 15px; Margin-top 15px; Border-radius 8px; Font-family: monospace; Font-size: 0.9em; Color: #81c784 (Terminal Green style).

    【Raw Data】
    {text_data}
    
    Output ONLY valid HTML code with internal CSS.
    """

    try:
        response = model.generate_content(prompt)
        return response.text.replace("```html", "").replace("```", "")
    except Exception as e:
        return f"<h1>生成出错</h1><p>{e}</p>"

# ================= 主程序 =================
if __name__ == "__main__":
    raw_data = get_data()
    if not raw_data: raw_data = "No data."
    
    html_page = analyze_to_html(raw_data)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_page)
    
    print("✅ 仪表盘生成完成")
