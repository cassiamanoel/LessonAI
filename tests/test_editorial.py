import pytest
from src.agents.editorial import ComicScriptGenerator

def test_clean_prefixes():
    generator = ComicScriptGenerator()
    
    # Teste 1: Prefixo clássico
    script_data = {
        "paginas": [
            {
                "quadros": [
                    {"dialogo": "NARRADOR: Olá mundo"},
                    {"dialogo": "PERSONAGEM: Oi!"},
                    {"dialogo": "Agente Prompt: Teste de limpeza"},
                ]
            }
        ]
    }
    
    cleaned = generator._clean_prefixes(script_data)
    assert cleaned["paginas"][0]["quadros"][0]["dialogo"] == "OLÁ MUNDO"
    assert cleaned["paginas"][0]["quadros"][1]["dialogo"] == "OI!"
    assert cleaned["paginas"][0]["quadros"][2]["dialogo"] == "TESTE DE LIMPEZA"

def test_clean_prefixes_no_prefix():
    generator = ComicScriptGenerator()
    script_data = {
        "paginas": [
            {
                "quadros": [
                    {"dialogo": "Apenas um texto livre de prefixo"}
                ]
            }
        ]
    }
    cleaned = generator._clean_prefixes(script_data)
    assert cleaned["paginas"][0]["quadros"][0]["dialogo"] == "APENAS UM TEXTO LIVRE DE PREFIXO"

def test_clean_prefixes_empty():
    generator = ComicScriptGenerator()
    assert generator._clean_prefixes(None) is None
    assert generator._clean_prefixes({}) == {}
