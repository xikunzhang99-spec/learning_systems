import time
import httpx
from openai import OpenAI
from config import settings

# 流式传输超时设置：连接 10s，读取 300s（长回复需要足够时间）
TIMEOUT = httpx.Timeout(10.0, read=300.0, write=60.0, pool=10.0)


def _get_client():
    provider = settings.AI_PROVIDER

    if provider == "deepseek":
        return OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            http_client=httpx.Client(timeout=TIMEOUT),
        )

    if provider == "claude":
        return OpenAI(
            api_key=settings.CLAUDE_API_KEY,
            base_url="https://api.anthropic.com/v1",
            http_client=httpx.Client(timeout=TIMEOUT),
        )

    return OpenAI(
        api_key=settings.OPENAI_API_KEY,
        http_client=httpx.Client(timeout=TIMEOUT),
    )


def _get_model_name():
    provider = settings.AI_PROVIDER

    if provider == "deepseek":
        return settings.DEEPSEEK_MODEL
    if provider == "claude":
        return settings.CLAUDE_MODEL
    return settings.OPENAI_MODEL


def chat(messages: list) -> str:
    client = _get_client()
    model = _get_model_name()

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
            )
            return response.choices[0].message.content
        except (httpx.RemoteProtocolError, httpx.ReadError,
                httpx.ConnectError) as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep((attempt + 1) * 2)
                client = _get_client()
            else:
                raise e



MAX_RETRIES = 3


def stream_chat(messages: list):
    client = _get_client()
    model = _get_model_name()

    yielded_chars = 0

    for attempt in range(MAX_RETRIES):
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
            )

            chars_in_attempt = 0
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    chars_in_attempt += len(delta)
                    # 重试时跳过已输出的内容
                    if chars_in_attempt > yielded_chars:
                        if yielded_chars > 0:
                            skip = yielded_chars - (chars_in_attempt - len(delta))
                            if skip > 0:
                                delta = delta[skip:]
                        yielded_chars += len(delta)
                        yield delta

            return  # 正常完成

        except (httpx.RemoteProtocolError, httpx.ReadError,
                httpx.ConnectError) as e:
            if attempt < MAX_RETRIES - 1:
                wait = (attempt + 1) * 2
                time.sleep(wait)
                # 重新创建 client 以获取新的连接
                client = _get_client()
            else:
                raise e
