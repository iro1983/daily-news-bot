import os
import google.generativeai as genai

# 获取 Key
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("❌ 致命错误：GitHub Secrets 里根本没有 GOOGLE_API_KEY！")
    exit(1)

print(f"🔑 正在检查 Key (前5位): {api_key[:5]}...")

try:
    # 配置 API
    genai.configure(api_key=api_key)
    
    print("📡 正在连接 Google 服务器查询模型列表...")
    
    # === 关键步骤：直接问 Google 我能用啥 ===
    available_models = []
    for m in genai.list_models():
        # 我们只关心能生成文本的模型
        if 'generateContent' in m.supported_generation_methods:
            print(f"   ✅ 发现可用模型: {m.name}")
            available_models.append(m.name)
            
    print("-" * 30)
    
    if not available_models:
        print("⚠️ 严重问题：连接成功，但 Google 说你的账号没有任何可用模型！")
        print("可能原因：")
        print("1. 你的 API Key 对应的 Google Cloud 项目没有开启 'Generative Language API'。")
        print("2. 你的 Key 是 Vertex AI 的 Key，而不是 AI Studio 的 Key。")
    else:
        print(f"🎉 恭喜！你的 Key 是好的！你可以使用以下模型名字：")
        print(available_models)
        print("\n👇 请把上面列表里的【第一个名字】发给我，我帮你改代码。")

except Exception as e:
    print("\n❌ 连接彻底失败！错误详情如下：")
    print(e)
    # 强制让 Workflow 报错，方便你看到红叉
    exit(1)
