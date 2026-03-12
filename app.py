import streamlit as st
import json
from io import BytesIO
from src.ui.sidebar import render_sidebar
from src.agents.editorial import ComicScriptGenerator
from src.pipeline.image_engine import ImageEngine
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
                    col1, col2, col3 = st.columns([2, 1, 0.5])
                    q["descricao"] = col1.text_area(f"Descrição Visual (Q{j+1})", value=q.get("descricao", ""), key=f"q_desc_{i}_{j}")
                    q["dialogo"] = col2.text_area(f"Diálogo/Narração (Q{j+1})", value=q.get("dialogo", ""), key=f"q_dial_{i}_{j}")
                    q["tipo_texto"] = col3.selectbox("Tipo", ["fala", "narracao", "sussurro", "grito"], index=0 if q.get("tipo_texto") == "fala" else (1 if q.get("tipo_texto") == "narracao" else (2 if q.get("tipo_texto") == "sussurro" else 3)), key=f"q_type_{i}_{j}")
                    q["personagens"] = col1.text_input(f"Personagens (Q{j+1})", value=", ".join(q.get("personagens", [])), key=f"q_char_{i}_{j}").split(",")
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
                                st.success(f"✅ Quadro {idx+1}: Arte gerada com sucesso!")
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
