"""
Curated catalog of open-source GGUF models for local LLM inference.
All models are downloaded from HuggingFace and stored in LLM_MODELS_DIR.
"""

MODELS = [
    {
        "id": "llama-3.2-1b",
        "name": "Llama 3.2 1B Instruct",
        "description": "Meta's smallest Llama. Fastest inference — runs on any modern device.",
        "params_b": 1,
        "quantization": "Q4_K_M",
        "size_gb": 0.8,
        "ram_min_gb": 4,
        "context_window": 131072,
        "hf_repo": "unsloth/Llama-3.2-1B-Instruct-GGUF",
        "hf_file": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "tags": ["fast", "lightweight"],
    },
    {
        "id": "llama-3.2-3b",
        "name": "Llama 3.2 3B Instruct",
        "description": "Good balance of speed and quality. Recommended for most laptops.",
        "params_b": 3,
        "quantization": "Q4_K_M",
        "size_gb": 2.0,
        "ram_min_gb": 8,
        "context_window": 131072,
        "hf_repo": "unsloth/Llama-3.2-3B-Instruct-GGUF",
        "hf_file": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "tags": ["recommended"],
    },
    {
        "id": "phi-3.5-mini",
        "name": "Phi-3.5 Mini Instruct",
        "description": "Microsoft's compact model. Strong reasoning relative to its size.",
        "params_b": 3.8,
        "quantization": "Q4_K_M",
        "size_gb": 2.4,
        "ram_min_gb": 8,
        "context_window": 128000,
        "hf_repo": "bartowski/Phi-3.5-mini-instruct-GGUF",
        "hf_file": "Phi-3.5-mini-instruct-Q4_K_M.gguf",
        "tags": ["reasoning"],
    },
    {
        "id": "mistral-7b",
        "name": "Mistral 7B Instruct v0.3",
        "description": "Strong instruction-following and structured output. Excellent for JSON.",
        "params_b": 7,
        "quantization": "Q4_K_M",
        "size_gb": 4.4,
        "ram_min_gb": 16,
        "context_window": 32768,
        "hf_repo": "bartowski/Mistral-7B-Instruct-v0.3-GGUF",
        "hf_file": "Mistral-7B-Instruct-v0.3-Q4_K_M.gguf",
        "tags": [],
    },
    {
        "id": "llama-3.1-8b",
        "name": "Llama 3.1 8B Instruct",
        "description": "Meta's flagship small model. Best quality under 10B parameters.",
        "params_b": 8,
        "quantization": "Q4_K_M",
        "size_gb": 4.9,
        "ram_min_gb": 16,
        "context_window": 131072,
        "hf_repo": "unsloth/Meta-Llama-3.1-8B-Instruct-GGUF",
        "hf_file": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "tags": [],
    },
    {
        "id": "gemma-2-9b",
        "name": "Gemma 2 9B Instruct",
        "description": "Google's Gemma 2. Excellent structured reasoning and factual accuracy.",
        "params_b": 9,
        "quantization": "Q4_K_M",
        "size_gb": 5.8,
        "ram_min_gb": 16,
        "context_window": 8192,
        "hf_repo": "bartowski/gemma-2-9b-it-GGUF",
        "hf_file": "gemma-2-9b-it-Q4_K_M.gguf",
        "tags": [],
    },
    {
        "id": "llama-3.1-70b",
        "name": "Llama 3.1 70B Instruct",
        "description": "Near GPT-4 quality. Requires a high-memory workstation or Mac Studio/Pro.",
        "params_b": 70,
        "quantization": "Q4_K_M",
        "size_gb": 42.5,
        "ram_min_gb": 64,
        "context_window": 131072,
        "hf_repo": "unsloth/Meta-Llama-3.1-70B-Instruct-GGUF",
        "hf_file": "Meta-Llama-3.1-70B-Instruct-Q4_K_M.gguf",
        "tags": ["powerful"],
    },
]

MODEL_BY_ID: dict = {m["id"]: m for m in MODELS}


def hf_download_url(model_id: str) -> str:
    meta = MODEL_BY_ID[model_id]
    return f"https://huggingface.co/{meta['hf_repo']}/resolve/main/{meta['hf_file']}"
