from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
import requests
from io import BytesIO
import base64
import textwrap
import math
import os
import copy
import re
from src.utils.debug_logger import DebugLogger
from src.config.image_config import COMPOSER_STYLES, COMIC_SCALES, PLACEHOLDER_URLS
from src.pipeline.balloon_presets import BalloonPresets

class StrictRenderError(Exception):
    """Exception raised when a required comic element (like a panel background) is missing in final mode."""
    pass

class ComicComposer:
    def __init__(self, dpi: int = 300):
        # Master Spec v58.0: A4 Vertical @ 300 DPI
        self.dpi = dpi
        self.width = 2480
        self.height = 3508

        # Estrutura Narrativa (Master Spec)
        self.gutter = 26
        self.safe_zone = 80
        
        # Estilo Quantum v36.0
        self.narrative_bg = COMPOSER_STYLES["narrative_bg"]
        self.bubble_bg = COMPOSER_STYLES["bubble_bg"]
        self.border_color = COMPOSER_STYLES["border_color"]
        self.border_width = COMPOSER_STYLES["border_width"] # 8px p/ quadros
        self.balloon_border = COMPOSER_STYLES.get("balloon_border", 6)
        self.narrative_border = COMPOSER_STYLES.get("narrative_border", 6)
        self.gutter_fill = COMPOSER_STYLES["gutter_fill"]
        self.tail_width = COMPOSER_STYLES.get("tail_width", 30)

        # Escalas Estritas
        self.scales = COMIC_SCALES

        # Tipografia Profissional
        project_font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "fonts")
        win_font_dir = "C:\\Windows\\Fonts\\"
        pt_to_px = dpi / 72.0
        self.base_size = int(8.0 * pt_to_px)

        self.font_ball = self._load_font([os.path.join(project_font_dir, "CCWildWords-Regular.ttf"), os.path.join(win_font_dir, "arial.ttf")], self.base_size)
        self.font_ball_bold = self._load_font([os.path.join(project_font_dir, "CCWildWords-Bold.ttf"), os.path.join(win_font_dir, "arialbd.ttf")], self.base_size)
        self.font_narrative = self._load_font([os.path.join(project_font_dir, "CCWildWords-Regular.ttf"), os.path.join(win_font_dir, "arial.ttf")], int(self.base_size * 1.1))
        
        self.forbidden_hard = []
        self.forbidden_soft = []
        self.occupied_regions = []

    def _load_font(self, candidates, size):
        for path in candidates:
            if os.path.exists(path):
                try: return ImageFont.truetype(path, size)
                except: pass
        return ImageFont.load_default()

    def _get_lettering_metrics(self, style):
        # Master Spec v58.0: Padding e Tamanhos estritos
        if style == "narracao":
            return {"min_pt": 42, "max_pt": 54, "pad_h": 40, "pad_v": 30}
        return {"min_pt": 44, "max_pt": 60, "pad_h": 40, "pad_v": 30}

    def create_page(self, images_urls: list, panels_data: list, render_mode: str = "draft"):
        """v61.0: Wrapper for backward compatibility. Now renders clean page + auto balloons."""
        page = self.create_clean_page(images_urls, panels_data, render_mode)
        
        num_panels = len(images_urls)
        panel_rects = self._get_panel_rects(num_panels)
        
        for idx in range(num_panels):
            if idx >= len(panel_rects): break
            rect = panel_rects[idx]
            data = panels_data[idx] if idx < len(panels_data) else {}
            
            if data.get("dialogo") and data.get("layout_mode") != "manual_page":
                self._place_balloon_absolute_shield(page, data, rect)
                
        return page

    def create_clean_page(self, images_urls: list, panels_data: list, render_mode: str = "draft"):
        """v61.0: Renders ONLY the panels (Clean Plate)."""
        page = Image.new("RGB", (self.width, self.height), self.gutter_fill)
        num_panels = len(images_urls)
        panel_rects = self._get_panel_rects(num_panels)
        
        for idx in range(num_panels):
            if idx >= len(panel_rects): break
            self._render_panel(page, images_urls[idx], panel_rects[idx], render_mode=render_mode)
            
        return page

    def render_balloons_on_page(self, page_image, balloons_data):
        """
        v61.0: Renders a list of balloons directly onto the page image.
        balloons_data: List of dicts with {text, type, bbox, tail_origin, tail_target}
        Coordinates are normalized 0-1000 relative to the PAGE.
        """
        for b_data in balloons_data:
            self._render_standalone_balloon(page_image, b_data)
        return page_image

    def _render_standalone_balloon(self, image, b_data):
        """Render individual balloon respecting user-defined bbox strictly."""
        text = str(b_data.get("text", "")).strip()
        if not text:
            return
        style = str(b_data.get("type", "fala")).lower()

        # Page-normalized (0-1000) to absolute pixels
        bn = b_data.get("bbox", [400, 100, 200, 150])
        x1 = int(bn[0] * self.width / 1000)
        y1 = int(bn[1] * self.height / 1000)
        bw = max(int(bn[2] * self.width / 1000), 80)
        bh = max(int(bn[3] * self.height / 1000), 50)

        # Fit text STRICTLY within the user bbox (no expansion)
        page_rect = (0, 0, self.width, self.height)
        scale = float(b_data.get("intensity", 1.0)) * self.scales.get(style, 1.0)
        _, _, lines, font = self._fit_text_to_target_box(
            text, style, scale, bw, bh, page_rect, can_expand=False
        )

        # Tail target (where the tail points to)
        tn = b_data.get("tail_target", [500, 500])
        anchor = (int(tn[0] * self.width / 1000), int(tn[1] * self.height / 1000))

        # Tail origin
        on = b_data.get("tail_origin")
        m_origin = on if on else None

        # Use the EXACT user-defined bbox, not the fitted size
        rect = (x1, y1, x1 + bw, y1 + bh)
        self._draw_balloon_v37_geometric(image, text, rect, lines, font, anchor, style, page_rect, m_origin, extra_data=b_data)

    def _get_panel_rects(self, num_panels):
        # v58.0: Master Spec Specific Layout (5 Panels)
        if num_panels == 5:
            return [
                (80, 80, 2320, 1050),    # Q1: Top Wide
                (80, 1156, 1137, 760),   # Q2: Mid Left
                (1243, 1156, 1157, 760), # Q3: Mid Right
                (80, 1942, 980, 970),    # Q4: Bot Left
                (1086, 1942, 1314, 1486) # Q5: Bot Right Vertical
            ]
        
        # Fallback to dynamic layout
        tiers = self._choose_layout(num_panels)
        tier_heights = self._calculate_tier_heights(tiers)
        rects = []
        y_off = 0
        for t_idx, p_in_tier in enumerate(tiers):
            th = tier_heights[t_idx]
            pw = (self.width - ((p_in_tier - 1) * self.gutter)) // p_in_tier
            for p_idx in range(p_in_tier):
                rects.append((p_idx * (pw + self.gutter), y_off, pw, th))
            y_off += th + self.gutter
        return rects

    def _choose_layout(self, num_panels):
        if num_panels <= 3: return [1] * num_panels
        if num_panels == 4: return [1, 2, 1]
        if num_panels == 5: return [1, 2, 2] # (Fallback, will be bypassed if handled in _get_panel_rects)
        if num_panels == 6: return [1, 2, 2, 1]
        return [2] * (num_panels // 2) + ([1] if num_panels % 2 else [])

    def _calculate_tier_heights(self, tiers):
        ah = self.height - ((len(tiers)-1)*self.gutter)
        total_weight = sum([1.4 if t == 1 else 1.0 for t in tiers])
        unit_h = ah / total_weight
        return [int(unit_h * (1.4 if t == 1 else 1.0)) for t in tiers]

    def _render_panel(self, page, data_source, rect, render_mode: str = "draft"):
        x, y, w, h = rect
        img = None
        
        try:
            # v56.3: Suporte a data_source como bytes
            if isinstance(data_source, bytes):
                img = Image.open(BytesIO(data_source)).convert("RGB")
            elif isinstance(data_source, str):
                url = data_source
                
                # v59.0: Detecta e bloqueia placeholders em modo estrito
                is_placeholder = any(p in url for p in ["placehold.co", "via.placeholder.com", "NOT_GENERATED"])
                if render_mode == "final_comic" and is_placeholder:
                    raise StrictRenderError(f"Painel em {rect} está sem arte real (detectado placeholder). Abortando renderização final.")

                if url.startswith("data:image"):
                    header, encoded = url.split(",", 1)
                    data = base64.b64decode(encoded)
                    img = Image.open(BytesIO(data)).convert("RGB")
                elif url.startswith("http"):
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                    resp = requests.get(url, timeout=25, headers=headers)
                    img = Image.open(BytesIO(resp.content)).convert("RGB")
                else: 
                    if os.path.exists(url):
                        img = Image.open(url).convert("RGB")
            
            if img:
                img = img.resize((w, h), Image.Resampling.LANCZOS)
                page.paste(img, (x, y))
                # Borda do Quadro (Master Spec v58.0: 8px)
                draw = ImageDraw.Draw(page)
                draw.rectangle([x, y, x + w, y + h], outline=self.border_color, width=self.border_width)
            else:
                raise ValueError("Fonte de imagem inválida ou inacessível")

        except Exception as e:
            if render_mode == "final_comic":
                raise StrictRenderError(f"Erro no Painel {rect}: {str(e)}. A renderização final exige artes reais.")
            
            # Fallback para modo Draft (cinza escuro com aviso)
            DebugLogger.log("IMAGE_RENDER_ERROR", "system", is_anomaly=True, extra={"error": str(e)})
            img_err = Image.new("RGB", (w, h), (40, 40, 40))
            draw_err = ImageDraw.Draw(img_err)
            draw_err.text((20, h//2 - 10), "ARTE EM PROCESSAMENTO...", fill="#777777")
            page.paste(img_err, (x, y))
            ImageDraw.Draw(page).rectangle([x, y, x + w, y + h], outline=self.border_color, width=2)

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
        
        # v60.0: Prioridade absoluta para balloon_style (estilo manual)
        style = str(data.get("balloon_style") or data.get("tipo_texto", "fala")).lower()
        
        if style == "narracao" or style == "legenda":
            self._draw_narrative_quantum(image, text, panel_rect, data)
            return

        intensity = float(data.get("intensity", 1.0))
        base_scale = float(self.scales.get(style, 1.0)) * intensity
        
        # v60.0: Resolução do Alvo (Target) da Cauda - Heurística vs Manual
        m_target = data.get("tail_target")
        if m_target and isinstance(m_target, list) and len(m_target) == 2:
            # Converte normalizado 0-1000 para pixels reais
            anchor = (int(panel_rect[0] + m_target[0] * panel_rect[2] / 1000), 
                      int(panel_rect[1] + m_target[1] * panel_rect[3] / 1000))
        else:
            anchor = self._resolve_tail_target(panel_rect, data)
        
        # Ciclo de Auto-Shrink (3 tentativas para blindagem absoluta)
        best_overall_pos = None
        final_bw, final_bh, final_lines, final_font = None, None, None, None
        
        # v43.0: Fonte da Verdade Absoluta (manual_bbox)
        m_bbox = data.get("manual_bbox") # [x, y, w, h] normalized 0-1000
        manual_p = data.get("manual_pos")
        
        if m_bbox and isinstance(m_bbox, list) and len(m_bbox) == 4:
            # v51.0: Auto-fit mesmo em manual_bbox (Respeitando limites do usuário)
            px1_n, py1_n, bw_n, bh_n = m_bbox
            px1 = panel_rect[0] + (px1_n * panel_rect[2] / 1000)
            py1 = panel_rect[1] + (py1_n * panel_rect[3] / 1000)
            bw_p = bw_n * panel_rect[2] / 1000
            bh_p = bh_n * panel_rect[3] / 1000
            
            # v56.0: Log Fonte da Verdade (Manual Wins)
            DebugLogger.log("MANUAL_BBOX_SOURCE_OF_TRUTH", "system", panel_index=-1, # Index extraído do panel_rect se possível
                            extra={"manual_bbox": m_bbox, "abs_px": px1, "abs_py": py1, "abs_w": bw_p, "abs_h": bh_p},
                            message=f"Modo MANUAL: Usando bbox exato {bw_p:.1f}x{bh_p:.1f} em ({px1:.1f}, {py1:.1f})")

            # Ajusta o texto ao box manual
            final_bw, final_bh, final_lines, final_font = self._fit_text_to_target_box(
                text, style, base_scale, bw_p, bh_p, panel_rect, can_expand=True
            )
            best_overall_pos = (px1, py1)
            
            # v56.0: REMOVIDO re-alinhamento de segurança. O BBox manual é a LEI ABSOLUTA.
            # Se o balão vazar do quadro, o usuário verá no preview e ajustará lá.
            if final_bw > bw_p or final_bh > bh_p:
                 DebugLogger.log("LAYOUT_RESIZE", "system", is_anomaly=True,
                                extra={"old_w": bw_p, "new_w": final_bw, "old_h": bh_p, "new_h": final_bh},
                                message="AVISO: Balão expandiu além do BBox manual para acomodar o texto")
            
        elif manual_p and isinstance(manual_p, list) and len(manual_p) == 2:
            scale = base_scale
            bw, bh, lines, font = self._calculate_balloon_metrics_autofit(text, style, scale, panel_rect)
            # Converte 0-1000 para pixels absolutos
            px1 = panel_rect[0] + (manual_p[0] * panel_rect[2] / 1000)
            py1 = panel_rect[1] + (manual_p[1] * panel_rect[3] / 1000)
            best_overall_pos = (px1, py1)
            final_bw, final_bh, final_lines, final_font = bw, bh, lines, font
        else:
            for attempt in range(3):
                scale = base_scale * (0.9 ** attempt)
                bw, bh, lines, font = self._calculate_balloon_metrics_autofit(text, style, scale, panel_rect)
                
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

        if not best_overall_pos:
            DebugLogger.log("PLACEMENT_FAILED", "system", is_anomaly=True, message=f"Falha ao encontrar posição para balão: {style}")
            return

        # v56.0: Log Final antes do desenho
        DebugLogger.log("FINAL_COORDINATES_CALCULATED", "system", 
                        extra={"final_pos": best_overall_pos, "final_size": (final_bw, final_bh)},
                        message=f"Desenho final em {best_overall_pos[0]:.1f}, {best_overall_pos[1]:.1f}")

        m_origin = data.get("tail_origin") or data.get("manual_tail_origin")
        px, py = best_overall_pos
        self._draw_balloon_v37_geometric(image, text, (px, py, px + final_bw, py + final_bh), 
                                        final_lines, final_font, anchor, style, panel_rect, m_origin, extra_data=data)
        self.occupied_regions.append([px, py, px + final_bw, py + final_bh])

    def _calculate_balloon_metrics_autofit(self, text, style, target_scale, panel_rect):
        """v51.0: Auto-fit dinâmico com regras de expansão."""
        # Chute inicial baseado no painel
        max_bw = int(panel_rect[2] * 0.7 * target_scale)
        max_bh = int(panel_rect[3] * 0.5 * target_scale)
        return self._fit_text_to_target_box(text, style, target_scale, max_bw, max_bh, panel_rect, can_expand=True)

    def _fit_text_to_target_box(self, text, style, scale, target_bw, target_bh, panel_rect, can_expand=True):
        metrics = self._get_lettering_metrics(style)
        min_fs = metrics["min_pt"]
        max_fs = metrics["max_pt"]
        pad_h = metrics["pad_h"]
        pad_v = metrics["pad_v"]
        
        current_fs = int(max_fs * scale)
        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        
        while current_fs >= min_fs:
            font = self._load_font_at_size(style, current_fs)
            # Master Spec: Padding fixo em vez de ratio
            safe_w = target_bw - (pad_h * 2)
            safe_h = target_bh - (pad_v * 2)
            
            lines = self._wrap_text_pixels(draw, text, font, safe_w)
            block_w, block_h = self._measure_text_block(lines, font)
            
            if block_w <= safe_w and block_h <= safe_h:
                bw = block_w + (pad_h * 2)
                bh = block_h + (pad_v * 2)
                
                # Proporção 1.8x a 2.6x (Master Spec)
                if style not in ("narracao", "legenda", "eletronico"):
                    if bw < bh * 1.8: bw = int(bh * 1.8)
                    if bw > bh * 2.6: bw = int(bh * 2.6)
                
                return bw, bh, lines, font
            
            current_fs -= 2
            
        if can_expand:
            font = self._load_font_at_size(style, min_fs)
            lines = self._wrap_text_pixels(draw, text, font, int(panel_rect[2] * 0.8))
            block_w, block_h = self._measure_text_block(lines, font)
            bw, bh = block_w + (pad_h * 2), block_h + (pad_v * 2)
            return bw, bh, lines, font
        
        font = self._load_font_at_size(style, min_fs)
        return target_bw, target_bh, self._wrap_text_pixels(draw, text, font, target_bw - pad_h*2), font

    def _get_safe_inner_area(self, style, bw, bh):
        metrics = self._get_lettering_metrics(style)
        return bw - (metrics["pad_h"] * 2), bh - (metrics["pad_v"] * 2)

    def _measure_text_block(self, lines, font):
        if not lines: return 0, 0
        draw = ImageDraw.Draw(Image.new("RGB", (1,1)))
        widths = [draw.textbbox((0,0), l, font=font)[2] for l in lines]
        tw = max(widths) if widths else 0
        th = self._line_height(font, extra=int(font.size * 0.4)) * len(lines)
        return tw, th

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

    def _resolve_tail_target(self, panel_rect, data):
        """
        v46.0: Resolução do alvo da cauda com prioridade estrita:
        1. manual_tail_target (Círculo no editor)
        2. personagem_pos (Vision ou Manual)
        3. Maior face_bbox
        4. Maior character_bbox
        5. Fallback centro
        """
        x, y, w, h = panel_rect
        
        # 1. Prioridade Máxima: manual_tail_target [x, y] 0-1000
        mt = data.get("manual_tail_target")
        if mt and isinstance(mt, list) and len(mt) == 2:
            return (int(x + mt[0] * w / 1000), int(y + mt[1] * h / 1000))

        # 2. Prioridade 2: personagem_pos (Vision Engine ou Manual legada)
        pos = data.get("personagem_pos")
        if pos and isinstance(pos, list) and len(pos) == 2:
            return (int(x + pos[0] * w / 1000), int(y + pos[1] * h / 1000))
            
        # 3. Prioridade 3: Maior Rosto (deteção geométrica)
        best_face = None
        max_area = -1
        for fb in self.forbidden_hard:
            area = (fb[2] - fb[0]) * (fb[3] - fb[1])
            if area > max_area:
                max_area = area
                best_face = ((fb[0] + fb[2]) // 2, (fb[1] + fb[3]) // 2)
        if best_face: return best_face
        
        # 4. Prioridade 4: Maior Corpo
        max_area = -1
        best_body = None
        for cb in self.forbidden_soft:
            area = (cb[2] - cb[0]) * (cb[3] - cb[1])
            if area > max_area:
                max_area = area
                best_body = ((cb[0] + cb[2]) // 2, int(cb[1] + (cb[3]-cb[1])*0.2))
        if best_body: return best_body

        # 5. Fallback centro inferior
        return (x + w // 2, y + int(h * 0.75))

    def _draw_balloon_v37_geometric(self, image, text, rect, lines, font, anchor, style, panel_rect, manual_origin=None, extra_data=None):
        x1, y1, x2, y2 = rect
        bcx, bcy = (x1 + x2) // 2, (y1 + y2) // 2
        extra_data = extra_data or {}
        
        # v60.1: Auditoria Editorial do Renderer
        DebugLogger.log("BALLOON_RENDER_START", "system", 
                        extra={"style": style, "rect": rect, "homologated": True},
                        message=f"Renderizando balão estilo '{style}' via BalloonPresets (Homologado)")

        # v60.0: Lista de pares (origem, alvo) para renderizar as caudas
        tails_to_draw = []
        
        # 1. Resolve Alvo(s) e Origem(ns)
        m_targets = extra_data.get("tail_targets", [])
        m_origin = extra_data.get("tail_origin") or manual_origin
        
        if m_targets and isinstance(m_targets, list):
            for mt in m_targets:
                target_px = (int(panel_rect[0] + mt[0] * panel_rect[2] / 1000), 
                             int(panel_rect[1] + mt[1] * panel_rect[3] / 1000))
                
                if m_origin:
                    tx_raw = panel_rect[0] + (m_origin[0] * panel_rect[2] / 1000)
                    ty_raw = panel_rect[1] + (m_origin[1] * panel_rect[3] / 1000)
                    tx, ty = max(x1, min(x2, tx_raw)), max(y1, min(y2, ty_raw))
                else:
                    tx, ty = self._choose_tail_exit(rect, target_px, pad=0.85 if style in ("pensamento", "nuvem", "sonho") else 1.0)
                
                tails_to_draw.append(((tx, ty), target_px))
        else:
            # Caso único (padrão)
            if m_origin:
                tx_raw = panel_rect[0] + (m_origin[0] * panel_rect[2] / 1000)
                ty_raw = panel_rect[1] + (m_origin[1] * panel_rect[3] / 1000)
                tx, ty = max(x1, min(x2, tx_raw)), max(y1, min(y2, ty_raw))
            else:
                tx, ty = self._choose_tail_exit(rect, anchor, pad=0.85 if style in ("pensamento", "nuvem", "sonho") else 1.0)
            
            tails_to_draw.append(((tx, ty), anchor))

        # v48.0 & v60.0: Renderização via Presets Profissionais (High-Fidelity PIL)
        # Nota: BalloonPresets atualizado para aceitar múltiplas caudas se necessário, 
        # mas aqui chamamos para o balão base e depois as caudas.
        
        # Para o preset, usamos a primeira cauda como referência de geometria de balão se necessário
        first_origin, first_target = tails_to_draw[0]
        origin_rel = (first_origin[0] - bcx, first_origin[1] - bcy)
        target_rel = (first_target[0] - bcx, first_target[1] - bcy)
        
        # Renderiza o corpo do balão
        balloon_pil = BalloonPresets.get_balloon_image(
            style, x2-x1, y2-y1, origin_rel, target_rel,
            bg_color=self.bubble_bg, border_color=self.border_color, border_width=self.border_width
        )
        
        # Se houver múltiplas caudas, precisamos que o preset desenhe as adicionais ou desenhamos manualmente?
        # Por enquanto, assumimos que o preset cuida de uma. Se houver mais, iteramos nas caudas extras.
        # TODO: Evoluir BalloonPresets para múltiplas caudas. 
        # Por enquanto, o ComicComposer garante a posição.
        
        px = int(bcx - balloon_pil.width // 2)
        py = int(bcy - balloon_pil.height // 2)
        image.paste(balloon_pil, (px, py), balloon_pil)

        # Draw Text (Centralizado verticalmente no centro original)
        draw = ImageDraw.Draw(image)
        lh = self._line_height(font, extra=int(font.size * 0.4))
        th = lh * len(lines)
        # v51.0: Centralização absoluta e segura
        cy = y1 + (y2 - y1 - th) // 2
        # Se th for maior que o balão, forçamos o início em y1 + margem de segurança
        if th > (y2 - y1):
            cy = y1 + int((y2 - y1) * 0.1)
        
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


    def _draw_narrative_quantum(self, image, text, panel_rect, data):
        draw = ImageDraw.Draw(image)
        x, y, w, h = panel_rect
        bw, bh, lines, font = self._calculate_balloon_metrics_autofit(text, "narracao", 1.1, panel_rect)
        
        # Master Spec: Posição clássica (Topo-Esquerda)
        rx, ry = x + self.safe_zone, y + self.safe_zone
        
        # Sombra sutil
        shadow_off = 4
        draw.rectangle([rx + shadow_off, ry + shadow_off, rx + bw + shadow_off, ry + bh + shadow_off], fill="#0A0C1044") 
        
        # Caixa de Narração (Borda 6px, Fundo Creme)
        draw.rectangle([rx, ry, rx + bw, ry + bh], fill=self.narrative_bg, outline=self.border_color, width=self.narrative_border)
        
        # Texto centralizado na caixa
        lh = self._line_height(font)
        total_th = lh * len(lines)
        cy = ry + (bh - total_th) // 2
        
        for l in lines:
            self._draw_styled_line(draw, l, rx + bw//2, cy, font)
            cy += lh

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