from __future__ import annotations

from io import BytesIO
from typing import Iterable, List, Optional, Sequence

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
from pypdf import PdfReader, PdfWriter
import fitz  # PyMuPDF


def _make_overlay_for_page(page_width: float, page_height: float, draw_fn) -> BytesIO:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))
    draw_fn(c, page_width, page_height)
    c.save()
    buf.seek(0)
    return buf


def _merge_overlay(reader: PdfReader, writer: PdfWriter, overlays_per_page: dict[int, BytesIO]):
    for i, page in enumerate(reader.pages):
        page = page
        if i in overlays_per_page:
            overlay_reader = PdfReader(overlays_per_page[i])
            overlay_page = overlay_reader.pages[0]
            page.merge_page(overlay_page)
        writer.add_page(page)


def write_text(
    input_pdf: str,
    output_pdf: str,
    text: str,
    x: float,
    y: float,
    page: int = 1,
    font_name: str = "Helvetica",
    font_size: int = 12,
    color: str = "black",
):
    reader = PdfReader(input_pdf)
    page_index = max(0, page - 1)
    page_obj = reader.pages[page_index]
    w = float(page_obj.mediabox.width)
    h = float(page_obj.mediabox.height)

    def draw(c: canvas.Canvas, pw, ph):
        # Optionally register custom TTF font if font_name points to a .ttf file
        if font_name.lower().endswith(".ttf"):
            reg_name = "CustomFont"
            pdfmetrics.registerFont(TTFont(reg_name, font_name))
            use_font = reg_name
        else:
            use_font = font_name
        c.setFillColor(getattr(colors, color, colors.black))
        c.setFont(use_font, font_size)
        c.drawString(x, y, text)

    overlay = _make_overlay_for_page(w, h, draw)
    writer = PdfWriter()
    _merge_overlay(reader, writer, {page_index: overlay})
    with open(output_pdf, "wb") as f:
        writer.write(f)


def add_image(
    input_pdf: str,
    output_pdf: str,
    image_path: str,
    x: float,
    y: float,
    width: Optional[float] = None,
    height: Optional[float] = None,
    page: int = 1,
):
    reader = PdfReader(input_pdf)
    page_index = max(0, page - 1)
    page_obj = reader.pages[page_index]
    w = float(page_obj.mediabox.width)
    h = float(page_obj.mediabox.height)

    img = Image.open(image_path)
    iw, ih = img.size
    if width is None and height is None:
        # default: scale to 2 inches width
        width = 2 * inch
        height = (width / iw) * ih
    elif width is not None and height is None:
        height = (width / iw) * ih
    elif height is not None and width is None:
        width = (height / ih) * iw

    def draw(c: canvas.Canvas, pw, ph):
        c.drawImage(image_path, x, y, width=width, height=height, mask='auto')

    overlay = _make_overlay_for_page(w, h, draw)
    writer = PdfWriter()
    _merge_overlay(reader, writer, {page_index: overlay})
    with open(output_pdf, "wb") as f:
        writer.write(f)


def sign_pdf(
    input_pdf: str,
    output_pdf: str,
    image_path: str,
    page: int = -1,
    margin_x: float = 36,
    margin_y: float = 36,
    width: float = 2.5 * inch,
):
    reader = PdfReader(input_pdf)
    if page == -1:
        page_index = len(reader.pages) - 1
    else:
        page_index = max(0, page - 1)
    page_obj = reader.pages[page_index]
    w = float(page_obj.mediabox.width)
    h = float(page_obj.mediabox.height)

    img = Image.open(image_path)
    iw, ih = img.size
    height = (width / iw) * ih
    x = w - margin_x - width
    y = margin_y

    def draw(c: canvas.Canvas, pw, ph):
        c.drawImage(image_path, x, y, width=width, height=height, mask='auto')

    overlay = _make_overlay_for_page(w, h, draw)
    writer = PdfWriter()
    _merge_overlay(reader, writer, {page_index: overlay})
    with open(output_pdf, "wb") as f:
        writer.write(f)


def merge_pdfs(inputs: Sequence[str], output_pdf: str):
    writer = PdfWriter()
    for p in inputs:
        r = PdfReader(p)
        for page in r.pages:
            writer.add_page(page)
    with open(output_pdf, "wb") as f:
        writer.write(f)


def _parse_ranges(ranges: str) -> List[int]:
    # pages returned 0-based
    selected: List[int] = []
    parts = [p.strip() for p in ranges.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            a, b = part.split("-", 1)
            start = int(a)
            end = int(b)
            for n in range(start, end + 1):
                selected.append(n - 1)
        else:
            selected.append(int(part) - 1)
    # unique and sorted
    return sorted(set(selected))


def split_pdf(input_pdf: str, ranges: str, output_dir: str):
    import os

    os.makedirs(output_dir, exist_ok=True)
    reader = PdfReader(input_pdf)
    idxs = _parse_ranges(ranges)
    for i in idxs:
        if i < 0 or i >= len(reader.pages):
            continue
        writer = PdfWriter()
        writer.add_page(reader.pages[i])
        out_path = os.path.join(output_dir, f"page_{i+1}.pdf")
        with open(out_path, "wb") as f:
            writer.write(f)


def rotate_pages(input_pdf: str, output_pdf: str, degrees: int, pages: Optional[Iterable[int]] = None):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    target = set([p - 1 for p in pages]) if pages else set(range(len(reader.pages)))
    for i, page in enumerate(reader.pages):
        if i in target:
            page.rotate(degrees)
        writer.add_page(page)
    with open(output_pdf, "wb") as f:
        writer.write(f)


def extract_text(input_pdf: str, pages: Optional[Iterable[int]] = None) -> str:
    reader = PdfReader(input_pdf)
    target = set([p - 1 for p in pages]) if pages else set(range(len(reader.pages)))
    chunks: List[str] = []
    for i, page in enumerate(reader.pages):
        if i in target:
            chunks.append(page.extract_text() or "")
    return "\n".join(chunks)


def fill_form(input_pdf: str, output_pdf: str, data: dict, flatten: bool = False):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    if reader.get_fields():
        writer.append(reader)
        writer.update_page_form_field_values(writer.pages, data)
        if flatten:
            for page in writer.pages:
                page.Annots = []
    else:
        for page in reader.pages:
            writer.add_page(page)
    with open(output_pdf, "wb") as f:
        writer.write(f)


def flatten_form(input_pdf: str, output_pdf: str):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    writer.append(reader)
    for page in writer.pages:
        try:
            page.Annots = []
        except Exception:
            pass
    with open(output_pdf, "wb") as f:
        writer.write(f)


def edit_text(
    input_pdf: str,
    output_pdf: str,
    page_num: int,
    old_text: str,
    new_text: str,
    font_name: Optional[str] = None,
    font_size: Optional[float] = None,
    color: Optional[str] = None,
):
    doc = fitz.open(input_pdf)
    page = doc[page_num - 1]  # PyMuPDF pages are 0-indexed

    # Search for the old_text and get its bounding box and properties
    text_instances = page.search_for(old_text)

    if not text_instances:
        print(f"Texto '{old_text}' não encontrado na página {page_num}.")
        doc.save(output_pdf)
        doc.close()
        return

    rect = text_instances[0] # Bounding box of the text

    # Delete the old text by drawing a filled rectangle over it (white color)
    # This is a common workaround for text redaction in PDFs.
    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)

    # Insert the new text. We need to determine the correct position, font, and size.
    # For now, we\\'ll use the top-left corner of the old text\\'s bounding box.
    # A more advanced implementation would handle multi-line text and alignment.
    
    # Use provided font properties or try to guess from the context
    # (guessing is hard, so we\\'ll stick to user-provided or default values for now)
    final_font_name = font_name if font_name else "helv"
    final_font_size = font_size if font_size else 12
    final_color = color if color else "black"

    # Convert color string to RGB tuple for PyMuPDF
    # For simplicity, we\\'ll handle a few common colors. A more robust solution would use a color library.
    color_map = {
        "black": (0, 0, 0),
        "red": (1, 0, 0),
        "green": (0, 1, 0),
        "blue": (0, 0, 1),
        "white": (1, 1, 1),
    }
    text_color = color_map.get(final_color.lower(), (0, 0, 0))

    # Insert the new text
    page.insert_text(rect.tl,
                     new_text,
                     fontname=final_font_name.lower(),
                     fontsize=final_font_size,
                     color=text_color)

    doc.save(output_pdf)
    doc.close()

def delete_pages(
    input_pdf: str,
    output_pdf: str,
    pages_to_delete: List[int],
):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    pages_to_delete_0_indexed = [p - 1 for p in pages_to_delete]

    for i, page in enumerate(reader.pages):
        if i not in pages_to_delete_0_indexed:
            writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)


def reorder_pages(
    input_pdf: str,
    output_pdf: str,
    new_order: List[int],
):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    
    # new_order should be 1-indexed page numbers
    for page_num in new_order:
        if 1 <= page_num <= len(reader.pages):
            writer.add_page(reader.pages[page_num - 1])
        else:
            print(f"Aviso: Número de página inválido na nova ordem: {page_num}. Ignorando.")

    with open(output_pdf, "wb") as f:
        writer.write(f)

def insert_blank_page(
    input_pdf: str,
    output_pdf: str,
    page_num: int,
    width: float = letter[0],
    height: float = letter[1],
):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    # Add pages before the insertion point
    for i in range(page_num - 1):
        if i < len(reader.pages):
            writer.add_page(reader.pages[i])

    # Insert blank page
    writer.add_blank_page(width=width, height=height)
    
    # Add pages after the insertion point
    for i in range(page_num - 1, len(reader.pages)):
        writer.add_page(reader.pages[i])

    with open(output_pdf, "wb") as f:
        writer.write(f)

