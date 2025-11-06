"""Prompt templates for image-to-image transformation models."""

from typing import Dict

BASIC_TRANSFORM = {
    "id": "basic-image-transform",
    "name": "Basic Image Transform",
    "description": "Simple template for image transformation with guidance text",
    "template": "{prompt}",
    "variables": {
        "prompt": "Text description of the desired transformation"
    },
    "model_type": "image-to-image",
    "version": "1.0.0",
}

STYLE_TRANSFER = {
    "id": "style-transfer",
    "name": "Style Transfer",
    "description": "Template for artistic style transfer with detailed style instructions",
    "template": "Transform the image in the style of {style_description}, {additional_details}",
    "variables": {
        "style_description": "Description of the target artistic style",
        "additional_details": "Additional style and quality specifications"
    },
    "model_type": "image-to-image",
    "version": "1.0.0",
}

INPAINTING = {
    "id": "inpainting",
    "name": "Image Inpainting",
    "description": "Template for image inpainting with mask and instructions",
    "template": "Replace the masked area with {replacement_description}, maintaining {consistency_instructions}",
    "variables": {
        "replacement_description": "Description of what to generate in the masked area",
        "consistency_instructions": "Instructions for maintaining consistency with the rest of the image"
    },
    "model_type": "image-to-image",
    "version": "1.0.0",
}

# Export all templates
TEMPLATES: Dict[str, dict] = {
    "basic": BASIC_TRANSFORM,
    "style": STYLE_TRANSFER,
    "inpainting": INPAINTING,
} 