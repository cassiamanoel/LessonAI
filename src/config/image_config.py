"""
Centralized configuration for the Image Generation Engine — Cyberpunk v2.0.
Contains aesthetic styles, API defaults, and visual constants.
"""

# Professional Cyberpunk Marvel/DC Grade Style (v2.0)
MARVEL_FIXED_STYLE = (
    "Professional Marvel/DC grade comic book illustration, cyberpunk aesthetic. "
    "VISUAL CORE: Clean sharp ink line art, professional digital painting, "
    "neon lighting on dark backgrounds, dramatic volumetric neon glow. "
    "TECHNICAL: 8k resolution, dynamic action poses, high-contrast chiaroscuro, "
    "cyberpunk atmosphere, ink line art with digital color. "
    "High fidelity textures: metal, glass, holographic screens, circuit boards. "
    "Masterpiece quality, tech-noir cyberpunk mood."
)

# Image Quality & Engine Specs
DEFAULT_QUALITY = "hd"               # Master Spec v58.0
DEFAULT_IMAGE_MODEL = "gpt-image-1"
DEFAULT_LLM_MODEL = "gpt-5.4"
DEFAULT_LANGUAGE = "Português"

AVAILABLE_IMG_MODELS = [
    "gpt-image-1",
    "dall-e-3",
    "black-forest-labs/flux-pro",
    "google/imagen-3"
]

# (LLM list remains same)
AVAILABLE_LLM_MODELS = [
    "gpt-5.4",
    "gpt-4o",
    "gpt-4o-mini",
    "claude-3-5-sonnet-20240620",
    "gemini-1.5-pro",
    "gemini-1.5-flash"
]

SUPPORTED_QUALITIES = ["low", "medium", "high", "hd", "standard", "auto"]

# Composer Styles (Master Spec v58.0)
COMPOSER_STYLES = {
    "narrative_bg": "#F4EEDC",  # Creme Legenda
    "bubble_bg": "#FCFCFC",     # Off-white nítido
    "border_color": "#0A0C10",  # Preto profundo
    "border_width": 8,          # Borda dos quadros (Padrão)
    "balloon_border": 6,        # Borda dos balões
    "narrative_border": 6,      # Borda das legendas
    "gutter_fill": "#FFFFFF",   # Gutter branco (Master Spec)
    "safe_zone_mm": 6.77,       # ~80px em 300DPI
    "tail_width": 30,           # Calibrado para 24-38px
    "tail_curve_factor": 0.1
}

COMIC_SCALES = {
    "sussurro": 0.6,
    "fala": 1.0,
    "pensamento": 0.9,
    "ideia": 1.0,
    "duvida": 1.0,
    "admiracao": 1.0,
    "musica": 1.0,
    "choro": 1.1,
    "enfatico": 1.2,
    "raiva": 1.3,
    "grito": 1.6,
    "narracao": 1.1,
    "silencio": 0.8,
    "eletronico": 0.95
}

# Lista consolidada de estilos para UI v38.0
COMIC_STYLE_NAMES = sorted(list(COMIC_SCALES.keys()))

# Placeholder Assets (v33.0 Definitivo: Base64 para evitar falhas de rede)
PLACEHOLDER_URLS = {
    "NOT_GENERATED": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
    "ERROR": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEgAF/posBDwAAAABJRU5ErkJggg=="
}
