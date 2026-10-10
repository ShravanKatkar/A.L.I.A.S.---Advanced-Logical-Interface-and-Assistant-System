"""
ALIAS — Image Generation Configuration
Centralized configuration for the image generation pipeline.
All magic numbers, model definitions, presets, and provider settings live here.
"""

# =============================================================================
# PROVIDER CONFIGURATION
# =============================================================================

PROVIDERS = {
    "pollinations": {
        "enabled": True,
        "priority": 1,
        "is_fallback": False,
        "label": "Pollinations AI",
        "base_url_keyless": "https://image.pollinations.ai/prompt/",
        "base_url_keyed": "https://gen.pollinations.ai/image/",
        "timeout": 30,
        "max_retries": 3,
        "retry_delay": 2.0,
    },
    "ai_horde": {
        "enabled": True,
        "priority": 2,
        "is_fallback": True,
        "label": "AI Horde",
        "base_url": "https://aihorde.net/api/v2",
        "anonymous_key": "0000000000",
        "timeout": 15,
        "poll_interval": 3,
        "poll_timeout": 90,
        # Anonymous fallback restricted to 512x512
        "max_anonymous_size": 512,
    },
}

# =============================================================================
# IMAGE MODEL DEFINITIONS
# =============================================================================

IMAGE_MODELS = {
    "flux": {
        "provider": "pollinations",
        "label": "FLUX (High Quality)",
        "description": "High-quality image generation with excellent detail and realism",
        "supports_negative_prompt": True,
        "supports_seed": True,
        "supports_custom_dimensions": True,
        "max_width": 2048,
        "max_height": 2048,
        "min_width": 256,
        "min_height": 256,
        "default_steps": 25,
    },
    "turbo": {
        "provider": "pollinations",
        "label": "Turbo (Fast)",
        "description": "Faster generation with good quality, ideal for quick iterations",
        "supports_negative_prompt": True,
        "supports_seed": True,
        "supports_custom_dimensions": True,
        "max_width": 2048,
        "max_height": 2048,
        "min_width": 256,
        "min_height": 256,
        "default_steps": 15,
    },
    "default": {
        "provider": "pollinations",
        "label": "Default",
        "description": "Standard Pollinations model",
        "supports_negative_prompt": False,
        "supports_seed": True,
        "supports_custom_dimensions": True,
        "max_width": 2048,
        "max_height": 2048,
        "min_width": 256,
        "min_height": 256,
        "default_steps": 20,
    },
    "ai_horde_default": {
        "provider": "ai_horde",
        "label": "AI Horde (Fallback)",
        "description": "Community-powered image generation fallback",
        "supports_negative_prompt": False,
        "supports_seed": False,
        "supports_custom_dimensions": False,
        "max_width": 512,
        "max_height": 512,
        "min_width": 512,
        "min_height": 512,
        "default_steps": 20,
    },
}

# =============================================================================
# QUALITY PRESETS
# =============================================================================

QUALITY_PRESETS = {
    "fast": {
        "label": "Fast",
        "description": "Quick generation, good for iterations",
        "preferred_model": "turbo",
        "steps_multiplier": 0.6,
    },
    "balanced": {
        "label": "Balanced",
        "description": "Good balance of speed and quality",
        "preferred_model": "flux",
        "steps_multiplier": 1.0,
    },
    "high": {
        "label": "High Quality",
        "description": "Maximum quality, slower generation",
        "preferred_model": "flux",
        "steps_multiplier": 1.6,
    },
}

# =============================================================================
# ASPECT RATIO PRESETS
# =============================================================================

ASPECT_RATIOS = {
    "1:1": {"width": 1024, "height": 1024, "label": "Square"},
    "16:9": {"width": 1344, "height": 768, "label": "Landscape Wide"},
    "9:16": {"width": 768, "height": 1344, "label": "Portrait Tall"},
    "4:3": {"width": 1024, "height": 768, "label": "Standard"},
    "3:2": {"width": 1024, "height": 680, "label": "Photography"},
    "3:4": {"width": 768, "height": 1024, "label": "Portrait"},
}

# =============================================================================
# STYLE PRESETS
# =============================================================================

STYLE_PRESETS = {
    "none": {
        "label": "None (Use prompt as-is)",
        "suffix": "",
    },
    "photorealistic": {
        "label": "Photorealistic",
        "suffix": "photorealistic, physically accurate materials, realistic lighting, natural shadows, high dynamic range, crisp details",
    },
    "cinematic": {
        "label": "Cinematic",
        "suffix": "cinematic composition, dramatic lighting, film grain, shallow depth of field, anamorphic lens, movie still",
    },
    "anime": {
        "label": "Anime",
        "suffix": "anime style, cel-shaded, vibrant colors, detailed linework, Japanese animation aesthetic",
    },
    "digital_art": {
        "label": "Digital Art",
        "suffix": "digital art, detailed illustration, vibrant colors, clean lines, professional digital painting",
    },
    "illustration": {
        "label": "Illustration",
        "suffix": "hand-drawn illustration, artistic, detailed, professional illustration style, editorial quality",
    },
    "3d_render": {
        "label": "3D Render",
        "suffix": "3D render, octane render, volumetric lighting, subsurface scattering, physically based rendering, high detail",
    },
    "oil_painting": {
        "label": "Oil Painting",
        "suffix": "oil painting style, rich colors, visible brushstrokes, textured canvas, classical painting technique",
    },
    "watercolor": {
        "label": "Watercolor",
        "suffix": "watercolor painting, soft gradients, paper texture, delicate washes, artistic watercolor technique",
    },
}

# =============================================================================
# PROMPT ENHANCEMENT CONFIGURATION
# =============================================================================

PROMPT_ENHANCER_SYSTEM_INSTRUCTION = """You are an expert image-generation prompt engineer.

Convert the user's short image request into a detailed production-quality image prompt.

Include when appropriate:
- Subject: precise description of the main subject
- Environment: setting, surroundings, background
- Composition: framing, perspective, focal point
- Camera: angle, lens type (e.g., 35mm, 85mm), depth of field
- Lighting: type (natural, dramatic, studio), direction, color temperature
- Materials: surface textures, reflections, material properties
- Colors: color palette, contrast, saturation
- Atmosphere: mood, weather, time of day
- Visual quality: level of detail, rendering style

Rules:
- Do NOT change the user's intended subject
- Do NOT add unnecessary objects or people that weren't requested
- Do NOT include explanations or commentary
- Do NOT include meta-instructions like "8K, masterpiece, best quality"
- DO use specific, descriptive visual language
- DO describe actual visual details rather than quality keywords
- Return ONLY the final image prompt as a single paragraph
"""

PROMPT_ENHANCER_MODEL = "gemini-2.5-flash"
PROMPT_ENHANCER_TEMPERATURE = 0.7

# =============================================================================
# INTENT DETECTION
# =============================================================================

# Primary verb-noun patterns for image generation intent (includes common typos)
IMAGE_INTENT_VERBS = [
    "generate", "genrate", "generat", "generating",
    "create", "creat", "creating",
    "make", "making",
    "draw", "drawing",
    "paint", "painting",
    "render", "rendering",
    "design", "produce", "craft", "sketch", "illustrate"
]

IMAGE_INTENT_NOUNS = [
    "image", "photo", "picture", "pic", "wallpaper", "logo", "drawing",
    "sketch", "illustration", "painting", "artwork", "portrait",
    "poster", "banner", "icon", "thumbnail", "render"
]

# Full phrase patterns (higher confidence)
IMAGE_INTENT_PHRASES = [
    "generate image", "genrate image", "create image", "make image", "draw image",
    "generate an image", "genrate an image", "generate a image", "genrate a image",
    "create an image", "create a image", "make an image", "make a image",
    "generate wallpaper", "create wallpaper", "make wallpaper",
    "generate logo", "create logo", "make logo",
    "generate photo", "create photo", "make photo", "generate a photo",
    "draw a picture", "draw an illustration", "paint a picture",
    "generate a picture", "create a picture", "make a picture",
    "design a logo", "design a poster", "design a banner",
    "render an image", "render a scene",
]

# Phrases that should NOT trigger image generation
IMAGE_INTENT_EXCLUSIONS = [
    "what is", "explain", "how does", "how do", "tell me about",
    "describe", "define", "analyze", "compare", "review",
    "fix", "debug", "code", "write code", "program",
]

# =============================================================================
# GENERATION LIMITS
# =============================================================================

MAX_GENERATION_ATTEMPTS = 2
GENERATION_TIMEOUT_SECONDS = 60
MAX_PROMPT_LENGTH = 800
HISTORY_MAX_ENTRIES = 100

# =============================================================================
# STORAGE
# =============================================================================

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent  # Alias2.0 root
IMAGE_STORAGE_DIR = BASE_DIR / "friday" / "project" / "images"
HISTORY_FILE = BASE_DIR / "friday" / "generation_history.json"

# Ensure directories exist
os.makedirs(IMAGE_STORAGE_DIR, exist_ok=True)


def get_available_image_models():
    """Returns a list of image model configs for the frontend."""
    models = []
    for model_id, config in IMAGE_MODELS.items():
        provider = PROVIDERS.get(config["provider"], {})
        if provider.get("enabled", False) and not provider.get("is_fallback", False):
            models.append({
                "id": model_id,
                "label": config["label"],
                "description": config["description"],
                "supports_negative_prompt": config["supports_negative_prompt"],
                "supports_seed": config["supports_seed"],
                "supports_custom_dimensions": config["supports_custom_dimensions"],
            })
    return models


def get_available_styles():
    """Returns style presets for the frontend."""
    return [{"id": k, "label": v["label"]} for k, v in STYLE_PRESETS.items()]


def get_available_aspect_ratios():
    """Returns aspect ratio presets for the frontend."""
    return [{"id": k, "label": v["label"], "width": v["width"], "height": v["height"]} for k, v in ASPECT_RATIOS.items()]


def get_available_quality_presets():
    """Returns quality presets for the frontend."""
    return [{"id": k, "label": v["label"], "description": v["description"]} for k, v in QUALITY_PRESETS.items()]
