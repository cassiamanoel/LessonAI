from PIL import Image, ImageDraw, ImageFont
import os
import sys

# Adiciona o diretório atual ao path para importar o pipeline
sys.path.append(os.getcwd())

from src.pipeline.balloon_presets import BalloonPresets

# LISTA OBRIGATÓRIA E MAPEAMENTO
BALLOONS_CONFIG = [
    {"label": "Balão de fala", "style": "fala", "mods": []},
    {"label": "Balão de pensamento", "style": "pensamento", "mods": []},
    {"label": "Balão de grito", "style": "grito", "mods": []},
    {"label": "Balão de sussurro", "style": "sussurro", "mods": []},
    {"label": "Balão eletrônico", "style": "eletronico", "mods": []},
    {"label": "Balão de rádio", "style": "radio", "mods": []},
    {"label": "Narração", "style": "narração", "mods": []},
    {"label": "Legenda", "style": "legenda", "mods": []},
    {"label": "Flashback", "style": "flashback", "mods": []},
    {"label": "Sonho", "style": "sonho", "mods": []},
    {"label": "Raiva", "style": "raiva", "mods": []},
    {"label": "Choro", "style": "choro", "mods": []},
    {"label": "Dúvida", "style": "duvida", "mods": []},
    {"label": "Exclamação", "style": "exclamação", "mods": []},
    {"label": "Canto", "style": "canto", "mods": []},
    {"label": "Múltipla fala", "style": "fala", "mods": ["múltipla_fala"]},
    {"label": "Balão interrompido", "style": "fala", "mods": ["interrompido"]},
    {"label": "Balão com cauda dupla", "style": "fala", "mods": ["cauda_dupla"]},
    {"label": "Balão sem cauda", "style": "fala", "mods": ["sem_cauda"]},
    {"label": "Balão serrilhado", "style": "serrilhado", "mods": []},
    {"label": "Balão nuvem", "style": "nuvem", "mods": []},
    {"label": "Balão orgânico", "style": "organico", "mods": []},
    {"label": "Balão retangular arredondado", "style": "retangular_arredondado", "mods": []},
    {"label": "Burst assimétrico", "style": "burst_assimetrico", "mods": []},
]

def validate_config():
    """Valida ortografia e contagem conforme requisitos."""
    required_labels = [
        "Balão de fala", "Balão de pensamento", "Balão de grito", "Balão de sussurro",
        "Balão eletrônico", "Balão de rádio", "Narração", "Legenda", "Flashback",
        "Sonho", "Raiva", "Choro", "Dúvida", "Exclamação", "Canto", "Múltipla fala",
        "Balão interrompido", "Balão com cauda dupla", "Balão sem cauda",
        "Balão serrilhado", "Balão nuvem", "Balão orgânico",
        "Balão retangular arredondado", "Burst assimétrico"
    ]
    labels_present = [b["label"] for b in BALLOONS_CONFIG]
    
    assert len(BALLOONS_CONFIG) == 24, f"Erro: Esperado 24 balões, encontrado {len(BALLOONS_CONFIG)}"
    for label in required_labels:
        assert label in labels_present, f"Erro: Rótulo '{label}' faltando!"
    print("Validação de rótulos: OK")

def generate_sheet():
    validate_config()
    
    # Configurações de Canvas (A4 @ 300DPI aprox 2480x3508)
    # Por praticidade para visualização digital rápida, usamos 1200x1800
    canvas_w, canvas_h = 1400, 2000
    sheet = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(sheet)
    
    # Título
    try:
        # Tenta carregar uma fonte sans-serif limpa (comum em Windows/Linux/Mac)
        font_path = "arial.ttf" # Windows default
        title_font = ImageFont.truetype(font_path, 60)
        label_font = ImageFont.truetype(font_path, 28)
    except:
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()

    title_text = "TIPOS DE BALÕES DE HQ"
    # draw.textbbox is newer, checking for compatibility
    try:
        tw = draw.textlength(title_text, font=title_font)
    except:
        tw = 400 # fallback
        
    draw.text((canvas_w//2 - tw//2, 80), title_text, fill="black", font=title_font)
    
    # Grid: 4 colunas x 6 linhas
    cols, rows = 4, 6
    cell_w, cell_h = canvas_w // cols, (canvas_h - 200) // rows
    
    for i, config in enumerate(BALLOONS_CONFIG):
        col = i % cols
        row = i // cols
        
        # Coordenadas da célula
        inner_cx = col * cell_w + cell_w // 2
        inner_cy = row * cell_h + 300 + cell_h // 2 - 50
        
        # Gera o balão
        # Tamanho do balão ajustado para a célula
        bw, bh = 220, 140
        # Target fixo para baixo para as caudas
        target = (60, 100) 
        
        balloon_img = BalloonPresets.get_balloon_image(
            style=config["style"],
            w=bw, h=bh,
            target_rel=target,
            modifiers=config["mods"]
        )
        
        # Centraliza o balão na célula
        paste_x = inner_cx - balloon_img.width // 2
        paste_y = inner_cy - balloon_img.height // 2
        sheet.paste(balloon_img, (paste_x, paste_y), balloon_img)
        
        # Rótulo abaixo do balão
        label = config["label"]
        try:
             lw = draw.textlength(label, font=label_font)
        except:
             lw = 100
        draw.text((inner_cx - lw//2, inner_cy + 130), label, fill="black", font=label_font)

    # Linha divisória fina para o clima técnico (opcional, prompt diz organizar em grade)
    # Aqui vamos manter a grade organizada sem linhas cruzadas pesadas para manter "limpo"
    
    output_path = "HQ_Balloon_Reference_Sheet.png"
    sheet.save(output_path)
    print(f"Prancha gerada com sucesso: {output_path}")

if __name__ == "__main__":
    generate_sheet()
