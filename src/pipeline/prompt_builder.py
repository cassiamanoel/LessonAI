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
    
    # v2.0: Master Spec DNA — 8 Cyberpunk Tech Team Characters
    MASTER_SPEC_DNA = {
        "kira": "Female, 30-35, short asymmetric black hair with neon cyan #00F0FF streaks. Black tactical jacket with luminous blue circuit lines sewn into seams. Left arm with light mechanical exoskeleton (not robotic). AR glasses with holographic HUD. Reinforced combat boots. Heroic agile silhouette.",
        "arquiteta": "Female, 30-35, short asymmetric black hair with neon cyan #00F0FF streaks. Black tactical jacket with luminous blue circuit lines sewn into seams. Left arm with light mechanical exoskeleton (not robotic). AR glasses with holographic HUD. Reinforced combat boots. Heroic agile silhouette.",
        "sofia": "Female, 32-38, wavy brown hair in informal bun. Dark blue futuristic blazer with holographic lapels projecting metrics. Holographic tablet always in hand. Purple glowing earrings. Confident posture, focused expression.",
        "estrategista": "Female, 32-38, wavy brown hair in informal bun. Dark blue futuristic blazer with holographic lapels projecting metrics. Holographic tablet always in hand. Purple glowing earrings. Confident posture, focused expression.",
        "yuki": "Female, 28-33, long straight platinum-white hair with tips that glow blue when processing data. White tech lab coat with floating data panels on wrists. Thin gloves with holographic sensors. Discreet neural implant on right temple. Serene intellectual expression.",
        "analista": "Female, 28-33, long straight platinum-white hair with tips that glow blue when processing data. White tech lab coat with floating data panels on wrists. Thin gloves with holographic sensors. Discreet neural implant on right temple. Serene intellectual expression.",
        "marcus": "Male, 35-42, short beard, shaved sides with short top hair. Robust strong build. Heavy black tactical vest with embedded monitoring panels (green LEDs = ok, red = alert). Reinforced gloves. Utility belt with holographic tools. Subtle chin scar. Imposing presence.",
        "guardiao": "Male, 35-42, short beard, shaved sides with short top hair. Robust strong build. Heavy black tactical vest with embedded monitoring panels (green LEDs = ok, red = alert). Reinforced gloves. Utility belt with holographic tools. Subtle chin scar. Imposing presence.",
        "luna": "Female, 26-30, colorful hair (purple to neon pink gradient). Futuristic headphones with holographic projection. White cropped jacket with luminous pink edges. Holographic stylus tucked behind ear. Subtle geometric forearm tattoo. Curious gentle expression.",
        "interprete": "Female, 26-30, colorful hair (purple to neon pink gradient). Futuristic headphones with holographic projection. White cropped jacket with luminous pink edges. Holographic stylus tucked behind ear. Subtle geometric forearm tattoo. Curious gentle expression.",
        "axiom": "Semi-translucent digital humanoid entity. Body made of code lines and luminous neural networks. Mouthless face with two bright geometric cyan eyes. Aura of floating data particles. Unstable form that occasionally glitches. NOT a physical robot — holographic manifestation.",
        "nao_humano": "Semi-translucent digital humanoid entity. Body made of code lines and luminous neural networks. Mouthless face with two bright geometric cyan eyes. Aura of floating data particles. Unstable form that occasionally glitches. NOT a physical robot — holographic manifestation.",
        "victor": "Male, 50-58, slicked-back gray hair, angular severe face. Impeccable black futuristic suit with luminous golden lines on lapels. Holographic wristwatch projecting performance graphs. Dominant standing posture. Calculated authority expression.",
        "pressionador": "Male, 50-58, slicked-back gray hair, angular severe face. Impeccable black futuristic suit with luminous golden lines on lapels. Holographic wristwatch projecting performance graphs. Dominant standing posture. Calculated authority expression.",
        "bia": "Young female, 22-26, natural curly brown hair, open questioning expression. Casual futuristic clothing: hoodie with luminous patches, tech backpack with retractable antenna. Holographic phone projecting product interface. More 'everyday' look than others — connects reader to real world.",
        "verdade": "Young female, 22-26, natural curly brown hair, open questioning expression. Casual futuristic clothing: hoodie with luminous patches, tech backpack with retractable antenna. Holographic phone projecting product interface. More 'everyday' look than others — connects reader to real world.",
    }

    # 3. DNA dos Personagens
    character_dna = ""
    for char_name in character_names:
        # Prioridade 1: Master Spec DNA (v58.0)
        lower_name = char_name.lower().replace(" ", "_")
        if lower_name in MASTER_SPEC_DNA:
            dna = f"\nCHARACTER DNA: {char_name.upper()} — {MASTER_SPEC_DNA[lower_name]}. " \
                  f"Consistency anchor: exact costume and face across all panels."
            character_dna += dna
        else:
            # Prioridade 2: Config do Personagem (Custom)
            char_info = next((c for c in characters_config if c["name"].lower() == char_name.lower()), None)
            if char_info:
                dna = f"\nCHARACTER DNA: {char_info['name']} — {char_info['description_visual'][:300]}. " \
                      f"Features: {char_info['traits_physical'][:200]}. Colors: {char_info['accent_colors'][:100]}. " \
                      f"Consistency anchor: same face, same outfit, same proportions."
                character_dna += dna
        
        if len(character_dna) > 1500: break 

    # 4. Paleta e Restrições (Master Spec priority)
    palette = ", ".join(selected_style.get("palette", []))[:200]
    if not palette:
        palette = "Neon Cyan #00F0FF, Electric Blue #59D7FF, Neon Pink #FF2D95, Glitch Magenta #FF00FF, Deep Black #0A0C10, Night Blue #102235, Terminal Green #39FF14, Rich Gold #FFB800"
    
    restrictions = ", ".join(selected_style.get("restrictions", []))[:200]

    # Master Engine Production Prompt (v2.0 Cyberpunk Tech Team)
    master_spec = "You are a world-class comic book ILLUSTRATOR. Style: professional Marvel/DC grade graphic novel, modern cyberpunk. " \
                  "ENVIRONMENT: High-tech corporate towers, neon-lit server rooms, holographic war rooms, futuristic open-plan offices with floating screens. " \
                  "ELEMENTS: Holographic dashboards, neural network visualizations, streaming data flows, glowing server racks, AR interfaces, code projections."

    # Cinematic Art Direction (Cyberpunk Marvel Grade)
    cinematic_dir = "Cinematic 8k resolution, professional Marvel/DC comic art, dynamic action poses, volumetric neon lighting, dramatic chiaroscuro, cyberpunk atmosphere, ink line art with digital color."

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
