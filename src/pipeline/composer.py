from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
import requests
from io import BytesIO
import textwrap
import math
import os
import re

class ComicComposer:
    def __init__(self, dpi: int = 300):
        # Página padrão HQ v21.0
        self.dpi = dpi
        self.width = int(174 / 25.4 * dpi)   # ~2055 px
        self.height = int(266 / 25.4 * dpi)  # ~3142 px

        # Estrutura
        self.gutter = int(1.2 / 25.4 * dpi)   # calha preta
        self.safe_zone = int(10 / 25.4 * dpi) # margem segura
        self.padding = int(7 / 25.4 * dpi)

        # Estilo
        self.narrative_bg = "white"
        self.bubble_bg = "white"
        self.border_color = "black"
        self.border_width = 1
        self.gutter_fill = "black"

        # Fontes profissionalizadas com fallback sênior
        project_font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "fonts")
        win_font_dir = "C:\\Windows\\Fonts\\"

        candidates_dialog = [
            os.path.join(project_font_dir, "CCWildWords-Regular.ttf"),
            os.path.join(project_font_dir, "WildWords.ttf"),
            os.path.join(project_font_dir, "AnimeAce2_reg.ttf"),
            os.path.join(project_font_dir, "Bangers-Regular.ttf"),
            os.path.join(win_font_dir, "arial.ttf"),
        ]
        candidates_dialog_bold = [
            os.path.join(project_font_dir, "CCWildWords-Bold.ttf"),
            os.path.join(project_font_dir, "WildWordsBold.ttf"),
            os.path.join(project_font_dir, "AnimeAce2_bld.ttf"),
            os.path.join(project_font_dir, "Bangers-Regular.ttf"),
            os.path.join(win_font_dir, "arialbd.ttf"),
        ]
        candidates_narr = [
            os.path.join(project_font_dir, "CCMeanwhile-Regular.ttf"),
            os.path.join(project_font_dir, "AnimeAce2_reg.ttf"),
            os.path.join(project_font_dir, "PermanentMarker-Regular.ttf"),
            os.path.join(win_font_dir, "arial.ttf"),
        ]
        candidates_computer = [
            os.path.join(project_font_dir, "Eurostile-Bold.ttf"),
            os.path.join(win_font_dir, "arialbd.ttf"),
        ]

        pt_to_px = dpi / 72.0

        # Tamanhos equilibrados para legibilidade HD
        self.font_ball = self._load_font(candidates_dialog, int(9.0 * pt_to_px))
        self.font_ball_bold = self._load_font(candidates_dialog_bold, int(9.0 * pt_to_px))
        self.font_narrative = self._load_font(candidates_narr, int(8.8 * pt_to_px))
        self.font_whisper = self._load_font(candidates_dialog, int(8.0 * pt_to_px))
        self.font_shout = self._load_font(candidates_dialog_bold, int(11.5 * pt_to_px))
        self.font_computer = self._load_font(candidates_computer, int(9.2 * pt_to_px))

    def _load_font(self, candidates, size):
        for path in candidates:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def create_page(self, images_urls: list, panels_data: list):
        page = Image.new("RGB", (self.width, self.height), self.gutter_fill)
        num_panels = len(images_urls)
        if num_panels == 0:
            return page

        # Layout otimizado para HQ Americana
        tiers = self._choose_layout(num_panels)
        tier_heights = self._calculate_tier_heights(tiers)

        y_offset = 0
        current_idx = 0

        for t_idx, panels_in_tier in enumerate(tiers):
            th = tier_heights[t_idx]
            available_w = self.width - ((panels_in_tier - 1) * self.gutter)
            pw = available_w // panels_in_tier

            for p_idx in range(panels_in_tier):
                if current_idx >= num_panels:
                    break

                url = images_urls[current_idx]
                data = panels_data[current_idx] if current_idx < len(panels_data) else {}

                x_offset = p_idx * (pw + self.gutter)
                panel_rect = (x_offset, y_offset, pw, th)

                self._render_panel(page, url, panel_rect)

                if data.get("dialogo"):
                    tipo = data.get("tipo_texto", "fala").lower().strip()
                    text = str(data.get("dialogo", "")).strip()

                    if tipo == "narracao":
                        self._draw_narrative(page, text, panel_rect)
                    else:
                        anchor = self._resolve_anchor(panel_rect, data)
                        self._draw_bubble(page, text, panel_rect, anchor, style=tipo)

                current_idx += 1

            y_offset += th + self.gutter

        return page

    def _choose_layout(self, num_panels):
        if num_panels <= 2: return [1] * num_panels
        if num_panels == 3: return [1, 2]
        if num_panels == 4: return [1, 2, 1]
        if num_panels == 5: return [2, 1, 2]
        if num_panels == 6: return [2, 2, 2]
        return [2, 2, 2, max(1, num_panels - 6)]

    def _calculate_tier_heights(self, tiers):
        available_h = self.height - ((len(tiers) - 1) * self.gutter)
        total_units = sum([1.5 if t == 1 else 1 for t in tiers])
        uh = available_h / total_units
        return [int(uh * 1.5 if t == 1 else uh) for t in tiers]

    def _render_panel(self, page, url, rect):
        x, y, w, h = rect
        try:
            if url.startswith("http"):
                resp = requests.get(url, timeout=20)
                resp.raise_for_status()
                img = Image.open(BytesIO(resp.content)).convert("RGB")
            else:
                img = Image.open(url).convert("RGB")

            # Melhores filtros para nitidez de HQ
            img_fit = ImageOps.fit(img, (w, h), Image.Resampling.BICUBIC)
            img_fit = img_fit.filter(ImageFilter.SHARPEN)
            img_fit = ImageEnhance.Contrast(img_fit).enhance(1.12)
            img_fit = ImageEnhance.Sharpness(img_fit).enhance(1.10)

            page.paste(img_fit, (x, y))
            draw = ImageDraw.Draw(page)
            draw.rectangle([x, y, x + w, y + h], outline=self.border_color, width=self.border_width)

        except Exception as e:
            print(f"Erro Arte: {e}")

    def _resolve_anchor(self, panel_rect, data):
        x, y, w, h = panel_rect
        # Fallback padrão: meio/baixo
        px, py = x + w // 2, y + int(h * 0.70)

        pos = data.get("personagem_pos")
        if isinstance(pos, (list, tuple)) and len(pos) == 2:
            try:
                return (int(pos[0]), int(pos[1]))
            except: pass

        for key in ("face_bbox", "character_bbox"):
            bbox = data.get(key)
            if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                try:
                    x1, y1, x2, y2 = map(int, bbox)
                    return ((x1 + x2) // 2, y2)
                except: pass
        return (px, py)

    def _draw_narrative(self, image, text, panel_rect):
        draw = ImageDraw.Draw(image)
        x, y, w, h = panel_rect

        max_text_width = int(w * 0.60)
        lines = self._wrap_text_pixels(draw, text, self.font_narrative, max_text_width)

        lh = self._line_height(self.font_narrative, extra=8)
        tw = max([draw.textbbox((0, 0), l, font=self.font_narrative)[2] for l in lines] or [0])
        th = lh * len(lines)

        pad_x, pad_y = int(self.padding * 0.9), int(self.padding * 0.55)
        rect_w, rect_h = tw + pad_x * 2, th + pad_y * 2

        rx, ry = x + self.safe_zone // 3, y + self.safe_zone // 3

        # Clamp Caption
        rect = [rx, ry, rx + rect_w, ry + rect_h]
        draw.rectangle(rect, fill=self.narrative_bg, outline=self.border_color, width=1)

        cy = ry + pad_y
        for l in lines:
            draw.text((rx + pad_x, cy), l, font=self.font_narrative, fill="black")
            cy += lh

    def _draw_bubble(self, image, text, panel_rect, anchor, style="fala"):
        draw = ImageDraw.Draw(image)
        x, y, w, h = panel_rect
        ax, ay = anchor

        font = self.font_ball
        if style == "grito": font = self.font_shout
        elif style == "sussurro": font = self.font_whisper
        elif style == "eletronico": font = self.font_computer

        # Quebra por pixels robusta
        max_text_width = max(int(w * 0.20), int(w * 0.46))
        lines = self._wrap_text_pixels(draw, text, font, max_text_width)

        lh = self._line_height(font, extra=8 if style != "grito" else 10)
        tw = max([draw.textbbox((0, 0), l, font=font)[2] for l in lines] or [0])
        th = lh * len(lines)

        pad_x, pad_y = self.padding + 34, self.padding - 8
        bw, bh = tw + pad_x * 2, th + pad_y * 2

        # Clamp Bubble
        x1 = max(x + 16, min(ax - bw // 2, x + w - bw - 16))
        y1 = max(y + 16, min(ay - bh - 58, y + h - bh - 30))
        x2, y2 = x1 + bw, y1 + bh
        
        bcx = (x1 + x2) // 2

        if style == "pensamento":
            self._draw_cloud(draw, (x1, y1, x2, y2))
            self._draw_thought_tail(draw, (bcx, y2), (ax, ay), panel_rect)
        elif style == "grito":
            self._draw_burst(draw, (x1, y1, x2, y2))
            self._draw_tail(draw, (bcx, y2), (ax, ay), panel_rect, width=26)
        elif style == "eletronico":
            self._draw_electronic(draw, (x1, y1, x2, y2))
            self._draw_tail(draw, (bcx, y2), (ax, ay), panel_rect, width=15)
        else:
            # Fala clássica
            draw.ellipse([x1, y1, x2, y2], fill=self.bubble_bg, outline=self.border_color, width=1)
            if style == "sussurro": self._apply_dashed_border(draw, [x1, y1, x2, y2])
            self._draw_tail(draw, (bcx, y2 - 2), (ax, ay), panel_rect, width=22)

        cy = y1 + pad_y + 4
        for l in lines:
            self._draw_styled_line(draw, l, bcx, cy, font)
            cy += lh

    def _wrap_text_pixels(self, draw, text, font, max_width):
        words = str(text).split()
        if not words: return [""]
        lines, line = [], ""
        for word in words:
            test = f"{line} {word}".strip()
            w = draw.textbbox((0, 0), test, font=font)[2]
            if w <= max_width: line = test
            else:
                if line: lines.append(line); line = word
                else:
                    broken = self._break_word(draw, word, font, max_width)
                    lines.extend(broken[:-1]); line = broken[-1]
        if line: lines.append(line)
        return lines

    def _break_word(self, draw, word, font, max_width):
        parts, cur = [], ""
        for ch in word:
            if draw.textbbox((0, 0), cur + ch, font=font)[2] <= max_width: cur += ch
            else:
                if cur: parts.append(cur)
                cur = ch
        if cur: parts.append(cur)
        return parts or [word]

    def _line_height(self, font, extra=8):
        bbox = font.getbbox("Ay")
        return (bbox[3] - bbox[1]) + extra

    def _draw_styled_line(self, draw, line, cx, y, base_font):
        parts = re.split(r'(\*\*.*?\*\*)', line)
        total_w = 0
        runs = []
        for p in parts:
            if p.startswith("**") and p.endswith("**"):
                content, font = p[2:-2], self.font_ball_bold
            else:
                content, font = p, base_font
            if not content: continue
            w = draw.textbbox((0, 0), content, font=font)[2]
            runs.append((content, font, w))
            total_w += w
        cur_x = cx - total_w // 2
        for c, f, w in runs:
            draw.text((cur_x, y), c, font=f, fill="black")
            cur_x += w

    def _apply_dashed_border(self, draw, rect):
        x1, y1, x2, y2 = rect
        for i in range(0, 360, 20):
            a1, a2 = math.radians(i), math.radians(i + 12)
            cx, cy = (x1+x2)/2, (y1+y2)/2
            w, h = x2-x1, y2-y1
            p1 = (cx + (w/2)*math.cos(a1), cy + (h/2)*math.sin(a1))
            p2 = (cx + (w/2)*math.cos(a2), cy + (h/2)*math.sin(a2))
            draw.line([p1, p2], fill=self.border_color, width=1)

    def _draw_cloud(self, draw, rect):
        x1, y1, x2, y2 = rect
        w, h = x2-x1, y2-y1
        for i in range(12):
            a = (2*math.pi/12)*i
            bx = x1+w/2+(w/2/2.1)*math.cos(a)
            by = y1+h/2+(h/2/2.2)*math.sin(a)
            draw.ellipse([bx-24, by-24, bx+24, by+24], fill=self.bubble_bg, outline=self.border_color, width=1)
        draw.ellipse([x1+10, y1+10, x2-10, y2-10], fill=self.bubble_bg, outline=self.bubble_bg)

    def _draw_burst(self, draw, rect):
        x1, y1, x2, y2 = rect
        cx, cy = (x1+x2)/2, (y1+y2)/2
        rx, ry = (x2-x1)/2, (y2-y1)/2
        pts = []
        spikes = 22
        for i in range(spikes*2):
            a = (math.pi/spikes)*i
            f = 1.18 if i%2==0 else 0.84
            pts.append((cx + rx*f*math.cos(a), cy + ry*f*math.sin(a)))
        draw.polygon(pts, fill=self.bubble_bg, outline=self.border_color, width=2)

    def _draw_electronic(self, draw, rect):
        draw.rectangle(rect, fill=self.bubble_bg, outline=self.border_color, width=2)

    def _draw_tail(self, draw, base_point, anchor, panel_rect, width=22):
        bx, by = base_point
        ax, ay = anchor
        x, y, w, h = panel_rect
        ax = max(x+8, min(ax, x+w-8))
        ay = max(y+8, min(ay, y+h-8))
        draw.polygon([(bx-width, by), (bx+6, by-2), (ax, ay)], fill=self.bubble_bg, outline=self.border_color)

    def _draw_thought_tail(self, draw, base_point, anchor, panel_rect):
        bx, by = base_point
        ax, ay = anchor
        points = [((bx+ax)//2, (by+ay)//2), ((bx*2+ax)//3, (by*2+ay)//3), ((bx*3+ax)//4, (by*3+ay)//4)]
        radii = [16, 11, 7]
        for (px, py), r in zip(points, radii):
            draw.ellipse([px-r, py-r, px+r, py+r], fill=self.bubble_bg, outline=self.border_color, width=1)

    def export_pdf(self, images: list) -> BytesIO:
        pil_imgs = [Image.open(BytesIO(i)).convert("RGB") if isinstance(i, bytes) else i.convert("RGB") for i in images]
        if not pil_imgs: return BytesIO()
        buf = BytesIO()
        pil_imgs[0].save(buf, format="PDF", save_all=True, append_images=pil_imgs[1:])
        buf.seek(0)
        return buf