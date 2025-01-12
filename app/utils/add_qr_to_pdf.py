from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import RectangleObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
import io

def add_qr_to_pdf(pdf_path, qr_path, output_path, x, y, width, height):
    try:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for page in reader.pages:
            packet = io.BytesIO()
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)

            # Konversi koordinat
            adjusted_x = x
            adjusted_y = page_height - y - height

            can = canvas.Canvas(packet, pagesize=(page_width, page_height))
            can.drawImage(qr_path, adjusted_x, adjusted_y, width=width, height=height)
            can.save()

            packet.seek(0)
            new_pdf = PdfReader(packet)
            page.merge_page(new_pdf.pages[0])
            writer.add_page(page)

        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        return True
    except Exception as e:
        print(f"Error saat menambahkan QR ke PDF: {e}")
        return False
