"""Parameter templates for LLaMA models."""

from typing import Dict, Any

LLAMA_70B_PARAMETERS = {
    "id": "llama-70b-base",
    "name": "LLaMA 70B Base Parameters",
    "description": "Default parameters for LLaMA 70B models",
    "model_type": "text-generation",
    "default_parameters": {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 512,
        "repetition_penalty": 1.1,
        "stop_sequences": [],
        "system_prompt": "You are a helpful AI assistant.",
    },
    "parameter_schema": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "The input text prompt"},
            "system_prompt": {"type": "string", "description": "System prompt for setting assistant behavior"},
            "temperature": {"type": "number", "minimum": 0, "maximum": 2},
            "top_p": {"type": "number", "minimum": 0, "maximum": 1},
            "max_tokens": {"type": "integer", "minimum": 1, "maximum": 4096},
            "repetition_penalty": {"type": "number", "minimum": 0.1, "maximum": 2.0},
            "stop_sequences": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["prompt"]
    },
    "version": "1.0.0",
}

LLAMA_13B_PARAMETERS = {
    "id": "llama-13b-base",
    "name": "LLaMA 13B Base Parameters",
    "description": "Default parameters for LLaMA 13B models",
    "model_type": "text-generation",
    "default_parameters": {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 256,
        "repetition_penalty": 1.1,
        "stop_sequences": [],
        "system_prompt": "You are a helpful AI assistant.",
    },
    "parameter_schema": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "The input text prompt"},
            "system_prompt": {"type": "string", "description": "System prompt for setting assistant behavior"},
            "temperature": {"type": "number", "minimum": 0, "maximum": 2},
            "top_p": {"type": "number", "minimum": 0, "maximum": 1},
            "max_tokens": {"type": "integer", "minimum": 1, "maximum": 2048},
            "repetition_penalty": {"type": "number", "minimum": 0.1, "maximum": 2.0},
            "stop_sequences": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["prompt"]
    },
    "version": "1.0.0",
}

# Export all templates
TEMPLATES: Dict[str, Dict[str, Any]] = {
    "llama70b": LLAMA_70B_PARAMETERS,
    "llama13b": LLAMA_13B_PARAMETERS,
} 