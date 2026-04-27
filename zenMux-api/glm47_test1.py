from openai import OpenAI
ZENMUX_API_KEY = 'sk-ai-v1-be789490e52e2133cf3843125aa12bb93386cea8c3ce308b66ae4dd745ed32e8'
client = OpenAI(
  base_url="https://zenmux.ai/api/v1",
  api_key=ZENMUX_API_KEY,
)

# Chat Completion
completion = client.chat.completions.create(
  model="z-ai/glm-4.7-flash-free",
  messages=[
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
)
print(completion.choices[0].message.content)

# Responses API
responses = client.responses.create(
  model="z-ai/glm-4.7-flash-free",
  input="What is the meaning of life?"
)
print(responses)