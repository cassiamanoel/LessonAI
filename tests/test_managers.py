import pytest
import os
import json
from src.config.managers import CharacterManager

def test_character_manager_save_load(tmp_path):
    # Usar um arquivo temporário para não sujar o original
    cm = CharacterManager()
    
    # Adicionar personagem de teste
    test_char = {"nome": "Teste", "dna": "Cabelo azul, olhos vermelhos", "imagem_ref": ""}
    cm.add(test_char)
    
    all_chars = cm.get_all()
    assert any(c["nome"] == "Teste" for c in all_chars)
    
    # Remover personagem de teste
    cm.delete("Teste")
    assert not any(c["nome"] == "Teste" for c in cm.get_all())

def test_character_manager_get_all():
    cm = CharacterManager()
    chars = cm.get_all()
    assert isinstance(chars, list)
