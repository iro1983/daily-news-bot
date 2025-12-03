import os
import feedparser
import google.generativeai as genai
from datetime import datetime
import time

# ================= 配置区 =================
api_key = os.environ.get("GOOGLE_API_KEY")

# ================= 1. 智能模型选择 =================
def get_best_model():
    if not api_key: return None
    genai.configure(api_key=api_key)
    try:
        # 必须用 Flash，因为这次数据量更大，Flash 的长文本处理能力最适合
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in all_models:
            if 'flash' in m and '1.5' in m: return genai.GenerativeModel(m)
        return genai.GenerativeModel('gemini-1.5-flash')
    except: return None

# ================= 2. 深度数据采集 (加大采集量) =================
def get_data():
    print("🚀 开始全网情报挖掘 (加量版)...")
    data_text = ""
    
    # 1. Google Trends (宏观) -> 增加到 20 条
    try:
        feed = feedparser.parse("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US")
        data_text += "\n【Google Trends (Macro Traffic)】:\n"
        for entry in feed.entries[:20]: # 抓取前 20 个
            traffic = getattr(entry, 'ht_approx_traffic', 'N/A')
            data_text += f"- Keyword: {entry.title} (Traffic: {traffic})\n  News: {entry.description}\n"
    except Exception as e:
        print(f"⚠️ Google 跳过: {e}")

    # 2. Reddit 垂直板块 (微观痛点) -> 每个板块增加到 8 条
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
                # 增加抓取量：每个板块抓 8 条，5个板块就是 40 条
                for entry in feed.entries[:8]: 
                    content_snippet = "No Content"
                    if hasattr(entry, 'content'):
                        content_snippet = entry.content[0].value[:600]
                    elif hasattr(entry, 'summary'):
                        content_snippet = entry.summary[:600]
                    content_snippet = content_snippet.replace("<p>", "").replace("</p>", "").replace("<br>", " ")
                    
                    data_text += f"--- Post ---\nTitle: {entry.title}\nLink: {entry.link}\nSnippet: {content_snippet}\n"
        except Exception as e:
            print(f"⚠️ {source_name} 跳过")
            
    return data_text

# ================= 3. AI 双语商业分析师 (强制 15+ 条) =================
def analyze_to_html(text_data):
    model = get_best_model()
    if not model: return "<h1>AI 配置失败</h1>"

    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"🧠 AI 正在进行大规模双语分析...")
    
    prompt = f"""
    You are an expert "Business Intelligence Analyst". Today is {date_str}.
    I have provided extensive raw data from Google Trends and Reddit.

    【Goal】
    Create a **Bilingual (English & Chinese)** Business Intelligence Report.
    Identify **Business Opportunities**, **User Pain Points**, and **Viral Trends**.

    【Quantity Requirement】
    **CRITICAL**: You MUST generate at least **15 to 20 items** in total. Do not output less than 15 items.

    【Output Structure】
    Please generate 3 sections. Each section must have 5-6 items.

    ### Section 1: 🚀 Business Opportunities & Pain Points (商机与痛点)
    *Target: 5-6 items* (Source: r/Entrepreneur, r/SideProject, r/marketing)
    * **Card Content**:
      - **Headline**: English Title / 中文标题
      - **Analysis (Bilingual)**:
        - **EN**: Briefly analyze the pain point or opportunity.
        - **CN**: 简要分析痛点或商机。
      - **Actionable Tip**: One specific advice (Bilingual).

    ### Section 2: 🔥 Viral Trends & Traffic (流量密码)
    *Target: 5-6 items* (Source: Google Trends & r/popular)
    * **Card Content**:
      - **Headline**: English Keyword / 中文热词
      - **Context (Bilingual)**:
        - **EN**: Why is this trending?
        - **CN**: 为什么火了？
      - **Marketing Angle**: How to use this trend? (Bilingual).

    ### Section 3: 💡 Tech & Industry Signals (行业信号)
    *Target: 5-6 items* (Source: r/technology, r/business)
    * **Card Content**:
      - **Headline**: English Event / 中文事件
      - **Impact (Bilingual)**:
        - **EN**: Why does it matter?
        - **CN**: 为什么重要？

    【Design & CSS】
    - **Theme**: Dark Professional Mode (#1a1b1e background).
    - **Typography**: English (Light Gray #ced4da), Chinese (White #ffffff).
    - **Layout**: Grid cards (Responsive).
    - **Tags**: Show Source & Category tags clearly.

    【Raw Data】
    {text_data}
    
    Output ONLY valid HTML code.
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
    
    print("✅ 15+条双语情报生成完成")
