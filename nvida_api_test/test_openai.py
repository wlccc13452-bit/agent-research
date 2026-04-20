from openai import OpenAI
NVIDIA_TOKEN ="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"
# 1. 配置客户端
client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = NVIDIA_TOKEN
)

# 2. 调用模型
completion = client.chat.completions.create(
  model="meta/llama-3.3-70b-instruct", # 也可以换成 qwen/qwen2.5-72b-instruct
  messages=[{"role":"user","content":"请解释什么是NVIDIA NIM以及它的优势。"}],
  temperature=0.5,
  top_p=1,
  max_tokens=1024,
  stream=True # 开启流式输出
)

# 3. 打印结果
for chunk in completion:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")