"""
ALIAS — Image Generation Service
The main orchestration layer that ties together:
  - Intent detection
  - Prompt enhancement (LLM-powered)
  - Provider routing
  - Generation execution
  - History tracking
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

import google.generativeai as genai

from core.image_config import (
    IMAGE_MODELS, QUALITY_PRESETS, ASPECT_RATIOS, STYLE_PRESETS,
    PROMPT_ENHANCER_SYSTEM_INSTRUCTION, PROMPT_ENHANCER_MODEL,
    PROMPT_ENHANCER_TEMPERATURE, IMAGE_INTENT_VERBS, IMAGE_INTENT_NOUNS,
    IMAGE_INTENT_PHRASES, IMAGE_INTENT_EXCLUSIONS,
    MAX_GENERATION_ATTEMPTS, MAX_PROMPT_LENGTH, HISTORY_MAX_ENTRIES,
    IMAGE_STORAGE_DIR, HISTORY_FILE,
    get_available_image_models, get_available_styles,
    get_available_aspect_ratios, get_available_quality_presets,
)
from core.image_models import ImageGenRequest, ImageGenResult
from core.image_providers import get_provider, get_fallback_providers


class ImageGenerationService:
    """
    Main image generation orchestration service.
    Handles the full pipeline from user input to generated image.
    """

    def __init__(self, llm=None):
        """
        Args:
            llm: Optional LLMEngine instance (used for future advanced features).
                 Prompt enhancement uses Gemini directly for isolation.
        """
        self.llm = llm
        self._gemini_configured = bool(os.getenv("GEMINI_API_KEY"))

    # =========================================================================
    # INTENT DETECTION
    # =========================================================================

    def detect_image_intent(self, text: str) -> bool:
        """
        Determine if the user's message is an image generation request.
        Uses pattern matching with exclusion rules for high accuracy.

        Args:
            text: The user's raw input text.

        Returns:
            True if this appears to be an image generation request.
        """
        if not text:
            return False

        lower = text.lower().strip()

        # Check exclusions first — educational/informational queries about images
        for exclusion in IMAGE_INTENT_EXCLUSIONS:
            if lower.startswith(exclusion):
                return False

        # Check full phrase patterns (highest confidence)
        for phrase in IMAGE_INTENT_PHRASES:
            if phrase in lower:
                return True

        # Check verb + noun combination patterns (flexible matching)
        import re
        verbs_pattern = r'\b(?:' + '|'.join(IMAGE_INTENT_VERBS) + r')\b'
        nouns_pattern = r'\b(?:' + '|'.join(IMAGE_INTENT_NOUNS) + r')\b'
        if re.search(rf'{verbs_pattern}.*?{nouns_pattern}', lower):
            return True

        return False

    # =========================================================================
    # PROMPT ENHANCEMENT
    # =========================================================================

    def enhance_prompt(self, user_prompt: str, style: str = None) -> str:
        """
        Use Gemini to expand a simple user prompt into a detailed image generation prompt.

        Args:
            user_prompt: The user's short/simple prompt.
            style: Optional style preset key to guide the enhancement.

        Returns:
            Enhanced prompt string. Falls back to original prompt on failure.
        """
        if not self._gemini_configured:
            print("[ImageService] Gemini not configured — skipping prompt enhancement")
            return self._apply_style_suffix(user_prompt, style)

        try:
            system_instruction = PROMPT_ENHANCER_SYSTEM_INSTRUCTION

            # Add style guidance if specified
            if style and style != "none" and style in STYLE_PRESETS:
                style_config = STYLE_PRESETS[style]
                system_instruction += f"\n\nThe user wants this style: {style_config['label']}. "
                system_instruction += f"Incorporate this aesthetic: {style_config['suffix']}"

            generation_config = genai.types.GenerationConfig(
                temperature=PROMPT_ENHANCER_TEMPERATURE,
                max_output_tokens=500,
            )

            model = genai.GenerativeModel(
                PROMPT_ENHANCER_MODEL,
                system_instruction=system_instruction,
            )

            response = model.generate_content(
                user_prompt,
                generation_config=generation_config,
            )

            enhanced = response.text.strip()
            if enhanced:
                print(f"[ImageService] Prompt enhanced: '{user_prompt[:40]}...' → '{enhanced[:60]}...'")
                return enhanced

        except Exception as e:
            print(f"[ImageService] Prompt enhancement failed: {e}")

        # Fallback: apply style suffix to original prompt
        return self._apply_style_suffix(user_prompt, style)

    def _apply_style_suffix(self, prompt: str, style: str = None) -> str:
        """Apply style suffix to a prompt as a fallback when LLM enhancement fails."""
        if style and style != "none" and style in STYLE_PRESETS:
            suffix = STYLE_PRESETS[style]["suffix"]
            if suffix:
                return f"{prompt}, {suffix}"
        return prompt

    # =========================================================================
    # GENERATION
    # =========================================================================

    def generate(self, request: ImageGenRequest) -> ImageGenResult:
        """
        Full image generation pipeline:
        1. Apply quality preset
        2. Apply aspect ratio
        3. Enhance prompt (if enabled)
        4. Select provider
        5. Generate image
        6. Fallback to alternative providers on failure
        7. Save to history

        Args:
            request: ImageGenRequest with all generation parameters.

        Returns:
            ImageGenResult with the generation outcome.
        """
        start_time = time.time()

        result = ImageGenResult(
            original_prompt=request.prompt,
            model=request.model,
            width=request.width,
            height=request.height,
            aspect_ratio=request.aspect_ratio,
            quality=request.quality,
            style=request.style,
            seed=request.seed,
            negative_prompt=request.negative_prompt,
        )

        # --- 1. Apply quality preset ---
        quality_config = QUALITY_PRESETS.get(request.quality, QUALITY_PRESETS["balanced"])
        if request.model == "flux" or request.model == "default":
            # Quality preset can override model if user selected "auto"
            pass

        # --- 2. Apply aspect ratio ---
        if request.aspect_ratio in ASPECT_RATIOS and request.width == 1024 and request.height == 1024:
            # Only override dimensions if user hasn't set custom ones
            ar = ASPECT_RATIOS[request.aspect_ratio]
            request.width = ar["width"]
            request.height = ar["height"]
            result.width = request.width
            result.height = request.height

        # --- 3. Enhance prompt ---
        if request.enhance_prompt:
            enhanced = self.enhance_prompt(request.prompt, request.style)
            request.enhanced_prompt = enhanced
            result.enhanced_prompt = enhanced
        else:
            # Still apply style suffix even without full enhancement
            enhanced = self._apply_style_suffix(request.prompt, request.style)
            request.enhanced_prompt = enhanced
            result.enhanced_prompt = enhanced

        # Use enhanced prompt for generation
        generation_prompt = request.enhanced_prompt or request.prompt

        # Truncate to max length
        if len(generation_prompt) > MAX_PROMPT_LENGTH:
            generation_prompt = generation_prompt[:MAX_PROMPT_LENGTH]

        # --- 4. Select primary provider ---
        model_config = IMAGE_MODELS.get(request.model, IMAGE_MODELS.get("flux"))
        provider_name = model_config.get("provider", "pollinations")

        # --- 5. Generate ---
        success = False
        attempts = 0

        while not success and attempts < MAX_GENERATION_ATTEMPTS:
            attempts += 1
            try:
                provider = get_provider(provider_name)
                print(f"[ImageService] Attempt {attempts}/{MAX_GENERATION_ATTEMPTS} via {provider.name}")

                gen_success, save_path, error_msg = provider.generate(
                    prompt=generation_prompt,
                    width=request.width,
                    height=request.height,
                    seed=request.seed,
                    model=request.model if request.model != "default" else None,
                    negative_prompt=request.negative_prompt,
                )

                if gen_success and save_path:
                    result.success = True
                    result.image_path = save_path
                    result.provider = provider.name
                    filename = os.path.basename(save_path)
                    result.image_url = f"http://127.0.0.1:8000/images/{filename}"
                    success = True
                else:
                    result.error_message = error_msg
                    print(f"[ImageService] Provider {provider.name} failed: {error_msg}")

            except Exception as e:
                result.error_message = str(e)
                print(f"[ImageService] Provider error: {e}")

        # --- 6. Fallback to alternative providers ---
        if not success:
            print("[ImageService] Primary provider failed — trying fallbacks...")
            for fallback_provider in get_fallback_providers():
                if fallback_provider.name == provider_name:
                    continue  # Skip the one we already tried

                try:
                    print(f"[ImageService] Fallback attempt via {fallback_provider.name}")
                    fb_success, fb_path, fb_error = fallback_provider.generate(
                        prompt=generation_prompt,
                        width=request.width,
                        height=request.height,
                    )

                    if fb_success and fb_path:
                        result.success = True
                        result.image_path = fb_path
                        result.provider = fallback_provider.name
                        filename = os.path.basename(fb_path)
                        result.image_url = f"http://127.0.0.1:8000/images/{filename}"
                        success = True
                        break
                    else:
                        result.error_message = f"{result.error_message} | {fb_error}"

                except Exception as e:
                    result.error_message = f"{result.error_message} | Fallback error: {e}"

        # --- 7. Finalize ---
        result.generation_time = time.time() - start_time

        # Save to history
        self._save_to_history(result)

        if result.success:
            print(f"[ImageService] ✓ Generated in {result.generation_time:.1f}s via {result.provider}")
        else:
            print(f"[ImageService] ✗ Failed after {result.generation_time:.1f}s: {result.error_message}")

        return result

    # =========================================================================
    # HISTORY
    # =========================================================================

    def _load_history(self) -> list:
        """Load generation history from JSON file."""
        history_path = str(HISTORY_FILE)
        if not os.path.exists(history_path):
            return []
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ImageService] Warning: Failed to read history: {e}")
            return []

    def _save_to_history(self, result: ImageGenResult):
        """Save a generation result to the history file."""
        history = self._load_history()
        history.insert(0, result.to_history_dict())

        if len(history) > HISTORY_MAX_ENTRIES:
            history = history[:HISTORY_MAX_ENTRIES]

        try:
            history_path = str(HISTORY_FILE)
            os.makedirs(os.path.dirname(history_path), exist_ok=True)
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ImageService] Warning: Failed to save history: {e}")

    def get_history(self, limit: int = 20) -> list:
        """Get generation history, most recent first."""
        history = self._load_history()
        return history[:limit]

    def get_generation_by_id(self, gen_id: str) -> dict:
        """Find a specific generation by its ID."""
        for item in self._load_history():
            if item.get("id") == gen_id:
                return item
        return None

    # =========================================================================
    # CONFIGURATION API
    # =========================================================================

    def get_config(self) -> dict:
        """Return the full image generation configuration for the frontend."""
        return {
            "models": get_available_image_models(),
            "styles": get_available_styles(),
            "aspect_ratios": get_available_aspect_ratios(),
            "quality_presets": get_available_quality_presets(),
        }
