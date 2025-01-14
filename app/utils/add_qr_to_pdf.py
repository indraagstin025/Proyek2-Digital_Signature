from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import io
import os
import logging

def add_qr_to_pdf(pdf_path, qr_path, output_path, x, y, width, height, target_page=0, canvas_width=None, canvas_height=None):
    try:
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        # Validasi file dan path
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"File PDF tidak ditemukan: {pdf_path}")
        if not os.path.exists(qr_path):
            raise FileNotFoundError(f"File QR Code tidak ditemukan: {qr_path}")

        # Validasi ukuran QR Code
        MIN_SIZE = 50  # Minimum ukuran (px)
        MAX_SIZE = 1000  # Maksimum ukuran (px)

        if width < MIN_SIZE or height < MIN_SIZE:
            raise ValueError(f"Ukuran QR Code terlalu kecil. Minimum adalah {MIN_SIZE}px x {MIN_SIZE}px.")
        if width > MAX_SIZE or height > MAX_SIZE:
            raise ValueError(f"Ukuran QR Code terlalu besar. Maksimum adalah {MAX_SIZE}px x {MAX_SIZE}px.")

        # Membaca PDF
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # Pastikan target page valid
        if target_page < 0 or target_page >= len(reader.pages):
            raise ValueError(f"Halaman target {target_page} tidak valid untuk dokumen ini.")

        for page_num, page in enumerate(reader.pages):
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)

            if page_num == target_page:
                # Perhitungan skala berdasarkan ukuran canvas frontend (jika diberikan)
                if canvas_width and canvas_height:
                    scale_x = page_width / canvas_width
                    scale_y = page_height / canvas_height
                    adjusted_x = x * scale_x
                    adjusted_y = (canvas_height - y - height) * scale_y
                    adjusted_width = width * scale_x
                    adjusted_height = height * scale_y
                else:
                    adjusted_x = x
                    adjusted_y = page_height - y - height
                    adjusted_width = width
                    adjusted_height = height

                # Validasi posisi agar tetap dalam batas halaman PDF
                adjusted_x = max(0, min(adjusted_x, page_width - adjusted_width))
                adjusted_y = max(0, min(adjusted_y, page_height - adjusted_height))

                logging.info(f"Menambahkan QR Code pada halaman {target_page} dengan koordinat "
                             f"x: {adjusted_x}, y: {adjusted_y}, width: {adjusted_width}, height: {adjusted_height}")

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

        logging.info(f"Dokumen bertanda tangan berhasil disimpan: {output_path}")
        return True
    except Exception as e:
        logging.error(f"Kesalahan saat menambahkan QR Code: {e}", exc_info=True)
        return False
