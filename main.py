import os
import google.generativeai as genai

# 获取 Key
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("❌ 致命错误：GitHub Secrets 里根本没有 GOOGLE_API_KEY！")
    exit(1)

print(f"🔑 读取到的 Key 前5位是: {api_key[:5]}...")

try:
    print("📡 正在尝试连接 Google...")
    genai.configure(api_key=api_key)
    
    # 列出所有能用的模型
    print("📋 正在获取可用模型列表...")
    count = 0
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"   ✅ 可用: {m.name}")
            count += 1
            
    if count > 0:
        print(f"\n🎉 恭喜！Key 是完全正常的！共发现了 {count} 个可用模型。")
        print("如果是网页报错，那肯定是代码逻辑问题，而不是 Key 的问题。")
    else:
        print("\n⚠️ 连接成功，但没有发现任何可用模型。这通常是因为账号权限问题。")

except Exception as e:
    print("\n❌ 连接彻底失败！原因如下：")
    print(f"ERROR DETAILS: {e}")
    # 强制让 Action 报错变红，引起注意
    exit(1)
