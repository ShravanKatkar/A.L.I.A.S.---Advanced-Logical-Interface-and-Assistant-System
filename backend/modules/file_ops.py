import os
import glob

class FileOps:
    def __init__(self):
        self.desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.documents_path = os.path.join(os.path.expanduser("~"), "Documents")

    def search_file(self, filename, search_path=None):
        """
        Basic recursive search for a file in Desktop or Documents.
        This is a heavy operation, so we limit depth or scope in real usage.
        """
        if not search_path:
            search_paths = [self.desktop_path, self.documents_path]
        else:
            search_paths = [search_path]

        found_files = []
        for path in search_paths:
            for root, dirs, files in os.walk(path):
                if filename.lower() in [f.lower() for f in files]:
                    # Find exact match or close match
                    for f in files:
                        if filename.lower() in f.lower():
                             found_files.append(os.path.join(root, f))
                
                # Limit depth to prevent hanging (optional safe guard)
                if root.count(os.sep) - path.count(os.sep) > 3:
                    del dirs[:] 
        
        if found_files:
            return found_files[0] # Return first match
        return None

    def read_file(self, filepath):
        """
        Reads text context from a file.
        """
        if not os.path.exists(filepath):
            return "File does not exist."
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return content[:2000] # Return first 2000 chars to avoid overloading context
        except Exception as e:
            return f"Error reading file: {e}"
            
    def open_file(self, filepath):
        try:
            os.startfile(filepath)
            return f"Opened {os.path.basename(filepath)}"
        except Exception as e:
            return f"Error opening file: {e}"
