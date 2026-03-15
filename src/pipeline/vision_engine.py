import os
import io
import json
import base64
import requests
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class VisionEngine:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            print("WARNING: GOOGLE_API_KEY não encontrada. VisionEngine desativado.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")

    def detect_main_character(self, image_source) -> list:
        """
        Detecta o personagem principal e retorna [x, y] normalizado (0-1000).
        Retorna [500, 500] (centro) em caso de falha.
        """
        if not self.model:
            return [500, 500]

        try:
            # Carregar Imagem
            img = self._load_image(image_source)
            if not img:
                return [500, 500]

            prompt = (
                "Identify the coordinates [x, y] of the center of the main character's face in this comic panel. "
                "The image coordinates must be normalized from 0 to 1000. "
                "Return ONLY a JSON object: {\"x\": number, \"y\": number}. "
                "If multiple characters are present, pick the one speaking or the most prominent one."
            )

            response = self.model.generate_content([prompt, img])
            
            # Limpeza básica do markdown se houver
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[-1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[-1].split("```")[0].strip()

            coords = json.loads(text)
            return [int(coords.get("x", 500)), int(coords.get("y", 500))]

        except Exception as e:
            print(f"Vision Error: {e}")
            return [500, 500]

    def _load_image(self, source):
        try:
            if isinstance(source, Image.Image):
                return source
            if source.startswith("data:image"):
                header, encoded = source.split(",", 1)
                data = base64.b64decode(encoded)
                return Image.open(io.BytesIO(data)).convert("RGB")
            if source.startswith("http"):
                resp = requests.get(source, timeout=10)
                return Image.open(io.BytesIO(resp.content)).convert("RGB")
            if os.path.exists(source):
                return Image.open(source).convert("RGB")
        except:
            pass
        return None
