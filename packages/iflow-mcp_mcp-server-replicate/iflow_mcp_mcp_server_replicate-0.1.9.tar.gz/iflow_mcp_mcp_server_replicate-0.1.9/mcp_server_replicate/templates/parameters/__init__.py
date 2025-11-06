"""Parameter templates for Replicate models."""

from .common_configs import TEMPLATES as COMMON_TEMPLATES
from .stable_diffusion import TEMPLATES as SD_TEMPLATES
from .controlnet import TEMPLATES as CONTROLNET_TEMPLATES

# Merge all templates
TEMPLATES = {
    **COMMON_TEMPLATES,
    **SD_TEMPLATES,
    **CONTROLNET_TEMPLATES,
}

__all__ = ["TEMPLATES"] 