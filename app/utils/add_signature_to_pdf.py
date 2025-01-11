from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

def add_signature_to_pdf(pdf_path, signature_path, output_path, x=50, y=50):
    """
    Menambahkan tanda tangan ke dokumen PDF.

    :param pdf_path: Path ke dokumen PDF asli.
    :param signature_path: Path ke gambar tanda tangan.
    :param output_path: Path untuk menyimpan PDF baru dengan tanda tangan.
    :param x: Koordinat X untuk gambar tanda tangan.
    :param y: Koordinat Y untuk gambar tanda tangan.
    """
    # Baca PDF asli
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    # Tambahkan tanda tangan ke halaman pertama
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.drawImage(signature_path, x, y, width=200, height=100)  # Atur ukuran tanda tangan
    can.save()

    # Gabungkan tanda tangan ke PDF asli
    packet.seek(0)
    overlay = PdfReader(packet)
    for page in reader.pages:
        page.merge_page(overlay.pages[0])  # Gabungkan dengan tanda tangan
        writer.add_page(page)

    # Simpan hasil PDF baru
    with open(output_path, "wb") as f_out:
        writer.write(f_out)
