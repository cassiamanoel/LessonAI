import os
import requests
from openai import OpenAI
import google.generativeai as genai
import replicate
from dotenv import load_dotenv

load_dotenv()

class ImageEngine:
    def __init__(self, provider: str = "openai", model_id: str = "dall-e-3"):
        self.provider = provider.lower()
        self.model_id = model_id
        
    def generate(self, prompt: str, size: str = "1024x1024") -> str:
        """Gera imagem e retorna a URL ou o path local."""
        # v40.0: Image Mocking System
        import streamlit as st
        mock_active = os.environ.get("IMAGE_MOCK", "false").lower() == "true" or st.session_state.get("image_mock", False)
        
        if mock_active:
            # Retorna uma imagem local em Base64 para economizar créditos e burlar problemas de rede
            mock_path = os.path.join("assets", "comic_mock.png")
            if os.path.exists(mock_path):
                import base64
                with open(mock_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode()
                    return f"data:image/png;base64,{encoded_string}"
            return "https://via.placeholder.com/1024x1024.png?text=MOCK+MODE+ACTIVE"

        provider = self.provider.lower()
        if provider == "openai":
            return self._generate_openai(prompt, size)
        elif provider == "google" or provider == "gemini":
            return self._generate_google(prompt)
        elif provider == "replicate" or provider == "flux":
            return self._generate_replicate(prompt)
        elif provider == "stability":
            return self._generate_stability(prompt)
        else:
            raise ValueError(f"Provider não suportado: {self.provider}")

    def _generate_openai(self, prompt, size):
        client = OpenAI()
        response = client.images.generate(
            model=self.model_id,
            prompt=prompt,
            size=size,
            quality="hd",
            n=1,
        )
        return response.data[0].url

    def _generate_google(self, prompt):
        # Gemini / Imagen 3
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash") # Fallback ou específico para Imagen
        # Nota: API do Imagen varia, aqui simulamos a chamada via SDK se disponível
        # Para este PRD, focamos em DALL-E e Flux como principais via Replicate
        return "https://via.placeholder.com/1024x1024.png?text=Gemini+Soon"

    def _generate_replicate(self, prompt):
        # Ex: Flux.1 Pro ou Schnell
        output = replicate.run(
            self.model_id if "/" in self.model_id else "black-forest-labs/flux-schnell",
            input={"prompt": prompt}
        )
        return output[0] # Retorna URL da imagem

    def _generate_stability(self, prompt):
        # Chamada via API da Stability
        return "https://via.placeholder.com/1024x1024.png?text=Stability+Soon"
