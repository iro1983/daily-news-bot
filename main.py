import os
import feedparser
import google.generativeai as genai
from pytrends.request import TrendReq
from datetime import datetime

# ================= 配置区 =================
api_key = os.environ.get("GOOGLE_API_KEY")

# ================= 1. 核心：智能寻找可用的 Flash 模型 =================
def get_best_model():
    if not api_key:
        print("❌ 错误：未找到 API Key")
        return None
    
    genai.configure(api_key=api_key)
    print("🔍 正在扫描可用模型列表...")
    
    try:
        # 获取所有支持生成的模型
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print(f"📋 你的账号支持这些模型: {all_models}")
        
        # 策略 1: 优先找稳定的 Flash (速度快，额度高)
        for m in all_models:
            if 'flash' in m and 'exp' not in m and '1.5' in m:
                print(f"✅ 选中最佳模型: {m}")
                return genai.GenerativeModel(m)
        
        # 策略 2: 如果没有标准 Flash，找任何带 Flash 的
        for m in all_models:
            if 'flash' in m:
                print(f"✅ 选中备用 Flash 模型: {m}")
                return genai.GenerativeModel(m)

        # 策略 3: 找 Pro
        for m in all_models:
            if 'pro' in m and 'exp' not in m:
                print(f"✅ 选中 Pro 模型: {m}")
                return genai.GenerativeModel(m)

        # 策略 4: 随便选一个能用的
        if all_models:
            print(f"⚠️ 没找到常用模型，强制使用第一个: {all_models[0]}")
            return genai.GenerativeModel(all_models[0])
            
    except Exception as e:
        print(f"❌ 获取模型列表失败: {e}")
        return None
    
    print("❌ 严重：未找到任何可用模型！")
    return None

# ================= 2. 抓取数据 =================
def get_data():
    print("🚀 开始采集数据...")
    data_text = ""
    
    # Reddit RSS
    try:
        print("正在连接 Reddit...")
        feed = feedparser.parse("https://www.reddit.com/r/popular/top/.rss?t=day", agent="Mozilla/5.0")
        if feed.entries:
            data_text += "【Reddit 热门话题】:\n"
            for entry in feed.entries[:7]:
                data_text += f"- {entry.title}\n"
    except Exception as e:
        print(f"⚠️ Reddit 跳过: {e}")

    # Google Trends (经常 404，不用管它，属于正常现象)
    try:
        print("正在连接 Google Trends...")
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25))
        trends = pytrends.trending_searches(pn='united_states').head(10)[0].tolist()
        data_text += "\n【Google 搜索热词】:\n"
        for t in trends:
            data_text += f"- {t}\n"
    except Exception as e:
        print(f"⚠️ Google Trends 跳过 (云服务器常被Google拦截，属正常): {e}")
            
    return data_text

# ================= 3. 生成网页 =================
def analyze_to_html(text_data):
    # 智能获取模型
    model = get_best_model()
    if not model:
        return "<h1>AI 配置失败</h1><p>无法找到可用模型，请检查 Logs。</p>"

    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"🤖 开始生成内容...")
    
    prompt = f"""
    今天是 {date_str}。
    请根据以下数据写一个 HTML5 网页。
    
    要求：
    1. 必须是完整的 HTML 结构，包含 <head> 和 <body>。
    2. 使用内嵌 CSS 美化，风格为“极简新闻日报”，背景色 #f4f4f9，卡片白底圆角。
    3. 标题：🇺🇸 美国全网热点日报 ({date_str})。
    4. 内容：选出 5 个最热事件，每个事件一个卡片。
    5. 只要输出 HTML 代码。
    
    数据：
    {text_data}
    """

    try:
        response = model.generate_content(prompt)
        return response.text.replace("```html", "").replace("```", "")
    except Exception as e:
        print(f"❌ 生成出错: {e}")
        return f"<h1>生成出错</h1><p>{e}</p>"

# ================= 主程序 =================
if __name__ == "__main__":
    raw_data = get_data()
    if not raw_data:
        raw_data = "暂无数据。"
    
    html_page = analyze_to_html(raw_data)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_page)
    
    print("✅ 任务完成")
