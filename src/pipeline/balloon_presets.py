from PIL import Image, ImageDraw, ImageFilter
import math
import random

class BalloonPresets:
    @staticmethod
    def get_balloon_image(style, w, h, origin_rel=None, target_rel=None, bg_color="white", border_color="black", border_width=4, modifiers=None):
        """
        Gera uma imagem PIL com o balão calibrado.
        w, h: dimensões úteis.
        modifiers: list de strings (ex: ['cauda_dupla', 'interrompido', 'sem_cauda'])
        """
        modifiers = modifiers or []
        margin = 150
        full_w, full_h = int(w + margin*2), int(h + margin*2)
        img = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        cx, cy = full_w // 2, full_h // 2
        
        # 1. Render Sombra (Opcional, removida para o manual técnico puro conforme pedido "fundo branco puro")
        # Se quiser sombra, pode reativar aqui. Para o manual, mantemos limpo.

        # 2. Render Balão Principal
        BalloonPresets._draw_calibrated_shape(draw, style, cx, cy, w, h, origin_rel, target_rel, 
                                             fill=bg_color, border=border_color, bw=border_width, modifiers=modifiers)
        
        return img

    @staticmethod
    def _draw_calibrated_shape(draw, style, cx, cy, w, h, origin_rel, target_rel, fill, border, bw, modifiers):
        """Desenha as formas refinadas baseadas na lista obrigatória."""
        
        pts = []
        is_path_based = False # Para estilos que usam paths vetoriais manuais
        
        # --- LÓGICA DE FORMA BASE ---
        
        if style in ("pensamento", "sonho", "nuvem"):
            BalloonPresets._draw_cloud_shape(draw, style, cx, cy, w, h, fill, border, bw)
            if "sem_cauda" not in modifiers and style == "pensamento":
                BalloonPresets._draw_thought_trail(draw, cx, cy, origin_rel, target_rel, fill, border, bw)
            return

        elif style == "flashback":
            BalloonPresets._draw_flashback_shape(draw, cx, cy, w, h, fill, border, bw)
            return

        elif style in ("grito", "raiva", "explosao", "burst_assimetrico"):
            pts = BalloonPresets._gen_burst_pts(cx, cy, w, h, asymmetric=(style=="burst_assimetrico"))
            
        elif style in ("eletronico", "radio"):
            BalloonPresets._draw_electronic_shape(draw, style, cx, cy, w, h, fill, border, bw)
            if style == "radio":
                BalloonPresets._draw_radio_waves(draw, cx, cy, w, h, border, bw)
            if "sem_cauda" not in modifiers:
                BalloonPresets._draw_horn_tail(draw, cx, cy, origin_rel, target_rel, fill, border, bw)
            return

        elif style in ("narração", "legenda", "retangular_arredondado"):
            radius = 20 if style == "retangular_arredondado" else 0
            BalloonPresets._draw_rect_shape(draw, cx, cy, w, h, fill, border, bw, radius)
            return

        elif style == "choro":
            pts = BalloonPresets._gen_wavy_pts(cx, cy, w, h)
            
        elif style == "organico":
            pts = BalloonPresets._gen_organic_pts(cx, cy, w, h)
            
        elif style == "serrilhado":
            pts = BalloonPresets._gen_serrated_pts(cx, cy, w, h)

        else: # Standard / Fala / Outros
            pts = BalloonPresets._gen_ellipse_pts(cx, cy, w, h, jitter=(style=="sussurro" or style=="duvida"))

        # --- RENDERIZAÇÃO DA FORMA ---
        
        # Clipping (Modificador Interrompido)
        if "interrompido" in modifiers:
            # Simula um corte reto na lateral
            pts = [p for p in pts if p[0] < cx + w/2 * 0.8]

        if style == "sussurro":
            # Render vetorial para tracejado
            BalloonPresets._draw_dashed_polygon(draw, pts, border, bw)
            draw.polygon(pts, fill=fill, outline=None) # Apenas preenchimento
        else:
            draw.polygon(pts, fill=fill, outline=border, width=bw if border else 0)

        # --- LÓGICA DE CAUDAS ---
        if "sem_cauda" not in modifiers and style not in ("narração", "legenda"):
            origins = [origin_rel] if origin_rel else []
            targets = [target_rel] if target_rel else []
            
            if "cauda_dupla" in modifiers:
                targets.append((target_rel[0] + 60, target_rel[1] - 20))
            if "múltipla_fala" in modifiers:
                targets.append((target_rel[0] - 100, target_rel[1]))
                
            for t in targets:
                BalloonPresets._draw_horn_tail(draw, cx, cy, origin_rel or (0, h/2), t, fill, border, bw)

        # --- ELEMENTOS INTERNOS (Exclamação, Dúvida, Canto) ---
        if style == "exclamação":
            # Gráfico de exclamação (Ênfase gráfica)
            draw.rectangle([cx-5, cy-h/3, cx+5, cy+h/6], fill=border)
            draw.ellipse([cx-7, cy+h/4, cx+7, cy+h/4+14], fill=border)
        elif style == "duvida":
            # Gráfico de interrogação (Hesitação visual)
            draw.arc([cx-20, cy-h/3, cx+20, cy-h/10], start=180, end=0, fill=border, width=bw+2)
            draw.line([cx+20, cy-h/5, cx+20, cy], fill=border, width=bw+2)
            draw.line([cx+20, cy, cx, cy], fill=border, width=bw+2)
            draw.line([cx, cy, cx, cy+15], fill=border, width=bw+2)
            draw.ellipse([cx-7, cy+h/4, cx+7, cy+h/4+14], fill=border)
        elif style == "canto":
            BalloonPresets._draw_musical_notes(draw, cx, cy, w, h, border, bw)

    @staticmethod
    def _gen_ellipse_pts(cx, cy, w, h, count=72, jitter=False):
        pts = []
        for i in range(count):
            angle = (i / count) * 2 * math.pi
            j = (1.0 + 0.01 * math.sin(angle * 12)) if jitter else 1.0
            pts.append((cx + (w/2) * j * math.cos(angle), cy + (h/2) * j * math.sin(angle)))
        return pts

    @staticmethod
    def _gen_burst_pts(cx, cy, w, h, count=36, asymmetric=False):
        pts = []
        for i in range(count):
            angle = (i / count) * 2 * math.pi
            noise = random.uniform(0.8, 1.2) if asymmetric else 1.0
            factor = (1.4 if i % 2 == 0 else 1.1) * noise
            pts.append((cx + (w/2) * factor * math.cos(angle), cy + (h/2) * factor * math.sin(angle)))
        return pts

    @staticmethod
    def _gen_wavy_pts(cx, cy, w, h, count=80):
        pts = []
        for i in range(count):
            angle = (i / count) * 2 * math.pi
            wave = 1.0 + 0.05 * math.sin(angle * 15)
            pts.append((cx + (w/2) * wave * math.cos(angle), cy + (h/2) * wave * math.sin(angle)))
        return pts

    @staticmethod
    def _gen_organic_pts(cx, cy, w, h, count=60):
        pts = []
        for i in range(count):
            angle = (i / count) * 2 * math.pi
            noise = 1.0 + 0.08 * math.sin(angle * 5) + 0.03 * math.cos(angle * 13)
            pts.append((cx + (w/2) * noise * math.cos(angle), cy + (h/2) * noise * math.sin(angle)))
        return pts

    @staticmethod
    def _gen_serrated_pts(cx, cy, w, h, count=100):
        pts = []
        for i in range(count):
            angle = (i / count) * 2 * math.pi
            serration = 1.0 + (0.04 if i % 2 == 0 else 0)
            pts.append((cx + (w/2) * serration * math.cos(angle), cy + (h/2) * serration * math.sin(angle)))
        return pts

    @staticmethod
    def _draw_cloud_shape(draw, style, cx, cy, w, h, fill, border, bw):
        count = 10 if style == "sonho" else 14
        opacity = 0.5 if style == "sonho" else 1.0
        circles = []
        for i in range(count):
            angle = (i / count) * 2 * math.pi
            rx, ry = (w/2) * math.cos(angle), (h/2) * math.sin(angle)
            rad = (w/count) * (2.2 if style == "nuvem" else 1.8)
            circles.append((cx + rx - rad, cy + ry - rad, cx + rx + rad, cy + ry + rad))
        
        draw.ellipse([cx-w/2, cy-h/2, cx+w/2, cy+h/2], fill=fill)
        for c in circles:
            draw.ellipse(c, fill=fill)
        if border:
            for c in circles:
                draw.arc(c, start=0, end=360, fill=border, width=bw)
            draw.ellipse([cx-w/2+bw, cy-h/2+bw, cx+w/2-bw, cy+h/2-bw], fill=fill)

    @staticmethod
    def _draw_flashback_shape(draw, cx, cy, w, h, fill, border, bw):
        # Múltiplas bordas para efeito de memória/profundidade
        for i in range(2):
            off = i * 8
            pts = BalloonPresets._gen_organic_pts(cx, cy, w + off, h + off)
            draw.polygon(pts, fill=fill if i==0 else None, outline=border, width=bw)

    @staticmethod
    def _draw_dashed_polygon(draw, pts, color, bw):
        for i in range(len(pts)):
            if i % 2 == 0:
                draw.line([pts[i], pts[(i+1)%len(pts)]], fill=color, width=bw)

    @staticmethod
    def _draw_electronic_shape(draw, style, cx, cy, w, h, fill, border, bw):
        r = [cx-w/2, cy-h/2, cx+w/2, cy+h/2]
        draw.rectangle(r, fill=fill, outline=border, width=bw)
        if style == "eletronico":
            off = 15
            draw.line([r[0]+off, r[1]-10, r[0]+off, r[1]+10], fill=border, width=bw)
            draw.line([r[2]-off, r[1]-10, r[2]-off, r[1]+10], fill=border, width=bw)

    @staticmethod
    def _draw_radio_waves(draw, cx, cy, w, h, border, bw):
        for i in range(2):
            off = 20 + i*15
            draw.arc([cx-w/2-off, cy-h/2-off, cx-w/2+off, cy-h/2+off], start=200, end=270, fill=border, width=bw)
            draw.arc([cx+w/2-off, cy-h/2-off, cx+w/2+off, cy-h/2+off], start=270, end=340, fill=border, width=bw)

    @staticmethod
    def _draw_rect_shape(draw, cx, cy, w, h, fill, border, bw, radius=0):
        r = [cx-w/2, cy-h/2, cx+w/2, cy+h/2]
        if radius > 0:
            draw.rounded_rectangle(r, radius=radius, fill=fill, outline=border, width=bw)
        else:
            draw.rectangle(r, fill=fill, outline=border, width=bw)

    @staticmethod
    def _draw_musical_notes(draw, cx, cy, w, h, border, bw):
        # Notas musicais simplificadas
        draw.line([cx+w/3, cy-h/3, cx+w/3, cy-h/3-20], fill=border, width=bw)
        draw.ellipse([cx+w/3-10, cy-h/3-5, cx+w/3, cy-h/3+5], fill=border)

    @staticmethod
    def _draw_thought_trail(draw, cx, cy, origin_rel, target_rel, fill, border, bw):
        ox, oy = cx + (origin_rel[0] if origin_rel else 0), cy + (origin_rel[1] if origin_rel else 0)
        tx, ty = cx + target_rel[0], cy + target_rel[1]
        steps = 3
        for i in range(1, steps + 1):
            f = i / (steps + 1)
            px, py = ox + (tx - ox) * f, oy + (ty - oy) * f
            rad = 12 * (1 - f * 0.5)
            draw.ellipse([px-rad, py-rad, px+rad, py+rad], fill=fill, outline=border, width=bw)

    @staticmethod
    def _draw_horn_tail(draw, cx, cy, origin_rel, target_rel, fill, border, bw):
        if not target_rel: return
        ox, oy = cx + (origin_rel[0] if origin_rel else 0), cy + (origin_rel[1] if origin_rel else 0)
        tx, ty = cx + target_rel[0], cy + target_rel[1]
        dist = math.sqrt((tx-ox)**2 + (ty-oy)**2)
        if dist < 10: return
        ux, uy = (tx-ox)/dist, (ty-oy)/dist
        nx, ny = -uy, ux
        base_w = 20
        p1 = (ox + nx * base_w, oy + ny * base_w)
        p2 = (ox - nx * base_w, oy - ny * base_w)
        p3 = (tx, ty)
        draw.polygon([p1, p3, p2], fill=fill)
        draw.line([p1, p3], fill=border, width=bw)
        draw.line([p2, p3], fill=border, width=bw)
        draw.line([p1, p2], fill=fill, width=bw + 2)
