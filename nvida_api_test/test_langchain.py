from langchain_nvidia_ai_endpoints import ChatNVIDIA
NVIDIA_TOKEN ="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"
# 初始化模型
llm = ChatNVIDIA(
    model="meta/llama-3.3-70b-instruct",
    nvidia_api_key=NVIDIA_TOKEN,
    temperature=0.2
)

# 直接调用
result = llm.invoke("用Python写一个快速排序算法。")
print(result.content)