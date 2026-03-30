import aiohttp
import os
from config import MODELS, PERSONAS

# Собираем все ключи: OPENROUTER_API_KEY, OPENROUTER_API_KEY_2, OPENROUTER_API_KEY_3 ...
def get_api_keys() -> list:
    keys = []
    primary = os.getenv("OPENROUTER_API_KEY", "")
    if primary:
        keys.append(primary)
    i = 2
    while True:
        key = os.getenv(f"OPENROUTER_API_KEY_{i}", "")
        if not key:
            break
        keys.append(key)
        i += 1
    return keys

async def call_ai(persona: str, messages: list) -> str:
    model = MODELS.get(persona, MODELS["neyro"])
    system = PERSONAS[persona]["system"]

    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}] + messages,
        "max_tokens": 250,
        "temperature": 1.05
    }

    keys = get_api_keys()
    if not keys:
        raise Exception("Нет ключей OpenRouter — добавь OPENROUTER_API_KEY в переменные")

    last_error = None
    for key in keys:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "X-Title": "Neyrohram Bot"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"].strip()
                    else:
                        text = await resp.text()
                        last_error = f"API error {resp.status}: {text[:200]}"
                        continue
        except Exception as e:
            last_error = str(e)
            continue

    raise Exception(f"Все ключи не сработали. Последняя ошибка: {last_error}")
