import os
from pathlib import Path

def load_prompt_reference(filename: str) -> str:
    """Carrega um arquivo de prompt da pasta references."""
    # Assume que o script roda de src/prompts/ ou da raiz
    base_dir = Path(__file__).parent.parent.parent
    ref_dir = base_dir / "references"
    file_path = ref_dir / filename
    
    if not file_path.exists():
        # Fallback para caminho relativo se falhar
        file_path = Path("references") / filename
        
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo de referência não encontrado: {file_path}")
        
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def get_all_roles() -> dict:
    """Carrega todos os papéis editoriais padrão."""
    return {
        "master":       load_prompt_reference("MASTER-PROMPT.txt"),
        "story_engine": load_prompt_reference("Story-Engine-Prompt.txt"),
        "panel_dir":    load_prompt_reference("Prompt-de-DIREÇÃO-CINEMATOGRÁFICA-DOS-QUADROS.txt"),
        "artist":       load_prompt_reference("Prompt-de-ARTE.txt"),
        "art_finisher": load_prompt_reference("Prompt-de-ARTE-FINAL.txt"),
        "colorist":     load_prompt_reference("Prompt-de-CORES.txt"),
        "continuity":   load_prompt_reference("Prompt-de-PERSONAGENS-CONSISTENTES.txt"),
        "letterer":     load_prompt_reference("Formatação-Marvel-DC.txt"),
    }
