"""
ALIAS — Image Generation Providers
Abstract provider interface with concrete implementations for Pollinations AI and AI Horde.
Each provider handles raw API communication and returns standardized results.
"""

import os
import time
import urllib.parse
import requests
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from core.image_config import PROVIDERS, IMAGE_MODELS, IMAGE_STORAGE_DIR

# Load env
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class ProviderCapabilities:
    """Describes what a provider supports."""
    def __init__(self, supports_negative_prompt=False, supports_seed=False,
                 supports_custom_dimensions=False, supports_img2img=False,
                 max_width=1024, max_height=1024, min_width=256, min_height=256):
        self.supports_negative_prompt = supports_negative_prompt
        self.supports_seed = supports_seed
        self.supports_custom_dimensions = supports_custom_dimensions
        self.supports_img2img = supports_img2img
        self.max_width = max_width
        self.max_height = max_height
        self.min_width = min_width
        self.min_height = min_height


class ImageProvider(ABC):
    """Abstract base class for image generation providers."""

    @abstractmethod
    def generate(self, prompt: str, width: int = 1024, height: int = 1024,
                 seed: int = None, model: str = None, negative_prompt: str = None,
                 save_path: str = None) -> tuple:
        """
        Generate an image.

        Returns:
            tuple: (success: bool, save_path: str or None, error_message: str or None)
        """
        pass

    @abstractmethod
    def get_capabilities(self, model: str = None) -> ProviderCapabilities:
        """Return the capabilities of this provider for the given model."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is currently reachable."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier string."""
        pass


class PollinationsProvider(ImageProvider):
    """
    Pollinations AI image generation provider.
    Supports both keyless (free) and keyed API endpoints.
    """

    def __init__(self):
        self.config = PROVIDERS.get("pollinations", {})
        self.api_key = os.getenv("POLLINATIONS_API_KEY")

    @property
    def name(self) -> str:
        return "pollinations"

    def _build_url(self, prompt: str, width: int = None, height: int = None,
                   seed: int = None, model: str = None, negative_prompt: str = None) -> str:
        """Construct the Pollinations API URL."""
        encoded_prompt = urllib.parse.quote(prompt)

        if self.api_key:
            base_url = self.config.get("base_url_keyed", "https://gen.pollinations.ai/image/")
        else:
            base_url = self.config.get("base_url_keyless", "https://image.pollinations.ai/prompt/")

        url = f"{base_url}{encoded_prompt}"

        params = {}
        if width is not None:
            params["width"] = width
        if height is not None:
            params["height"] = height
        if seed is not None:
            params["seed"] = seed
        if model is not None and model.lower() != "default":
            params["model"] = model.lower()
        if negative_prompt:
            params["negative"] = negative_prompt

        # Disable watermark
        params["nologo"] = "true"

        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"

        return url

    def generate(self, prompt: str, width: int = 1024, height: int = 1024,
                 seed: int = None, model: str = None, negative_prompt: str = None,
                 save_path: str = None) -> tuple:
        """Generate an image via Pollinations AI with retry and self-healing."""
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            save_path = str(IMAGE_STORAGE_DIR / f"generated_{timestamp}.jpg")

        url = self._build_url(prompt, width=width, height=height, seed=seed,
                              model=model, negative_prompt=negative_prompt)

        headers = {
            "User-Agent": "ALIAS-Assistant/2.0 (Image Generation Pipeline)"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        retries = self.config.get("max_retries", 3)
        delay = self.config.get("retry_delay", 2.0)
        timeout = self.config.get("timeout", 30)
        last_error = "Unknown error"

        for attempt in range(1, retries + 1):
            try:
                print(f"[ImageProvider:Pollinations] Attempt {attempt}/{retries} — URL: {url[:100]}...")
                response = requests.get(url, headers=headers, timeout=timeout)

                # Self-healing: strip premium params on 402 and use free tier
                if response.status_code == 402:
                    print("[ImageProvider:Pollinations] 402 Payment Required — falling back to standard free model")
                    parsed_url = urllib.parse.urlparse(url)
                    clean_params = {"model": "turbo", "nologo": "true"}
                    fallback_query = urllib.parse.urlencode(clean_params)
                    fallback_url = urllib.parse.urlunparse((
                        parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                        parsed_url.params, fallback_query, parsed_url.fragment
                    ))
                    response = requests.get(fallback_url, headers=headers, timeout=timeout)
                    if response.status_code == 402:
                        # Try completely unparameterized URL
                        clean_base = urllib.parse.urlunparse((
                            parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                            "", "", ""
                        ))
                        response = requests.get(clean_base, headers=headers, timeout=timeout)

                if response.status_code == 200:
                    content_type = response.headers.get("Content-Type", "")
                    if "image" in content_type:
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        with open(save_path, "wb") as f:
                            f.write(response.content)
                        print(f"[ImageProvider:Pollinations] Success — saved to {save_path}")
                        return True, save_path, None
                    else:
                        last_error = f"Invalid content type: {content_type}"
                        print(f"[ImageProvider:Pollinations] {last_error}")
                else:
                    last_error = f"HTTP {response.status_code}"
                    print(f"[ImageProvider:Pollinations] {last_error}: {response.text[:200]}")

            except requests.exceptions.RequestException as e:
                last_error = f"Network error: {e}"
                print(f"[ImageProvider:Pollinations] {last_error}")

            if attempt < retries:
                print(f"[ImageProvider:Pollinations] Retrying in {delay:.1f}s...")
                time.sleep(delay)
                delay *= 1.5

        return False, None, last_error

    def get_capabilities(self, model: str = None) -> ProviderCapabilities:
        model_config = IMAGE_MODELS.get(model or "flux", IMAGE_MODELS["flux"])
        return ProviderCapabilities(
            supports_negative_prompt=model_config.get("supports_negative_prompt", True),
            supports_seed=model_config.get("supports_seed", True),
            supports_custom_dimensions=model_config.get("supports_custom_dimensions", True),
            max_width=model_config.get("max_width", 2048),
            max_height=model_config.get("max_height", 2048),
            min_width=model_config.get("min_width", 256),
            min_height=model_config.get("min_height", 256),
        )

    def is_available(self) -> bool:
        try:
            resp = requests.head("https://image.pollinations.ai/", timeout=5)
            return resp.status_code < 500
        except Exception:
            return False


class AIHordeProvider(ImageProvider):
    """
    AI Horde image generation provider.
    Free, community-powered, used as fallback when Pollinations fails.
    """

    def __init__(self):
        self.config = PROVIDERS.get("ai_horde", {})
        self.api_key = self.config.get("anonymous_key", "0000000000")

    @property
    def name(self) -> str:
        return "ai_horde"

    def generate(self, prompt: str, width: int = 512, height: int = 512,
                 seed: int = None, model: str = None, negative_prompt: str = None,
                 save_path: str = None) -> tuple:
        """Generate an image via AI Horde async API."""
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            save_path = str(IMAGE_STORAGE_DIR / f"generated_{timestamp}.jpg")

        # Anonymous key restricted to 512x512
        max_size = self.config.get("max_anonymous_size", 512)
        horde_width = min(width, max_size)
        horde_height = min(height, max_size)

        print(f"[ImageProvider:AIHorde] Generating ({horde_width}x{horde_height}): '{prompt[:50]}...'")

        base_url = self.config.get("base_url", "https://aihorde.net/api/v2")
        headers = {
            "apikey": self.api_key,
            "Client-Agent": "ALIAS:2.0:https://github.com/ShravanKatkar/A.L.I.A.S."
        }

        payload = {
            "prompt": prompt,
            "params": {
                "width": horde_width,
                "height": horde_height,
                "steps": 20,
                "n": 1
            }
        }

        try:
            # Submit job
            r = requests.post(f"{base_url}/generate/async", headers=headers, json=payload, timeout=15)
            if r.status_code != 202:
                return False, None, f"AI Horde submission failed (HTTP {r.status_code})"

            job_id = r.json().get("id")
            if not job_id:
                return False, None, "AI Horde returned empty job ID"

            print(f"[ImageProvider:AIHorde] Job started: {job_id}")

            # Poll for completion
            poll_interval = self.config.get("poll_interval", 3)
            poll_timeout = self.config.get("poll_timeout", 90)
            start_time = time.time()

            while time.time() - start_time < poll_timeout:
                time.sleep(poll_interval)
                try:
                    check = requests.get(f"{base_url}/generate/check/{job_id}", timeout=15)
                    if check.status_code != 200:
                        continue
                    check_json = check.json()
                    if check_json.get("done"):
                        break
                    elif check_json.get("faulted"):
                        return False, None, "AI Horde job faulted during processing"
                except requests.RequestException as e:
                    print(f"[ImageProvider:AIHorde] Poll warning: {e}")
                    continue
            else:
                return False, None, "AI Horde generation timed out"

            # Retrieve result
            status = requests.get(f"{base_url}/generate/status/{job_id}", timeout=15)
            if status.status_code == 200:
                generations = status.json().get("generations", [])
                if generations:
                    img_url = generations[0].get("img")
                    img_resp = requests.get(img_url, timeout=20)
                    if img_resp.status_code == 200:
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        with open(save_path, "wb") as f:
                            f.write(img_resp.content)
                        print(f"[ImageProvider:AIHorde] Success — saved to {save_path}")
                        return True, save_path, None
                    return False, None, f"Failed to download from Horde (HTTP {img_resp.status_code})"
                return False, None, "AI Horde returned empty generations"
            return False, None, f"Failed to get status (HTTP {status.status_code})"

        except Exception as e:
            return False, None, f"AI Horde error: {e}"

    def get_capabilities(self, model: str = None) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_negative_prompt=False,
            supports_seed=False,
            supports_custom_dimensions=False,
            max_width=512,
            max_height=512,
            min_width=512,
            min_height=512,
        )

    def is_available(self) -> bool:
        try:
            resp = requests.get("https://aihorde.net/api/v2/status/heartbeat", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


# =============================================================================
# Provider Registry
# =============================================================================

_provider_instances = {}


def get_provider(provider_name: str) -> ImageProvider:
    """Get or create a provider instance by name."""
    if provider_name not in _provider_instances:
        if provider_name == "pollinations":
            _provider_instances[provider_name] = PollinationsProvider()
        elif provider_name == "ai_horde":
            _provider_instances[provider_name] = AIHordeProvider()
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
    return _provider_instances[provider_name]


def get_fallback_providers() -> list:
    """Get providers marked as fallback, sorted by priority."""
    fallback = []
    for name, config in PROVIDERS.items():
        if config.get("enabled") and config.get("is_fallback"):
            fallback.append((config.get("priority", 99), name))
    fallback.sort()
    return [get_provider(name) for _, name in fallback]
