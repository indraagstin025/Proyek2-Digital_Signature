from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import io
import os

def add_qr_to_pdf(pdf_path, qr_path, output_path, x, y, width, height, target_page=0, canvas_width=None, canvas_height=None):
    try:
        # Membaca PDF
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for page_num, page in enumerate(reader.pages):
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)

            if page_num == target_page:
                # Perhitungan skala berdasarkan ukuran canvas frontend (jika diberikan)
                if canvas_width and canvas_height:
                    scale_x = page_width / canvas_width
                    scale_y = page_height / canvas_height
                    # Transformasi koordinat dan dimensi ke skala backend
                    adjusted_x = x * scale_x
                    adjusted_y = (canvas_height - y - height) * scale_y
                    adjusted_width = width * scale_x
                    adjusted_height = height * scale_y
                else:
                    # Gunakan koordinat langsung jika tidak ada informasi skala
                    adjusted_x = x
                    adjusted_y = page_height - y - height
                    adjusted_width = width
                    adjusted_height = height
                    
                if not canvas_width:
                    canvas_width = 595.28  # Lebar A4
                if not canvas_height:
                    canvas_height = 841.89  # Tinggi A4


                # Validasi posisi agar tetap dalam batas halaman PDF
                adjusted_x = max(0, min(adjusted_x, page_width - adjusted_width))
                adjusted_y = max(0, min(adjusted_y, page_height - adjusted_height))

                # Debug informasi posisi
                print(f"Target Page: {target_page}, x: {adjusted_x}, y: {adjusted_y}, "
                      f"width: {adjusted_width}, height: {adjusted_height}")

                # Membuat canvas untuk QR code
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=(page_width, page_height))
                can.drawImage(qr_path, adjusted_x, adjusted_y, width=adjusted_width, height=adjusted_height)
                can.save()

                # Gabungkan halaman PDF dengan QR Code
                packet.seek(0)
                new_pdf = PdfReader(packet)
                page.merge_page(new_pdf.pages[0])

            writer.add_page(page)

        # Simpan hasil PDF
        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        print(f"Dokumen bertanda tangan berhasil disimpan: {output_path}")
        return True
    except Exception as e:
        print(f"Kesalahan saat menambahkan QR Code: {e}")
        return False
