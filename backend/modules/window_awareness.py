import pygetwindow as gw
import time

class WindowAwareness:
    def __init__(self):
        pass

    def get_active_window(self):
        """
        Returns the title of the currently active window.
        """
        try:
            window = gw.getActiveWindow()
            if window:
                return window.title
            return "Unknown Window"
        except Exception as e:
            return f"Error detecting window: {e}"

    def get_active_app_name(self):
        """
        Tries to extract the app name from the window title.
        """
        title = self.get_active_window()
        if " - " in title:
            return title.split(" - ")[-1] # Heuristic: "Song - Artist" or "Doc - Word"
        return title
