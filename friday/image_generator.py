"""
Friday AI Assistant - Image Generation Module (Core)
This file handles core communication with the Pollinations AI API.
It includes functions to generate images, sanitize prompts, manage request retries,
save metadata history, and automatically display the generated images.
"""

import os
import random
import urllib.parse
import json
import time
from datetime import datetime
import subprocess
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load env variables from backend/.env if it exists
env_path = Path(__file__).parent.parent / 'backend' / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# Base URL for the free Pollinations AI Image API (legacy keyless endpoint)
POLLINATIONS_IMAGE_URL = "https://image.pollinations.ai/prompt/"
# New unified endpoint used when an API key is present
POLLINATIONS_API_IMAGE_URL = "https://gen.pollinations.ai/image/"

# Directory structure configurations
# We use absolute paths based on the file location to keep it robust and independent of the current working directory.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FOLDER = os.path.join(BASE_DIR, "project", "images")
HISTORY_FILE = os.path.join(BASE_DIR, "generation_history.json")


def ensure_directories():
    """
    Checks if the output image folder exists. If not, creates it.
    """
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)
        print(f"[+] Created image directory at: {IMAGE_FOLDER}")


def sanitize_prompt(prompt: str) -> str:
    """
    Cleans the prompt by stripping whitespace, removing special characters
    that are troublesome for URLs, and ensuring it's valid.
    
    Args:
        prompt (str): The raw input prompt.
        
    Returns:
        str: A sanitized prompt.
    """
    if not prompt:
        return ""
    
    # Strip leading/trailing spaces
    sanitized = prompt.strip()
    
    # Replace line breaks or tabs with single spaces
    sanitized = " ".join(sanitized.split())
    
    # Truncate to a maximum sensible URL length (e.g., 800 characters)
    if len(sanitized) > 800:
        sanitized = sanitized[:800]
        
    return sanitized


def get_unique_filename() -> str:
    """
    Generates a unique filename based on the current timestamp (with millisecond precision).
    
    Returns:
        str: File name matching 'generated_<timestamp>.jpg'.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    return f"generated_{timestamp}.jpg"


def open_image(filepath: str):
    """
    Automatically opens the generated image in the system's default viewer.
    Optimized for Windows but includes fallback commands for macOS and Linux.
    
    Args:
        filepath (str): The absolute path of the image file.
    """
    try:
        # Check if file exists before trying to open it
        if not os.path.exists(filepath):
            print(f"[-] Cannot open image. File does not exist: {filepath}")
            return
            
        print(f"[+] Opening image in default viewer: {os.path.basename(filepath)}")
        if os.name == 'nt':  # Windows
            os.startfile(filepath)
        else:  # macOS/Linux fallback
            import platform
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["open", filepath], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", filepath], check=True)
    except Exception as e:
        print(f"[-] Error opening image file: {e}")


def load_history() -> list:
    """
    Loads the generation history from the local JSON file.
    
    Returns:
        list: List of historical generation dictionaries.
    """
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[-] Warning: Failed to read generation history. {e}")
        return []


def save_to_history(prompt: str, filename: str, width: int, height: int, seed: int, model: str, success: bool, error_message: str = None):
    """
    Saves metadata about the image generation attempt to a history log.
    
    Args:
        prompt (str): The prompt used.
        filename (str): The filename of the saved image.
        width (int): Width of the image.
        height (int): Height of the image.
        seed (int): The seed number.
        model (str): The model used (flux, default, etc.).
        success (bool): Whether the generation was successful.
        error_message (str): Optional error message if failed.
    """
    history = load_history()
    
    history_item = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "prompt": prompt,
        "filename": filename,
        "width": width,
        "height": height,
        "seed": seed,
        "model": model,
        "success": success
    }
    if error_message:
        history_item["error_message"] = error_message
    
    # Prepend to history so latest is first
    history.insert(0, history_item)
    
    # Cap history at 100 entries to keep it lightweight
    if len(history) > 100:
        history = history[:100]
        
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[-] Warning: Failed to save history item. {e}")


def generate_via_horde_fallback(prompt: str, save_path: str, width: int = 1024, height: int = 1024) -> tuple[bool, str]:
    """
    Generates an image via the free, keyless AI Horde API as a backup provider.
    
    Args:
        prompt (str): The sanitized prompt.
        save_path (str): Filepath to save the generated image.
        width (int): Requested image width.
        height (int): Requested image height.
        
    Returns:
        tuple[bool, str]: (Success status, error message or empty string)
    """
    print(f"\n[!] Falling back to AI Horde for prompt: '{prompt}'")
    headers = {
        'apikey': '0000000000',
        'Client-Agent': 'ALIAS:2.0:https://github.com/ShravanKatkar/A.L.I.A.S.'
    }
    
    # AI Horde requires Kudos upfront for requests over 580x580 on the anonymous key '0000000000'.
    # We restrict anonymous fallback generation to 512x512 to guarantee acceptance.
    horde_width = 512
    horde_height = 512
    
    payload = {
        'prompt': prompt,
        'params': {
            'width': horde_width,
            'height': horde_height,
            'steps': 20,
            'n': 1
        }
    }
    
    try:
        r = requests.post('https://aihorde.net/api/v2/generate/async', headers=headers, json=payload, timeout=15)
        if r.status_code != 202:
            err = f"AI Horde submission failed (HTTP {r.status_code})"
            print(f"[-] {err}")
            return False, err
            
        job_id = r.json().get('id')
        if not job_id:
            return False, "AI Horde returned empty job ID"
            
        print(f"[+] AI Horde job started. Job ID: {job_id}. Polling for completion...")
        
        # Poll up to 90 seconds
        start_time = time.time()
        while time.time() - start_time < 90:
            time.sleep(3)
            try:
                check = requests.get(f'https://aihorde.net/api/v2/generate/check/{job_id}', timeout=15)
                if check.status_code != 200:
                    continue
                check_json = check.json()
                if check_json.get('done'):
                    break
                elif check_json.get('faulted'):
                    return False, "AI Horde job faulted during processing"
            except requests.RequestException as re:
                print(f"[!] Warning: AI Horde status check request failed: {re}. Retrying...")
                continue
        else:
            return False, "AI Horde generation timed out"
            
        try:
            status = requests.get(f'https://aihorde.net/api/v2/generate/status/{job_id}', timeout=15)
            if status.status_code == 200:
                generations = status.json().get('generations', [])
                if generations:
                    img_url = generations[0].get('img')
                    # Download final image
                    img_resp = requests.get(img_url, timeout=20)
                    if img_resp.status_code == 200:
                        with open(save_path, "wb") as f:
                            f.write(img_resp.content)
                        print(f"[+] Successfully generated and saved image via AI Horde: {save_path}")
                        return True, ""
                    return False, f"Failed to download image from Horde storage (HTTP {img_resp.status_code})"
                return False, "AI Horde returned empty generations array"
            return False, f"Failed to get AI Horde status (HTTP {status.status_code})"
        except requests.RequestException as re:
            return False, f"Failed to retrieve AI Horde result: {re}"
    except Exception as e:
        err_msg = f"AI Horde error: {e}"
        print(f"[-] {err_msg}")
        return False, err_msg


def download_image_with_retry(url: str, save_path: str, prompt: str = "", width: int = 1024, height: int = 1024, retries: int = 3, delay: float = 2.0) -> tuple[bool, str]:
    """
    Downloads the image from the given URL and writes the binary content to a file.
    Includes a retry mechanism for failed requests, self-healing, and automatic
    fallback to AI Horde if Pollinations fails.
    
    Args:
        url (str): The full Pollinations API URL.
        save_path (str): The local path where the image will be saved.
        prompt (str): Prompt used for fallback generation.
        width (int): Width for fallback.
        height (int): Height for fallback.
        retries (int): Number of retries on failure.
        delay (float): Wait time in seconds between retries.
        
    Returns:
        tuple[bool, str]: (True if succeeded, error message if failed)
    """
    api_key = os.getenv("POLLINATIONS_API_KEY")
    headers = {
        "User-Agent": "Friday-Assistant/1.0 (Pollinations AI Image Downloader)"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    last_error = "Unknown error"
    for attempt in range(1, retries + 1):
        try:
            # Setting a 30 second timeout to handle slow generations on server
            response = requests.get(url, headers=headers, timeout=30)
            
            # Self-healing fallback: If custom parameters triggered 402 (Payment Required)
            if response.status_code == 402:
                print("\n[!] Pollinations AI returned 402 (Payment Required / Limit Reached).")
                print("[!] This occurs when custom parameters (dimensions, seeds, nologo) require a paid key.")
                print("[!] Retrying with automatic fallback: stripping premium parameters...")
                
                # Parse URL and strip query params other than model
                parsed_url = urllib.parse.urlparse(url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                
                clean_params = {}
                if "model" in query_params:
                    # Keep the model selection (e.g. flux), as it's typically allowed
                    clean_params["model"] = query_params["model"][0]
                
                # Rebuild URL without seed, width, height, or nologo
                fallback_query = urllib.parse.urlencode(clean_params)
                fallback_url = urllib.parse.urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    fallback_query,
                    parsed_url.fragment
                ))
                
                print(f"[+] Fallback URL: {fallback_url}")
                # Make request to the clean fallback URL
                response = requests.get(fallback_url, headers=headers, timeout=30)
            
            # Check if the server returned success (status code 200)
            if response.status_code == 200:
                # Double-check that we actually received an image and not an HTML error page
                content_type = response.headers.get("Content-Type", "")
                if "image" in content_type:
                    # Write the binary data to the destination file
                    with open(save_path, "wb") as f:
                        f.write(response.content)
                    return True, ""
                else:
                    last_error = f"Invalid content type: {content_type}"
                    print(f"[-] Attempt {attempt}: {last_error}")
            else:
                last_error = f"Pollinations HTTP {response.status_code}"
                print(f"[-] Attempt {attempt}: Server responded with status code {response.status_code}")
                # Try to print more details from 402 or other status codes
                print(f"[-] Response details: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            last_error = f"Pollinations network error: {e}"
            print(f"[-] Attempt {attempt}: Network error occurred: {e}")
            
        # If we failed and have retries left, wait before retrying
        if attempt < retries:
            print(f"[!] Retrying in {delay} seconds...")
            time.sleep(delay)
            # Exponential backoff
            delay *= 1.5
            
    # Primary generator failed, initiate AI Horde fallback
    print("\n[!] Pollinations AI failed. Initiating fallback to AI Horde...")
    horde_success, horde_error = generate_via_horde_fallback(prompt, save_path, width, height)
    if horde_success:
        return True, ""
        
    return False, f"{last_error} | {horde_error}"


def _build_url(prompt: str, width: int = None, height: int = None, seed: int = None, model: str = None) -> str:
    """
    Constructs the final URL for Pollinations AI including query parameters.
    
    Args:
        prompt (str): The sanitized, unencoded prompt.
        width (int): Optional width.
        height (int): Optional height.
        seed (int): Optional seed.
        model (str): Optional model name.
        
    Returns:
        str: The fully formatted URL.
    """
    # URL encode the prompt to handle spaces, punctuation, emojis, and special characters
    encoded_prompt = urllib.parse.quote(prompt)
    
    # Check if API key is present to determine base URL
    api_key = os.getenv("POLLINATIONS_API_KEY")
    if api_key:
        base_url = POLLINATIONS_API_IMAGE_URL
    else:
        base_url = POLLINATIONS_IMAGE_URL
        
    # Construct base URL path
    url = f"{base_url}{encoded_prompt}"
    
    # Build query parameters dictionary
    params = {}
    if width is not None:
        params["width"] = width
    if height is not None:
        params["height"] = height
    if seed is not None:
        params["seed"] = seed
    if model is not None and model.lower() != "default":
        params["model"] = model.lower()
    
    # Disable watermark (clean output)
    params["nologo"] = "true"
    
    # Append query parameters to the URL
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}"
        
    return url


# --- REQUIRED INTERFACE FUNCTIONS ---

def generate_image(prompt: str) -> str:
    """
    Generates a standard image from a text prompt (default 1024x1024, default model).
    
    Args:
        prompt (str): Text describing the image.
        
    Returns:
        str: Path to the saved image file on success, or empty string on failure.
    """
    ensure_directories()
    clean_p = sanitize_prompt(prompt)
    if not clean_p:
        print("[-] Error: Prompt cannot be empty.")
        return ""
        
    filename = get_unique_filename()
    save_path = os.path.join(IMAGE_FOLDER, filename)
    
    # Build URL with defaults (omitting width and height to avoid 402 status codes)
    url = _build_url(clean_p, model="default")
    
    print(f"[+] Requesting standard image: '{clean_p}'")
    print(f"[+] API URL: {url}")
    
    success, error_msg = download_image_with_retry(url, save_path, prompt=clean_p, width=1024, height=1024)
    
    # Track results in local history
    save_to_history(clean_p, filename, 1024, 1024, -1, "default", success, error_msg if not success else None)
    
    if success:
        print(f"[+] Success! Image saved to: {save_path}")
        open_image(save_path)
        return save_path
    else:
        print("[-] Failed to generate image. Please check your network connection or try again later.")
        return ""


def generate_image_with_size(prompt: str, width: int, height: int) -> str:
    """
    Generates an image from a text prompt with custom width and height.
    
    Args:
        prompt (str): Text describing the image.
        width (int): Width in pixels.
        height (int): Height in pixels.
        
    Returns:
        str: Path to the saved image file on success, or empty string on failure.
    """
    ensure_directories()
    clean_p = sanitize_prompt(prompt)
    if not clean_p:
        print("[-] Error: Prompt cannot be empty.")
        return ""
        
    if width is None:
        width = 1024
    if height is None:
        height = 1024

    # Standard fallback constraints to keep the API stable
    width = max(256, min(width, 2048))
    height = max(256, min(height, 2048))
    
    filename = get_unique_filename()
    save_path = os.path.join(IMAGE_FOLDER, filename)
    
    url = _build_url(clean_p, width=width, height=height, model="default")
    
    print(f"[+] Requesting sized image ({width}x{height}): '{clean_p}'")
    print(f"[+] API URL: {url}")
    
    success, error_msg = download_image_with_retry(url, save_path, prompt=clean_p, width=width, height=height)
    
    save_to_history(clean_p, filename, width, height, -1, "default", success, error_msg if not success else None)
    
    if success:
        print(f"[+] Success! Image saved to: {save_path}")
        open_image(save_path)
        return save_path
    else:
        print("[-] Failed to generate image.")
        return ""


def generate_flux_image(prompt: str) -> str:
    """
    Generates an image specifically using the high-quality FLUX model.
    
    Args:
        prompt (str): Text describing the image.
        
    Returns:
        str: Path to the saved image file on success, or empty string on failure.
    """
    ensure_directories()
    clean_p = sanitize_prompt(prompt)
    if not clean_p:
        print("[-] Error: Prompt cannot be empty.")
        return ""
        
    filename = get_unique_filename()
    save_path = os.path.join(IMAGE_FOLDER, filename)
    
    # Generate using flux model (omitting width and height to avoid 402 status codes)
    url = _build_url(clean_p, model="flux")
    
    print(f"[+] Requesting FLUX model image: '{clean_p}'")
    print(f"[+] API URL: {url}")
    
    success, error_msg = download_image_with_retry(url, save_path, prompt=clean_p, width=1024, height=1024)
    
    save_to_history(clean_p, filename, 1024, 1024, -1, "flux", success, error_msg if not success else None)
    
    if success:
        print(f"[+] Success! FLUX Image saved to: {save_path}")
        open_image(save_path)
        return save_path
    else:
        print("[-] Failed to generate image using FLUX model.")
        return ""


def generate_random_image(prompt: str) -> str:
    """
    Generates an image using a randomized seed to ensure variations.
    If the prompt is empty, it selects a random high-quality template prompt.
    
    Args:
        prompt (str): Text describing the image, or empty to pick a random prompt.
        
    Returns:
        str: Path to the saved image file on success, or empty string on failure.
    """
    ensure_directories()
    
    # List of sample high-quality prompts to use if the user didn't specify one
    sample_prompts = [
        "A mystical forest with glowing mushrooms, fireflies, and a crystal clear stream, digital art, highly detailed",
        "A cyberpunk street scene at night with neon lights, rain reflections, flying cars, hyper-detailed",
        "An adorable golden retriever puppy wearing a detective hat, magnifying glass, detective agency background, cinematic lighting",
        "A futuristic space station orbiting a ringed gas giant planet, sci-fi concept art, photorealistic",
        "A cozy cabin in the snowy mountains during sunset, smoke rising from the chimney, warm glowing windows, digital painting",
        "A sleek, modern sports car speeding down a coastal highway at sunrise, motion blur, realistic 3D render",
        "An ancient temple hidden in the jungle with giant waterfalls, vines, and ruins, adventure game style"
    ]
    
    if not prompt or not prompt.strip():
        chosen_prompt = random.choice(sample_prompts)
        print(f"[+] Prompt empty. Selected random prompt: '{chosen_prompt}'")
    else:
        chosen_prompt = prompt
        
    clean_p = sanitize_prompt(chosen_prompt)
    
    # Generate a random seed integer between 0 and 1 billion
    random_seed = random.randint(0, 1000000000)
    
    filename = get_unique_filename()
    save_path = os.path.join(IMAGE_FOLDER, filename)
    
    # Randomly select a model to showcase variety (default or flux)
    chosen_model = random.choice(["default", "flux"])
    
    url = _build_url(clean_p, width=1024, height=1024, seed=random_seed, model=chosen_model)
    
    print(f"[+] Requesting randomized image (Seed: {random_seed}, Model: {chosen_model}): '{clean_p}'")
    print(f"[+] API URL: {url}")
    
    success, error_msg = download_image_with_retry(url, save_path, prompt=clean_p, width=1024, height=1024)
    
    save_to_history(clean_p, filename, 1024, 1024, random_seed, chosen_model, success, error_msg if not success else None)
    
    if success:
        print(f"[+] Success! Randomized image saved to: {save_path}")
        open_image(save_path)
        return save_path
    else:
        print("[-] Failed to generate randomized image.")
        return ""


# General utility functions for higher-level applications
def generate_custom_image(prompt: str, width: int = 1024, height: int = 1024, seed: int = None, model: str = "flux") -> str:
    """
    A fully customizable image generation function that allows setting all parameters.
    
    Args:
        prompt (str): Text describing the image.
        width (int): Image width.
        height (int): Image height.
        seed (int): Optional seed number.
        model (str): Model selection ('default' or 'flux').
        
    Returns:
        str: Path to the saved image file on success, or empty string on failure.
    """
    ensure_directories()
    clean_p = sanitize_prompt(prompt)
    if not clean_p:
        print("[-] Error: Prompt cannot be empty.")
        return ""
        
    filename = get_unique_filename()
    save_path = os.path.join(IMAGE_FOLDER, filename)
    
    if width is None:
        width = 1024
    if height is None:
        height = 1024

    # Validate width/height bounds
    width = max(256, min(width, 2048))
    height = max(256, min(height, 2048))
    
    url = _build_url(clean_p, width=width, height=height, seed=seed, model=model)
    
    print(f"[+] Generating image (Model: {model}, Size: {width}x{height}, Seed: {seed if seed is not None else 'random'}): '{clean_p}'")
    print(f"[+] API URL: {url}")
    
    success, error_msg = download_image_with_retry(url, save_path, prompt=clean_p, width=width, height=height)
    
    seed_val = seed if seed is not None else -1
    save_to_history(clean_p, filename, width, height, seed_val, model, success, error_msg if not success else None)
    
    if success:
        print(f"[+] Success! Image saved to: {save_path}")
        open_image(save_path)
        return save_path
    else:
        print("[-] Failed to generate custom image.")
        return ""
