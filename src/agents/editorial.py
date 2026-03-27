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

# Estilo Cyberpunk Marvel Grade (v2.0)
MARVEL_FIXED_STYLE = (
    "Professional modern Marvel/DC comic book illustration, cyberpunk aesthetic, "
    "clean sharp ink line art, vibrant neon colors on dark backgrounds, "
    "dramatic chiaroscuro lighting, volumetric neon glow, masterpiece quality."
)

# Elenco fixo de 8 personagens (v2.0 Cyberpunk Tech Team)
CAST_ROSTER = {
    "Kira": {"role": "Arquiteta (Backend Engineer)", "narrative": "Protagonista e narradora. Lidera a investigação técnica."},
    "Sofia": {"role": "Estrategista (Product Manager)", "narrative": "Define o problema e prioridades. Questiona premissas."},
    "Yuki": {"role": "Analista (Data Scientist)", "narrative": "Explica conceitos de IA com clareza e metáforas visuais."},
    "Marcus": {"role": "Guardião (DevOps/SRE)", "narrative": "Mostra impacto operacional. Voz da razão sob pressão."},
    "Luna": {"role": "Intérprete (UX Designer)", "narrative": "Visualiza soluções e interfaces. Traduz complexidade."},
    "AXIOM": {"role": "Não-Humano (AI Agent)", "narrative": "Representa automação e risco. Pode fugir do controle."},
    "Victor": {"role": "Pressionador (Stakeholder)", "narrative": "Cobra resultado, prazo e ROI. Gera urgência."},
    "Bia": {"role": "Verdade (Cliente Final)", "narrative": "Mostra impacto real. Faz perguntas que expõem falhas."},
}

# Arco narrativo obrigatório de 6 atos
NARRATIVE_ARC = """
ESTRUTURA NARRATIVA OBRIGATÓRIA (6 ATOS):
1. MISTÉRIO — Um problema ou anomalia aparece no sistema. Victor (Stakeholder) pressiona por respostas. Kira (Arquiteta) assume a investigação.
2. INVESTIGAÇÃO — Kira lidera a equipe. Sofia (PM) define prioridades. Marcus (DevOps) mostra dados operacionais. Tensão crescente.
3. EXPLICAÇÃO — Yuki (Data Scientist) explica o conceito de IA envolvido. Use analogias e metáforas visuais. AXIOM (AI Agent) demonstra o conceito em ação.
4. VISUALIZAÇÃO — Luna (UX Designer) projeta interfaces e fluxos holográficos. AXIOM materializa o conceito visualmente. Momento de "eureka" visual.
5. ENTENDIMENTO — A equipe implementa a solução. Kira conecta as peças. Bia (Cliente) testa e valida o resultado real.
6. GANCHO — Novo mistério ou pergunta emerge. AXIOM mostra comportamento inesperado. Curiosidade para o próximo episódio.

REGRAS DE DISTRIBUIÇÃO DE PERSONAGENS:
- Kira aparece em TODOS os atos (protagonista)
- Cada personagem deve aparecer em pelo menos 2-3 atos
- AXIOM é o catalisador de tensão — pode ser aliado OU ameaça
- Victor aparece no início (pressão) e no final (cobrança/satisfação)
- Bia aparece nos atos finais (validação real)
- Yuki e Luna são as "explicadoras" — atos 3 e 4
- Marcus aparece quando há caos operacional — atos 2 e 3
- Distribua as falas de forma equilibrada — ninguém domina sozinho
"""

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
    """Retorna o agente responsável por escrever o roteiro no padrão v2.0 Cyberpunk."""

    # Monta descrição do elenco para o agente
    cast_description = "ELENCO FIXO (use EXATAMENTE estes nomes no campo 'personagens'):\n"
    for name, info in CAST_ROSTER.items():
        cast_description += f"  - {name}: {info['role']} — {info['narrative']}\n"

    base_instructions = [
        f"Você é o Roteirista sênior da LessonAI. Idioma: {language}.",
        "TEMA: HQs educativas sobre Inteligência Artificial em estilo cyberpunk profissional.",
        cast_description,
        NARRATIVE_ARC,
        "PADRÃO EDITORIAL v2.0:",
        "  1. ARTE: FOQUE APENAS NA CENA. O estilo cyberpunk Marvel será injetado automaticamente.",
        "  2. CONSCIÊNCIA DE DENSIDADE: Máximo 22 palavras por diálogo. Ideal 12-15 palavras.",
        "  3. PLANEJAMENTO DE LAYOUT (OBRIGATÓRIO):",
        "     - Use 'personagem_pos' [x, y] com valores de 0 a 1000.",
        "     - Ex: [500, 500] é o centro absoluto. [200, 200] é topo-esquerda.",
        "  4. ZERO RUÍDO: NÃO inclua nomes ou 'NARRADOR:' no campo 'dialogo'.",
        "  5. ALL CAPS: Todo o conteúdo de 'dialogo' EM MAIÚSCULAS.",
        "  6. QUADROS: Gere sempre entre 4 e 6 quadros por página.",
        "  7. PERSONAGENS: Use SOMENTE os nomes do elenco fixo (Kira, Sofia, Yuki, Marcus, Luna, AXIOM, Victor, Bia).",
        "  8. DISTRIBUIÇÃO: Cada personagem deve ter falas proporcionais ao seu papel no ato narrativo.",
        "  9. ANALOGIAS: Use analogias criativas e recursos visuais para explicar conceitos de IA.",
        " 10. AMBIENTE: Cenários cyberpunk — salas de servidores, war rooms holográficas, torres corporativas neon."
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
            "Você coordena a produção Cyberpunk Marvel Grade v2.0.",
            "Garanta que o conceito educacional de IA seja preservado em frases curtas e impactantes.",
            "Rigor absoluto no limite de 22 palavras por quadro.",
            "Valide que os 8 personagens do elenco fixo estão sendo usados corretamente.",
            "Valide que a estrutura de 6 atos está presente: Mistério → Investigação → Explicação → Visualização → Entendimento → Gancho."
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
        num_pages = min(num_pages, 5)  # Limite máximo de 5 páginas

        v2_rules = (
            "REGRAS v2.0 CYBERPUNK:\n"
            "- 4 A 6 QUADROS POR PÁGINA.\n"
            "- DIÁLOGOS: 8-18 PALAVRAS (MAX 22).\n"
            "- ALL CAPS / SEM PREFIXOS.\n"
            "- ARTE: SEM MENÇÃO A BALÕES/TEXTO.\n"
            f"- EXATAMENTE {num_pages} PÁGINAS.\n"
            "- USE OS 8 PERSONAGENS DO ELENCO FIXO.\n"
            "- SIGA A ESTRUTURA DE 6 ATOS OBRIGATÓRIA.\n"
            "- CENÁRIOS CYBERPUNK: neon, hologramas, tech corporativo.\n"
            "- CONCISÃO: Quanto menos páginas, mais curto e objetivo deve ser o conteúdo. "
            "Se num_pages <= 3, seja extremamente direto e esqueça introduções longas."
        )

        for attempt in range(max_retries + 1):
            prompt = (
                f"Crie roteiro de HQ educativa sobre o conceito de IA: '{theme}' em {num_pages} páginas. "
                f"Idioma: {self.language}.\n"
                f"Use os 8 personagens do elenco fixo (Kira, Sofia, Yuki, Marcus, Luna, AXIOM, Victor, Bia).\n"
                f"Siga a estrutura narrativa: Mistério → Investigação → Explicação → Visualização → Entendimento → Gancho.\n"
                f"Distribua os personagens conforme seus papéis narrativos.\n"
                f"{v2_rules}"
            )
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
