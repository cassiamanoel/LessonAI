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
    num_pages = st.sidebar.slider("Quantidade de Páginas", 1, 10, 5)
    
    llm_provider = st.sidebar.selectbox("Provedor LLM", ["OpenAI", "Gemini", "Claude", "OpenRouter"])
    llm_model = st.sidebar.text_input("Modelo LLM", value="gpt-4o")
    
    img_provider = st.sidebar.selectbox("Provedor Imagem", ["OpenAI", "Replicate", "Stability", "Gemini"])
    img_model = st.sidebar.text_input("Modelo Imagem", value="dall-e-3")
    
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
