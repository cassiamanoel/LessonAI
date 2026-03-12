import pytest
from io import BytesIO
from PIL import Image
from src.pipeline.composer import ComicComposer

def test_export_pdf():
    composer = ComicComposer()
    
    # Criar 2 imagens de teste (bytes)
    img1 = Image.new("RGB", (100, 100), "red")
    img2 = Image.new("RGB", (100, 100), "blue")
    
    buf1 = BytesIO()
    img1.save(buf1, format="PNG")
    buf2 = BytesIO()
    img2.save(buf2, format="PNG")
    
    images_list = [buf1.getvalue(), buf2.getvalue()]
    
    pdf_buffer = composer.export_pdf(images_list)
    assert pdf_buffer is not None
    assert pdf_buffer.getvalue().startswith(b"%PDF")

def test_export_pdf_empty():
    composer = ComicComposer()
    pdf_buffer = composer.export_pdf([])
    assert isinstance(pdf_buffer, BytesIO)
    assert pdf_buffer.getvalue() == b""

def test_create_page_empty():
    composer = ComicComposer()
    # Deve retornar uma página branca se não houver imagens
    page = composer.create_page([], [])
    assert page.size == (composer.width, composer.height)
