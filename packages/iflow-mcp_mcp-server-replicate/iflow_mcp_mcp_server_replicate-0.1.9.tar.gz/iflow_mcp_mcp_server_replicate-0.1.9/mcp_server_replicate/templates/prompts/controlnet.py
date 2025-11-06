"""Prompt templates for ControlNet-guided image generation."""

from typing import Dict

CANNY_CONTROL = {
    "id": "canny-controlnet",
    "name": "Canny Edge Control",
    "description": "Template for generating images guided by Canny edge detection",
    "template": "Generate {prompt}, following the edge guidance, {style_instructions}",
    "variables": {
        "prompt": "Description of the image to generate",
        "style_instructions": "Additional style and artistic instructions"
    },
    "model_type": "controlnet",
    "version": "1.0.0",
}

DEPTH_CONTROL = {
    "id": "depth-controlnet",
    "name": "Depth Map Control",
    "description": "Template for generating images guided by depth maps",
    "template": "Create {prompt}, maintaining the provided depth structure, {composition_notes}",
    "variables": {
        "prompt": "Description of the image to generate",
        "composition_notes": "Notes about composition and spatial arrangement"
    },
    "model_type": "controlnet",
    "version": "1.0.0",
}

POSE_CONTROL = {
    "id": "pose-controlnet",
    "name": "Pose Control",
    "description": "Template for generating images guided by pose estimation",
    "template": "Generate {prompt}, following the pose structure, {detail_instructions}",
    "variables": {
        "prompt": "Description of the image to generate",
        "detail_instructions": "Instructions for details and refinements"
    },
    "model_type": "controlnet",
    "version": "1.0.0",
}

SEGMENTATION_CONTROL = {
    "id": "segmentation-controlnet",
    "name": "Segmentation Control",
    "description": "Template for generating images guided by segmentation maps",
    "template": "Create {prompt}, following the segmentation layout, {region_instructions}",
    "variables": {
        "prompt": "Description of the image to generate",
        "region_instructions": "Specific instructions for different regions"
    },
    "model_type": "controlnet",
    "version": "1.0.0",
}

# Export all templates
TEMPLATES: Dict[str, dict] = {
    "canny": CANNY_CONTROL,
    "depth": DEPTH_CONTROL,
    "pose": POSE_CONTROL,
    "segmentation": SEGMENTATION_CONTROL,
} 