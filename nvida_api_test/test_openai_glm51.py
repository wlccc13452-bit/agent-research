import os
import sys

import httpx
from openai import OpenAI
NVIDIA_TOKEN ="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"

def get_nvidia_token() -> str:
    # token = os.getenv("NVIDIA_TOKEN") or os.getenv("NVIDIA_API_KEY")
    # if not token:
    #     print("Environment variable NVIDIA_TOKEN or NVIDIA_API_KEY is required.")
    #     sys.exit(1)
    return NVIDIA_TOKEN


client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=get_nvidia_token(),
)


SYSTEM_MESSAGE = {
    "role": "system",
    "content": "你是一个精通地震工程和 BIM 自动化的资深专家。",
}

USER_MESSAGE = {
    "role": "user",
    "content": "请分析 Dushanbe City Tower 项目在 PSHA 评估中可能遇到的主要断层类型。",
}


def call_glm51_non_stream() -> None:
    completion = client.chat.completions.create(
        model="z-ai/glm-5.1",
        messages=[SYSTEM_MESSAGE, USER_MESSAGE],
        temperature=0.2,
        top_p=0.7,
        max_tokens=1024,
        stream=False,
    )
    content = completion.choices[0].message.content
    if content:
        print(content)


def call_glm51_stream_with_retry(max_retries: int = 2) -> None:
    attempt = 0
    while attempt <= max_retries:
        try:
            completion = client.chat.completions.create(
                model="z-ai/glm-5.1",
                messages=[SYSTEM_MESSAGE, USER_MESSAGE],
                temperature=0.2,
                top_p=0.7,
                max_tokens=1024,
                stream=True,
            )
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    print(chunk.choices[0].delta.content, end="")
            print()
            return
        except httpx.RemoteProtocolError as exc:
            attempt += 1
            print()
            if attempt > max_retries:
                print(f"Streaming failed with RemoteProtocolError: {exc}")
                return
            print(f"Streaming interrupted, retrying {attempt}/{max_retries}...")


if __name__ == "__main__":
    print("Running non-streaming call...")
    call_glm51_non_stream()
    print("\nRunning streaming call with retry...")
    call_glm51_stream_with_retry()
