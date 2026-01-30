import os
import pyautogui
import time
import subprocess

class AppController:
    def __init__(self):
        # Common paths for Windows apps (Can be expanded)
        self.app_paths = {
            "spotify": "spotify", # Usually in path
            "chrome": "chrome", 
            "notepad": "notepad",
            "calculator": "calc",
            "vscode": "code",
            "explorer": "explorer",
        }

    def open_app(self, app_name):
        """
        Attempts to open an application.
        """
        app_name = app_name.lower().replace(" ", "")
        
        # 1. Check known shortcuts
        if app_name in self.app_paths:
            try:
                os.system(f"start {self.app_paths[app_name]}")
                return f"Opening {app_name}..."
            except Exception as e:
                return f"Failed to open {app_name}: {e}"
        
        # 2. Try generic start command
        try:
            os.system(f"start {app_name}")
            return f"Attempting to open {app_name}..."
        except Exception as e:
            return f"Could not find application: {app_name}"

    def close_constants(self):
        # Placeholder for closing logic if needed
        pass

    def control_media(self, action):
        """
        Controls media playback using global hotkeys.
        """
        if action == "play" or action == "pause":
            pyautogui.press("playpause")
            return "Toggled playback."
        elif action == "next":
            pyautogui.press("nexttrack")
            return "Skipped to next track."
        elif action == "previous":
            pyautogui.press("prevtrack")
            return "Playing previous track."
        elif action == "volume_up":
            pyautogui.press("volumeup")
            return "Increased volume."
        elif action == "volume_down":
            pyautogui.press("volumedown")
            return "Decreased volume."
        
        return "Unknown media command."
