"""Probe NVIDIA API for available models with tool calling support."""

import json
import sys

sys.path.insert(0, r"C:\Users\hardi\Downloads\ACD-agent")

from openai import OpenAI

from core.config import NVIDIA_API_KEY, NVIDIA_BASE_URL

client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)

print("Listing available NVIDIA models...")
try:
    models = client.models.list()
    model_ids = sorted([m.id for m in models.data])
    print(f"Total models: {len(model_ids)}")
    # Filter to models likely to support tool calling
    llama_models = [m for m in model_ids if "llama" in m.lower()]
    nemotron_models = [m for m in model_ids if "nemotron" in m.lower()]
    mistral_models = [m for m in model_ids if "mistral" in m.lower()]
    qwen_models = [m for m in model_ids if "qwen" in m.lower()]
    print("\nLlama models:", json.dumps(llama_models, indent=2))
    print("\nNemotron models:", json.dumps(nemotron_models, indent=2))
    print("\nMistral models:", json.dumps(mistral_models, indent=2))
    print("\nQwen models:", json.dumps(qwen_models, indent=2))
except Exception as e:
    print(f"Error listing models: {e}")
