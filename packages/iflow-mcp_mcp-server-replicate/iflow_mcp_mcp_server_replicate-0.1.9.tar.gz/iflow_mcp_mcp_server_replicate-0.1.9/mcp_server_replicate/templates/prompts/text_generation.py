"""Prompt templates for text generation models."""

from typing import Dict

BASIC_PROMPT = {
    "id": "basic-text-generation",
    "name": "Basic Text Generation",
    "description": "Simple prompt template for text generation",
    "template": "{prompt}",
    "variables": {
        "prompt": "The main text input for generation"
    },
    "model_type": "text-generation",
    "version": "1.0.0",
}

CHAT_PROMPT = {
    "id": "chat-text-generation",
    "name": "Chat Completion",
    "description": "Chat-style prompt template with system and user messages",
    "template": "System: {system_message}\nUser: {user_message}",
    "variables": {
        "system_message": "Instructions or context for the model's behavior",
        "user_message": "The user's input message or query"
    },
    "model_type": "text-generation",
    "version": "1.0.0",
}

STRUCTURED_PROMPT = {
    "id": "structured-text-generation",
    "name": "Structured Text Generation",
    "description": "Template for generating text with specific format instructions",
    "template": "{context}\n\nTask: {task}\n\nFormat: {format_instructions}\n\nInput: {input}",
    "variables": {
        "context": "Background information or context",
        "task": "Specific task or objective",
        "format_instructions": "Instructions for output format",
        "input": "The specific input to process"
    },
    "model_type": "text-generation",
    "version": "1.0.0",
}

# Export all templates
TEMPLATES: Dict[str, dict] = {
    "basic": BASIC_PROMPT,
    "chat": CHAT_PROMPT,
    "structured": STRUCTURED_PROMPT,
} 