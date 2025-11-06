"""Parameter templates for ControlNet models."""

from typing import Dict, Any
from enum import Enum

class ControlMode(str, Enum):
    """Control modes for ControlNet."""
    BALANCED = "balanced"
    PROMPT = "prompt"
    CONTROL = "control"

CONTROLNET_PARAMETERS = {
    "id": "controlnet-base",
    "name": "ControlNet Base Parameters",
    "description": "Parameters for ControlNet-enabled Stable Diffusion models",
    "model_type": "controlnet",
    "default_parameters": {
        "control_mode": "balanced",
        "control_scale": 0.9,
        "begin_control_step": 0.0,
        "end_control_step": 1.0,
        "detection_resolution": 512,
        "image_resolution": 512,
        "guess_mode": False,
    },
    "parameter_schema": {
        "type": "object",
        "properties": {
            "control_image": {
                "type": "string",
                "format": "uri",
                "description": "URL or base64 of the control image (edge map, depth map, pose, etc.)"
            },
            "control_mode": {
                "type": "string",
                "enum": ["balanced", "prompt", "control"],
                "description": "How to balance between prompt and control. balanced=0.5/0.5, prompt=0.25/0.75, control=0.75/0.25"
            },
            "control_scale": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 2.0,
                "description": "Overall influence of the control signal. Higher values = stronger control."
            },
            "begin_control_step": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "When to start applying control (0.0 = start, 1.0 = end)"
            },
            "end_control_step": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "When to stop applying control (0.0 = start, 1.0 = end)"
            },
            "detection_resolution": {
                "type": "integer",
                "minimum": 256,
                "maximum": 1024,
                "multipleOf": 8,
                "description": "Resolution for control signal detection. Higher = more detail but slower."
            },
            "image_resolution": {
                "type": "integer",
                "minimum": 256,
                "maximum": 1024,
                "multipleOf": 8,
                "description": "Output image resolution. Should match detection_resolution for best results."
            },
            "guess_mode": {
                "type": "boolean",
                "description": "Enable 'guess mode' for reference-only control (no exact matching)"
            },
            "preprocessor": {
                "type": "string",
                "enum": [
                    "canny",
                    "depth",
                    "mlsd",
                    "normal",
                    "openpose",
                    "scribble",
                    "seg",
                    "shuffle",
                    "softedge",
                    "tile"
                ],
                "description": "Type of preprocessing to apply to control image"
            }
        },
        "required": ["control_image", "preprocessor"],
        "dependencies": {
            "preprocessor": {
                "oneOf": [
                    {
                        "properties": {
                            "preprocessor": {"enum": ["canny"]},
                            "low_threshold": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 255,
                                "description": "Lower threshold for Canny edge detection"
                            },
                            "high_threshold": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 255,
                                "description": "Upper threshold for Canny edge detection"
                            }
                        }
                    },
                    {
                        "properties": {
                            "preprocessor": {"enum": ["mlsd"]},
                            "score_threshold": {
                                "type": "number",
                                "minimum": 0.1,
                                "maximum": 0.9,
                                "description": "Confidence threshold for line detection"
                            },
                            "distance_threshold": {
                                "type": "number",
                                "minimum": 0.1,
                                "maximum": 20.0,
                                "description": "Distance threshold for line merging"
                            }
                        }
                    }
                ]
            }
        }
    },
    "version": "1.0.0"
}

# Export all templates
TEMPLATES: Dict[str, Dict[str, Any]] = {
    "controlnet": CONTROLNET_PARAMETERS,
} 