import os
import yaml

class Murmur:
    def __init__(self, filename=".murmur"):
        self.filepath = os.path.expanduser(f"~/{filename}")
        self.data = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.filepath):
            return
        with open(self.filepath, "r", encoding="utf-8") as f:
            try:
                self.data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise RuntimeError(f"Error parsing murmur file: {e}")

    def Lookup(self, key, default=None):
        """Return the value for a given key, or default if not found."""
        return self.data.get(key, default)
