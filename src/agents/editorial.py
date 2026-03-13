from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import re
import json
from dotenv import load_dotenv
from src.prompts.loader import get_all_roles
from src.search.web_search import search_web

load_dotenv()

# Carrega os prompts base das referências
ROLES = get_all_roles()

# Estilo Marvel Fixo para injeção automática (v22.0)
MARVEL_FIXED_STYLE = (
    "Modern Marvel digital comic illustration, clean sharp ink line art, "
    "vibrant colors, cinematic lighting, cell shading."
)

class QuadroSchema(BaseModel):
    descricao: str = Field(..., description="Descrição visual: [personagem + ação], [ambiente], [iluminação], [clima].")
    dialogo: str = Field("", description="Somente o texto do balão. ALL CAPS. Sem nomes/prefixos.")
    tipo_texto: str = Field("fala", description="fala, narracao, pensamento, grito, sussurro, eletronico.")
    personagens: List[str] = Field(default_factory=list, description="Lista de personagens.")
    # Âncora para o Composer v21.0+
    personagem_pos: Optional[List[int]] = Field(None, description="[x, y] do personagem no quadro para a cauda do balão.")
    face_bbox: Optional[List[int]] = Field(None, description="[x1, y1, x2, y2] do rosto.")
    character_bbox: Optional[List[int]] = Field(None, description="[x1, y1, x2, y2] do corpo.")

class PaginaSchema(BaseModel):
    titulo: str = Field(..., description="Tema da página.")
    quadros: List[QuadroSchema] = Field(..., description="Lista obrigatória de 4 a 6 quadros.")

class RoteiroSchema(BaseModel):
    titulo_hq: str = Field(..., description="Título da HQ.")
    paginas: List[PaginaSchema] = Field(..., description="Lista de páginas.")

def get_script_writer_agent(model_id: str = "gpt-4o", language: str = "Português", custom_instructions: list = None):
    """Retorna o agente responsável por escrever o roteiro no padrão v22.0."""
    base_instructions = [
        f"Você é o Roteirista sênior da LessonAI. Idioma: {language}.",
        "PADRÃO EDITORIAL PIXEL-PERFECT v22.0:",
        "  1. ARTE: FOQUE APENAS NA CENA. O estilo Marvel será injetado automaticamente. "
        "     PROIBIDO usar palavras como 'speech bubble', 'caption', 'text', 'panel' na descrição.",
        "  2. CONSISTÊNCIA: Descreva sempre 'same outfit', 'same hairstyle' e 'same physical design' para personagens recorrentes.",
        "  3. ESTRUTURA VISUAL: [Personagem + Ação], [Ambiente], [Iluminação], [Clima Visual].",
        "  4. DIÁLOGOS (CRÍTICO): Ideal 8-18 palavras. Máximo absoluto 22. UMA ideia por balão.",
        "  5. ZERO RUÍDO: NÃO inclua nomes de personagens ou 'NARRADOR:' no campo 'dialogo'.",
        "  6. ALL CAPS: Escreva todo o conteúdo de 'dialogo' EM MAIÚSCULAS.",
        "  7. LAYOUT: Gere sempre entre 4 e 6 quadros por página para encaixar no layout físico.",
        "  8. TIPOS: Use obrigatoriamente: fala, narracao, pensamento, grito, sussurro, eletronico.",
        "  9. ÂNCORAS: Se possível, estime personagem_pos [x, y] onde 0,0 é topo-esquerda do quadro."
    ]
    if custom_instructions:
        base_instructions.extend(custom_instructions)

    return Agent(
        name="Roteirista LessonAI",
        model=OpenAIChat(id=model_id),
        tools=[search_web],
        description=ROLES["story_engine"],
        instructions=base_instructions,
        output_schema=RoteiroSchema,
    )

def get_editor_chief_agent(model_id: str = "gpt-4o"):
    return Agent(
        name="Editor-Chefe LessonAI",
        model=OpenAIChat(id=model_id),
        description=ROLES["master"],
        instructions=[
            "Você coordena a produção Marvel Grade v22.0.",
            "Garanta que o conceito educacional seja preservado em frases curtas e impactantes.",
            "Rigor absoluto no limite de 22 palavras por quadro."
        ]
    )

class ComicScriptGenerator:
    def __init__(self, llm_provider: str = "openai", model_id: str = "gpt-4o", language: str = "Português"):
        self.language = language
        self.writer = get_script_writer_agent(model_id, language)
        self.editor = get_editor_chief_agent(model_id)

    def _clean_prefixes(self, script_data: dict) -> dict:
        """Alias para compatibilidade com testes legados."""
        return self._format_script(script_data)

    def _format_script(self, script_data: dict) -> dict:
        """Aplica formatação avançada v22.0 (Limpeza, Estilo Fixo, Maiúsculas)."""
        if not isinstance(script_data, dict): return script_data
        
        # Regex para limpeza agressiva
        regex_prefix = re.compile(r'^([A-ZÀ-Úa-zà-ú\s]+[:\-]\s*)', re.IGNORECASE)
        
        for pagina in script_data.get("paginas", []):
            for quadro in pagina.get("quadros", []):
                # 1. Injeção de Estilo Marvel Fixo
                desc = quadro.get("descricao", "").strip()
                if desc and MARVEL_FIXED_STYLE not in desc:
                    quadro["descricao"] = f"{desc}. {MARVEL_FIXED_STYLE}"
                
                # 2. Limpeza e Formatação de Diálogo
                text = quadro.get("dialogo", "")
                if text:
                    # Remove prefixos (ex: NARRADOR:)
                    text = regex_prefix.sub("", text).strip()
                    # Remove quebras de linha e excesso de espaços
                    text = " ".join(text.split())
                    # Remove pontuação duplicada (ex: !! -> !) exceto reticências
                    text = re.sub(r'([!?])\1+', r'\1', text)
                    # Força ALL CAPS mantendo as marcações de negrito do Composer
                    quadro["dialogo"] = text.upper()
                    
        return script_data

    def generate(self, theme: str, num_pages: int = 5):
        max_retries = 2
        result = None
        
        v22_rules = (
            "REGRAS V22.0 (PIXEL-PERFECT):\n"
            "- 4 A 6 QUADROS POR PÁGINA.\n"
            "- DIÁLOGOS: 8-18 PALAVRAS (MAX 22).\n"
            "- ALL CAPS / SEM PREFIXOS.\n"
            "- ARTE: SEM MENÇÃO A BALÕES/TEXTO.\n"
            f"- EXATAMENTE {num_pages} PÁGINAS."
        )

        for attempt in range(max_retries + 1):
            prompt = f"Crie roteiro educacional sobre '{theme}' em {num_pages} páginas. Idioma: {self.language}.\n{v22_rules}"
            try:
                response = self.writer.run(prompt)
                if hasattr(response.content, "model_dump"):
                    result = response.content.model_dump()
                else:
                    result = json.loads(response.content) if isinstance(response.content, str) else response.content
                
                if isinstance(result, dict) and len(result.get("paginas", [])) >= num_pages:
                    result["paginas"] = result["paginas"][:num_pages]
                    return self._format_script(result)
            except Exception as e:
                print(f"[EDITORIAL] Erro {attempt}: {e}")

        # Padding Fallback
        if isinstance(result, dict):
            paginas = result.get("paginas", [])
            while len(paginas) < num_pages:
                page_num = len(paginas) + 1
                try:
                    extra_res = self.writer.run(f"Gere a página {page_num} de {num_pages} sobre {theme}.\n{v22_rules}")
                    extra_data = extra_res.content.model_dump() if hasattr(extra_res.content, "model_dump") else json.loads(extra_res.content)
                    if extra_data.get("paginas"):
                        paginas.append(extra_data["paginas"][0])
                except:
                    if paginas: paginas.append(dict(paginas[-1]))
            result["paginas"] = paginas[:num_pages]
            
        return self._format_script(result)
