import os
import json
import time
import feedparser
import google.generativeai as genai
from pytrends.request import TrendReq
from datetime import datetime

# 1. 配置谷歌AI
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("❌ 错误：找不到 API Key")
    exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash') # 使用免费且快速的模型

# 2. 抓取数据函数
def get_data():
    print("正在采集数据...")
    data_text = ""

    # --- 抓取 Reddit RSS (免API) ---
    try:
        # 抓取 r/popular 的每日最热
        feed = feedparser.parse("https://www.reddit.com/r/popular/top/.rss?t=day")
        data_text += "【Reddit 热门话题】:\n"
        for entry in feed.entries[:7]: # 取前7条
            data_text += f"- {entry.title}\n"
    except Exception as e:
        print(f"Reddit 抓取失败: {e}")

    # --- 抓取 Google Trends ---
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        # 抓取美国今日热搜
        trends = pytrends.trending_searches(pn='united_states').head(10)[0].tolist()
        data_text += "\n【Google 搜索热词】:\n"
        for t in trends:
            data_text += f"- {t}\n"
    except Exception as e:
        print(f"Google Trends 抓取失败: {e}")

    return data_text

# 3. AI 分析函数
def analyze(text_data):
    print("正在发送给 AI 分析...")
    date_str = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
    你是美国新闻分析师。今天是 {date_str}。
    请阅读以下抓取到的 Reddit 和 Google 数据，写一份《美国今日热点日报》。

    要求：
    1. 挑选最热门的 3-5 个事件。
    2. 用中文撰写。
    3. 格式使用 Markdown。
    4. 风格要像简报一样清晰，每个事件包含“事件概述”和“舆论反应”。

    原始数据：
    {text_data}
    """

    response = model.generate_content(prompt)
    return response.text

# --- 主程序 ---
if __name__ == "__main__":
    # 第一步：抓
    raw_data = get_data()
    print("采集到的原始数据：")
    print(raw_data)

    if not raw_data:
        print("没有采集到数据，程序结束")
        exit()

    # 第二步：写
    report = analyze(raw_data)

    # 第三步：存
    filename = "DAILY_REPORT.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 🇺🇸 美国热点日报 ({datetime.now().strftime('%Y-%m-%d')})\n\n")
        f.write(report)
        f.write("\n\n---\n*Powered by Gemini 1.5 Flash & GitHub Actions*")

    print(f"✅ 报告已生成：{filename}")
