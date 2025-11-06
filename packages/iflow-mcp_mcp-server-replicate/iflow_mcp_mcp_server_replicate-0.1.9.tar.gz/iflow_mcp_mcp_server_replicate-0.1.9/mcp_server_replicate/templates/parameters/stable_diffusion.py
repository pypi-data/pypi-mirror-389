"""Parameter templates for Stable Diffusion models."""

from typing import Dict, Any

SDXL_PARAMETERS = {
    "id": "sdxl-base",
    "name": "SDXL Base Parameters",
    "description": "Default parameters for SDXL models with comprehensive options for high-quality image generation",
    "model_type": "stable-diffusion",
    "default_parameters": {
        "width": 1024,
        "height": 1024,
        "num_inference_steps": 50,
        "guidance_scale": 7.5,
        "prompt_strength": 1.0,
        "refine": "expert_ensemble_refiner",
        "scheduler": "K_EULER",
        "num_outputs": 1,
        "high_noise_frac": 0.8,
        "seed": None,
        "apply_watermark": True,
    },
    "parameter_schema": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string", 
                "description": "Text prompt for image generation. Use descriptive language and artistic terms for better results.",
                "minLength": 1,
                "maxLength": 2000
            },
            "negative_prompt": {
                "type": "string", 
                "description": "Text prompt for elements to avoid. Common defaults: 'ugly, blurry, low quality, distorted'",
                "maxLength": 2000
            },
            "width": {
                "type": "integer", 
                "minimum": 512, 
                "maximum": 2048, 
                "multipleOf": 8,
                "description": "Image width in pixels. Must be multiple of 8. Larger sizes need more memory."
            },
            "height": {
                "type": "integer", 
                "minimum": 512, 
                "maximum": 2048, 
                "multipleOf": 8,
                "description": "Image height in pixels. Must be multiple of 8. Larger sizes need more memory."
            },
            "num_inference_steps": {
                "type": "integer", 
                "minimum": 1, 
                "maximum": 150,
                "description": "Number of denoising steps. Higher values = better quality but slower generation."
            },
            "guidance_scale": {
                "type": "number", 
                "minimum": 1, 
                "maximum": 20,
                "description": "How closely to follow the prompt. Higher values = more literal but may be less creative."
            },
            "prompt_strength": {
                "type": "number", 
                "minimum": 0, 
                "maximum": 1,
                "description": "Strength of the prompt in image-to-image tasks. 1.0 = full prompt strength."
            },
            "refine": {
                "type": "string", 
                "enum": ["no_refiner", "expert_ensemble_refiner", "base_image_refiner"],
                "description": "Type of refinement to apply. expert_ensemble_refiner provides best quality."
            },
            "scheduler": {
                "type": "string", 
                "enum": ["DDIM", "DPM_MULTISTEP", "K_EULER", "PNDM", "KLMS"],
                "description": "Sampling method. K_EULER is a good default, DDIM for more deterministic results."
            },
            "num_outputs": {
                "type": "integer", 
                "minimum": 1, 
                "maximum": 4,
                "description": "Number of images to generate in parallel. More outputs = longer generation time."
            },
            "high_noise_frac": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Fraction of inference steps to use for high noise. Higher = more variation."
            },
            "seed": {
                "type": ["integer", "null"],
                "minimum": 0,
                "maximum": 2147483647,
                "description": "Random seed for reproducible generation. null for random seed."
            },
            "apply_watermark": {
                "type": "boolean",
                "description": "Whether to apply invisible watermarking to detect AI-generated images."
            }
        },
        "required": ["prompt"]
    },
    "version": "1.1.0",
}

SD_15_PARAMETERS = {
    "id": "sd-1.5-base",
    "name": "Stable Diffusion 1.5 Parameters",
    "description": "Default parameters for SD 1.5 models with comprehensive options for stable image generation",
    "model_type": "stable-diffusion",
    "default_parameters": {
        "width": 512,
        "height": 512,
        "num_inference_steps": 50,
        "guidance_scale": 7.5,
        "scheduler": "K_EULER",
        "num_outputs": 1,
        "seed": None,
        "apply_watermark": True,
    },
    "parameter_schema": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string", 
                "description": "Text prompt for image generation. Use descriptive language and artistic terms.",
                "minLength": 1,
                "maxLength": 2000
            },
            "negative_prompt": {
                "type": "string", 
                "description": "Text prompt for elements to avoid. Common defaults: 'ugly, blurry, low quality'",
                "maxLength": 2000
            },
            "width": {
                "type": "integer", 
                "minimum": 256, 
                "maximum": 1024, 
                "multipleOf": 8,
                "description": "Image width in pixels. Must be multiple of 8. SD 1.5 works best at 512x512."
            },
            "height": {
                "type": "integer", 
                "minimum": 256, 
                "maximum": 1024, 
                "multipleOf": 8,
                "description": "Image height in pixels. Must be multiple of 8. SD 1.5 works best at 512x512."
            },
            "num_inference_steps": {
                "type": "integer", 
                "minimum": 1, 
                "maximum": 150,
                "description": "Number of denoising steps. Higher values = better quality but slower."
            },
            "guidance_scale": {
                "type": "number", 
                "minimum": 1, 
                "maximum": 20,
                "description": "How closely to follow the prompt. 7.5 is a good default."
            },
            "scheduler": {
                "type": "string", 
                "enum": ["DDIM", "DPM_MULTISTEP", "K_EULER", "PNDM", "KLMS"],
                "description": "Sampling method. K_EULER is a good default for quality/speed balance."
            },
            "num_outputs": {
                "type": "integer", 
                "minimum": 1, 
                "maximum": 4,
                "description": "Number of images to generate in parallel. More outputs = longer time."
            },
            "seed": {
                "type": ["integer", "null"],
                "minimum": 0,
                "maximum": 2147483647,
                "description": "Random seed for reproducible generation. null for random seed."
            },
            "apply_watermark": {
                "type": "boolean",
                "description": "Whether to apply invisible watermarking to detect AI-generated images."
            }
        },
        "required": ["prompt"]
    },
    "version": "1.1.0",
}

# Export all templates
TEMPLATES: Dict[str, Dict[str, Any]] = {
    "sdxl": SDXL_PARAMETERS,
    "sd15": SD_15_PARAMETERS,
} 