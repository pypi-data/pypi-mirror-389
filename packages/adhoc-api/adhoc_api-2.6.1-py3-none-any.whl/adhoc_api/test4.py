from google import genai
from google.genai import types as genai_types
import os
from pathlib import Path
from adhoc_api.uaii import GeminiMessage, GeminiRole

here = Path(__file__).parent


import pdb


model = 'gemini-1.5-pro-001' 
cache_name = 'testing-the-gemini-cache'

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
context_str = (here / '../examples/gdc/gdc.md').read_text()
cache = client.caches.create(
    model=model,
    config=genai_types.CreateCachedContentConfig(
        display_name=cache_name,
        contents=GeminiMessage(role=GeminiRole.user, content=context_str),
        ttl='300s'
    )
)

pdb.set_trace()
response = client.models.generate_content_stream(
    model=model,
    contents=GeminiMessage(
        role=GeminiRole.user,
        content="how do I list all the cases in GDC filtering for individuals over 50",
    ),
    config=genai_types.GenerateContentConfig(cached_content=cache.name)
)

for i in response:
    if text:=i.text:
        print(text, end='', flush=True)
print()  # Ensure a newline at the end of the output