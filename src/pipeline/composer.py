from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
from io import BytesIO
import textwrap
import math
import os

class ComicComposer:
    def __init__(self, dpi: int = 300):
        # Medidas Padrão Marvel/DC: 6.625” x 10.25” (~1988 x 3075 px)
        self.dpi = dpi
        self.width = int(6.625 * dpi)
        self.height = int(10.25 * dpi)
        
        self.narrative_bg = "#FFF9E3"
        self.bubble_bg = "white"
        self.text_color = "black"
        self.gutter = 8 # Espaço entre painéis (Marvel Style)
        
        # Fontes Marvel/DC Grade (Bangers = balões, PermanentMarker = narração)
        project_font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "fonts")
        win_font_dir = "C:\\\\Windows\\\\Fonts\\\\"
        
        # Fontes primárias (estilo Marvel/DC profissional)
        font_balloon_path = os.path.join(project_font_dir, "Bangers-Regular.ttf")
        font_narrative_path = os.path.join(project_font_dir, "PermanentMarker-Regular.ttf")
        
        # Fallback para fontes do sistema se as profissionais não existirem
        if not os.path.exists(font_balloon_path):
            font_balloon_path = os.path.join(win_font_dir, "comic.ttf")
            if not os.path.exists(font_balloon_path):
                font_balloon_path = os.path.join(win_font_dir, "arial.ttf")
        
        if not os.path.exists(font_narrative_path):
            font_narrative_path = os.path.join(win_font_dir, "comicbd.ttf")
            if not os.path.exists(font_narrative_path):
                font_narrative_path = os.path.join(win_font_dir, "arialbd.ttf")

        pt_to_px = dpi / 72.0
        try:
            self.font_balloon = ImageFont.truetype(font_balloon_path, int(10 * pt_to_px))
            self.font_narrative = ImageFont.truetype(font_narrative_path, int(9 * pt_to_px))
            self.font_whisper = ImageFont.truetype(font_balloon_path, int(7.5 * pt_to_px))
            self.font_shout = ImageFont.truetype(font_balloon_path, int(14 * pt_to_px))
        except Exception as e:
            print(f"[COMPOSER] Fallback para fontes padrão: {e}")
            self.font_balloon = ImageFont.load_default()
            self.font_narrative = ImageFont.load_default()
            self.font_whisper = ImageFont.load_default()
            self.font_shout = ImageFont.load_default()

    def create_page(self, images_urls: list, panels_data: list):
        """
        Página Marvel Grade: Tiers dinâmicos e Preservação Extrema.
        """
        page = Image.new("RGB", (self.width, self.height), "white")
        num_panels = len(images_urls)
        if num_panels == 0: return page

        # Definição Narrative de Tiers (v5.0)
        # T1: Establishing (1), T2: Action (2), T3: Detail (2), T4: Punchline (1)
        if num_panels == 1: tiers = [1]
        elif num_panels == 2: tiers = [1, 1]
        elif num_panels == 3: tiers = [1, 2]
        elif num_panels == 4: tiers = [1, 2, 1]
        elif num_panels == 5: tiers = [1, 2, 2]
        elif num_panels == 6: tiers = [1, 2, 2, 1]
        else: tiers = [2] * (num_panels // 2) + ([1] if num_panels % 2 else [])

        current_idx = 0
        total_tiers = len(tiers)
        tier_heights = self._calculate_tier_heights(tiers)
        
        y_offset = 0
        draw = ImageDraw.Draw(page)

        for t_idx, panels_in_tier in enumerate(tiers):
            th = tier_heights[t_idx]
            panel_w = (self.width - (panels_in_tier + 1) * self.gutter) // panels_in_tier
            
            for p_idx in range(panels_in_tier):
                if current_idx >= num_panels: break
                
                url = images_urls[current_idx]
                data = panels_data[current_idx]
                x_offset = self.gutter + p_idx * (panel_w + self.gutter)
                
                # REGRA CRÍTICA: ImageOps.contain() logic
                # Vamos renderizar o painel dentro do box (x_offset, y_offset, panel_w, th)
                self._render_panel_marvel_style(page, url, (x_offset, y_offset, panel_w, th))
                
                # Lettering
                if data.get("dialogo"):
                    text = data["dialogo"].upper()
                    tipo = data.get("tipo_texto", "fala").lower()
                    
                    if tipo == "narracao":
                        self._draw_narrative_box(page, text, x_offset + 30, y_offset + 30)
                    else:
                        # Mapeamento Marvel DC Grade v9.0
                        style = "normal"
                        if tipo in ["grito", "shout"]: style = "grito"
                        elif tipo in ["sussurro", "whisper"]: style = "sussurro"
                        elif tipo in ["pensamento", "thought"]: style = "pensamento"
                        elif tipo in ["onomatopeia", "sfx"]: style = "onomatopeia"
                        
                        # Balões posicionados com inteligência narrativa (não apenas centro)
                        self._draw_speech_bubble(page, text, x_offset + panel_w//2, y_offset + 60, style=style)
                
                current_idx += 1
            
            y_offset += th + self.gutter
            
        return page

    def export_pdf(self, images_list: list) -> BytesIO:
        """
        Gera um PDF a partir de uma lista de imagens (bytes do Streamlit ou objetos PIL).
        """
        pil_images = []
        for img_data in images_list:
            if isinstance(img_data, bytes):
                pil_images.append(Image.open(BytesIO(img_data)).convert("RGB"))
            elif isinstance(img_data, Image.Image):
                pil_images.append(img_data.convert("RGB"))
        
        if not pil_images:
            return BytesIO()
            
        pdf_buffer = BytesIO()
        # Salva o PDF: primeira imagem é a base, as outras são anexadas
        pil_images[0].save(
            pdf_buffer, 
            format="PDF", 
            save_all=True, 
            append_images=pil_images[1:]
        )
        pdf_buffer.seek(0)
        return pdf_buffer

    def _calculate_tier_heights(self, tiers):
        """Distribui a altura total entre os tiers de forma ponderada."""
        total_units = sum([1.5 if t == 1 else 1 for t in tiers])
        unit_h = (self.height - (len(tiers) + 1) * self.gutter) / total_units
        return [int(unit_h * 1.5 if t == 1 else unit_h) for t in tiers]

    def _render_panel_marvel_style(self, page, url, rect):
        """Implementação estrita de contain (No-Crop)."""
        x, y, w_box, h_box = rect
        try:
            if url.startswith("http"):
                resp = requests.get(url, timeout=15)
                img = Image.open(BytesIO(resp.content))
            else:
                img = Image.open(url)
            
            # REGRA CRÍTICA: ImageOps.contain() logic (Aceite Checklist Item 1)
            img_resized = ImageOps.contain(img, (w_box, h_box), Image.Resampling.LANCZOS)
            new_w, new_h = img_resized.size
            
            # Centralizar no box
            off_x = (w_box - new_w) // 2
            off_y = (h_box - new_h) // 2
            
            page.paste(img_resized, (x + off_x, y + off_y))
            
            # Borda preta fina e elegante
            draw = ImageDraw.Draw(page)
            draw.rectangle([x + off_x, y + off_y, x + off_x + new_w, y + off_y + new_h], outline="black", width=3)
            
        except Exception as e:
            print(f"Erro Marvel Engine: {e}")

    def _draw_narrative_box(self, image, text, x, y):
        draw = ImageDraw.Draw(image)
        font = self.font_narrative
        lines = textwrap.wrap(text, width=35)
        
        line_h = int((draw.textbbox((0, 0), "Ay", font=font)[3] - draw.textbbox((0, 0), "Ay", font=font)[1]) * 1.25)
        tw = max([draw.textbbox((0, 0), l, font=font)[2] - draw.textbbox((0, 0), l, font=font)[0] for l in lines])
        th = line_h * len(lines)
        
        pad = 25
        rect = [x, y, x + tw + pad*2, y + th + pad*2]
        
        draw.rectangle(rect, fill=self.narrative_bg, outline="black", width=3)
        
        curr_y = y + pad
        for line in lines:
            draw.text((x + pad, curr_y), line, font=font, fill="black")
            curr_y += line_h

    def _draw_speech_bubble(self, image, text, cx, ty, style="normal"):
        draw = ImageDraw.Draw(image)
        font = self.font_balloon
        if style == "grito": font = self.font_shout
        elif style == "sussurro": font = self.font_whisper
        elif style == "onomatopeia": font = self.font_shout
        
        # Onomatopeia: Apenas texto estilizado
        if style == "onomatopeia":
            self._draw_onomatopoeia(image, text, cx, ty)
            return

        lines = textwrap.wrap(text, width=22)
        if not lines: return
        
        line_h = int((draw.textbbox((0, 0), "Ay", font=font)[3] - draw.textbbox((0, 0), "Ay", font=font)[1]) * 1.3)
        tw = max([draw.textbbox((0, 0), l, font=font)[2] - draw.textbbox((0, 0), l, font=font)[0] for l in lines])
        th = line_h * len(lines)
        
        margin = 35
        bw, bh = tw + margin*2, th + margin*2
        bx1, by1, bx2, by2 = cx - bw//2, ty, cx + bw//2, ty + bh
        
        if style == "pensamento":
            self._draw_cloud_bubble(image, (bx1, by1, bx2, by2))
        elif style == "grito":
            self._draw_explosive_bubble(image, (bx1, by1, bx2, by2))
        elif style == "sussurro":
            # Borda pontilhada simulada
            draw.ellipse([bx1, by1, bx2, by2], fill=self.bubble_bg, outline="black", width=2)
            # Cauda simples
            draw.polygon([(cx, by2 - 5), (cx - 20, by2 + 40), (cx + 5, by2 - 5)], fill=self.bubble_bg, outline="black")
        else:
            # Normal: Oval com cauda
            draw.polygon([(cx, by2 - 5), (cx - 30, by2 + 60), (cx + 10, by2 - 5)], fill=self.bubble_bg, outline="black")
            draw.ellipse([bx1, by1, bx2, by2], fill=self.bubble_bg, outline="black", width=3)

        # Desenhar texto
        curr_y = by1 + margin
        for line in lines:
            lw = draw.textbbox((0, 0), line, font=font)[2] - draw.textbbox((0, 0), line, font=font)[0]
            draw.text((cx - lw//2, curr_y), line, font=font, fill="black")
            curr_y += line_h

    def _draw_cloud_bubble(self, image, rect):
        """Desenha um balão de pensamento estilo nuvem."""
        draw = ImageDraw.Draw(image)
        x1, y1, x2, y2 = rect
        w, h = x2 - x1, y2 - y1
        
        # Bolhas principais (nuvem)
        draw.ellipse([x1, y1, x2, y2], fill=self.bubble_bg, outline="black", width=3)
        # Adiciona bolhas extras nas bordas para efeito de nuvem
        num_bumps = 8
        for i in range(num_bumps):
            angle = (2 * math.pi / num_bumps) * i
            bx = x1 + w/2 + (w/2) * math.cos(angle)
            by = y1 + h/2 + (h/2) * math.sin(angle)
            br = 30
            draw.ellipse([bx-br, by-br, bx+br, by+br], fill=self.bubble_bg, outline="black", width=2)
            
        # Cauda de bolhas (Tail)
        draw.ellipse([x1 + w//2 - 20, y2 + 10, x1 + w//2, y2 + 30], fill=self.bubble_bg, outline="black", width=2)
        draw.ellipse([x1 + w//2 - 40, y2 + 40, x1 + w//2 - 25, y2 + 55], fill=self.bubble_bg, outline="black", width=2)

    def _draw_explosive_bubble(self, image, rect):
        """Desenha um balão de grito com bordas em zigue-zague."""
        draw = ImageDraw.Draw(image)
        x1, y1, x2, y2 = rect
        w, h = x2 - x1, y2 - y1
        cx, cy = x1 + w/2, y1 + h/2
        
        points = []
        num_points = 16
        for i in range(num_points * 2):
            angle = (math.pi / num_points) * i
            dist = (w/2 + 20) if i % 2 == 0 else (w/2 - 10)
            px = cx + dist * math.cos(angle)
            py = cy + dist * math.sin(angle) * (h/w) # Ajusta proporção
            points.append((px, py))
            
        draw.polygon(points, fill=self.bubble_bg, outline="black")

    def _draw_onomatopoeia(self, image, text, cx, ty):
        """Desenha onomatopeias grandes e estilizadas fora de balões."""
        draw = ImageDraw.Draw(image)
        font = self.font_shout
        
        # Efeito de contorno (Sombra/Outline)
        lw, lh = draw.textbbox((0, 0), text, font=font)[2], draw.textbbox((0, 0), text, font=font)[3]
        for off in [(-2,-2), (2,-2), (-2,2), (2,2)]:
            draw.text((cx - lw//2 + off[0], ty + off[1]), text, font=font, fill="yellow")
        
        draw.text((cx - lw//2, ty), text, font=font, fill="red")
