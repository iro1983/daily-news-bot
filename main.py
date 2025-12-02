import os
import feedparser
import google.generativeai as genai
from pytrends.request import TrendReq
from datetime import datetime

# ================= 配置区 =================
api_key = os.environ.get("GOOGLE_API_KEY")

# ================= 1. 抓取数据函数 (防报错版) =================
def get_data():
    print("🚀 开始采集数据...")
    data_text = ""
    
    # --- Reddit (RSS) ---
    try:
        print("正在连接 Reddit...")
        # 增加 User-Agent 防止被拦截
        feed = feedparser.parse("https://www.reddit.com/r/popular/top/.rss?t=day", agent="Mozilla/5.0")
        if feed.entries:
            data_text += "【Reddit 热门话题】:\n"
            for entry in feed.entries[:7]:
                data_text += f"- {entry.title}\n"
            print("✅ Reddit 抓取成功")
        else:
            print("⚠️ Reddit 返回为空")
    except Exception as e:
        print(f"❌ Reddit 抓取出错 (已跳过): {e}")

    # --- Google Trends ---
    try:
        print("正在连接 Google Trends...")
        # 增加超时设置，防止卡死
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25))
        trends = pytrends.trending_searches(pn='united_states').head(10)[0].tolist()
        data_text += "\n【Google 搜索热词】:\n"
        for t in trends:
            data_text += f"- {t}\n"
        print("✅ Google Trends 抓取成功")
    except Exception as e:
        print(f"❌ Google Trends 抓取出错 (已跳过): {e}")
            
    return data_text

# ================= 2. AI 分析函数 (含自动降级) =================
def analyze_to_html(text_data):
    if not api_key:
        return "<h1>错误：未配置 API Key</h1>"

    genai.configure(api_key=api_key)
    
    # 优先尝试 1.5 Pro，如果失败自动降级到 Pro
    models_to_try = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""
    今天是 {date_str}。
    请根据以下数据写一个 HTML5 网页。
    
    要求：
    1. 必须是完整的 HTML 结构，包含 <head> 和 <body>。
    2. 使用内嵌 CSS 美化，风格为“极简新闻日报”，卡片式布局，移动端友好。
    3. 标题：🇺🇸 美国全网热点日报 ({date_str})。
    4. 内容：选出 5 个最热事件，每个事件一个卡片。
    5. 不要输出 markdown 符号（如 ```html），只输出纯 HTML 代码。
    
    数据：
    {text_data}
    """

    for model_name in models_to_try:
        try:
            print(f"🤖 正在尝试使用模型: {model_name} ...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            # 清洗数据
            html = response.text.replace("```html", "").replace("```", "")
            print(f"✅ 成功！使用模型: {model_name}")
            return html
        except Exception as e:
            print(f"❌ 模型 {model_name} 失败: {e}")
            print("尝试下一个模型...")
            
    return "<h1>AI 生成失败</h1><p>所有模型均无法访问，请检查 API Key 权限。</p>"

# ================= 主程序 =================
if __name__ == "__main__":
    # 1. 抓取
    raw_data = get_data()
    
    if not raw_data:
        raw_data = "暂无数据，可能是网络连接失败，请检查 Actions 日志。"
    
    # 2. 生成网页
    html_page = analyze_to_html(raw_data)
    
    # 3. 保存
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_page)
    
    print("✅ 任务完成：index.html 已生成")
