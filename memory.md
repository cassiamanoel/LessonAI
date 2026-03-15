# 🧠 LessonAI Implementation Memory

Este arquivo serve como o diário de bordo técnico e estratégico do projeto LessonAI. Aqui registro cada implementação, o raciocínio por trás dela e os problemas resolvidos.

---

## 🏛️ Histórico de Versões e Pensamentos

### v1.0 - v6.0: Fundação e Orquestração
*   **O que realizei:** Inicialização do projeto com `uv`, configuração do `pyproject.toml` e `agno`. Criação dos agentes (Editor-Chefe e Roteirista).
*   **Meu Pensamento:** A fundação precisava ser sólida e baseada em agentes com ferramentas (Web Search). A escolha do `agno` (antigo Phidata) foi para garantir uma orquestração moderna.

### v7.0 - v8.2: Estabilidade e Limpeza de Dados
*   **O que realizei:** Implementação de loops de retry para contagem de páginas e limpeza de prefixos (ex: "Narrador:").
*   **Meu Pensamento:** O LLM frequentemente falhava em entregar a quantidade exata de páginas ou injetava metadados nos diálogos. A limpeza por regex foi a solução pragmática para garantir o "Marvel Standard".

### v9.0 - v15.0: Revolução Visual (The Lettering Shift)
*   **O que realizei:** Implementação do `ComicComposer` usando Pillow. Fim do "Gibberish" (texto randômico da IA na imagem).
*   **Meu Pensamento:** Tentar fazer a IA gerar texto legível em 2024/2025 ainda é arriscado. Decidi separar as camadas: a IA gera a **arte pura** e o Python gera o **lettering perfeito**. Isso deu o visual profissional que o projeto precisava.

### v16.0 - v25.0: Refinamento Estético e Variedade
*   **O que realizei:** Diferenciação entre falas, pensamentos (clouds), gritos (bursts) e sussurros. Implementação de 12 tipos de balões.
*   **Meu Pensamento:** Uma HQ é feita de nuances. Usei geometria (math/PIL) para criar balões dinâmicos que se adaptam ao texto, inspirados em softwares como Clip Studio Paint.

### v26.0 - v32.0: Consciência Composicional e Estabilidade
*   **O que realizei:** O roteirista passou a pedir "espaço negativo" nos prompts. Implementação de detecção de rostos (bboxes) para evitar cobrir personagens.
*   **Meu Pensamento:** Balões em cima de rostos matam a arte. Treinei o agente para "imaginar" o layout antes de gerar a imagem, garantindo que a composição ficasse harmoniosa.

### v33.0 - [x] v37.0: Blindagem Definitiva (Absolute Art Shield)
*   **O que realizei:**
    - [x] Sincronia de Coordenadas 0-1000 (Composer + Editorial)
    - [x] Proteção Multinível: Hard (Rosto) vs Soft (Corpo)
    - [x] Auto-Shrink de emergência (redução progressiva de fonte)
    - [x] Geometric Hull Tail: Saída precisa para Burst/Cloud
    - [x] Regra de Ouro: Interseção Zero com Rostos após fallback
*   **Meu Pensamento:** Usuários odeiam placeholders vazios. Se o modelo customizado falhar, o sistema agora troca de modelo no meio do processo para garantir que a arte apareça. O Base64 removeu o problema de "expired URLs".

### v35.0: Saneamento de Sessão e Limpeza de Depreciação
*   **O que realizei:** Saneador de URLs no `Composer` e conformidade com `width='stretch'` no Streamlit.
*   **Meu Pensamento:** Resolvi bugs "fantasmas" causados por caches antigos do navegador do usuário, garantindo que o sistema cure a si mesmo de URLs inválidas herdadas de sessões passadas.

### v36.0: Quantum Upgrade - Anatomia Superior
*   **O que realizei:**
    - **v36.0 (Quantum Upgrade)**: Reconstrução da anatomia dos balões, caudas 360º, geometria "tapered" e sistema de pontuação para evitar rostos (Art Guard).
    - **v37.0 (Definitive Art Shield)**: Implementação da blindagem absoluta. Coordenadas sincronizadas 0-1000, proteção multinível (Rosto = Bloqueio total, Corpo = Penalidade), Auto-Shrink reincidente e geometria de cauda ultra-precisa baseada na forma do balão. Regra de aceito: zero colisão com rostos.
*   **Meu Pensamento:** Balões devem servir à arte, não cobri-la. Ao implementar a busca de candidatos para a posição do balão e o descarte de colisões com rostos, o software passou a atuar como um editor de arte humano. A remoção do estilo fixo de "brain" devolveu a versatilidade ao projeto.

### [x] v38.0: Manual Balloon Control (Editor Mode)
*   **O que realizei:**
    - [x] Config: Exportar lista de estilos de balão em `image_config.py`
    - [x] App: Implementar sliders de Intensidade e Posição (X, Y) na revisão de roteiro
    - [x] App: Expandir seleção de `tipo_texto` na UI
    - [x] Composer: Ajustar lógica de estilo `raiva`, `choro` e `eletronico`
    - [x] Validação: Testar ajustes manuais no fluxo completo
*   **Meu Pensamento:** Usuários odeiam placeholders vazios. Se o modelo customizado falhar, o sistema agora troca de modelo no meio do processo para garantir que a arte apareça. O Base64 removeu o problema de "expired URLs".

### [x] v39.0: Interactive Layout Editor (Drag & Drop)
*   **O que realizei:**
    - [x] v39.0: Interactive Layout Editor (Drag & Drop)
    - [x] Dependências: Instalar `streamlit-drawable-canvas`
    - [x] App: Integrar componente de Canvas para posicionamento interativo
    - [x] App: Mapeamento bidirecional Canvas <-> normalized (0-1000)
    - [x] Composer: Implementar `manual_pos` para respeitar arrasto exato
    - [x] Validação: Garantir que o arrasto atualize o script em tempo real
*   **Meu Pensamento:** Balões devem servir à arte, não cobri-la. Ao implementar a busca de candidatos para a posição do balão e o descarte de colisões com rostos, o software passou a atuar como um editor de arte humano. A remoção do estilo fixo de "brain" devolveu a versatilidade ao projeto.

---
### [x] v40.0: Image Generation Mocking (Cost Saver)
*   **O que realizei:**
    - [x] Assets: Gereu uma imagem premium (`assets/comic_mock.png`) para testes.
    - [x] ImageEngine: Adicionei lógica para capturar `IMAGE_MOCK` e retornar a imagem local em Base64.
    - [x] Sidebar: Toggle manual para economia de créditos.
*   **Meu Pensamento:** Economizar custos durante o polimento de layout é essencial.

### [x] v40.1: Fix Mock Mode Compatibility
*   **O que realizei:** Corrigi o erro `InvalidSchema` no `app.py` que impedia o uso de URLs Base64 no Editor de Layout.
*   **Meu Pensamento:** A robustez do sistema depende de lidar com diferentes protocolos de transporte de imagem (HTTP vs Data).

---
### [x] v41.0: Unified Interactive Balloon Editor
*   **O que realizei:**
    - [x] App: Uni no mesmo lugar (Editor de Layout) a escolha do tipo de balão, a escala e o arrasto de posição.
*   **Meu Pensamento:** O usuário quer o controle total sobre o enquadramento. Ao colocar o seletor de estilo e escala junto com o canvas de arrasto, fecho o ciclo de feedback visual imediato. Se o balão cair no rosto, ele arrasta; se ficar pequeno, aumenta a escala; se o tom mudar, troca o estilo — tudo num só clique.

### [x] v42.0: Aesthetic Refinement & Distortion Fix
*   **O que realizei:**
    - [x] Composer: Implementar controle de Aspect Ratio para balões
    - [x] Composer: Adicionar sombras e suavização de bordas
    - [x] Composer: Refinar geometria de caudas (Quantum Tails 2.0)
    - [x] Validação: Comparar com visual reportado pelo usuário
*   **Meu Pensamento:** HQ é contraste. O visual anterior era muito plano ("flat"). Com as sombras e o controle de aspect ratio, a página ganha tridimensionalidade e os balões param de parecer "esticados" artificialmente.

### [x] v42.1: UI Cleanup
*   **O que realizei:**
    - [x] App: Removi os campos redundantes (Estilo, Escala, Posição) da seção "Revisão do Roteiro".
*   **Meu Pensamento:** Uma interface limpa é fundamental. Como o controle interativo no Layout Editor (v41.0) é superior, manter os controles antigos no roteiro estava apenas gerando confusão e potenciais conflitos de estado. Agora o roteiro foca no texto e o layout foca na arte.

### [x] v43.0: Absolute Bbox Fidelity (Source of Truth)
*   **O que realizei:**
    - [x] App: Passei a capturar o BBox completo (`left`, `top`, `width`, `height`) do editor.
    - [x] Composer: Implementei o override absoluto. Se o BBox manual existir, o Pillow usa exatamente aquelas dimensões, sem recalcular nada.
*   **Meu Pensamento:** O balão agora é previsível. Antes, o `manual_pos` era apenas uma sugestão de "ancoragem", mas o tamanho ainda era flutuante. Agora, o retângulo vermelho no editor é o contrato final: o que você desenha ali é o que sai no PNG.

### [x] v45.0: Smart Character Targeting (Vision-Based)
*   **O que realizei:**
    - [x] Pipeline: Criei o `VisionEngine` usando Gemini 1.5 Flash para detectar automaticamente as coordenadas do rosto do personagem principal.
    - [x] App: Integrei a análise visual logo após a geração da imagem, preenchendo o campo `personagem_pos` automaticamente.
*   **Meu Pensamento:** A composição agora é "consciente" do conteúdo da imagem. Antes as caudas apontavam para um ponto genérico; hoje, a I.A. "olha" para o quadro, vê quem é o protagonista e direciona a fala exatamente para ele, poupando trabalho manual de ajuste.

### [x] v45.1: Smart Anchor Precision (Target Selection)
*   **O que realizei:**
    - [x] Composer: Refinei `_resolve_anchor_v37` para selecionar o alvo da cauda baseando-se no personagem mais evidente (maior área de rosto/corpo).
    - [x] Lógica de Separação: Garanti que a posição manual do balão (`manual_bbox`) não interfira na âncora, mantendo o alvo sempre no personagem.
*   **Meu Pensamento:** A inteligência visual agora tem prioridade narrativa. Mesmo que o usuário arraste o balão para longe, a cauda sabe exatamente quem está falando porque ela "busca" o rosto mais proeminente no quadro. Isso resolve o problema de caudas apontando para o vazio.

### [x] v46.0: Manual Tail Target Control
*   **O que realizei:**
    - [x] App: Adicionei um segundo "handle" (círculo verde) no Editor de Layout via `st_canvas`. Agora o usuário pode mover o balão e o alvo da cauda de forma independente.
    - [x] Composer: Implementei `_resolve_tail_target` com prioridade estrita: Ajuste Manual > Detecção Vision > Geometria de Rostos > Geometria de Corpos > Centro.
*   **Meu Pensamento:** Demos o "controle de diretor" final para o usuário. A automação (Vision) faz 90% do trabalho, mas se o usuário quiser que a cauda aponte para um detalhe específico (como uma arma, um objeto ou um personagem secundário), ele simplesmente arrasta a mira verde.

### [x] v47.0: 360º Tail Control (Handle Origin & Target)
*   **O que realizei:**
    - [x] App: Controle triplo no Editor (Balão + Alvo + Origem). Adicionei um handle azul para a origem da cauda e uma linha de guia visual.
    - [x] Composer: Implementei o suporte ao `manual_tail_origin` com lógica de "snapping". A cauda agora gruda na borda do balão mesmo se o handle for movido para fora, garantindo integridade visual.
*   **Meu Pensamento:** Liberdade criativa total. O usuário agora pode rotacionar a seta 360º, movendo a saída do balão para o topo, lados ou base, permitindo composições muito mais dinâmicas e evitando que a cauda cruze o texto ou o rosto do personagem de forma estranha.

---
*Última atualização: 2026-03-15 - Antigravity AI*
