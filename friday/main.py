"""
Friday AI Assistant - Image Generation CLI
This file provides the Command Line Interface (CLI) and command parsing logic.
It accepts voice/text-like instructions, parses them, starts a visual loading animation,
calls the core generator, and manages user interaction.
"""

import os
import sys
import time
import threading
from datetime import datetime

# Import core image generator functions
import image_generator

# Example prompts requested by user
EXAMPLE_PROMPTS = {
    "realistic": "A photorealistic portrait of an old sailor, weathered face, deep wrinkles, dramatic cinematic lighting, shot on 85mm lens, hyper-detailed",
    "anime": "Anime style illustration of a magical girl standing on a skyscraper rooftop at twilight, wind in her hair, starry night sky, colorful, highly detailed",
    "cyberpunk": "Cyberpunk city street scene at night with vibrant neon signs, rain reflections on wet tarmac, flying vehicles, retro-futurism, 8k resolution",
    "logos": "A minimalist geometric logo for a tech startup, clean lines, white background, vector style, flat design, modern teal and orange color palette",
    "wallpapers": "Breathtaking landscape of a glowing fantasy forest with a giant moon, pastel colors, 16:9 aspect ratio, digital painting, desktop wallpaper",
    "thumbnails": "Eye-catching YouTube thumbnail background, abstract glowing digital pattern, dark theme with vibrant orange accents, high contrast, copy space"
}


class LoadingSpinner:
    """
    A terminal-based loading animation runner that spins in a background thread.
    Useful for representing long-running network requests like image generation.
    """
    def __init__(self, message="Friday is generating your image"):
        self.message = message
        self.running = False
        self._thread = None

    def _spin(self):
        # Spinner characters
        spinner = ["|", "/", "-", "\\"]
        idx = 0
        while self.running:
            # \r returns cursor to start of line, writing the spinner
            sys.stdout.write(f"\r[+] {self.message}... {spinner[idx]} ")
            sys.stdout.flush()
            idx = (idx + 1) % len(spinner)
            time.sleep(0.1)
        # Clean the line when stopped
        sys.stdout.write("\r" + " " * (len(self.message) + 20) + "\r")
        sys.stdout.flush()

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join()


def parse_command(command_str: str) -> dict:
    """
    Parses voice/text-like commands to extract the prompt, size, and model.
    E.g., "generate image of a futuristic city 1920x1080 using flux"
    
    Args:
        command_str (str): Input text command.
        
    Returns:
        dict: Extracted parameters.
    """
    import re
    
    cmd = command_str.strip()
    if not cmd:
        return {}

    # Define prefixes used in voice/text commands
    prefixes = [
        "generate image of ", "generate an image of ", "generate image ", "generate ",
        "create image of ", "create an image of ", "create image ", "create ",
        "make image of ", "make an image of ", "make ",
        "draw image of ", "draw a ", "draw "
    ]

    # Find and strip out prefixes to get the raw prompt
    parsed_prompt = cmd
    for prefix in prefixes:
        if cmd.lower().startswith(prefix.lower()):
            parsed_prompt = cmd[len(prefix):]
            break

    # Look for dimensions (e.g., 1024x768 or 512 x 512)
    width = None
    height = None
    
    size_match = re.search(r'\b(\d{3,4})\s*[xX]\s*(\d{3,4})\b', parsed_prompt)
    if size_match:
        width = int(size_match.group(1))
        height = int(size_match.group(2))
        # Remove dimensions from prompt so it's not passed as text to the API
        parsed_prompt = parsed_prompt.replace(size_match.group(0), "")

    # Look for aspect ratio keywords
    if "square" in parsed_prompt.lower():
        width = 1024
        height = 1024
        parsed_prompt = re.sub(r'\bsquare\b', '', parsed_prompt, flags=re.IGNORECASE)
    elif "portrait" in parsed_prompt.lower():
        width = 768
        height = 1024
        parsed_prompt = re.sub(r'\bportrait\b', '', parsed_prompt, flags=re.IGNORECASE)
    elif "landscape" in parsed_prompt.lower():
        width = 1024
        height = 768
        parsed_prompt = re.sub(r'\blandscape\b', '', parsed_prompt, flags=re.IGNORECASE)

    # Check if FLUX model is explicitly requested
    model = "default"
    if "flux" in parsed_prompt.lower():
        model = "flux"
        # Remove flux related instructions from prompt text
        parsed_prompt = re.sub(r'\busing flux\b', '', parsed_prompt, flags=re.IGNORECASE)
        parsed_prompt = re.sub(r'\bflux model\b', '', parsed_prompt, flags=re.IGNORECASE)
        parsed_prompt = re.sub(r'\bflux\b', '', parsed_prompt, flags=re.IGNORECASE)

    # Clean up multiple whitespaces and trailing commas/dots
    parsed_prompt = " ".join(parsed_prompt.split())
    parsed_prompt = parsed_prompt.strip(",. ")

    return {
        "prompt": parsed_prompt,
        "width": width,
        "height": height,
        "model": model
    }


def execute_parsed_command(parsed: dict):
    """
    Invokes the core generator based on parsed configurations.
    
    Args:
        parsed (dict): The dictionary from parse_command.
    """
    if not parsed or not parsed.get("prompt"):
        print("[-] Command parsed, but no valid prompt was found.")
        return

    prompt = parsed["prompt"]
    width = parsed["width"]
    height = parsed["height"]
    model = parsed["model"]

    spinner = LoadingSpinner(f"Friday is generating '{prompt[:30]}...'")
    spinner.start()

    try:
        if width and height:
            # Custom size generation
            # If the user specified flux model as well, we call custom generator directly
            image_generator.generate_custom_image(prompt, width=width, height=height, model=model)
        elif model == "flux":
            # Standard flux generation
            image_generator.generate_flux_image(prompt)
        else:
            # Default generation
            image_generator.generate_image(prompt)
    finally:
        spinner.stop()


def show_examples():
    """
    Prints example prompts that show off different design styles.
    """
    print("\n" + "=" * 60)
    print("                 EXAMPLE DESIGN PROMPTS")
    print("=" * 60)
    for category, prompt in EXAMPLE_PROMPTS.items():
        print(f"\n* {category.upper()}:")
        print(f"  Prompt: \"{prompt}\"")
    print("=" * 60)


def show_history():
    """
    Prints a formatted table of past image generations.
    """
    history = image_generator.load_history()
    if not history:
        print("\n[i] No image generation history found yet.")
        return

    print("\n" + "=" * 90)
    print("                             IMAGE GENERATION HISTORY")
    print("=" * 90)
    # Print headers
    print(f"{'Timestamp':<20} | {'Model':<8} | {'Dimensions':<11} | {'Status':<7} | {'Prompt Preview'}")
    print("-" * 90)
    
    for item in history[:10]:  # Limit display to top 10 items
        timestamp = item.get("timestamp", "N/A")
        model = item.get("model", "default")
        dims = f"{item.get('width', 1024)}x{item.get('height', 1024)}"
        status = "SUCCESS" if item.get("success", False) else "FAILED"
        prompt = item.get("prompt", "")
        # Truncate prompt if too long
        prompt_preview = prompt[:40] + "..." if len(prompt) > 40 else prompt
        
        print(f"{timestamp:<20} | {model:<8} | {dims:<11} | {status:<7} | {prompt_preview}")
    print("=" * 90)


def main():
    """
    Main loop running the interactive CLI.
    """
    # Ensure folders are set up on startup
    image_generator.ensure_directories()
    
    print("\n" + "=" * 60)
    print("      FRIDAY AI ASSISTANT - IMAGE GENERATION TERMINAL")
    print("=" * 60)
    print("Optimized for Windows. Uses Pollinations AI free API.")
    print("Commands can be descriptive or natural language, e.g.:")
    print("  > generate image of a cybernetic tiger 1920x1080 using flux")
    print("  > create anime girl portrait")
    print("  > make startup logo")
    print("=" * 60)

    while True:
        try:
            print("\nOptions:")
            print("1. Enter Voice/Text command")
            print("2. Browse template prompts")
            print("3. View generation history")
            print("4. Exit")
            
            choice = input("\nFriday > Select an option (1-4): ").strip()
            
            if choice == "1":
                command = input("Friday > Enter command: ").strip()
                if not command:
                    print("[-] Command cannot be empty.")
                    continue
                
                # Parse and execute
                parsed = parse_command(command)
                execute_parsed_command(parsed)
                
            elif choice == "2":
                show_examples()
                # Let user choose one immediately
                sub_choice = input("\nFriday > Select a category name (or press Enter to return): ").strip().lower()
                if sub_choice in EXAMPLE_PROMPTS:
                    prompt = EXAMPLE_PROMPTS[sub_choice]
                    
                    # Ask if they want flux
                    use_flux = input("Friday > Use FLUX model? (y/n, default yes): ").strip().lower()
                    model = "flux" if use_flux != "n" else "default"
                    
                    # Ask for size
                    size_input = input("Friday > Enter size (e.g. 1024x1024, or press Enter for default): ").strip()
                    width, height = None, None
                    if size_input:
                        import re
                        match = re.search(r'(\d+)\s*[xX]\s*(\d+)', size_input)
                        if match:
                            width = int(match.group(1))
                            height = int(match.group(2))
                            
                    parsed = {
                        "prompt": prompt,
                        "width": width,
                        "height": height,
                        "model": model
                    }
                    execute_parsed_command(parsed)
                elif sub_choice:
                    print(f"[-] Invalid category: '{sub_choice}'")
                    
            elif choice == "3":
                show_history()
                
            elif choice == "4" or choice.lower() == "exit":
                print("\n[+] Goodbye, Shravan! Exiting Friday Image Generation Module.")
                break
            else:
                # Fallback: Treat raw input as option 1 if it doesn't match 1-4
                if choice:
                    print(f"[i] Treating input as natural language command...")
                    parsed = parse_command(choice)
                    execute_parsed_command(parsed)
                    
        except KeyboardInterrupt:
            print("\n\n[i] Operation interrupted. Returning to main menu.")
        except Exception as e:
            print(f"\n[-] An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
