"""Common model configuration templates that can be reused across different models."""

from typing import Any

QUALITY_PRESETS = {
    "id": "quality-presets",
    "name": "Quality Presets",
    "description": "Common quality presets for different generation scenarios",
    "model_type": "any",
    "presets": {
        "draft": {
            "description": "Fast draft quality for quick iterations",
            "parameters": {
                "num_inference_steps": 20,
                "guidance_scale": 5.0,
                "width": 512,
                "height": 512,
            },
        },
        "balanced": {
            "description": "Balanced quality and speed for most use cases",
            "parameters": {
                "num_inference_steps": 30,
                "guidance_scale": 7.5,
                "width": 768,
                "height": 768,
            },
        },
        "quality": {
            "description": "High quality for final outputs",
            "parameters": {
                "num_inference_steps": 50,
                "guidance_scale": 7.5,
                "width": 1024,
                "height": 1024,
            },
        },
        "extreme": {
            "description": "Maximum quality, very slow",
            "parameters": {
                "num_inference_steps": 150,
                "guidance_scale": 8.0,
                "width": 1536,
                "height": 1536,
            },
        },
    },
    "version": "1.0.0",
}

STYLE_PRESETS = {
    "id": "style-presets",
    "name": "Style Presets",
    "description": "Common style presets for different artistic looks",
    "model_type": "any",
    "presets": {
        "photorealistic": {
            "description": "Highly detailed photorealistic style",
            "parameters": {
                "prompt_prefix": "professional photograph, photorealistic, highly detailed, 8k uhd",
                "negative_prompt": "painting, drawing, illustration, anime, cartoon, artistic, unrealistic",
                "guidance_scale": 8.0,
            },
        },
        "cinematic": {
            "description": "Dramatic cinematic style",
            "parameters": {
                "prompt_prefix": "cinematic shot, dramatic lighting, movie scene, high budget film",
                "negative_prompt": "low quality, amateur, poorly lit",
                "guidance_scale": 7.5,
            },
        },
        "anime": {
            "description": "Anime/manga style",
            "parameters": {
                "prompt_prefix": "anime style, manga art, clean lines, vibrant colors",
                "negative_prompt": "photorealistic, 3d render, photograph, western art style",
                "guidance_scale": 7.0,
            },
        },
        "digital_art": {
            "description": "Digital art style",
            "parameters": {
                "prompt_prefix": "digital art, vibrant colors, detailed illustration",
                "negative_prompt": "photograph, realistic, grainy, noisy",
                "guidance_scale": 7.0,
            },
        },
        "oil_painting": {
            "description": "Oil painting style",
            "parameters": {
                "prompt_prefix": "oil painting, textured brushstrokes, artistic, rich colors",
                "negative_prompt": "photograph, digital art, 3d render, smooth",
                "guidance_scale": 7.0,
            },
        },
    },
    "version": "1.0.0",
}

ASPECT_RATIO_PRESETS = {
    "id": "aspect-ratio-presets",
    "name": "Aspect Ratio Presets",
    "description": "Common aspect ratio presets for different use cases",
    "model_type": "any",
    "presets": {
        "square": {
            "description": "1:1 square format",
            "parameters": {
                "width": 1024,
                "height": 1024,
            },
        },
        "portrait": {
            "description": "2:3 portrait format",
            "parameters": {
                "width": 832,
                "height": 1216,
            },
        },
        "landscape": {
            "description": "3:2 landscape format",
            "parameters": {
                "width": 1216,
                "height": 832,
            },
        },
        "wide": {
            "description": "16:9 widescreen format",
            "parameters": {
                "width": 1344,
                "height": 768,
            },
        },
        "mobile": {
            "description": "9:16 mobile format",
            "parameters": {
                "width": 768,
                "height": 1344,
            },
        },
    },
    "version": "1.0.0",
}

NEGATIVE_PROMPT_PRESETS = {
    "id": "negative-prompt-presets",
    "name": "Negative Prompt Presets",
    "description": "Common negative prompts for quality control",
    "model_type": "any",
    "presets": {
        "quality_control": {
            "description": "Basic quality control negative prompt",
            "parameters": {"negative_prompt": "ugly, blurry, low quality, distorted, disfigured, bad anatomy"},
        },
        "strict_quality": {
            "description": "Strict quality control negative prompt",
            "parameters": {
                "negative_prompt": "ugly, blurry, low quality, distorted, disfigured, bad anatomy, bad proportions, duplicate, extra limbs, missing limbs, poorly drawn face, poorly drawn hands, mutation, mutated, extra fingers, missing fingers, floating limbs, disconnected limbs, malformed limbs, oversaturated, undersaturated"
            },
        },
        "photo_quality": {
            "description": "Photo-specific quality control",
            "parameters": {
                "negative_prompt": "blurry, low quality, noise, grain, chromatic aberration, lens flare, overexposed, underexposed, bad composition, amateur, poorly lit"
            },
        },
        "artistic_quality": {
            "description": "Art-specific quality control",
            "parameters": {
                "negative_prompt": "amateur, poorly drawn, bad art, poorly drawn hands, poorly drawn face, poorly drawn eyes, poorly drawn nose, poorly drawn mouth, poorly drawn ears, poorly drawn body, poorly drawn legs, poorly drawn feet"
            },
        },
    },
    "version": "1.0.0",
}

# Export all templates
TEMPLATES: dict[str, dict[str, Any]] = {
    "quality": QUALITY_PRESETS,
    "style": STYLE_PRESETS,
    "aspect_ratio": ASPECT_RATIO_PRESETS,
    "negative_prompt": NEGATIVE_PROMPT_PRESETS,
}
