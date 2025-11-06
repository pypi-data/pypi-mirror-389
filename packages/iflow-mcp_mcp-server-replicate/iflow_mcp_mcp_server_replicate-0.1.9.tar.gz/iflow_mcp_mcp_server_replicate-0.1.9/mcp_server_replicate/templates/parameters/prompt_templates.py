"""Prompt templates for different generation tasks and styles."""

from typing import Dict, Any

TEXT_TO_IMAGE_TEMPLATES = {
    "id": "text-to-image-prompts",
    "name": "Text to Image Prompt Templates",
    "description": "Templates for generating effective text-to-image prompts",
    "model_type": "any",
    "templates": {
        "detailed_scene": {
            "description": "Template for detailed scene descriptions",
            "format": "{subject} in {setting}, {lighting} lighting, {mood} atmosphere, {style} style, {details}",
            "examples": [
                {
                    "parameters": {
                        "subject": "a young explorer",
                        "setting": "ancient temple ruins",
                        "lighting": "dramatic golden hour",
                        "mood": "mysterious",
                        "style": "cinematic",
                        "details": "vines growing on weathered stone, dust particles in light beams"
                    },
                    "result": "a young explorer in ancient temple ruins, dramatic golden hour lighting, mysterious atmosphere, cinematic style, vines growing on weathered stone, dust particles in light beams"
                }
            ],
            "parameter_descriptions": {
                "subject": "Main subject or focus of the image",
                "setting": "Location or environment",
                "lighting": "Type and quality of lighting",
                "mood": "Overall emotional tone",
                "style": "Visual or artistic style",
                "details": "Additional specific details"
            }
        },
        "character_portrait": {
            "description": "Template for character portraits",
            "format": "{gender} {character_type}, {appearance}, {clothing}, {expression}, {pose}, {style} style, {background}",
            "examples": [
                {
                    "parameters": {
                        "gender": "female",
                        "character_type": "warrior",
                        "appearance": "long red hair, battle-scarred",
                        "clothing": "ornate plate armor",
                        "expression": "determined look",
                        "pose": "heroic stance",
                        "style": "digital art",
                        "background": "stormy sky"
                    },
                    "result": "female warrior, long red hair, battle-scarred, ornate plate armor, determined look, heroic stance, digital art style, stormy sky"
                }
            ],
            "parameter_descriptions": {
                "gender": "Character's gender",
                "character_type": "Role or profession",
                "appearance": "Physical characteristics",
                "clothing": "Outfit description",
                "expression": "Facial expression",
                "pose": "Body position",
                "style": "Visual style",
                "background": "Background setting"
            }
        },
        "landscape": {
            "description": "Template for landscape scenes",
            "format": "{environment} landscape, {time_of_day}, {weather}, {features}, {style} style, {mood} mood",
            "examples": [
                {
                    "parameters": {
                        "environment": "mountain",
                        "time_of_day": "sunset",
                        "weather": "partly cloudy",
                        "features": "snow-capped peaks, alpine lake, pine forest",
                        "style": "oil painting",
                        "mood": "peaceful"
                    },
                    "result": "mountain landscape, sunset, partly cloudy, snow-capped peaks, alpine lake, pine forest, oil painting style, peaceful mood"
                }
            ],
            "parameter_descriptions": {
                "environment": "Type of landscape",
                "time_of_day": "Time of day",
                "weather": "Weather conditions",
                "features": "Notable landscape features",
                "style": "Visual style",
                "mood": "Emotional atmosphere"
            }
        }
    },
    "version": "1.0.0"
}

IMAGE_TO_IMAGE_TEMPLATES = {
    "id": "image-to-image-prompts",
    "name": "Image to Image Prompt Templates",
    "description": "Templates for effective image-to-image modification prompts",
    "model_type": "any",
    "templates": {
        "style_transfer": {
            "description": "Template for transferring style to an image",
            "format": "Transform into {style} style, {quality} quality, maintain {preserve} from original",
            "examples": [
                {
                    "parameters": {
                        "style": "oil painting",
                        "quality": "masterpiece",
                        "preserve": "composition and lighting"
                    },
                    "result": "Transform into oil painting style, masterpiece quality, maintain composition and lighting from original"
                }
            ],
            "parameter_descriptions": {
                "style": "Target artistic style",
                "quality": "Quality level",
                "preserve": "Elements to preserve"
            }
        },
        "variation": {
            "description": "Template for creating variations",
            "format": "Similar to original but with {changes}, {style} style, {quality} quality",
            "examples": [
                {
                    "parameters": {
                        "changes": "different color scheme",
                        "style": "same",
                        "quality": "high quality"
                    },
                    "result": "Similar to original but with different color scheme, same style, high quality"
                }
            ],
            "parameter_descriptions": {
                "changes": "Desired changes",
                "style": "Style modification",
                "quality": "Quality level"
            }
        }
    },
    "version": "1.0.0"
}

CONTROLNET_TEMPLATES = {
    "id": "controlnet-prompts",
    "name": "ControlNet Prompt Templates",
    "description": "Templates for ControlNet-guided image generation",
    "model_type": "controlnet",
    "templates": {
        "pose_guided": {
            "description": "Template for pose-guided generation",
            "format": "{subject} in {pose_description}, {clothing}, {style} style, {background}",
            "examples": [
                {
                    "parameters": {
                        "subject": "young athlete",
                        "pose_description": "dynamic running pose",
                        "clothing": "sports attire",
                        "style": "photorealistic",
                        "background": "track field"
                    },
                    "result": "young athlete in dynamic running pose, sports attire, photorealistic style, track field"
                }
            ],
            "parameter_descriptions": {
                "subject": "Main subject",
                "pose_description": "Description of the pose",
                "clothing": "Outfit description",
                "style": "Visual style",
                "background": "Background setting"
            }
        },
        "depth_guided": {
            "description": "Template for depth-guided generation",
            "format": "{subject} with {depth_elements}, {perspective}, {style} style",
            "examples": [
                {
                    "parameters": {
                        "subject": "forest path",
                        "depth_elements": "trees fading into distance",
                        "perspective": "one-point perspective",
                        "style": "photorealistic"
                    },
                    "result": "forest path with trees fading into distance, one-point perspective, photorealistic style"
                }
            ],
            "parameter_descriptions": {
                "subject": "Main subject",
                "depth_elements": "Elements showing depth",
                "perspective": "Type of perspective",
                "style": "Visual style"
            }
        }
    },
    "version": "1.0.0"
}

# Export all templates
TEMPLATES: Dict[str, Dict[str, Any]] = {
    "text_to_image": TEXT_TO_IMAGE_TEMPLATES,
    "image_to_image": IMAGE_TO_IMAGE_TEMPLATES,
    "controlnet": CONTROLNET_TEMPLATES,
} 