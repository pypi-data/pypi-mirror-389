"""Prompt templates for text-to-image models."""

from typing import Dict

BASIC_PROMPT = {
    "id": "basic-text-to-image",
    "name": "Basic Text to Image",
    "description": "Simple prompt template for text-to-image generation",
    "template": "{prompt}",
    "variables": {
        "prompt": "The main text description of the image to generate"
    },
    "model_type": "text-to-image",
    "version": "1.0.0",
}

DETAILED_PROMPT = {
    "id": "detailed-text-to-image",
    "name": "Detailed Text to Image",
    "description": "Detailed prompt template with style and quality modifiers",
    "template": "{prompt}, {style}, {quality}",
    "variables": {
        "prompt": "The main text description of the image to generate",
        "style": "The artistic style (e.g., 'oil painting', 'digital art')",
        "quality": "Quality modifiers (e.g., 'high quality', '4K, detailed')"
    },
    "model_type": "text-to-image",
    "version": "1.0.0",
}

NEGATIVE_PROMPT = {
    "id": "negative-text-to-image",
    "name": "Text to Image with Negative Prompt",
    "description": "Prompt template with both positive and negative prompts",
    "template": "{prompt} || {negative_prompt}",
    "variables": {
        "prompt": "The main text description of what to include",
        "negative_prompt": "Description of elements to avoid"
    },
    "model_type": "text-to-image",
    "version": "1.0.0",
}

# Export all templates
TEMPLATES: Dict[str, dict] = {
    "basic": BASIC_PROMPT,
    "detailed": DETAILED_PROMPT,
    "negative": NEGATIVE_PROMPT,
} 