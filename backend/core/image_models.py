"""
ALIAS — Image Generation Data Models
Pydantic models for image generation requests and results.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class ImageGenRequest(BaseModel):
    """Request model for image generation."""
    prompt: str = Field(..., description="User's image prompt")
    enhanced_prompt: Optional[str] = Field(None, description="LLM-enhanced prompt (filled by service)")
    width: int = Field(1024, ge=256, le=2048, description="Image width in pixels")
    height: int = Field(1024, ge=256, le=2048, description="Image height in pixels")
    aspect_ratio: str = Field("1:1", description="Aspect ratio preset key")
    quality: str = Field("balanced", description="Quality preset: fast, balanced, high")
    style: Optional[str] = Field(None, description="Style preset key")
    model: str = Field("flux", description="Image model to use")
    seed: Optional[int] = Field(None, description="Seed for reproducibility")
    negative_prompt: Optional[str] = Field(None, description="What to avoid in the image")
    enhance_prompt: bool = Field(True, description="Whether to auto-enhance the prompt via LLM")
    user_email: Optional[str] = Field(None, description="User email for history tracking")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")

    @classmethod
    def from_text(cls, text: str, **overrides):
        """
        Create a request from a raw text command (e.g., from chat).
        Basic parsing — the service handles prompt enhancement.
        """
        import re

        prompt = text.strip()

        # Strip common prefixes (with typo tolerance, optional "please", and flexible articles)
        prefix_pattern = r'^(?:please\s+)?(?:can\s+you\s+)?(?:generate|genrate|generat|create|creat|make|draw|paint|render|produce)\s+(?:an?\s+)?(?:image|photo|picture|pic|wallpaper|logo|drawing|artwork|portrait|sketch)?\s*(?:of\s+|for\s+|with\s+)?'
        prompt = re.sub(prefix_pattern, '', prompt, flags=re.IGNORECASE).strip()

        # Extract dimensions if present (e.g., 1024x768)
        width = overrides.get("width")
        height = overrides.get("height")
        size_match = re.search(r'\b(\d{3,4})\s*[xX]\s*(\d{3,4})\b', prompt)
        if size_match and width is None:
            width = int(size_match.group(1))
            height = int(size_match.group(2))
            prompt = prompt.replace(size_match.group(0), "").strip()

        # Extract model if specified
        model = overrides.get("model", "flux")
        if "using flux" in prompt.lower() or "flux model" in prompt.lower():
            model = "flux"
            prompt = re.sub(r'\busing flux\b', '', prompt, flags=re.IGNORECASE)
            prompt = re.sub(r'\bflux model\b', '', prompt, flags=re.IGNORECASE)
            prompt = re.sub(r'\bflux\b', '', prompt, flags=re.IGNORECASE)
        elif "using turbo" in prompt.lower() or "turbo model" in prompt.lower():
            model = "turbo"
            prompt = re.sub(r'\busing turbo\b', '', prompt, flags=re.IGNORECASE)
            prompt = re.sub(r'\bturbo model\b', '', prompt, flags=re.IGNORECASE)

        # Clean up
        prompt = " ".join(prompt.split()).strip(",. ")

        params = {
            "prompt": prompt,
            "model": model,
        }
        if width is not None:
            params["width"] = max(256, min(width, 2048))
        if height is not None:
            params["height"] = max(256, min(height, 2048))

        # Apply any additional overrides
        for k, v in overrides.items():
            if v is not None:
                params[k] = v

        return cls(**params)


class ImageGenResult(BaseModel):
    """Result model for a completed image generation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    success: bool = False
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    original_prompt: str = ""
    enhanced_prompt: Optional[str] = None
    model: str = "flux"
    provider: str = "pollinations"
    width: int = 1024
    height: int = 1024
    aspect_ratio: str = "1:1"
    quality: str = "balanced"
    style: Optional[str] = None
    seed: Optional[int] = None
    negative_prompt: Optional[str] = None
    generation_time: float = 0.0
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_history_dict(self) -> dict:
        """Convert to a dictionary suitable for the generation history JSON."""
        return {
            "id": self.id,
            "timestamp": self.created_at,
            "prompt": self.original_prompt,
            "enhanced_prompt": self.enhanced_prompt,
            "filename": os.path.basename(self.image_path) if self.image_path else None,
            "width": self.width,
            "height": self.height,
            "aspect_ratio": self.aspect_ratio,
            "quality": self.quality,
            "style": self.style,
            "seed": self.seed if self.seed is not None else -1,
            "model": self.model,
            "provider": self.provider,
            "generation_time": round(self.generation_time, 2),
            "success": self.success,
            "error_message": self.error_message,
        }


# We need os for to_history_dict
import os


class ImageGenAPIRequest(BaseModel):
    """Request model for the /api/images/generate endpoint."""
    prompt: str
    model: str = "flux"
    quality: str = "balanced"
    aspect_ratio: str = "1:1"
    style: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    seed: Optional[int] = None
    negative_prompt: Optional[str] = None
    enhance_prompt: bool = True
    user_email: Optional[str] = None
    conversation_id: Optional[str] = None
