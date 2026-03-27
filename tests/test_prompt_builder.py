import pytest
from src.pipeline.prompt_builder import build_consolidated_visual_prompt

def test_prompt_builder_basic():
    description = "Um robô em Marte"
    dialogue = "Olá Terráqueos!"
    personagens = ["Robô X"]
    style = {"art_style": "Cyberpunk"}
    character_dna = {}
    
    prompt = build_consolidated_visual_prompt(description, dialogue, personagens, style, character_dna)
    
    # Verificar se as diretrizes Marvel/DC de proibição de texto estão presentes
    assert "NO TEXT" in prompt
    assert "NO TEXT, NO LETTERS" in prompt
    assert "Cyberpunk" in prompt
    assert "Um robô em Marte" in prompt

def test_prompt_builder_no_dialogue():
    style = {"art_style": "Noir"}
    prompt = build_consolidated_visual_prompt("Fundo espacial", None, [], style, {})
    assert "Fundo espacial" in prompt
    assert "Noir" in prompt
    assert "NO TEXT" in prompt
