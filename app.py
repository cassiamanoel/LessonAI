from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import streamlit as st
import json
from io import BytesIO
import streamlit.elements.lib.image_utils as image_utils
import streamlit.elements.image as st_image
from streamlit.runtime.runtime import Runtime
import io
import requests

# v39.2: Monkeypatch cirúrgico para compatibilidade com streamlit-drawable-canvas no Streamlit 1.55+
def image_to_url_patch(image, layout_config, clamp, channels, output_format, image_id):
    if isinstance(image, str) and (image.startswith("http") or image.startswith("data:")):
        return image
    if not isinstance(image, (bytes, str)):
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        image_data = buffered.getvalue()
    else:
        image_data = image
    mimetype = "image/png"
    try:
        return Runtime.instance().media_file_mgr.add(image_data, mimetype, image_id)
    except Exception:
        return ""

if not hasattr(image_utils, "image_to_url"):
    image_utils.image_to_url = image_to_url_patch
if not hasattr(st_image, "image_to_url"):
    st_image.image_to_url = image_to_url_patch

from src.ui.sidebar import render_sidebar
from src.agents.editorial import ComicScriptGenerator
from src.pipeline.image_engine import ImageEngine
from src.pipeline.vision_engine import VisionEngine
from src.pipeline.prompt_builder import build_consolidated_visual_prompt
from src.pipeline.composer import ComicComposer, StrictRenderError
from src.config.managers import CharacterManager

st.set_page_config(page_title="LessonAI Comic Generator", layout="wide")

from src.utils.debug_logger import DebugLogger
DebugLogger.increment_rerun()

# ======================================================================
# INICIALIZAÇÃO DO ESTADO
# ======================================================================
if "step" not in st.session_state:
    st.session_state.step = "tema"
if "script" not in st.session_state:
    st.session_state.script = None
if "pages_images" not in st.session_state:
    st.session_state.pages_images = {}
if "resumo" not in st.session_state:
    st.session_state.resumo = None
if "tema_atual" not in st.session_state:
    st.session_state.tema_atual = ""

# Migração de estados legados
if st.session_state.step in ("imagens", "exportar"):
    st.session_state.step = "paginas"

config = render_sidebar()

st.title("LessonAI: HQs Educativas sobre IA")


def _generate_panel_image(engine, prompt: str, page_idx: int, panel_idx: int) -> bytes:
    """Gera uma imagem para um quadro e retorna bytes validados.
    Em caso de falha, retorna bytes de uma imagem placeholder vermelha."""
    import base64

    try:
        result = engine.generate(prompt)
        if not result:
            raise ValueError("Gerador retornou resultado vazio")

        content = None

        # Caso 1: base64 inline (mock ou API que retorna base64)
        if isinstance(result, str) and result.startswith("data:image"):
            encoded = result.split(",", 1)[1]
            content = base64.b64decode(encoded)

        # Caso 2: bytes diretos (alguns SDKs retornam assim)
        elif isinstance(result, bytes):
            content = result

        # Caso 3: URL HTTP (DALL-E, Flux, etc.)
        elif isinstance(result, str) and result.startswith("http"):
            resp = requests.get(result, timeout=30)
            resp.raise_for_status()
            content = resp.content

        # Caso 4: lista de URLs (Replicate retorna lista)
        elif isinstance(result, list) and len(result) > 0:
            url = str(result[0])
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            content = resp.content

        else:
            raise ValueError(f"Formato inesperado do gerador: {type(result)}")

        # Valida que os bytes são uma imagem real
        img = Image.open(BytesIO(content))
        img.load()
        st.success(f"P{page_idx+1} Q{panel_idx+1}: {img.size[0]}x{img.size[1]}")
        return content

    except Exception as e:
        st.error(f"P{page_idx+1} Q{panel_idx+1}: {e}")
        # Gera placeholder visual para não travar o compositor
        placeholder = Image.new("RGB", (1024, 1024), (80, 0, 0))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(placeholder)
        draw.text((100, 480), f"ERRO: {str(e)[:60]}", fill="#FF4444")
        buf = BytesIO()
        placeholder.save(buf, format="PNG")
        return buf.getvalue()

# Barra de progresso visual
STEPS = ["tema", "resumo", "roteiro", "paginas", "editor"]
STEP_LABELS = ["1. Tema", "2. Resumo", "3. Roteiro", "4. Páginas", "5. Editor"]
current_idx = STEPS.index(st.session_state.step) if st.session_state.step in STEPS else 0
cols_progress = st.columns(len(STEPS))
for i, label in enumerate(STEP_LABELS):
    if i < current_idx:
        cols_progress[i].markdown(f"~~{label}~~")
    elif i == current_idx:
        cols_progress[i].markdown(f"**{label}**")
    else:
        cols_progress[i].markdown(f"<span style='color:gray'>{label}</span>", unsafe_allow_html=True)

st.divider()

# ======================================================================
# TELA 1: TEMA
# ======================================================================
if st.session_state.step == "tema":
    st.subheader("Qual conceito de IA você quer ensinar?")

    tema_selecionado = config["theme"]
    tema_livre = st.text_input(
        "Digite o tema",
        placeholder="Ex: RAG (Retrieval Augmented Generation), Machine Learning, AI Agents...",
        key="tema_livre_input"
    )

    target_theme = tema_livre if tema_livre else tema_selecionado

    if st.button("Gerar Resumo", type="primary", disabled=not target_theme):
        st.session_state.tema_atual = target_theme
        with st.spinner("Pesquisando e gerando resumo sobre o tema..."):
            generator = ComicScriptGenerator(config["llm"]["provider"], config["llm"]["model"], config["language"])
            # Gera um resumo detalhado do tema usando o LLM
            from agno.agent import Agent
            from agno.models.openai import OpenAIChat
            from src.search.web_search import search_web

            resumo_agent = Agent(
                name="Resumo Educacional",
                model=OpenAIChat(id=config["llm"]["model"]),
                tools=[search_web],
                instructions=[
                    f"Idioma: {config['language']}.",
                    "Você é um especialista em Inteligência Artificial.",
                    "Gere um resumo educacional DETALHADO sobre o conceito de IA solicitado.",
                    "O resumo deve ter 3-5 parágrafos cobrindo:",
                    "  1. O que é o conceito (definição clara)",
                    "  2. Como funciona na prática (mecanismo)",
                    "  3. Por que é importante (aplicações reais)",
                    "  4. Uma analogia criativa para facilitar o entendimento",
                    "Escreva de forma acessível mas precisa. Use linguagem profissional.",
                    "NÃO use markdown, bullet points ou formatação especial. Apenas texto corrido em parágrafos.",
                ],
            )
            response = resumo_agent.run(f"Gere um resumo educacional detalhado sobre: {target_theme}")
            st.session_state.resumo = response.content if isinstance(response.content, str) else str(response.content)

        st.session_state.step = "resumo"
        st.rerun()

# ======================================================================
# TELA 2: RESUMO
# ======================================================================
elif st.session_state.step == "resumo":
    st.subheader(f"Resumo: {st.session_state.tema_atual}")
    st.caption("Revise e edite o resumo. Ele será usado como base para criar o roteiro da HQ.")

    resumo_editado = st.text_area(
        "Resumo do tema",
        value=st.session_state.resumo or "",
        height=300,
        key="resumo_editor"
    )
    st.session_state.resumo = resumo_editado

    st.divider()

    # Escolha da quantidade de páginas
    num_pages = st.slider("Quantidade de páginas da HQ", 1, 5, config["num_pages"], key="num_pages_resumo")

    col1, col2 = st.columns(2)
    if col1.button("Voltar ao Tema"):
        st.session_state.step = "tema"
        st.rerun()
    if col2.button("Gerar Roteiro", type="primary"):
        with st.spinner("Criando roteiro com os 8 personagens..."):
            generator = ComicScriptGenerator(config["llm"]["provider"], config["llm"]["model"], config["language"])
            # Injeta o resumo como contexto extra para o roteirista
            enriched_theme = (
                f"{st.session_state.tema_atual}\n\n"
                f"CONTEXTO DETALHADO (use como base para o enredo):\n{st.session_state.resumo}"
            )
            script_data = generator.generate(enriched_theme, num_pages=num_pages)

            if isinstance(script_data, str):
                try:
                    st.session_state.script = json.loads(script_data)
                except Exception:
                    st.session_state.script = script_data
            else:
                st.session_state.script = script_data

        st.session_state.step = "roteiro"
        st.rerun()

# ======================================================================
# TELA 3: ROTEIRO (visão geral, sem edição por quadro individual)
# ======================================================================
elif st.session_state.step == "roteiro":
    st.subheader("Roteiro da HQ")

    script = st.session_state.script
    if isinstance(script, dict):
        script["titulo_hq"] = st.text_input("Título da HQ", value=script.get("titulo_hq", ""), key="hq_title")

        for i, pg in enumerate(script.get("paginas", [])):
            with st.expander(f"Página {i+1}: {pg.get('titulo', '')}", expanded=True):
                pg["titulo"] = st.text_input(f"Título", value=pg.get("titulo", ""), key=f"pg_title_{i}")

                for j, q in enumerate(pg.get("quadros", [])):
                    col1, col2 = st.columns([3, 2])
                    with col1:
                        q["descricao"] = st.text_area(
                            f"Cena {j+1} — Descrição visual",
                            value=q.get("descricao", ""),
                            height=80,
                            key=f"q_desc_{i}_{j}"
                        )
                    with col2:
                        q["dialogo"] = st.text_area(
                            f"Cena {j+1} — Diálogo",
                            value=q.get("dialogo", ""),
                            height=80,
                            key=f"q_dial_{i}_{j}"
                        )
                    # Personagens em linha
                    q["personagens"] = st.text_input(
                        f"Personagens (Cena {j+1})",
                        value=", ".join(q.get("personagens", [])),
                        key=f"q_char_{i}_{j}"
                    ).split(",")
                    q["personagens"] = [p.strip() for p in q["personagens"] if p.strip()]
                    if j < len(pg.get("quadros", [])) - 1:
                        st.markdown("---")
    else:
        st.error("Erro ao gerar roteiro estruturado.")
        st.code(script)

    st.divider()
    col1, col2 = st.columns(2)
    if col1.button("Voltar ao Resumo"):
        st.session_state.step = "resumo"
        st.rerun()
    if col2.button("Gerar Páginas", type="primary"):
        st.session_state.step = "paginas"
        st.rerun()

# ======================================================================
# TELA 4: PÁGINAS — Geração e exibição de páginas compostas
# ======================================================================
elif st.session_state.step == "paginas":
    st.subheader("Geração de Páginas")

    if not isinstance(st.session_state.script, dict) or "paginas" not in st.session_state.script:
        st.warning("Roteiro não disponível. Volte e gere o roteiro primeiro.")
    else:
        paginas = st.session_state.script["paginas"]
        total_pages = len(paginas)

        # Botão para gerar TODAS as páginas de uma vez
        all_generated = all(f"clean_page_composed_{i}" in st.session_state for i in range(total_pages))

        if not all_generated:
            if st.button("Gerar Todas as Páginas", type="primary"):
                img_engine = ImageEngine(config["img"]["provider"], config["img"]["model"])
                cm = CharacterManager()

                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, pg in enumerate(paginas):
                    quadros = pg.get("quadros", [])
                    status_text.text(f"Gerando página {i+1}/{total_pages} ({len(quadros)} quadros)...")

                    panel_bytes_list = []
                    for idx, q in enumerate(quadros):
                        prompt = build_consolidated_visual_prompt(
                            q["descricao"], q.get("dialogo", ""), q.get("personagens", []),
                            config["style"], cm.get_all()
                        )

                        img_bytes = _generate_panel_image(img_engine, prompt, i, idx)
                        panel_bytes_list.append(img_bytes)

                        # Detecta posição do personagem (opcional)
                        if isinstance(img_bytes, bytes):
                            try:
                                vision = VisionEngine()
                                target_pos = vision.detect_main_character(
                                    Image.open(BytesIO(img_bytes))
                                )
                                if target_pos != [500, 500]:
                                    q["personagem_pos"] = target_pos
                            except Exception:
                                pass

                    st.session_state.pages_images[i] = panel_bytes_list

                    # Compõe a página automaticamente
                    try:
                        composer = ComicComposer()
                        composed_page = composer.create_clean_page(
                            st.session_state.pages_images[i], quadros, render_mode="draft"
                        )
                        buf = BytesIO()
                        composed_page.save(buf, format="PNG")
                        st.session_state[f"clean_page_composed_{i}"] = buf.getvalue()
                    except Exception as e:
                        st.error(f"Erro ao compor página {i+1}: {e}")

                    progress_bar.progress((i + 1) / total_pages)

                status_text.text("Todas as páginas geradas!")
                st.rerun()

        # Exibe páginas compostas
        for i in range(total_pages):
            page_key = f"clean_page_composed_{i}"
            if page_key in st.session_state:
                st.image(
                    st.session_state[page_key],
                    caption=f"Página {i+1}: {paginas[i].get('titulo', '')}",
                    use_container_width=True
                )
            else:
                st.info(f"Página {i+1} ainda não gerada.")

        # Ações
        st.divider()
        col1, col2, col3 = st.columns(3)
        if col1.button("Voltar ao Roteiro"):
            st.session_state.step = "roteiro"
            st.rerun()
        if col2.button("Regenerar Páginas"):
            # Limpa cache de páginas para regenerar
            for i in range(total_pages):
                if i in st.session_state.pages_images:
                    del st.session_state.pages_images[i]
                if f"clean_page_composed_{i}" in st.session_state:
                    del st.session_state[f"clean_page_composed_{i}"]
            st.rerun()
        if col3.button("Ir para Editor de Balões", type="primary", disabled=not all_generated):
            st.session_state.step = "editor"
            st.rerun()

# ======================================================================
# TELA 5: EDITOR VISUAL DE BALÕES
# ======================================================================
elif st.session_state.step == "editor":
    from src.config.image_config import COMIC_STYLE_NAMES
    from streamlit_drawable_canvas import st_canvas
    import copy as _copy

    BALLOON_TYPES = [
        "fala", "pensamento", "grito", "sussurro", "narracao",
        "eletronico", "enfatico", "raiva", "choro", "duvida",
        "admiracao", "ideia", "musica", "silencio",
    ]
    COLORS = ["#FF4444", "#44FF44", "#4488FF", "#FFAA00", "#FF44FF",
              "#44FFFF", "#FFFF44", "#AA88FF", "#FF8844", "#88FF44"]

    if "balloons_by_page" not in st.session_state:
        st.session_state.balloons_by_page = {
            i: [] for i in range(len(st.session_state.script.get("paginas", [])))
        }
    # Counter que incrementa APENAS quando balões são adicionados/removidos.
    # Isso força o canvas a reinicializar com novos objetos.
    if "canvas_version" not in st.session_state:
        st.session_state.canvas_version = 0

    num_pages = len(st.session_state.script.get("paginas", []))
    pg_idx = st.selectbox(
        "Pagina:", range(num_pages),
        format_func=lambda x: f"Pagina {x+1}",
        key="editor_page_sel"
    )
    pg = st.session_state.script["paginas"][pg_idx]
    balloons = st.session_state.balloons_by_page.get(pg_idx, [])

    # --- Helpers ---
    def _add_balloon(q_idx, q_data):
        """Adiciona balão com posição distribuída e incrementa canvas version."""
        n = len(balloons)
        # Distribui em grid para não sobrepor
        col_pos = n % 3
        row_pos = n // 3
        x = 30 + col_pos * 320
        y = 30 + (row_pos * 180) % 750
        balloons.append({
            "text": q_data.get("dialogo", "").strip(),
            "type": q_data.get("tipo_texto", "fala"),
            "bbox": [x, y, 280, 140],
            "tail_target": q_data.get("personagem_pos", [500, 500]),
            "intensity": 1.0,
            "_source_q": q_idx,
        })
        st.session_state.balloons_by_page[pg_idx] = balloons
        st.session_state.canvas_version += 1

    def _read_canvas_positions(canvas_result, canvas_w, canvas_h):
        """Lê posições do canvas por ORDEM dos objetos (não por id).
        Padrão: para cada balão i → objects[2*i] = rect, objects[2*i+1] = circle."""
        live = _copy.deepcopy(balloons)
        if not canvas_result.json_data or "objects" not in canvas_result.json_data:
            return live
        objs = canvas_result.json_data["objects"]
        for i in range(len(live)):
            rect_idx = 2 * i
            tail_idx = 2 * i + 1
            # Retângulo do balão
            if rect_idx < len(objs):
                obj = objs[rect_idx]
                sx = obj.get("scaleX", 1)
                sy = obj.get("scaleY", 1)
                live[i]["bbox"] = [
                    max(0, int(obj["left"] * 1000 / canvas_w)),
                    max(0, int(obj["top"] * 1000 / canvas_h)),
                    max(60, int(obj["width"] * sx * 1000 / canvas_w)),
                    max(40, int(obj["height"] * sy * 1000 / canvas_h)),
                ]
            # Círculo da cauda
            if tail_idx < len(objs):
                obj = objs[tail_idx]
                r = obj.get("radius", 10) * obj.get("scaleX", 1)
                live[i]["tail_target"] = [
                    max(0, min(int((obj["left"] + r) * 1000 / canvas_w), 1000)),
                    max(0, min(int((obj["top"] + r) * 1000 / canvas_h), 1000)),
                ]
        return live

    # ---- LAYOUT ----
    col_script, col_canvas, col_props = st.columns([1.2, 3, 1.8])

    # === COLUNA ESQUERDA: ROTEIRO ===
    with col_script:
        st.markdown("### Roteiro")
        for q_idx, q in enumerate(pg.get("quadros", [])):
            dialogo = q.get("dialogo", "").strip()
            if not dialogo:
                continue
            already = any(b.get("_source_q") == q_idx for b in balloons)
            with st.expander(f"Q{q_idx+1} {'✓' if already else ''}", expanded=not already):
                chars = ", ".join(q.get("personagens", []))
                if chars:
                    st.caption(f"[{chars}]")
                st.write(dialogo)
                if not already:
                    if st.button("Adicionar", key=f"inj_{pg_idx}_{q_idx}"):
                        _add_balloon(q_idx, q)
                        st.rerun()

        st.markdown("---")
        all_done = all(
            any(b.get("_source_q") == qi for b in balloons)
            for qi, q in enumerate(pg.get("quadros", []))
            if q.get("dialogo", "").strip()
        )
        if not all_done:
            if st.button("Adicionar todos"):
                for qi, q in enumerate(pg.get("quadros", [])):
                    d = q.get("dialogo", "").strip()
                    if d and not any(b.get("_source_q") == qi for b in balloons):
                        _add_balloon(qi, q)
                st.rerun()

    # === COLUNA CENTRAL: CANVAS INTERATIVO ===
    with col_canvas:
        clean_key = f"clean_page_composed_{pg_idx}"
        if clean_key not in st.session_state:
            st.warning("Pagina nao gerada.")
        else:
            clean_img = Image.open(BytesIO(st.session_state[clean_key]))
            CANVAS_W = 700
            CANVAS_H = int(CANVAS_W * clean_img.height / clean_img.width)
            bg = clean_img.resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)

            # Monta objetos iniciais (só usado quando canvas_version muda)
            objects = []
            for i, b in enumerate(balloons):
                color = COLORS[i % len(COLORS)]
                bx = b["bbox"][0] * CANVAS_W / 1000
                by = b["bbox"][1] * CANVAS_H / 1000
                bw = b["bbox"][2] * CANVAS_W / 1000
                bh = b["bbox"][3] * CANVAS_H / 1000
                objects.append({
                    "type": "rect",
                    "left": bx, "top": by, "width": bw, "height": bh,
                    "fill": f"{color}40", "stroke": color, "strokeWidth": 3,
                    "id": f"b_{i}",
                })
                tx = b["tail_target"][0] * CANVAS_W / 1000
                ty = b["tail_target"][1] * CANVAS_H / 1000
                objects.append({
                    "type": "circle",
                    "left": tx - 10, "top": ty - 10, "radius": 10,
                    "fill": color, "stroke": "#FFFFFF", "strokeWidth": 2,
                    "id": f"t_{i}",
                })

            st.caption("Arraste retangulos = mover/redimensionar balao. Arraste circulos = direcionar cauda.")

            # Key muda APENAS quando balões são add/removidos (canvas_version)
            # Isso garante que arrastar NÃO reseta o canvas
            canvas_key = f"cv_{pg_idx}_v{st.session_state.canvas_version}"
            result = st_canvas(
                background_image=bg,
                drawing_mode="transform",
                initial_drawing={"version": "4.4.0", "objects": objects},
                update_streamlit=True,
                height=CANVAS_H,
                width=CANVAS_W,
                key=canvas_key,
            )

            # Lê posições LIVE do canvas (sem feedback loop)
            live_balloons = _read_canvas_positions(result, CANVAS_W, CANVAS_H)

            # Preview renderizado
            if live_balloons:
                st.markdown("---")
                composer = ComicComposer()
                preview = composer.render_balloons_on_page(clean_img.copy(), live_balloons)
                st.image(preview, use_container_width=True)

                # Botão para salvar posições definitivamente
                if st.button("Salvar posicoes", type="primary"):
                    st.session_state.balloons_by_page[pg_idx] = live_balloons
                    balloons = live_balloons
                    st.session_state.canvas_version += 1
                    st.rerun()

    # === COLUNA DIREITA: PROPRIEDADES ===
    with col_props:
        if not balloons:
            st.info("Injete baloes pelo roteiro.")
        else:
            st.markdown("### Baloes")
            for i, b in enumerate(balloons):
                color = COLORS[i % len(COLORS)]
                with st.expander(f"B{i+1}: {b['text'][:18]}...", expanded=False):
                    st.markdown(f"<span style='color:{color}'>&#9632;</span> {b['type']}", unsafe_allow_html=True)

                    cur = b["type"] if b["type"] in BALLOON_TYPES else "fala"
                    b["type"] = st.selectbox(
                        "Tipo", BALLOON_TYPES,
                        index=BALLOON_TYPES.index(cur),
                        key=f"bt_{pg_idx}_{i}"
                    )

                    new_txt = st.text_area("Texto", b["text"], height=60, key=f"tx_{pg_idx}_{i}")
                    if new_txt != b["text"]:
                        b["text"] = new_txt

                    if st.button("Remover", key=f"rm_{pg_idx}_{i}"):
                        balloons.pop(i)
                        st.session_state.balloons_by_page[pg_idx] = balloons
                        st.session_state.canvas_version += 1
                        st.rerun()

            st.markdown("---")
            if st.button("Limpar todos"):
                st.session_state.balloons_by_page[pg_idx] = []
                st.session_state.canvas_version += 1
                st.rerun()

            st.markdown("---")
            if st.button("Limpar todos"):
                st.session_state.balloons_by_page[pg_idx] = []
                st.rerun()

    # === EXPORTAÇÃO ===
    st.divider()
    col_back, col_export = st.columns([1, 2])
    if col_back.button("Voltar para Paginas"):
        st.session_state.step = "paginas"
        st.rerun()
    if col_export.button("FINALIZAR E EXPORTAR PDF", type="primary"):
        composer = ComicComposer()
        final_pages = []
        for i in range(num_pages):
            c_key = f"clean_page_composed_{i}"
            if c_key in st.session_state:
                c_img = Image.open(BytesIO(st.session_state[c_key]))
                p_final = composer.render_balloons_on_page(
                    c_img, st.session_state.balloons_by_page.get(i, [])
                )
                buf = BytesIO()
                p_final.save(buf, format="PNG")
                final_pages.append(buf.getvalue())

        if final_pages:
            pdf_buf = ComicComposer().export_pdf(final_pages)
            st.success("HQ gerada com sucesso!")
            st.download_button(
                "Baixar PDF", pdf_buf,
                f"lessonai_{st.session_state.tema_atual[:30]}.pdf",
                "application/pdf"
            )
