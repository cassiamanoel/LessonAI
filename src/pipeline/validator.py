from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.media import Image as AgnoImage
from dotenv import load_dotenv
from typing import List, Tuple
import os
import unicodedata
import re

load_dotenv()

class VisionValidator:
    """
    Motor de Validação Marvel Grade v6.0.
    Atua como um revisor de provas (copy-editor) profissional com suporte multi-idioma.
    """
    def __init__(self, model_id: str = "gpt-4o"):
        self.agent = Agent(
            model=OpenAIChat(id=model_id),
            instructions=[
                "Você é um REVISOR DE PROVAS (Copy-editor) da Marvel/DC Comics.",
                "Sua missão é garantir que o texto na imagem seja FIEL ao roteiro e sem erros editoriais.",
                "CHECKLIST DE ERROS (AS 7 PRAGAS DA IA):",
                "1. Texto fora do balão.",
                "2. Texto cortado ou truncado.",
                "3. Palavras incompletas ou letras deformadas.",
                "4. Balões vazios ou borrões no lugar de letras.",
                "5. Repetição de diálogo ou 'TEXTO FANTASMA'.",
                "6. Texto pequeno demais ou GIBBERISH (caracteres sem sentido, letras sobrepostas).",
                "7. Balão apontando para o personagem errado ou sem cauda lógica.",
                "REGRA DE OURO:",
                "- Se o texto estiver minimamente deformado ou parecer 'sopa de letrinhas', marque como INVALIDO.",
                "- O texto deve ser IDENTICO ao SCRIPT. UMA letra errada = INVALIDO.",
                "Responda no formato:",
                "STATUS: [VALIDO|INVALIDO]",
                "MOTIVO: [Explicação detalhada]"
            ]
        )

    def normalize_text(self, text: str) -> str:
        """
        Normaliza o texto para comparação robusta.
        """
        if not text: return ""
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        text = text.lower()
        text = re.sub(r'[^a-z0-9 ]', '', text)
        text = " ".join(text.split())
        return text

    def validate_panel_text(self, image_url: str, expected_text: str, language: str = "Português") -> Tuple[bool, str]:
        """
        Executa a validação OCR-style e Auditoria Editorial via Agno Vision.
        Retorna (Status, Motivo).
        """
        if not expected_text: return True, "Nenhum texto esperado"
        
        prompt = f"IDIOMA ESPERADO: {language}\n" \
                 f"SCRIPT ESPERADO: '{expected_text.upper()}'\n" \
                 f"AUDITORIA EDITORIAL:\n" \
                 f"1. O texto na imagem é idêntico ou semanticamente perfeito em relação ao script? (Ignore pontuação menor ou capitalização se a mensagem estiver correta).\n" \
                 f"2. Existe GIBBERISH (letras deformadas, sobrepostas, sopa de letrinhas)? Se sim, REJEITE IMEDIATAMENTE.\n" \
                 f"3. O texto está legível e bem posicionado?\n" \
                 f"Responda no formato:\n" \
                 f"STATUS: [VALIDO|INVALIDO]\n" \
                 f"MOTIVO: [Sua explicação]"
        
        try:
            response = self.agent.run(prompt, images=[AgnoImage(url=image_url)])
            result = response.content.upper()
            
            # Extração de Motivo
            reason = "Motivo não especificado"
            if "MOTIVO:" in result:
                reason = result.split("MOTIVO:")[1].strip()

            if "STATUS: INVALIDO" in result:
                print(f"[AUDITORIA EDITORIAL] FALHA NO QUADRO: {result}")
                return False, reason

            if "STATUS: VALIDO" in result:
                return True, "Aprovado pela auditoria"
            
            return False, "Agente não retornou um status claro"
            
        except Exception as e:
            msg = f"Falha técnica na API de Visão: {e}"
            print(f"[ERRO CRÍTICO NA VALIDAÇÃO] {msg}")
            return False, msg
