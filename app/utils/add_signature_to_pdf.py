from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import logging

def add_signature_to_pdf(pdf_path, qr_path, output_path, position):
    try:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        x, y, width, height = position

        for page in reader.pages:
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.drawImage(qr_path, x, y, width=width, height=height)
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


