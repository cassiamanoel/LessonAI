# Plano de Implementação — LessonAI Comic Generator

Este plano detalha a construção do gerador de HQs utilizando a stack **Python + uv + Agno + Streamlit**.

## Proposed Changes

### [Infra] Build & Dependency Management
Implementação da estrutura base do projeto usando `uv`.

#### [NEW] [pyproject.toml](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/pyproject.toml)
- Definição de dependências: `streamlit`, `agno`, `pydantic`, `python-dotenv`, `pillow`, `reportlab`, `duckduckgo-search`, `tavily-python`, `litellm`.

#### [NEW] [.env](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/.env)
- Template para chaves de API (OpenAI, Anthropic, Replicate, etc.).

---

### [Core] Agentes Agno
Orquestração da sala editorial de HQs.

#### [NEW] [src/agents/editorial.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/src/agents/editorial.py)
- `EditorChiefAgent`: Coordenador do fluxo.
- `ScriptWriterAgent`: Responsável pelo roteiro + ferramentas de busca.
- `VisualDirectorAgent`: Criação de prompts visuais consolidados (1 único prompt por quadro).

---

### [Services] Imagem & Composição
Lógica de geração de imagem multi-provider e montagem final.

#### [NEW] [src/pipeline/image_engine.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/src/pipeline/image_engine.py)
- Factory para suportar DALL-E 3, Gemini Imagen, SDXL e Flux de forma dinâmica por página/quadro.

#### [NEW] [src/pipeline/composer.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/src/pipeline/composer.py)
- Uso de `Pillow` para:
    - Desenhar balões de fala baseados nas coordenadas do roteiro.
    - Aplicar letragem e onomatopeias.
    - Gerar a página final composta (layout de 4-6 quadros).

#### [NEW] [src/pipeline/exporter.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/src/pipeline/exporter.py)
- Conversão das páginas geradas em PDF (A4/Digital) usando `ReportLab`.

---

### [Frontend] Interface Streamlit
UI interativa e CRUDs de configuração.

#### [NEW] [app.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/app.py)
- Ponto de entrada. Gerenciamento do estado da sessão (`st.session_state`) para o fluxo linear: Tema -> Roteiro -> Imagens -> Exportação.

#### [NEW] [src/ui/config_views.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/src/ui/config_views.py)
- Implementação das telas de CRUD de Personagens, Estilos e Temas.

---

## Verification Plan

### Automated Tests
Como o projeto é novo, implementaremos testes base:
- `pytest tests/test_agents.py`: Verificar se o agente roteirista gera o formato JSON esperado para as páginas.
- `pytest tests/test_image_prompts.py`: Validar se a consolidação de prompts (Bíblia Visual + Personagens) funciona corretamente.
- Comando para rodar: `uv run pytest`

### Manual Verification
1. **Fluxo de Tema**: Selecionar um tema da lista e verificar se a pesquisa web traz fatos reais para o roteiro.
2. **Edição de Personagem**: Criar um novo personagem (ex: "Robô Vermelho"), gerar uma página e validar se a descrição do novo personagem foi injetada no prompt de imagem.
3. **Parametrização de Imagem**: Escolher modelos diferentes (DALL-E vs Flux) para duas páginas diferentes e validar o resultado visual.
4. **Exportação**: Baixar o PDF gerado e verificar se a ordem das páginas e os balões estão legíveis.
5. **Redes Sociais**: Simular a publicação (em modo debug) para as APIs de LinkedIn/Facebook.
