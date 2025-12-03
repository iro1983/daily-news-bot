import os
import feedparser
import google.generativeai as genai
from datetime import datetime

# ================= 配置区 =================
api_key = os.environ.get("GOOGLE_API_KEY")

# ================= 1. 智能模型选择 =================
def get_best_model():
    if not api_key:
        print("❌ 错误：未找到 API Key")
        return None
    genai.configure(api_key=api_key)
    try:
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # 优先找 Flash (速度快，长文本能力强，适合双语输出)
        for m in all_models:
            if 'flash' in m and 'exp' not in m and '1.5' in m: return genai.GenerativeModel(m)
        for m in all_models:
            if 'flash' in m: return genai.GenerativeModel(m)
        if all_models: return genai.GenerativeModel(all_models[0])
    except: return None
    return None

# ================= 2. 强力数据采集 (Google RSS + Reddit) =================
def get_data():
    print("🚀 开始全网热点采集...")
    data_text = ""
    
    # 1. Google Trends RSS (极稳)
    try:
        print("🔥 正在抓取 Google 实时热搜...")
        feed = feedparser.parse("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US")
        if feed.entries:
            data_text += "\n【Source: Google Trends US】:\n"
            for entry in feed.entries[:20]: # 抓前20个
                traffic = getattr(entry, 'ht_approx_traffic', 'N/A')
                data_text += f"- Keyword: {entry.title} (Traffic: {traffic})\n"
                data_text += f"  News Snippet: {entry.description}\n"
    except Exception as e:
        print(f"⚠️ Google RSS 抓取异常: {e}")

    # 2. Reddit 吃瓜与热议
    reddit_feeds = [
        ("r/popular", "https://www.reddit.com/r/popular/top/.rss?t=day"),
        ("r/technology", "https://www.reddit.com/r/technology/top/.rss?t=day"),
        ("r/entertainment", "https://www.reddit.com/r/entertainment/top/.rss?t=day")
    ]

    for source_name, url in reddit_feeds:
        try:
            print(f"💬 正在抓取 {source_name}...")
            feed = feedparser.parse(url, agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
            if feed.entries:
                data_text += f"\n【Source: {source_name}】:\n"
                for entry in feed.entries[:20]: 
                    data_text += f"- Title: {entry.title}\n  Link: {entry.link}\n"
        except Exception as e:
            print(f"⚠️ {source_name} 抓取跳过")
            
    return data_text

# ================= 3. AI 双语分析与网页生成 =================
def analyze_to_html(text_data):
    model = get_best_model()
    if not model: return "<h1>AI 配置失败</h1>"

    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"🤖 AI 正在进行中英文双语编译...")
    
    # --- 核心修改：双语 Prompt ---
    prompt = f"""
    You are the editor-in-chief of "Daily US Trends". Today is {date_str}.
    Based on the raw data from Google Trends and Reddit provided below, create a **Bilingual (English & Chinese)** HTML news report.

    【Content Strategy】
    1. **Selection**: Pick top 20 most interesting/viral stories. Prioritize topics with high traffic on Google or intense discussion on Reddit.
    2. **Bilingual Requirement**: Every section MUST correspond in English and Chinese.
    
    【Card Structure (HTML)】
    For each story card, include:
    - **Header**: 
      - English Headline (Catchy)
      - 中文标题 (翻译要接地气，有吸引力)
    - **Meta Info**: Source (e.g., Google Trends) & Tags.
    - **The Story (Content)**:
      - A paragraph in **English** summarizing the event (approx 60-100 words).
      - A paragraph in **Chinese** summarizing the same event.
    - **Netizen Vibe (Reaction)**:
      - What are people saying? (One sentence EN / One sentence CN).

    【Design & CSS Requirements】
    - **Theme**: Dark Mode (#121212 background).
    - **Typography**: Clean sans-serif. 
    - **Contrast**: 
       - Make the **English text** a slightly lighter gray (e.g., #e0e0e0).
       - Make the **Chinese text** bright white (e.g., #ffffff) or a highlight color to distinguish them easily.
    - **Layout**: Grid layout (responsive). Card background: #1e1e1e. Border-radius: 12px.
    - **Styling**: Use distinct spacing or a subtle divider line between English and Chinese sections within the card.

    【Raw Data】
    {text_data}
    
    Output ONLY valid HTML code. Do not use Markdown blocks.
    """

    try:
        response = model.generate_content(prompt)
        return response.text.replace("```html", "").replace("```", "")
    except Exception as e:
        return f"<h1>生成出错</h1><p>{e}</p>"

# ================= 主程序 =================
if __name__ == "__main__":
    raw_data = get_data()
    if not raw_data: raw_data = "No data available."
    
    html_page = analyze_to_html(raw_data)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_page)
    
    print("✅ 双语日报生成完成")
