import os
import feedparser
import google.generativeai as genai
from pytrends.request import TrendReq
from datetime import datetime

# ================= 配置区 =================
# 即使没有 Key 也不要直接崩溃，而是打印警告
api_key = os.environ.get("GOOGLE_API_KEY")

# ================= 抓取函数 (增加防报错机制) =================
def get_data():
    print("🚀 开始采集数据...")
    data_text = ""
    
    # --- 1. 抓取 Reddit (RSS) ---
    try:
        print("正在连接 Reddit...")
        feed = feedparser.parse("https://www.reddit.com/r/popular/top/.rss?t=day")
        if feed.entries:
            data_text += "【Reddit 热门话题】:\n"
            for entry in feed.entries[:7]:
                data_text += f"- {entry.title}\n"
            print("✅ Reddit 抓取成功")
        else:
            print("⚠️ Reddit 返回为空")
    except Exception as e:
        print(f"❌ Reddit 抓取出错 (已跳过): {e}")

    # --- 2. 抓取 Google Trends (最容易报错的地方) ---
    try:
        print("正在连接 Google Trends...")
        # 增加重试机制和超时设置
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25))
        trends = pytrends.trending_searches(pn='united_states').head(10)[0].tolist()
        data_text += "\n【Google 搜索热词】:\n"
        for t in trends:
            data_text += f"- {t}\n"
        print("✅ Google Trends 抓取成功")
    except Exception as e:
        print(f"❌ Google Trends 抓取出错 (通常是网络限制，已跳过): {e}")
        # 如果 Google 失败，不中断程序，继续往下走
            
    return data_text

# ================= AI 生成函数 =================
def analyze_to_html(text_data):
    if not api_key:
        print("⚠️ 警告：未检测到 GOOGLE_API_KEY，将生成静态测试页面。")
        return "<h1>错误：未配置 API Key</h1><p>请在 GitHub Settings -> Secrets 中配置 GOOGLE_API_KEY。</p>"

    print("🤖 正在让 AI 生成网页...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        prompt = f"""
        今天是 {date_str}。
        请根据以下数据写一个 HTML5 网页。
        
        要求：
        1. 必须是完整的 HTML 结构，包含 <head> 和 <body>。
        2. 使用内嵌 CSS 美化，风格为“极简新闻日报”，背景浅灰，卡片白底圆角。
        3. 标题：🇺🇸 美国全网热点日报 ({date_str})。
        4. 内容：选出 5 个最热事件，每个事件一个卡片。
        5. 不要输出 markdown 符号（如 ```html），只输出纯 HTML 代码。
        
        数据：
        {text_data}
        """
        response = model.generate_content(prompt)
        # 清洗数据
        return response.text.replace("```html", "").replace("```", "")
    except Exception as e:
        print(f"❌ AI 生成出错: {e}")
        return f"<h1>AI 生成失败</h1><p>{e}</p>"

# ================= 主程序 =================
if __name__ == "__main__":
    # 1. 抓取
    raw_data = get_data()
    
    # 2. 如果什么都没抓到，给一个默认值，防止程序空跑
    if not raw_data:
        raw_data = "暂无数据，可能是网络连接失败。"
    
    # 3. 生成网页
    html_page = analyze_to_html(raw_data)
    
    # 4. 强制写入文件，确保文件存在
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_page)
    
    print("✅ 任务完成：index.html 已生成")
