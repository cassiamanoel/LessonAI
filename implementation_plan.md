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

### [v42.0] Aesthetic Refinement & Distortion Fix
Melhoria na geometria e aparência dos balões para eliminar distorção (pancakes) e layout "pobre".

#### [MODIFY] [src/pipeline/composer.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/src/pipeline/composer.py)
- **Aspect Ratio Control**: Adaptar `_calculate_balloon_metrics` para garantir proporções equilibradas (fuga do achatamento horizontal).
- **Quantum Tails 2.0**: Implementar bases mais largas e caudas "espessas" (tapered) para melhor visual.
- **Visual Depth**: Adicionar sombras (dropshadows) sutis nos balões.
- **Smoothing**: Aplicar filtros de suavização nas bordas das formas geométricas.
- **Shape Adaptive**: Usar Rounded Rectangles para textos longos de linha única.

---

### [v43.0] Absolute BBox Fidelity (Source of Truth)
Eliminar discrepâncias entre o Editor de Layout e a imagem final usando `manual_bbox` como prioridade absoluta.

#### [MODIFY] [app.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/app.py)
- **BBox Tracking**: Capturar `left`, `top`, `width * scaleX` e `height * scaleY` do canvas.
- **Normalization**: Salvar como `manual_bbox` em coordenadas 0-1000.

#### [MODIFY] [src/pipeline/composer.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/src/pipeline/composer.py)
- **Absolute Override**: Se `manual_bbox` existir, ignorar `_calculate_balloon_metrics` para dimensões.
- **Fixed Dimensions**: Forçar `bw` e `bh` do balão para bater com o BBox manual.
- **No Snapping**: Desativar heurísticas de ajuste fino quando o posicionamento for manual.

---

### [v45.0] Smart Character Targeting (Vision-Based)
Analisar imagens geradas via I.A. Vision para identificar personagens e apontar balões automaticamente.

#### [NEW] [vision_engine.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/src/pipeline/vision_engine.py)
- **Character Detection**: Usar Gemini 1.5 Flash para detectar `[x, y]` do rosto do personagem principal.
- **Normalization**: Converter coordenadas da imagem para o sistema 0-1000.

#### [MODIFY] [app.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/app.py)
- **Vision Integration**: Chamar `VisionEngine` após cada geração bem-sucedida.
- **Data Injection**: Salvar o resultado em `personagem_pos` no dicionário do quadro.

#### [MODIFY] [src/pipeline/composer.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/src/pipeline/composer.py)
- **Anchor Priority**: Garantir que a cauda do balão use preferencialmente o ponto detectado pela visão.

---

### [v45.1] Smart Anchor Precision (Target Selection)
Garantir que a cauda do balão aponte sempre para o personagem mais importante, priorizando rostos.

#### [MODIFY] [src/pipeline/composer.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/src/pipeline/composer.py)
- **Anchor Priority Search**: Modificar `_resolve_anchor_v37` para:
    1. Buscar o maior `face_bbox` (pela área).
    2. Buscar o maior `character_bbox` (pela área).
    3. Usar `personagem_pos` como fallback/override.
- **Robust Mapping**: Garantir que as coordenadas normalizadas sejam convertidas corretamente em pixels reais do painel antes do desenho.

---

### [v46.0] Manual Tail Target Control
Adicionar um handle específico no editor para controlar o alvo da seta do balão.

#### [MODIFY] [app.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/app.py)
- **Dual Control Editor**: Configurar `st_canvas` para aceitar múltiplos objetos (um retângulo para o balão e um círculo para o alvo).
- **Initial State**: Pré-carregar o alvo na última posição conhecida ou no centro detectado.
- **Coord Capture**: Identificar qual objeto é o "alvo" no JSON de retorno e salvar como `manual_tail_target` (0-1000).

#### [MODIFY] [src/pipeline/composer.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/src/pipeline/composer.py)
- **Target Resolution**: Implementar `_resolve_tail_target` substituindo a lógica antiga de âncora.
- **Strict Priority**: Seguir a ordem `manual_tail_target > personagem_pos > maior face_bbox > maior character_bbox > fallback`.

---

### [v47.0] 360º Tail Control (Handle Origin & Target)
Permitir que o usuário controle tanto onde a cauda aponta quanto de onde ela sai do balão.

#### [MODIFY] [app.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/app.py)
- **Triple Control Editor**: Adicionar um terceiro objeto ao `st_canvas` (um círculo azul) para definir o `manual_tail_origin` (0-1000).
- **Visualization**: Traçar uma linha (id: "tail_line") em tempo real no editor conectando a Origem ao Alvo para facilitar a visualização 360º.
- **State Persistence**: Salvar `manual_tail_origin` e `manual_tail_target`.

#### [MODIFY] [src/pipeline/composer.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/src/pipeline/composer.py)
- **Origin Override**: Atualizar `_draw_balloon_v37_geometric` para usar `manual_tail_origin` se existir.
- **Edge Projection**: Garantir que se a origem manual estiver "fora" do balão, ela seja projetada na borda mais próxima para manter a estética.

---

### [v48.0] Professional PIL-Based Balloon Presets
Migrar o desenho de balões de geometria simples para um motor de "High-Fidelity PIL" que simula balões profissionais de HQ através de caminhos orgânicos e jittering.

#### [NEW] [balloon_presets.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/src/pipeline/balloon_presets.py)
- **Professional Engine**: Criar um catálogo de presets que gera polígonos complexos em PIL:
    - `Standard`: Elipse orgânica com jitter de 1-2% para visual hand-drawn.
    - `Burst`: Burst dinâmico com pontas de comprimentos variáveis para gritos.
    - `Cloud`: Estrutura de nuvem composta por múltiplos "blobs" orgânicos.
    - `Narrative`: Caixa retangular com bordas levemente "trêmulas" (ink style).
- **Ink Control**: Implementar suporte a bordas com espessura variável e hachuras simples.

#### [MODIFY] [composer.py](file:///c:/Users/andre/OneDrive/Documentos/LessonAI/src/pipeline/composer.py)
- **Integration**: Substituir a lógica geométrica antiga pela chamada ao novo `BalloonPresets`.

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
