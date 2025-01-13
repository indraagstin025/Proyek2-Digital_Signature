from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import RectangleObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
import io

def add_qr_to_pdf(pdf_path, qr_path, output_path, x, y, width, height, target_page=0):
    try:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for page_num, page in enumerate(reader.pages):
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)

            print(f"Dimensi halaman PDF: width={page_width}, height={page_height}")

            if page_num == target_page:
                adjusted_x = max(0, min(x, page_width - width))
                adjusted_y = max(0, min(page_height - y - height, page_height - height))

                print(f"Posisi QR Code: x={adjusted_x}, y={adjusted_y}, width={width}, height={height}")
                
                # Tambahkan QR Code ke halaman
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=(page_width, page_height))
                can.drawImage(qr_path, adjusted_x, adjusted_y, width=width, height=height)
                can.save()

                packet.seek(0)
                new_pdf = PdfReader(packet)
                page.merge_page(new_pdf.pages[0])

            writer.add_page(page)

        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        print(f"Dokumen bertanda tangan berhasil disimpan di: {output_path}")
        return True
    except Exception as e:
        print(f"Error saat menambahkan QR ke PDF: {e}")
        return False
