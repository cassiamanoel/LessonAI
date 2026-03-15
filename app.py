import streamlit as st
import json
from io import BytesIO
import streamlit.elements.lib.image_utils as image_utils
import streamlit.elements.image as st_image
from streamlit.runtime.runtime import Runtime
import io

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
from src.pipeline.composer import ComicComposer
from src.config.managers import CharacterManager

st.set_page_config(page_title="LessonAI Comic Generator", layout="wide")

# Inicialização do estado
if "step" not in st.session_state:
    st.session_state.step = "tema"
if "script" not in st.session_state:
    st.session_state.script = None
if "pages_images" not in st.session_state:
    st.session_state.pages_images = {}

config = render_sidebar()

st.title("🚀 LessonAI: O Seu Criador de HQs Educativas")

# TELA 1: TEMA
if st.session_state.step == "tema":
    st.subheader("1. Defina o Tema da sua HQ")
    tema_selecionado = config["theme"]
    tema_livre = st.text_input("Ou digite um tema customizado", placeholder="Ex: O Ciclo da Água explicado por robôs", key="tema_livre_input")
    
    target_theme = tema_livre if tema_livre else tema_selecionado
    
    if st.button("🔍 Gerar Roteiro e Pesquisar"):
        with st.spinner("Pesquisando e escrevendo roteiro..."):
            generator = ComicScriptGenerator(config["llm"]["provider"], config["llm"]["model"], config["language"])
            script_data = generator.generate(target_theme, num_pages=config["num_pages"])
            # Se for string (fallback), tenta converter. Se já for dict (Pydantic dump), usa direto.
            if isinstance(script_data, str):
                try:
                    st.session_state.script = json.loads(script_data)
                except:
                    st.session_state.script = script_data
            else:
                st.session_state.script = script_data
            st.session_state.step = "roteiro"
            if isinstance(st.session_state.script, dict):
                p_count = len(st.session_state.script.get("paginas", []))
                st.info(f"Roteiro gerado com sucesso! ({p_count} páginas encontradas)")
            st.rerun()

# TELA 2: ROTEIRO
elif st.session_state.step == "roteiro":
    st.subheader("📖 2. Revisão do Roteiro")
    st.write("Ajuste as descrições e diálogos se necessário. Suas alterações são salvas automaticamente.")
    
    script = st.session_state.script
    if isinstance(script, dict):
        # Título Geral
        script["titulo_hq"] = st.text_input("Título da HQ", value=script.get("titulo_hq", ""), key="hq_title_main")
        
        # Iterar sobre páginas
        for i, pg in enumerate(script.get("paginas", [])):
            with st.expander(f"Página {i+1}: {pg.get('titulo', '')}", expanded=True):
                pg["titulo"] = st.text_input(f"Título da Página {i+1}", value=pg.get("titulo", ""), key=f"pg_title_{i}")
                
                # Iterar sobre quadros
                for j, q in enumerate(pg.get("quadros", [])):
                    st.markdown(f"**Quadro {j+1}**")
                    col1, col2 = st.columns([2, 1])
                    q["descricao"] = col1.text_area(f"Descrição Visual (Q{j+1})", value=q.get("descricao", ""), key=f"q_desc_{i}_{j}")
                    q["dialogo"] = col2.text_area(f"Diálogo/Narração (Q{j+1})", value=q.get("dialogo", ""), key=f"q_dial_{i}_{j}")
                    
                    # Controles Manuais v38.0
                    q["personagens"] = st.text_input(f"Personagens (Q{j+1})", value=", ".join(q.get("personagens", [])), key=f"q_char_{i}_{j}").split(",")
                    q["personagens"] = [p.strip() for p in q["personagens"] if p.strip()]
                    st.divider()
    else:
        st.error("Erro ao gerar roteiro estruturado. Verifique o formato retornado pela IA.")
        st.code(script)

    col1, col2 = st.columns(2)
    if col1.button("⬅️ Trocar Tema"):
        st.session_state.step = "tema"
        st.rerun()
    if col2.button("🎨 Aprovar e Ir para Imagens"):
        # Salva o script editado (os campos do streamlit já atualizam o dicionário por referência)
        st.session_state.step = "imagens"
        st.rerun()

# TELA 3: IMAGENS
elif st.session_state.step == "imagens":
    st.subheader("🎨 3. Geração de Imagens por Página")
    
    if isinstance(st.session_state.script, dict) and "paginas" in st.session_state.script:
        paginas = st.session_state.script["paginas"]
    else:
        st.warning("Roteiro não estruturado em JSON. A geração automática pode falhar.")
        paginas = [] # Fallback
        
    for i, pg in enumerate(paginas):
        with st.expander(f"Página {i+1}: {pg.get('titulo', 'Sem título')}"):
            if st.button(f"▶ Gerar Imagens da Página {i+1}", key=f"gen_pg_{i}"):
                quadros = pg.get("quadros", [])
                img_engine = ImageEngine(config["img"]["provider"], config["img"]["model"])
                cm = CharacterManager()
                
                urls = []
                with st.spinner(f"Gerando arte para {len(quadros)} quadros (texto será adicionado na composição)..."):
                    for idx, q in enumerate(quadros):
                        prompt = build_consolidated_visual_prompt(
                            q["descricao"], 
                            q.get("dialogo", ""),
                            q.get("personagens", []),
                            config["style"],
                            cm.get_all()
                        )
                        
                        try:
                            url = img_engine.generate(prompt)
                            if url:
                                urls.append(url)
                                # v45.0: Smart Vision Targeting
                                with st.spinner(f"🔍 Analisando Quadro {idx+1} para identificar personagens..."):
                                    vision = VisionEngine()
                                    target_pos = vision.detect_main_character(url)
                                    if target_pos != [500, 500]:
                                        q["personagem_pos"] = target_pos
                                        # Também injetamos como face_bbox se for muito preciso, 
                                        # mas personaggio_pos é mais seguro p/ a cauda
                                st.success(f"✅ Quadro {idx+1}: Arte gerada e personagem identificado!")
                            else:
                                st.error(f"❌ Quadro {idx+1}: Falha na geração de arte.")
                                urls.append("https://placehold.co/1024x1024?text=ARTE+NAO+GERADA")
                        except Exception as e:
                            st.error(f"❌ Quadro {idx+1}: Erro: {e}")
                            urls.append("https://placehold.co/1024x1024?text=ERRO+NA+GERACAO")
                
                st.session_state.pages_images[i] = urls
                
                # COMPOSIÇÃO DA PÁGINA
                with st.spinner(f"Compondo Página {i+1} com balões e layout..."):
                    composer = ComicComposer()
                    composed_page = composer.create_page(urls, quadros)
                    # Salva em buffer para exibir
                    buf = BytesIO()
                    composed_page.save(buf, format="PNG")
                    st.session_state[f"page_composed_{i}"] = buf.getvalue()
                st.success(f"Página {i+1} concluída!")

            # v39.0: Editor de Layout Interativo
            if i in st.session_state.pages_images:
                from streamlit_drawable_canvas import st_canvas
                import numpy as np
                from PIL import Image
                import requests
                
                st.write("---")
                st.markdown(f"#### 🛠️ Editor de Layout: Página {i+1}")
                st.info("Arraste o retângulo vermelho para posicionar o balão. A página será recomposta automaticamente.")
                
                urls = st.session_state.pages_images[i]
                quadros = pg.get("quadros", [])
                
                changed = False
                cols_canvas = st.columns(len(urls))
                for idx, (url, q) in enumerate(zip(urls, quadros)):
                    with cols_canvas[idx]:
                        st.caption(f"Quadro {idx+1}")
                        
                        # Carrega background
                        if url.startswith("data:image"):
                            import base64
                            header, encoded = url.split(",", 1)
                            data = base64.b64decode(encoded)
                            bg_img = Image.open(BytesIO(data)).convert("RGB")
                        else:
                            res = requests.get(url)
                            bg_img = Image.open(BytesIO(res.content)).convert("RGB")
                        
                        # v41.0: Controles Unificados
                        from src.config.image_config import COMIC_STYLE_NAMES
                        
                        col_params = st.columns([2, 1])
                        with col_params[0]:
                            new_style = st.selectbox(
                                "Estilo", 
                                COMIC_STYLE_NAMES, 
                                index=COMIC_STYLE_NAMES.index(q.get("tipo_texto", "fala")),
                                key=f"style_{i}_{idx}"
                            )
                        with col_params[1]:
                            new_intensity = st.number_input(
                                "Escala", 
                                0.5, 2.0, 
                                float(q.get("intensity", 1.0)), 
                                0.1,
                                key=f"scale_{i}_{idx}"
                            )
                        
                        if new_style != q.get("tipo_texto") or new_intensity != q.get("intensity"):
                            q["tipo_texto"] = new_style
                            q["intensity"] = new_intensity
                            changed = True
                        
                        # Valor inicial do balão, do alvo e da origem
                        m_bbox = q.get("manual_bbox")
                        if m_bbox:
                            rl, rt, rw, rh = [v * 250 / 1000 for v in m_bbox]
                        else:
                            m_pos_fallback = q.get("manual_pos") or [400, 100]
                            rl, rt = m_pos_fallback[0] * 250 / 1000, m_pos_fallback[1] * 250 / 1000
                            rw, rh = 80, 50 
                        
                        t_pos = q.get("manual_tail_target") or q.get("personagem_pos") or [500, 500]
                        tl, tt = t_pos[0] * 250 / 1000, t_pos[1] * 250 / 1000
                        
                        o_pos = q.get("manual_tail_origin") or [rl*1000/250 + rw*500/250, rt*1000/250 + rh*500/250]
                        ol, ot = o_pos[0] * 250 / 1000, o_pos[1] * 250 / 1000

                        canvas_result = st_canvas(
                            fill_color="rgba(255, 0, 0, 0.3)",
                            stroke_width=2,
                            stroke_color="#ff0000",
                            background_image=bg_img,
                            update_streamlit=q.get("manual_bbox") is not None,
                            height=250,
                            width=250,
                            drawing_mode="transform",
                            initial_drawing={
                                "version": "4.4.0",
                                "objects": [
                                    {
                                        "type": "line",
                                        "left": ol, "top": ot, "width": tl-ol, "height": tt-ot,
                                        "x1": 0, "y1": 0, "x2": tl-ol, "y2": tt-ot,
                                        "stroke": "rgba(255, 255, 255, 0.5)", "strokeWidth": 2, "id": "tail_line", "selectable": False
                                    },
                                    {
                                        "type": "rect",
                                        "left": rl, "top": rt, "width": rw, "height": rh,
                                        "fill": "rgba(255, 0, 0, 0.3)", "stroke": "#ff0000", "id": "balloon"
                                    },
                                    {
                                        "type": "circle",
                                        "left": ol - 4, "top": ot - 4, "radius": 4,
                                        "fill": "rgba(0, 0, 255, 0.7)", "stroke": "#0000ff", "id": "origin"
                                    },
                                    {
                                        "type": "circle",
                                        "left": tl - 5, "top": tt - 5, "radius": 5,
                                        "fill": "rgba(0, 255, 0, 0.7)", "stroke": "#00ff00", "id": "target"
                                    }
                                ]
                            },
                            key=f"canvas_{i}_{idx}",
                        )
                        
                        if canvas_result.json_data and "objects" in canvas_result.json_data:
                            objects = canvas_result.json_data["objects"]
                            current_bbox = None
                            current_target = None
                            current_origin = None
                            
                            for obj in objects:
                                vis_l = obj["left"]
                                vis_t = obj["top"]
                                if obj["type"] == "rect":
                                    vis_w = obj["width"] * obj["scaleX"]
                                    vis_h = obj["height"] * obj["scaleY"]
                                    current_bbox = [
                                        int(vis_l * 1000 / 250),
                                        int(vis_t * 1000 / 250),
                                        int(vis_w * 1000 / 250),
                                        int(vis_h * 1000 / 250)
                                    ]
                                elif obj["type"] == "circle":
                                    rad = obj["radius"] * obj["scaleX"]
                                    cx = int((vis_l + rad) * 1000 / 250)
                                    cy = int((vis_t + rad) * 1000 / 250)
                                    
                                    # Diferencia origem de alvo pela cor ou pela ordem (simplificado aqui por tipo e ID se disponível)
                                    if obj.get("stroke") == "#00ff00": # Alvo (Verde)
                                        current_target = [cx, cy]
                                    else: # Origem (Azul)
                                        current_origin = [cx, cy]
                            
                            if current_bbox and q.get("manual_bbox") != current_bbox:
                                q["manual_bbox"] = current_bbox
                                q["manual_pos"] = current_bbox[:2]
                                changed = True
                            if current_target and q.get("manual_tail_target") != current_target:
                                q["manual_tail_target"] = current_target
                                changed = True
                            if current_origin and q.get("manual_tail_origin") != current_origin:
                                q["manual_tail_origin"] = current_origin
                                changed = True

                if changed:
                    # Recompor a página se houve mudança no arrasto
                    composer = ComicComposer()
                    composed_page = composer.create_page(urls, quadros)
                    buf = BytesIO()
                    composed_page.save(buf, format="PNG")
                    st.session_state[f"page_composed_{i}"] = buf.getvalue()
                    st.rerun()

            if f"page_composed_{i}" in st.session_state:
                st.image(st.session_state[f"page_composed_{i}"], caption=f"Página {i+1} Finalizada", use_container_width=True)
                if st.button(f"📥 Baixar Página {i+1}", key=f"dl_{i}"):
                    st.download_button("Clique aqui para baixar", st.session_state[f"page_composed_{i}"], f"pagina_{i+1}.png")
            
            # Atalho: Ver quadros individuais se necessário
            with st.expander("Ver quadros originais"):
                if i in st.session_state.pages_images:
                    cols = st.columns(len(st.session_state.pages_images[i]))
                    for idx, url in enumerate(st.session_state.pages_images[i]):
                        cols[idx].image(url, caption=f"Q{idx+1}")

    col1, col2 = st.columns(2)
    if col1.button("⬅️ Voltar para Roteiro"):
        st.session_state.step = "roteiro"
        st.rerun()
    if col2.button("📄 Finalizar e Exportar PDF"):
        st.session_state.step = "exportar"
        st.rerun()

# TELA 4: EXPORTAR
elif st.session_state.step == "exportar":
    st.subheader("📦 4. Exportação")
    st.write("Seu gibi está pronto para ser montado!")
    
    if st.button("⬇️ Gerar PDF"):
        with st.spinner("Compilando seu gibi em PDF..."):
            composer = ComicComposer()
            # Coleta todas as páginas em ordem
            all_pages = []
            if isinstance(st.session_state.script, dict):
                p_count = len(st.session_state.script.get("paginas", []))
                for i in range(p_count):
                    key = f"page_composed_{i}"
                    if key in st.session_state:
                        all_pages.append(st.session_state[key])
            
            if all_pages:
                pdf_buffer = composer.export_pdf(all_pages)
                if pdf_buffer:
                    st.success("✅ PDF Gerado com sucesso!")
                    st.download_button(
                        label="📥 Clique para Baixar o PDF",
                        data=pdf_buffer,
                        file_name=f"{st.session_state.script.get('titulo_hq', 'minha_hq').replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("Erro ao converter imagens para PDF.")
            else:
                st.error("Nenhuma página gerada ou encontrada. Gere as imagens primeiro!")
    
    if st.button("⬅️ Voltar"):
        st.session_state.step = "imagens"
        st.rerun()
