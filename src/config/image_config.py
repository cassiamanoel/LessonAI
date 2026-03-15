"""
Centralized configuration for the Image Generation Engine v28.0 - Quantum Upgrade v36.0.
Contains aesthetic styles, API defaults, and visual constants.
"""

# Professional Marvel Comic Style v36.0 (Generic Base)
MARVEL_FIXED_STYLE = (
    "Professional modern Marvel comic book illustration. "
    "VISUAL CORE: Clean sharp ink line art, vibrant cinematic colors, "
    "dynamic composition, high-end digital rendering. "
    "LIGHTING: Dramatic chiaroscuro light and shadow, atmospheric depth. "
    "TECHNICAL: 8k resolution, sharp focus, marvel cinematic aesthetic, "
    "masterpiece illustration, intense detail."
)

# Image Quality & Engine Specs
DEFAULT_QUALITY = "high"
DEFAULT_IMAGE_MODEL = "dall-e-3"  # Padrão de estabilidade v36.0
DEFAULT_LLM_MODEL = "gpt-4o"
DEFAULT_LANGUAGE = "Português"
SUPPORTED_QUALITIES = ["low", "medium", "high", "hd", "standard", "auto"]
EMERGENCY_FALLBACK_MODEL = "dall-e-3"

# Composer Styles (Premium Standard v36.0)
COMPOSER_STYLES = {
    "narrative_bg": "#fffbd0",  # Creme clássico
    "bubble_bg": "white",
    "border_color": "black",
    "border_width": 2,
    "gutter_fill": "black",
    "safe_zone_mm": 10,
    "tail_width": 25,
    "tail_curve_factor": 0.15
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
