from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image
import os

class PdfExporter:
    def __init__(self, output_path: str = "output/pdfs/lessonai_comic.pdf"):
        self.output_path = output_path
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    def export(self, pil_images: list):
        """
        Recebe uma lista de objetos Image do Pillow e gera um PDF.
        """
        c = canvas.Canvas(self.output_path, pagesize=A4)
        width, height = A4
        
        for pil_img in pil_images:
            # Salva temporário para o ReportLab
            temp_path = "temp_page.png"
            pil_img.save(temp_path)
            
            # Desenha no PDF
            c.drawImage(temp_path, 0, 0, width, height)
            c.showPage()
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        c.save()
        return self.output_path
