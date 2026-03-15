from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
import requests
from io import BytesIO
import base64
import textwrap
import math
import os
import re
from src.config.image_config import COMPOSER_STYLES, COMIC_SCALES, PLACEHOLDER_URLS

class ComicComposer:
    def __init__(self, dpi: int = 300):
        # Professional Standard v36.0: Quantum Anatomy
        self.dpi = dpi
        self.width = int(174 / 25.4 * dpi)   # ~2055 px
        self.height = int(266 / 25.4 * dpi)  # ~3142 px

        # Estrutura Narrativa
        self.gutter = int(1.2 / 25.4 * dpi)
        
        # Estilo Quantum v36.0
        self.narrative_bg = COMPOSER_STYLES["narrative_bg"]
        self.bubble_bg = COMPOSER_STYLES["bubble_bg"]
        self.border_color = COMPOSER_STYLES["border_color"]
        self.border_width = COMPOSER_STYLES["border_width"]
        self.gutter_fill = COMPOSER_STYLES["gutter_fill"]
        self.safe_zone = int(COMPOSER_STYLES["safe_zone_mm"] / 25.4 * dpi)
        self.tail_width = COMPOSER_STYLES.get("tail_width", 25)

        # Escalas Estritas
        self.scales = COMIC_SCALES

        # Tipografia Profissional
        project_font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "fonts")
        win_font_dir = "C:\\Windows\\Fonts\\"
        pt_to_px = dpi / 72.0
        self.base_size = int(8.0 * pt_to_px)

        candidates_dialog = [
            os.path.join(project_font_dir, "CCWildWords-Regular.ttf"),
            os.path.join(project_font_dir, "AnimeAce2_reg.ttf"),
            os.path.join(win_font_dir, "arial.ttf"),
        ]
        candidates_bold = [
            os.path.join(project_font_dir, "CCWildWords-Bold.ttf"),
            os.path.join(project_font_dir, "AnimeAce2_bld.ttf"),
            os.path.join(win_font_dir, "arialbd.ttf"),
        ]

        self.font_ball = self._load_font(candidates_dialog, self.base_size)
        self.font_ball_bold = self._load_font(candidates_bold, self.base_size)
        self.font_narrative = self._load_font(candidates_dialog, int(self.base_size * 1.1))
        
        # Collision Map v37.0
        self.forbidden_regions = []
        self.forbidden_hard = []
        self.forbidden_soft = []
        self.occupied_regions = []

    def _load_font(self, candidates, size):
        for path in candidates:
            if os.path.exists(path):
                try: return ImageFont.truetype(path, size)
                except: pass
        return ImageFont.load_default()

    def create_page(self, images_urls: list, panels_data: list):
        page = Image.new("RGB", (self.width, self.height), self.gutter_fill)
        num_panels = len(images_urls)
        if num_panels == 0: return page

        tiers = self._choose_layout(num_panels)
        tier_heights = self._calculate_tier_heights(tiers)
        y_offset, current_idx = 0, 0

        for t_idx, p_in_tier in enumerate(tiers):
            th = tier_heights[t_idx]
            pw = (self.width - ((p_in_tier - 1) * self.gutter)) // p_in_tier
            for p_idx in range(p_in_tier):
                if current_idx >= num_panels: break
                rect = (p_idx * (pw + self.gutter), y_offset, pw, th)
                data = panels_data[current_idx] if current_idx < len(panels_data) else {}
                
                self._render_panel(page, images_urls[current_idx], rect)
                
                # Absolute Art Shield v37.0: Reset e Mapeamento Multinível
                self.forbidden_hard = []  # Faces (Zero tolerância)
                self.forbidden_soft = []  # Corpos (Tolerância parcial)
                self._map_art_guard_v37(rect, data)
                self.occupied_regions = []

                if data.get("dialogo"):
                    self._place_balloon_absolute_shield(page, data, rect)
                
                current_idx += 1
            y_offset += th + self.gutter
        return page

    def _choose_layout(self, num_panels):
        if num_panels <= 3: return [1] * num_panels
        if num_panels == 4: return [1, 2, 1]
        if num_panels == 5: return [1, 2, 2]
        if num_panels == 6: return [1, 2, 2, 1]
        return [2] * (num_panels // 2) + ([1] if num_panels % 2 else [])

    def _calculate_tier_heights(self, tiers):
        ah = self.height - ((len(tiers)-1)*self.gutter)
        total_weight = sum([1.4 if t == 1 else 1.0 for t in tiers])
        unit_h = ah / total_weight
        return [int(unit_h * (1.4 if t == 1 else 1.0)) for t in tiers]

    def _render_panel(self, page, url, rect):
        x, y, w, h = rect
        if "placehold.co" in url or "via.placeholder.com" in url:
            url = PLACEHOLDER_URLS["ERROR"] if "ERRO" in url.upper() else PLACEHOLDER_URLS["NOT_GENERATED"]

        try:
            if url.startswith("data:image"):
                header, encoded = url.split(",", 1)
                data = base64.b64decode(encoded)
                img = Image.open(BytesIO(data)).convert("RGB")
            elif url.startswith("http"):
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                resp = requests.get(url, timeout=25, headers=headers)
                img = Image.open(BytesIO(resp.content)).convert("RGB")
            else: 
                try: img = Image.open(url).convert("RGB")
                except:
                    img = Image.new("RGB", (w, h), (180, 180, 180))
                    ImageDraw.Draw(img).text((10, h//2), "ARTE NAO ENCONTRADA", fill="black")
            
            img_fit = ImageOps.fit(img, (w, h), Image.Resampling.BICUBIC)
            img_fit = img_fit.filter(ImageFilter.SHARPEN)
            img_fit = ImageEnhance.Contrast(img_fit).enhance(1.1)
            page.paste(img_fit, (x, y))
            ImageDraw.Draw(page).rectangle([x, y, x+w, y+h], outline=self.border_color, width=self.border_width)

            if url.startswith("data:image"):
                msg = "FALHA NA API - USANDO PLACEHOLDER" if "ERROR" in url else "AGUARDANDO GERACAO"
                ImageDraw.Draw(page).text((x + 10, y + h - 30), msg, fill="yellow")
        except Exception as e: 
            print(f"Erro Arte: {e}")

    def _map_art_guard_v37(self, rect, data):
        # Converte normalizado (0-1000) para pixels absolutos do painel
        def n2p(norm_rect):
            nx1, ny1, nx2, ny2 = norm_rect
            px1 = rect[0] + (nx1 * rect[2] / 1000)
            py1 = rect[1] + (ny1 * rect[3] / 1000)
            px2 = rect[0] + (nx2 * rect[2] / 1000)
            py2 = rect[1] + (ny2 * rect[3] / 1000)
            return [px1, py1, px2, py2]

        # 1. HARD GUARD: Rostos
        fb = data.get("face_bbox")
        if fb and isinstance(fb, list) and len(fb) == 4:
            self.forbidden_hard.append(n2p(fb))

        # 2. SOFT GUARD: Corpos
        cb = data.get("character_bbox")
        if cb and isinstance(cb, list) and len(cb) == 4:
            self.forbidden_soft.append(n2p(cb))

    def _place_balloon_absolute_shield(self, image, data, panel_rect):
        text = str(data.get("dialogo", "")).strip()
        style = str(data.get("tipo_texto", "fala")).lower()
        if style == "narracao":
            self._draw_narrative_quantum(image, text, panel_rect, data)
            return

        intensity = float(data.get("intensity", 1.0))
        base_scale = float(self.scales.get(style, 1.0)) * intensity
        
        # Sincronia de Âncora v37.0
        anchor = self._resolve_anchor_v37(panel_rect, data)
        
        # Ciclo de Auto-Shrink (3 tentativas para blindagem absoluta)
        best_overall_pos = None
        final_bw, final_bh, final_lines, final_font = None, None, None, None
        
        # v43.0: Fonte da Verdade Absoluta (manual_bbox)
        m_bbox = data.get("manual_bbox") # [x, y, w, h] normalized 0-1000
        manual_p = data.get("manual_pos")
        
        if m_bbox and isinstance(m_bbox, list) and len(m_bbox) == 4:
            # Converte 0-1000 para pixels reais no painel
            px1 = panel_rect[0] + (m_bbox[0] * panel_rect[2] / 1000)
            py1 = panel_rect[1] + (m_bbox[1] * panel_rect[3] / 1000)
            bw = m_bbox[2] * panel_rect[2] / 1000
            bh = m_bbox[3] * panel_rect[3] / 1000
            
            # Para o texto, usamos o bw forçado e calculamos as linhas
            draw_tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
            fs = int(self.base_size * base_scale)
            font = self._load_font_at_size(style, fs)
            # Padding dinâmico baseado no tamanho do balão
            pad_w = bw * 0.18
            lines = self._wrap_text_pixels(draw_tmp, text, font, bw - pad_w)
            
            best_overall_pos = (px1, py1)
            final_bw, final_bh, final_lines, final_font = bw, bh, lines, font
            
        elif manual_p and isinstance(manual_p, list) and len(manual_p) == 2:
            scale = base_scale
            bw, bh, lines, font = self._calculate_balloon_metrics(text, style, scale, panel_rect)
            # Converte 0-1000 para pixels absolutos
            px1 = panel_rect[0] + (manual_p[0] * panel_rect[2] / 1000)
            py1 = panel_rect[1] + (manual_p[1] * panel_rect[3] / 1000)
            best_overall_pos = (px1, py1)
            final_bw, final_bh, final_lines, final_font = bw, bh, lines, font
        else:
            for attempt in range(3):
                scale = base_scale * (0.9 ** attempt)
                bw, bh, lines, font = self._calculate_balloon_metrics(text, style, scale, panel_rect)
                
                candidates = self._get_candidate_positions(panel_rect, bw, bh)
                best_score, best_pos = -float('inf'), None

                for pos in candidates:
                    score = self._score_position_v37(pos, bw, bh, anchor, panel_rect)
                    if score > best_score:
                        best_score, best_pos = score, pos

                # Se a melhor posição não colide com rosto, aceitamos
                if best_pos and best_score > -50000.0:
                    best_overall_pos = best_pos
                    final_bw, final_bh, final_lines, final_font = bw, bh, lines, font
                    break
                
                # Se é a última tentativa, pegamos o melhor do que sobrou (fallback de emergência)
                if attempt == 2:
                    best_overall_pos = best_pos
                    final_bw, final_bh, final_lines, final_font = bw, bh, lines, font

        if not best_overall_pos: return

        px, py = best_overall_pos
        self._draw_balloon_v37_geometric(image, text, (px, py, px + final_bw, py + final_bh), 
                                        final_lines, final_font, anchor, style, panel_rect)
        self.occupied_regions.append([px, py, px + final_bw, py + final_bh])

    def _calculate_balloon_metrics(self, text, style, scale, panel_rect):
        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        fs = int(self.base_size * scale)
        font = self._load_font_at_size(style, fs)
        
        # v42.0: Controle Dinâmico de Wrapping para Aspect Ratio
        # Reduzimos max_w para forçar quebras em textos curtos, evitando "panquecas"
        max_w = int(panel_rect[2] * 0.45 * scale)
        lines = self._wrap_text_pixels(draw, text, font, max_w)
        
        lh = self._line_height(font, extra=int(fs * 0.45))
        tw = max([draw.textbbox((0,0), l, font=font)[2] for l in lines] or [0])
        th = lh * len(lines)
        
        # Padding Profissional
        pw, ph = int(tw * 0.22) + 25, int(th * 0.35) + 20
        bw, bh = tw + pw * 2, th + ph * 2
        
        # v42.0: Regra Anti-Panqueca (Min Aspect Ratio 1.2:1 para elipses)
        if style not in ("narracao", "eletronico"):
            if bw > bh * 2.5: # Muito achatado
                bh = int(bw / 2.2)
        
        return bw, bh, lines, font

    def _get_candidate_positions(self, rect, bw, bh):
        x, y, w, h = rect
        candidates = []
        for ix in range(10):
            for iy in range(10):
                cx = x + (ix * (w - bw) // 9)
                cy = y + (iy * (h - bh) // 9)
                candidates.append((cx, cy))
        return candidates

    def _rect_overlap(self, r1, r2):
        return not (r1[2] < r2[0] or r1[0] > r2[2] or r1[3] < r2[1] or r1[1] > r2[3])

    def _score_position_v37(self, pos, bw, bh, anchor, rect):
        px, py = pos
        bubble_rect = [px, py, px + bw, py + bh]
        score = 0.0
        
        # 1. HARD SHIELD: Rostos (Penalidade fatal)
        for fh in self.forbidden_hard:
            if self._rect_overlap(bubble_rect, fh): 
                return -1000000.0 
        
        # 2. SOFT SHIELD: Corpos (Penalidade moderada)
        for fs in self.forbidden_soft:
            if self._rect_overlap(bubble_rect, fs):
                score -= 5000.0
        
        # 3. Evitar sobreposição de outros balões
        for or_ in self.occupied_regions:
            if self._rect_overlap(bubble_rect, or_): score -= 15000.0
            
        # 4. Atratividade (Distância e Posição)
        dist = math.sqrt((px + bw/2 - anchor[0])**2 + (py + bh/2 - anchor[1])**2)
        score -= dist * 0.4
        score -= py * 0.15 # Prefere topo
        
        # 5. Penalidade por sair do painel (Borda de segurança)
        x, y, w, h = rect
        if px < x + 10 or px + bw > x + w - 10: score -= 20000.0
        if py < y + 10 or py + bh > y + h - 10: score -= 20000.0
        
        return score

    def _resolve_anchor_v37(self, panel_rect, data):
        x, y, w, h = panel_rect
        # 1. Prioridade: personnage_pos (0-1000)
        pos = data.get("personagem_pos")
        if pos and isinstance(pos, list) and len(pos) == 2:
            return (int(x + pos[0] * w / 1000), int(y + pos[1] * h / 1000))
            
        # 2. Fallback: centro do rosto ou corpo
        for fh in self.forbidden_hard:
            return ((fh[0] + fh[2]) // 2, (fh[1] + fh[3]) // 2)
        for fs in self.forbidden_soft:
            return ((fs[0] + fs[2]) // 2, fs[1] + 20) # Topo do corpo
            
        return (x + w // 2, y + int(h * 0.75))

    def _draw_balloon_v37_geometric(self, image, text, rect, lines, font, anchor, style, panel_rect):
        draw = ImageDraw.Draw(image)
        x1, y1, x2, y2 = rect
        bcx, bcy = (x1 + x2) // 2, (y1 + y2) // 2
        
        # v42.0: Dropshadow (Profundidade Visual)
        shadow_offset = 6
        shadow_rect = [x1+shadow_offset, y1+shadow_offset, x2+shadow_offset, y2+shadow_offset]
        
        # Geometric Fidelity v42.0
        if style in ("pensamento", "ideia", "duvida", "admiracao", "silencio", "musica", "raiva"):
            tx, ty = self._choose_tail_exit(rect, anchor, pad=0.85)
            # Sombra da nuvem/cloud
            self._draw_cloud(draw, shadow_rect, dark=False, is_shadow=True)
            self._draw_cloud(draw, rect, dark=(style=="raiva"))
            
            if style not in ("musica", "raiva"): self._draw_thought_tail(draw, (tx, ty), anchor)
            if style == "raiva": self._draw_tail_quantum(draw, (tx, ty), anchor, width=35)
        elif style in ("grito", "enfatico", "choro"):
            tx, ty = self._choose_tail_exit(rect, anchor, pad=1.1)
            spikes = 26 if style == "grito" else 18
            # Sombra do burst
            self._draw_burst(draw, shadow_rect, spikes=spikes, is_shadow=True)
            self._draw_burst(draw, rect, spikes=spikes, dripping=(style=="choro"))
            self._draw_tail_quantum(draw, (tx, ty), anchor, width=36 if style == "grito" else 28)
        elif style == "eletronico":
            tx, ty = self._choose_tail_exit(rect, anchor, pad=1.0)
            # Sombra do jagged
            self._draw_jagged_rect(draw, shadow_rect, is_shadow=True)
            self._draw_jagged_rect(draw, rect)
            self._draw_tail_quantum(draw, (tx, ty), anchor, width=24)
        else:
            tx, ty = self._choose_tail_exit(rect, anchor, pad=0.98)
            # v42.0: Sombra e Forma Dinâmica (Elipse vs Rounded Rect)
            is_long = (x2 - x1) > (y2 - y1) * 1.8
            radius = 35
            
            if is_long:
                draw.rounded_rectangle(shadow_rect, radius=radius, fill="#222222")
                draw.rounded_rectangle(rect, radius=radius, fill=self.bubble_bg, outline=self.border_color, width=self.border_width)
            else:
                draw.ellipse(shadow_rect, fill="#222222")
                draw.ellipse(rect, fill=self.bubble_bg, outline=self.border_color, width=self.border_width)
                
            if style == "sussurro": self._apply_dashed_border(draw, rect)
            
            # v42.0: Quantum Tail Enhanced
            self._draw_tail_quantum(draw, (tx, ty), anchor, width=self.tail_width + 8)

        # Render Text (Centralizado verticalmente)
        lh = self._line_height(font, extra=int(font.size * 0.4))
        th = lh * len(lines)
        cy = y1 + (y2 - y1 - th) // 2
        for l in lines:
            self._draw_styled_line(draw, l, bcx, cy, font); cy += lh

    def _choose_tail_exit(self, rect, anchor, pad=1.0):
        """Calcula o ponto 360º com padding adaptativo para cada forma."""
        x1, y1, x2, y2 = rect
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        ax, ay = anchor
        dx, dy = ax - cx, ay - cy
        angle = math.atan2(dy, dx)
        rx, ry = (x2 - x1) / 2 * pad, (y2 - y1) / 2 * pad
        tx = cx + rx * math.cos(angle)
        ty = cy + ry * math.sin(angle)
        return int(tx), int(ty)

    def _draw_tail_quantum(self, draw, base_point, anchor, width=22):
        bx, by = base_point
        ax, ay = anchor
        dx, dy = ax - bx, ay - by
        dist = math.sqrt(dx**2 + dy**2)
        if dist < 5: return
        nx, ny = -dy / dist, dx / dist
        
        # v42.0: Tapered Tail (Mais larga na base, afinando)
        p1 = (bx + nx * width/2, by + ny * width/2)
        p2 = (bx - nx * width/2, by - ny * width/2)
        
        # Ponto médio para curvatura
        mx, my = (bx + ax) / 2, (by + ay) / 2
        # Offset perpendicular
        ox, oy = nx * 15, ny * 15
        ctrl = (mx + ox, my + oy)
        
        # Desenha com leve curva via polígono denso ou triângulo fiel
        draw.polygon([p1, p2, (ax, ay)], fill=self.bubble_bg, outline=self.border_color)

    def _draw_cloud(self, draw, rect, dark=False, is_shadow=False):
        x1, y1, x2, y2 = rect
        w, h = x2-x1, y2-y1
        fill = "#222222" if is_shadow else ("#e0e0e0" if dark else self.bubble_bg)
        outline = None if is_shadow else self.border_color
        
        # Nuvem v42: Círculos variados
        for i in range(18):
            a = (2.0*math.pi/18.0)*i
            size = 35 + (i % 3) * 5
            bx, by = x1+w/2+(w/2/2.0)*math.cos(a), y1+h/2+(h/2/2.1)*math.sin(a)
            draw.ellipse([int(bx)-size, int(by)-size, int(bx)+size, int(by)+size], fill=fill, outline=outline, width=1)
        draw.ellipse([x1+15, y1+15, x2-15, y2-15], fill=fill)

    def _draw_burst(self, draw, rect, spikes=24, dripping=False, is_shadow=False):
        x1, y1, x2, y2 = rect
        cx, cy, rx, ry = (x1+x2)/2.0, (y1+y2)/2.0, (x2-x1)/2.0, (y2-y1)/2.0
        fill = "#222222" if is_shadow else self.bubble_bg
        outline = None if is_shadow else self.border_color
        
        pts = []
        for i in range(spikes * 2):
            a = (math.pi/spikes) * i
            f = 1.28 if i % 2 == 0 else 0.75
            pts.append((cx + rx * f * math.cos(a), cy + ry * f * math.sin(a)))
        draw.polygon(pts, fill=fill, outline=outline, width=2)
        
        if dripping and not is_shadow:
            # Efeito de choro (pingos na base do balão)
            for i in range(6):
                dx = x1 + (x2-x1) * (0.15 + 0.14*i)
                dy = y2 - 8
                draw.ellipse([dx, dy, dx+14, dy+28], fill=self.bubble_bg, outline=self.border_color)

    def _draw_jagged_rect(self, draw, rect, is_shadow=False):
        x1, y1, x2, y2 = rect
        fill = "#222222" if is_shadow else self.bubble_bg
        outline = None if is_shadow else self.border_color
        pts = []
        steps = 14
        # Top
        for i in range(steps):
            pts.append((x1 + (x2-x1)*i/steps, y1 + (12 if i%2==0 else -6)))
        # Right
        for i in range(steps):
            pts.append((x2 + (12 if i%2==0 else -6), y1 + (y2-y1)*i/steps))
        # Bottom
        for i in range(steps):
            pts.append((x2 - (x2-x1)*i/steps, y2 + (12 if i%2==0 else -6)))
        # Left
        for i in range(steps):
            pts.append((x1 + (-12 if i%2==0 else 6), y2 - (y2-y1)*i/steps))
        draw.polygon(pts, fill=fill, outline=outline, width=2)

    def _draw_thought_tail(self, draw, base_point, anchor):
        bx, by, ax, ay = base_point[0], base_point[1], anchor[0], anchor[1]
        # Bolhas mais nítidas v37
        pts = [((bx*4+ax)//5, (by*4+ay)//5), ((bx*2+ax)//3, (by*2+ay)//3), ((bx+ax*2)//3, (by+ay*2)//3)]
        radii = [20, 14, 10]
        for i in range(len(pts)):
            px, py = pts[i]; r = radii[i]
            draw.ellipse([px-r, py-r, px+r, py+r], fill=self.bubble_bg, outline=self.border_color, width=1)

    def _draw_narrative_quantum(self, image, text, panel_rect, data):
        draw = ImageDraw.Draw(image)
        x, y, w, h = panel_rect
        bw, bh, lines, font = self._calculate_balloon_metrics(text, "narracao", 1.1, panel_rect)
        rx, ry = x + int(w * 0.05), y + int(h * 0.05)
        # Sombra suave v37
        draw.rectangle([rx+6, ry+6, rx + bw+6, ry + bh+6], fill="#333333") 
        draw.rectangle([rx, ry, rx + bw, ry + bh], fill=self.narrative_bg, outline=self.border_color, width=2)
        cy = ry + (bh - (self._line_height(font)*len(lines))) // 2
        for l in lines:
            self._draw_styled_line(draw, l, rx + bw//2, cy, font)
            cy += self._line_height(font)

    def _load_font_at_size(self, style, size):
        project_font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "fonts")
        win_font_dir = "C:\\Windows\\Fonts\\"
        cand = [os.path.join(project_font_dir, "CCWildWords-Regular.ttf"), os.path.join(win_font_dir, "arial.ttf")]
        if style in ("grito", "enfatico", "raiva"):
            cand = [os.path.join(project_font_dir, "CCWildWords-Bold.ttf"), os.path.join(win_font_dir, "arialbd.ttf")]
        return self._load_font(cand, size)

    def _wrap_text_pixels(self, draw, text, font, max_width):
        words = str(text).split()
        if not words: return [""]
        lines, line = [], ""
        for word in words:
            test = f"{line} {word}".strip()
            if draw.textbbox((0, 0), test, font=font)[2] <= max_width: line = test
            else:
                if line: lines.append(line); line = word
                else: 
                    parts = self._break_word(draw, word, font, max_width)
                    lines.extend(parts[:-1]); line = parts[-1]
        if line: lines.append(line)
        return lines

    def _break_word(self, draw, word, font, max_width):
        parts, cur = [], ""
        for ch in word:
            if draw.textbbox((0, 0), cur + ch, font=font)[2] <= max_width: cur += ch
            else:
                if cur: parts.append(cur); cur = ch
        if cur: parts.append(cur)
        return parts

    def _line_height(self, font, extra=8):
        bbox = font.getbbox("Ay")
        return (bbox[3] - bbox[1]) + extra

    def _draw_styled_line(self, draw, line, cx, y, base_font):
        parts = re.split(r'(\*\*.*?\*\*)', line)
        total_w, runs = 0, []
        bold_font = self._load_font_at_size("grito", base_font.size)
        for p in parts:
            content, font = (p[2:-2], bold_font) if p.startswith("**") else (p, base_font)
            if not content: continue
            w = draw.textbbox((0, 0), content, font=font)[2]
            runs.append((content, font, w)); total_w += w
        cur_x = cx - total_w // 2
        for c, f, w in runs:
            draw.text((cur_x, y), c, font=f, fill="black"); cur_x += w

    def _apply_dashed_border(self, draw, rect):
        x1, y1, x2, y2 = rect
        cx, cy, w, h = (x1+x2)/2.0, (y1+y2)/2.0, float(x2-x1), float(y2-y1)
        for i in range(0, 360, 24):
            a1, a2 = math.radians(i), math.radians(i + 14)
            p1 = (cx + (w/2)*math.cos(a1), cy + (h/2)*math.sin(a1))
            p2 = (cx + (w/2)*math.cos(a2), cy + (h/2)*math.sin(a2))
            draw.line([p1, p2], fill=self.border_color, width=1)

    def export_pdf(self, images: list) -> BytesIO:
        pil_imgs = [Image.open(BytesIO(i)).convert("RGB") if isinstance(i, bytes) else i.convert("RGB") for i in images]
        if not pil_imgs: return BytesIO()
        buf = BytesIO()
        pil_imgs[0].save(buf, format="PDF", save_all=True, append_images=pil_imgs[1:])
        buf.seek(0)
        return buf