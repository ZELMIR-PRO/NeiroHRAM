import aiohttp
from config import OPENROUTER_API_KEY, MODELS, PERSONAS

async def call_ai(persona: str, messages: list) -> str:
    model = MODELS.get(persona, MODELS["neyro"])
    system = PERSONAS[persona]["system"]

    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}] + messages,
        "max_tokens": 250,
        "temperature": 1.05
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "X-Title": "Neyrohram Bot"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"API error {resp.status}: {text[:200]}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"].strip()
