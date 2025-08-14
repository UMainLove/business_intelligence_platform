import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
model = os.getenv("ANTHROPIC_MODEL_SPECIALISTS", "claude-sonnet-4-20250514")
resp = client.messages.create(
    model=model,
    max_tokens=40,
    messages=[{"role": "user", "content": "Reply with exactly: pong"}],
)
print(resp.content[0].text)
