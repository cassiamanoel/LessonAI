from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field
from typing import List
import os
from dotenv import load_dotenv
from src.prompts.loader import get_all_roles
from src.search.web_search import search_web

load_dotenv()

# Carrega os prompts base das referências
ROLES = get_all_roles()

class QuadroSchema(BaseModel):
    descricao: str = Field(..., description="Descrição visual detalhada para a IA de imagem.")
    dialogo: str = Field("", description="Texto do balão de fala ou narração.")
    tipo_texto: str = Field("fala", description="Tipo do texto: 'fala', 'narracao', 'sussurro', 'grito', 'pensamento', 'onomatopeia'.")
    personagens: List[str] = Field(default_factory=list, description="Lista de nomes de personagens presentes no quadro.")

class PaginaSchema(BaseModel):
    titulo: str = Field(..., description="Título ou tema da página.")
    quadros: List[QuadroSchema] = Field(..., description="Lista de 4 a 6 quadros.")

class RoteiroSchema(BaseModel):
    titulo_hq: str = Field(..., description="Título geral da HQ.")
    paginas: List[PaginaSchema] = Field(..., description="Lista de páginas da HQ.")

def get_script_writer_agent(model_id: str = "gpt-4o", language: str = "Português"):
    """Retorna o agente responsável por pesquisar e escrever o roteiro."""
    return Agent(
        name="Roteirista LessonAI",
        model=OpenAIChat(id=model_id),
        tools=[search_web], # Usando ferramenta customizada
        description=ROLES["story_engine"],
        instructions=[
            f"Você é o Roteirista da equipe editorial LessonAI, especializado em padrão Marvel/DC.",
            f"TODA A CONSTRUÇÃO DO ROTEIRO DEVE SER NO IDIOMA: {language}.",
            "REGRA DE VOLUME: Você DEVE gerar EXATAMENTE a quantidade de páginas solicitada pelo usuário no prompt.",
            "PROIBIDO CONDENSAR: Não resuma a história em 1 página se o pedido for maior. Cada página deve conter de 4 a 6 quadros.",
            "MAREAMENTO DE ATOS: Distribua os 6 atos da estrutura narrativa (Mystery, Investigation, Explanation, Visualization, Realization, Hook) ao longo de TODAS as páginas solicitadas.",
            "DENSIDADE NARRATIVA: No mínimo 80% de todos os quadros devem conter texto (fala, narração, etc).",
            "PADRÃO MARVEL/DC DE LETTERING (OBRIGATÓRIO):",
            "  1. FALA: Balões ovais com cauda. Texto em MAIÚSCULAS.",
            "  2. NARRAÇÃO: Caixas retangulares (captions) no topo/canto. Sem cauda. Texto em MAIÚSCULAS.",
            "  3. SUSSURRO: Diálogo com tom baixo ou secreto. Texto em MAIÚSCULAS.",
            "  4. GRITO: Diálogo explosivo ou urgente. Texto em MAIÚSCULAS.",
            "  5. PENSAMENTO: Diálogo interno do personagem. Texto em MAIÚSCULAS.",
            "  6. ÊNFASE: Destaque palavras importantes para dar ritmo à leitura.",
            "  7. ONOMATOPEIAS: Use efeitos sonoros (BOOM, CRASH, THWIP) fora dos balões.",
            "  8. LIMITE: Máximo de 25 palavras por balão para fluidez.",
            "LIMPEZA DE TEXTO: O campo 'dialogo' DEVE conter APENAS o texto final. REMOVA rótulos como 'PERSONAGEM:' ou 'NARRADOR:'.",
            "Storytelling Cinematográfico: Descreva a ação visual CLARAMENTE antes dos diálogos.",
            "Sua saída DEVE ser um objeto JSON seguindo TOTALMENTE o esquema RoteiroSchema."
        ],
        output_schema=RoteiroSchema,
    )

def get_editor_chief_agent(model_id: str = "gpt-4o"):
    """Retorna o Editor-Chefe que coordena a equipe."""
    return Agent(
        name="Editor-Chefe LessonAI",
        model=OpenAIChat(id=model_id),
        description=ROLES["master"],
        instructions=[
            "Você coordena a produção da HQ educativa com o padrão de qualidade Marvel Grade.",
            "Garanta que o conceito de IA seja ensinado de forma clara e didática.",
            "Supervisione o roteiro para garantir enquadramentos cinematográficos e narrativa visual clara.",
            "Garanta que a HQ siga exatamente a quantidade de páginas planejada no roteiro."
        ],
        markdown=True
    )

class ComicScriptGenerator:
    def __init__(self, llm_provider: str = "openai", model_id: str = "gpt-4o", language: str = "Português"):
        self.language = language
        self.writer = get_script_writer_agent(model_id, language)
        self.editor = get_editor_chief_agent(model_id)

    def _clean_prefixes(self, script_data: dict) -> dict:
        """Remove prefixos como 'Narrador:', 'Personagem:' do início dos diálogos/narração."""
        if not isinstance(script_data, dict): return script_data
        
        for pagina in script_data.get("paginas", []):
            for quadro in pagina.get("quadros", []):
                text = quadro.get("dialogo", "")
                if text:
                    # Remove padrões como "NOME: ", "NARRADOR: ", "AGENTE PROMPT: "
                    # Regex para remover qualquer palavra seguida de dois pontos no início da string
                    import re
                    # Remove "TEXTO: " (case insensitive, opcionalmente com espaços extras)
                    cleaned = re.sub(r'^[A-Za-zÀ-ÖØ-öø-ÿ\s]+:\s*', '', text)
                    quadro["dialogo"] = cleaned
        return script_data

    def generate(self, theme: str, num_pages: int = 5):
        max_retries = 2
        result = None
        
        for attempt in range(max_retries + 1):
            if attempt == 0:
                prompt = (
                    f"Crie um roteiro completo de HQ EDUCACIONAL no idioma {self.language} sobre o tema: '{theme}'.\n"
                    f"EXIGÊNCIA EDITORIAL OBRIGATÓRIA: A HQ DEVE ter EXATAMENTE {num_pages} PÁGINAS.\n"
                    f"DIAGRAMAÇÃO MARVEL GRADE:\n"
                    f"1. FALA (balão oval), 2. NARRAÇÃO (caixa), 3. SUSSURRO (tracejado), 4. GRITO (explosivo), 5. PENSAMENTO (nuvem).\n"
                    f"6. ÊNFASE (negrito em palavras-chave), 7. ONOMATOPEIAS (BOOM!, etc), 8. LIMITE (max 25 palavras/balão).\n"
                    f"ESTRUTURA JSON: O campo 'paginas' DEVE conter uma lista com EXATAMENTE {num_pages} objetos PaginaSchema.\n"
                    f"Cada página DEVE ter entre 4 e 6 quadros.\n"
                    f"Distribua os 6 atos narrativos ao longo das {num_pages} páginas. NÃO condense tudo em 1 página."
                )
            else:
                prompt = (
                    f"ATENÇÃO: Sua resposta anterior falhou em seguir o padrão editorial.\n"
                    f"REESCREVA o roteiro com EXATAMENTE {num_pages} páginas e use o PADRÃO MARVEL de diálogos.\n"
                    f"Lembre-se: 1.Fala, 2.Narração, 3.Sussurro, 4.Grito, 5.Pensamento, 6.Ênfase, 7.Onomatopeias, 8.Limite.\n"
                    f"Tema: '{theme}'. Idioma: {self.language}."
                )
            
            response = self.writer.run(prompt)
            
            if hasattr(response.content, "model_dump"):
                result = response.content.model_dump()
            elif isinstance(response.content, str):
                import json
                try:
                    result = json.loads(response.content)
                except:
                    result = {"titulo_hq": theme, "paginas": []}
            else:
                result = response.content
            
            # Verificação programática
            if isinstance(result, dict):
                got_pages = len(result.get("paginas", []))
                print(f"[EDITORIAL] Tentativa {attempt+1}: Gerou {got_pages}/{num_pages} páginas")
                if got_pages >= num_pages:
                    # Sucesso! Truncar se gerou mais do que o pedido
                    result["paginas"] = result["paginas"][:num_pages]
                    return result
            else:
                got_pages = 0
        
        # Fallback: Se ainda temos menos páginas, fazer padding inteligente
        if isinstance(result, dict) and got_pages < num_pages:
            paginas = result.get("paginas", [])
            print(f"[EDITORIAL] Padding: {got_pages} → {num_pages} páginas")
            while len(paginas) < num_pages:
                # Gerar página extra com prompt específico
                page_num = len(paginas) + 1
                extra_prompt = (
                    f"Gere APENAS 1 página extra (página {page_num} de {num_pages}) para a HQ '{result.get('titulo_hq', theme)}'.\n"
                    f"Idioma: {self.language}. Tema: '{theme}'.\n"
                    f"A página deve ter 4 a 6 quadros e continuar a narrativa educativa.\n"
                    f"Retorne como um RoteiroSchema com 1 página na lista 'paginas'."
                )
                try:
                    extra_response = self.writer.run(extra_prompt)
                    if hasattr(extra_response.content, "model_dump"):
                        extra_data = extra_response.content.model_dump()
                    else:
                        import json
                        extra_data = json.loads(extra_response.content) if isinstance(extra_response.content, str) else {}
                    
                    extra_pages = extra_data.get("paginas", [])
                    if extra_pages:
                        paginas.append(extra_pages[0])
                    else:
                        # Último recurso: duplicar última página com título diferente
                        if paginas:
                            clone = dict(paginas[-1])
                            clone["titulo"] = f"Continuação - Parte {page_num}"
                            paginas.append(clone)
                except Exception as e:
                    print(f"[EDITORIAL] Erro no padding da página {page_num}: {e}")
                    if paginas:
                        clone = dict(paginas[-1])
                        clone["titulo"] = f"Continuação - Parte {page_num}"
                        paginas.append(clone)
            
            result["paginas"] = paginas[:num_pages]
        
        return self._clean_prefixes(result)
