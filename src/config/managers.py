import json
import os
from pathlib import Path
from typing import List, Dict, Any

class ConfigManager:
    def __init__(self, filename: str, default_data: Any = None):
        self.base_dir = Path(__file__).parent.parent.parent / "config"
        self.base_dir.mkdir(exist_ok=True)
        self.file_path = self.base_dir / filename
        self.data = self._load() if self.file_path.exists() else (default_data or [])

    def _load(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get_all(self):
        return self.data

    def add(self, item: Dict[str, Any]):
        self.data.append(item)
        self.save()

    def delete(self, name: str):
        # Assume que o item tem uma chave 'nome' ou 'name'
        self.data = [i for i in self.data if i.get("nome") != name and i.get("name") != name]
        self.save()

class ThemeManager(ConfigManager):
    def __init__(self):
        super().__init__("themes.json")
        if not self.data:
            self._seed_from_txt()

    def _seed_from_txt(self):
        ref_path = Path(__file__).parent.parent.parent / "references" / "tema.txt"
        if ref_path.exists():
            with open(ref_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                themes = []
                for line in lines[1:]: # Pula cabeçalho
                    if "." in line:
                        themes.append(line.split(".", 1)[1].strip())
                self.data = themes
                self.save()

class CharacterManager(ConfigManager):
    def __init__(self):
        super().__init__("characters.json")

class StyleManager(ConfigManager):
    def __init__(self):
        # Estilos padrão do PRD
        defaults = [
            {
                "name": "Marvel / DC",
                "art_style": "cinematic american comic book, modern graphic novel, clean dramatic ink line art",
                "palette": ["black", "white", "electric blue", "neon cyan", "deep red"],
                "restrictions": ["no cartoon", "no 3D toy look", "no plastic rendering"]
            },
            {
                "name": "Anime",
                "art_style": "japanese anime style, vibrant colors, expressive eyes, speed lines",
                "palette": ["vibrant colors", "soft gradients"],
                "restrictions": ["no american comic style", "no high contrast shadows"]
            },
            {
                "name": "Ghibli",
                "art_style": "Studio Ghibli style, soft watercolor textures, lush detailed backgrounds",
                "palette": ["pastel colors", "natural tones"],
                "restrictions": ["no strong black ink lines", "no high contrast"]
            }
        ]
        super().__init__("styles.json", default_data=defaults)
        if not self.data:
            self.data = defaults
            self.save()
