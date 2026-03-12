from src.prompts.loader import get_all_roles

ROLES = get_all_roles()

def build_consolidated_visual_prompt(
    panel_description: str,
    dialogue: str,
    character_names: list,
    selected_style: dict,
    characters_config: list,
    is_anime: bool = False,
    language: str = "Português"
) -> str:
    """
    Consolida todos os papéis editoriais em um único prompt visual.
    """
    # 1. Âncora de Estilo Global (do PRD/Referências)
    style_anchor = selected_style.get("art_style", "High-quality professional comic book art style.")
    if len(style_anchor) > 500:
        style_anchor = style_anchor[:500] + "..."
    
    # 2. Instruções de Arte e Acabamento (Otimizadas)
    art_instructions = ROLES["artist"][:600]
    finish_instructions = ROLES["art_finisher"][:400]
    color_instructions = ROLES["colorist"][:400]
    
    # 3. DNA dos Personagens
    character_dna = ""
    for char_name in character_names:
        # Busca config do personagem nos dados do usuário
        char_info = next((c for c in characters_config if c["name"].lower() == char_name.lower()), None)
        if char_info:
            dna = f"\nCHARACTER DNA: {char_info['name']} — {char_info['description_visual'][:300]}. " \
                  f"Features: {char_info['traits_physical'][:200]}. Colors: {char_info['accent_colors'][:100]}. " \
                  f"Consistency anchor: same face, same outfit, same proportions."
            character_dna += dna
            if len(character_dna) > 1000: break # Limite de sanidade

    # 4. Paleta e Restrições
    palette = ", ".join(selected_style.get("palette", []))[:200]
    restrictions = ", ".join(selected_style.get("restrictions", []))[:200]

    # Master Engine Production Prompt (Fixo e Curto)
    master_spec = "You are a professional comic book ILLUSTRATION engine following Marvel/DC editorial standards. " \
                  "Generate ONLY the visual artwork for each panel. " \
                  "DO NOT render ANY text, letters, words, speech bubbles, caption boxes, or typography in the image. " \
                  "The lettering will be added separately by the professional lettering department. " \
                  "Focus on: dramatic composition, expressive characters, cinematic lighting, and rich backgrounds."

    # Cinematic Art Direction (Fixo e Curto)
    cinematic_dir = "Cinematic composition, dramatic framing, chiaroscuro lighting, strong contrast. Marvel/DC graphic novel aesthetic."

    # Prompt Final Consolidado
    prompt = f"ENGINE ROLE: {master_spec}\n" \
             f"VISUAL STYLE: {style_anchor}\n" \
             f"ART DIRECTION: {cinematic_dir}\n" \
             f"TECHNICAL SPECS: {art_instructions}\n" \
             f"FINISHING: {finish_instructions}\n" \
             f"COLORS: {palette}. {color_instructions}\n" \
             f"CHARACTERS DNA: {character_dna}\n" \
             f"SCENE DESCRIPTION: {panel_description}\n" \
             f"NEGATIVE PROMPT: {restrictions}. NO TEXT, NO LETTERS, NO WORDS, NO SPEECH BUBBLES, NO CAPTIONS in the image."
             
    # Safety Truncate a 3900 caracteres (OpenAI limite é 4000)
    if len(prompt) > 3900:
        prompt = prompt[:3900] + "..."
        
    return prompt
