import streamlit as st
from src.config.managers import ThemeManager, CharacterManager, StyleManager

def render_sidebar():
    st.sidebar.title("🎨 LessonAI Comic")
    
    # 1. Seleção de Estilo
    sm = StyleManager()
    styles = sm.get_all()
    style_names = [s["name"] for s in styles]
    selected_style_name = st.sidebar.selectbox("Estilo da HQ", style_names)
    selected_style = next(s for s in styles if s["name"] == selected_style_name)
    
    st.sidebar.divider()
    
    # 2. Configurações de IA
    st.sidebar.subheader("Configurações Globais")
    language = st.sidebar.selectbox("Idioma do roteiro", ["Português", "English", "Español", "Français", "Deutsch", "Italiano"], index=0)
    num_pages = st.sidebar.slider("Quantidade de Páginas", 1, 5, 5)
    
    from src.config.image_config import AVAILABLE_IMG_MODELS, AVAILABLE_LLM_MODELS, DEFAULT_IMAGE_MODEL, DEFAULT_LLM_MODEL
    
    llm_provider = st.sidebar.selectbox("Provedor LLM", ["OpenAI", "Gemini", "Claude", "OpenRouter"])
    llm_model = st.sidebar.selectbox(
        "Modelo LLM", 
        AVAILABLE_LLM_MODELS, 
        index=AVAILABLE_LLM_MODELS.index(DEFAULT_LLM_MODEL)
    )
    
    img_provider = st.sidebar.selectbox("Provedor Imagem", ["OpenAI", "Replicate", "Stability", "Gemini"])
    img_model = st.sidebar.selectbox(
        "Modelo Imagem", 
        AVAILABLE_IMG_MODELS, 
        index=AVAILABLE_IMG_MODELS.index(DEFAULT_IMAGE_MODEL)
    )
    
    # v40.0: Mock Mode Toggle
    st.sidebar.markdown("---")
    st.sidebar.subheader("💰 Economia de Custos")
    st.session_state.image_mock = st.sidebar.checkbox(
        "Modo Mock (Sem gasto de IA)", 
        value=st.session_state.get("image_mock", True), 
        help="Quando ativo, usa uma imagem local fixa em vez de chamar a API paga."
    )
    
    st.sidebar.divider()
    
    # 3. Gerenciamento (CRUDs)
    with st.sidebar.expander("👤 Gerenciar Personagens"):
        cm = CharacterManager()
        chars = cm.get_all()
        for char in chars:
            st.text(f"• {char['name']}")
        if st.button("+ Novo Personagem"):
            st.session_state.show_char_editor = True

    with st.sidebar.expander("📚 Gerenciar Temas"):
        tm = ThemeManager()
        themes = tm.get_all()
        selected_theme = st.selectbox("Selecione um tema", themes)
        if st.button("+ Adicionar Tema"):
            st.session_state.show_theme_editor = True
            
    return {
        "style": selected_style,
        "language": language,
        "num_pages": num_pages,
        "llm": {"provider": llm_provider, "model": llm_model},
        "img": {"provider": img_provider, "model": img_model},
        "theme": selected_theme
    }
