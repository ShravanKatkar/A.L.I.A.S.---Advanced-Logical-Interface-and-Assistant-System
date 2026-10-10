import os
import re
import sys
import shutil
import time
import urllib.parse
import webbrowser
import subprocess
import pyautogui

class AppController:
    """
    Robust application and web control module for ALIAS.
    Handles desktop apps, system tools, Windows URI schemes,
    popular web services (YouTube, Google, etc.), and custom web searches.
    """

    def __init__(self):
        # Known web services and their direct URLs + optional search templates
        self.web_services = {
            "youtube": ("https://www.youtube.com", "https://www.youtube.com/results?search_query={query}"),
            "google": ("https://www.google.com", "https://www.google.com/search?q={query}"),
            "github": ("https://www.github.com", "https://github.com/search?q={query}"),
            "gmail": ("https://mail.google.com", None),
            "reddit": ("https://www.reddit.com", "https://www.reddit.com/search/?q={query}"),
            "twitter": ("https://x.com", "https://x.com/search?q={query}"),
            "x": ("https://x.com", "https://x.com/search?q={query}"),
            "linkedin": ("https://www.linkedin.com", "https://www.linkedin.com/search/results/all/?keywords={query}"),
            "chatgpt": ("https://chatgpt.com", None),
            "claude": ("https://claude.ai", None),
            "netflix": ("https://www.netflix.com", "https://www.netflix.com/search?q={query}"),
            "amazon": ("https://www.amazon.com", "https://www.amazon.com/s?k={query}"),
            "wikipedia": ("https://www.wikipedia.org", "https://en.wikipedia.org/wiki/Special:Search?search={query}"),
            "instagram": ("https://www.instagram.com", None),
            "facebook": ("https://www.facebook.com", None),
            "whatsapp": ("https://web.whatsapp.com", None),
            "twitch": ("https://www.twitch.tv", "https://www.twitch.tv/search?term={query}"),
            "spotify web": ("https://open.spotify.com", "https://open.spotify.com/search/{query}"),
            "maps": ("https://www.google.com/maps", "https://www.google.com/maps/search/{query}"),
            "drive": ("https://drive.google.com", None),
            "docs": ("https://docs.google.com", None),
            "flipkart": ("https://www.flipkart.com", "https://www.flipkart.com/search?q={query}"),
            "canva": ("https://www.canva.com", None),
            "pinterest": ("https://www.pinterest.com", "https://www.pinterest.com/search/pins/?q={query}"),
        }

        # Common Windows desktop applications and URI schemes
        self.app_targets = {
            "calc": "calc",
            "calculator": "calc",
            "notepad": "notepad",
            "paint": "mspaint",
            "mspaint": "mspaint",
            "cmd": "cmd",
            "commandprompt": "cmd",
            "terminal": "wt",
            "powershell": "powershell",
            "taskmanager": "taskmgr",
            "taskmgr": "taskmgr",
            "explorer": "explorer",
            "files": "explorer",
            "fileexplorer": "explorer",
            "mycomputer": "explorer",
            "word": "winword",
            "winword": "winword",
            "microsoftword": "winword",
            "excel": "excel",
            "microsoftexcel": "excel",
            "powerpoint": "powerpnt",
            "powerpnt": "powerpnt",
            "ppt": "powerpnt",
            "code": "code",
            "vscode": "code",
            "vs code": "code",
            "visualstudiocode": "code",
            "chrome": "chrome",
            "googlechrome": "chrome",
            "edge": "msedge",
            "msedge": "msedge",
            "microsoftedge": "msedge",
            "brave": "brave",
            "firefox": "firefox",
            "spotify": "spotify",
            "discord": "discord",
            "slack": "slack",
            "telegram": "telegram",
            "zoom": "zoom",
            "vlc": "vlc",
            "settings": "ms-settings:",
            "windowssettings": "ms-settings:",
            "camera": "microsoft.windows.camera:",
            "windowscamera": "microsoft.windows.camera:",
            "store": "ms-windows-store:",
            "windowsstore": "ms-windows-store:",
            "photos": "ms-photos:",
        }

    def detect_open_intent(self, text: str):
        """
        Detects if text is a command to open an app, website, or search YouTube/Google.
        Returns a dict with action details or None.
        """
        if not text:
            return None

        clean = text.strip()
        lower = clean.lower()

        # Remove polite prefixes and greeting fillers
        lower = re.sub(r'^(can you |could you |please |hey alias |alias |would you kindly )+', '', lower).strip()
        lower = re.sub(r'[.!?]+$', '', lower).strip()

        # 1. Search YouTube pattern: "search [for] X on youtube", "find X on youtube", "play X on youtube"
        m = re.match(r'^(?:(?:search(?:\s+for)?|find|look\s+up|play)\s+)?(.+?)\s+(?:on|in)\s+youtube$', lower)
        if m:
            query = m.group(1).strip()
            # Clean accidental keywords
            query = re.sub(r'^(search for|search|play|find)\s+', '', query).strip()
            if query:
                return {"action": "youtube_search", "query": query, "raw": text}

        # "open youtube and search/play X"
        m = re.match(r'^open\s+youtube\s+(?:and\s+)?(?:search(?:\s+for)?|play|find)\s+(.+)$', lower)
        if m:
            return {"action": "youtube_search", "query": m.group(1).strip(), "raw": text}

        # 2. Search Google pattern: "search [for] X on google", "google X"
        m = re.match(r'^(?:(?:search(?:\s+for)?|find|look\s+up)\s+)?(.+?)\s+(?:on|in)\s+google$', lower)
        if m:
            query = m.group(1).strip()
            query = re.sub(r'^(search for|search|find)\s+', '', query).strip()
            if query:
                return {"action": "google_search", "query": query, "raw": text}

        m = re.match(r'^open\s+google\s+(?:and\s+)?(?:search(?:\s+for)?|find)\s+(.+)$', lower)
        if m:
            return {"action": "google_search", "query": m.group(1).strip(), "raw": text}

        m = re.match(r'^google\s+(.+)$', lower)
        if m and not m.group(1).strip().startswith("chrome"):
            return {"action": "google_search", "query": m.group(1).strip(), "raw": text}

        # 3. Open target pattern: "open [up] X", "launch X", "start X", "run X", "go to X"
        m = re.match(r'^(?:open(?:\s+up)?|launch|start|run|go\s+to|bring\s+up)\s+(.+)$', lower)
        if m:
            target = m.group(1).strip()
            # Clean common trailing punctuation or polite words
            target = re.sub(r'\s+(for me|please)$', '', target).strip()
            return {"action": "open_target", "target": target, "raw": text}

        return None

    def execute_open(self, intent: dict) -> str:
        """
        Executes a parsed open/search intent.
        """
        action = intent.get("action")
        if action == "youtube_search":
            query = intent.get("query", "")
            encoded = urllib.parse.quote_plus(query)
            url = f"https://www.youtube.com/results?search_query={encoded}"
            try:
                webbrowser.open_new_tab(url)
                return f"Searching YouTube for \"{query}\" in your browser..."
            except Exception as e:
                return f"Failed to search YouTube: {e}"

        elif action == "google_search":
            query = intent.get("query", "")
            encoded = urllib.parse.quote_plus(query)
            url = f"https://www.google.com/search?q={encoded}"
            try:
                webbrowser.open_new_tab(url)
                return f"Searching Google for \"{query}\" in your browser..."
            except Exception as e:
                return f"Failed to search Google: {e}"

        elif action == "open_target":
            target = intent.get("target", "")
            return self.open_app(target)

        return "I didn't recognize that command."

    def open_app(self, app_name: str) -> str:
        """
        Opens an application or website given its name or URL.
        """
        if not app_name:
            return "Please specify what you would like to open."

        raw_target = app_name.strip()
        normalized = raw_target.lower().strip()
        # Remove spaces and dashes for key lookup
        compact = re.sub(r'[\s\-_]+', '', normalized)

        # -------------------------------------------------------------
        # 1. Direct Web URLs (http, https, www, or top-level domains)
        # -------------------------------------------------------------
        if normalized.startswith("http://") or normalized.startswith("https://"):
            try:
                webbrowser.open_new_tab(normalized)
                return f"Opening {normalized} in your browser..."
            except Exception as e:
                return f"Failed to open URL: {e}"

        if normalized.startswith("www."):
            url = f"https://{normalized}"
            try:
                webbrowser.open_new_tab(url)
                return f"Opening {normalized} in your browser..."
            except Exception as e:
                return f"Failed to open URL: {e}"

        tld_pattern = r'^[a-zA-Z0-9\-]+\.(com|org|net|io|in|ai|co|edu|gov|app|dev|me|tv)$'
        if re.match(tld_pattern, normalized):
            url = f"https://{normalized}"
            try:
                webbrowser.open_new_tab(url)
                return f"Opening {normalized} in your browser..."
            except Exception as e:
                return f"Failed to open website: {e}"

        # -------------------------------------------------------------
        # 2. Known Web Services (YouTube, Google, GitHub, etc.)
        # -------------------------------------------------------------
        for site_key, (site_url, _) in self.web_services.items():
            compact_key = re.sub(r'[\s\-_]+', '', site_key)
            if normalized == site_key or compact == compact_key or normalized == f"{site_key}.com":
                try:
                    webbrowser.open_new_tab(site_url)
                    display_name = site_key.capitalize()
                    return f"Opening {display_name} in your browser..."
                except Exception as e:
                    return f"Failed to open {site_key}: {e}"

        # -------------------------------------------------------------
        # 3. Known Desktop Apps & Windows URI Schemes
        # -------------------------------------------------------------
        matched_target = None
        if compact in self.app_targets:
            matched_target = self.app_targets[compact]
        elif normalized in self.app_targets:
            matched_target = self.app_targets[normalized]

        if matched_target:
            # Check for Windows URI scheme (e.g. ms-settings:, microsoft.windows.camera:)
            if ":" in matched_target:
                try:
                    if hasattr(os, 'startfile'):
                        os.startfile(matched_target)
                    else:
                        subprocess.Popen(f"start {matched_target}", shell=True)
                    return f"Opening {raw_target.capitalize()}..."
                except Exception as e:
                    return f"Failed to launch {raw_target}: {e}"

            # Try system PATH lookup
            executable = shutil.which(matched_target) or shutil.which(f"{matched_target}.exe")
            if executable:
                try:
                    subprocess.Popen([executable], shell=True)
                    return f"Opening {raw_target.capitalize()}..."
                except Exception as e:
                    return f"Failed to launch {raw_target}: {e}"

            # Fallback to os.system start command
            try:
                subprocess.Popen(f"start {matched_target}", shell=True)
                return f"Opening {raw_target.capitalize()}..."
            except Exception as e:
                pass

        # -------------------------------------------------------------
        # 4. Dynamic Desktop Discovery (Start Menu, Program Files, PATH)
        # -------------------------------------------------------------
        # Try finding executable directly
        direct_which = shutil.which(raw_target) or shutil.which(f"{raw_target}.exe")
        if direct_which:
            try:
                subprocess.Popen([direct_which], shell=True)
                return f"Opening {raw_target}..."
            except Exception as e:
                pass

        # Search Windows Start Menu shortcuts
        shortcut_found = self._search_start_menu(raw_target)
        if shortcut_found:
            try:
                if hasattr(os, 'startfile'):
                    os.startfile(shortcut_found)
                else:
                    subprocess.Popen([shortcut_found], shell=True)
                return f"Opening {raw_target}..."
            except Exception as e:
                pass

        # -------------------------------------------------------------
        # 5. Fallback: Treat single-word unknown target as website or web search
        # -------------------------------------------------------------
        # If it's a single word and not a recognized local app, open as .com in browser
        if " " not in raw_target and len(raw_target) > 2:
            web_url = f"https://www.{raw_target}.com"
            try:
                webbrowser.open_new_tab(web_url)
                return f"Could not find local application '{raw_target}'. Opening {web_url} in your browser..."
            except Exception:
                pass

        # Final Fallback: Google search
        search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(raw_target)}"
        try:
            webbrowser.open_new_tab(search_url)
            return f"Opening search for '{raw_target}' in your browser..."
        except Exception as e:
            return f"Could not find application or website '{raw_target}'."

    def _search_start_menu(self, app_name: str):
        """
        Searches Windows Start Menu directories for matching shortcuts (.lnk).
        """
        search_dirs = [
            os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
            os.path.join(os.environ.get("PROGRAMDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs"),
        ]

        app_clean = app_name.lower().replace(" ", "")
        for base_dir in search_dirs:
            if not os.path.exists(base_dir):
                continue
            for root, _, files in os.walk(base_dir):
                for f in files:
                    f_lower = f.lower()
                    if (f_lower.endswith(".lnk") or f_lower.endswith(".exe")) and app_clean in f_lower.replace(" ", ""):
                        return os.path.join(root, f)
        return None

    def close_constants(self):
        pass

    def control_media(self, action: str) -> str:
        """
        Controls media playback using global hotkeys.
        """
        action = action.lower()
        if action in ("play", "pause"):
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
