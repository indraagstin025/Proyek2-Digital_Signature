from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

def add_signature_to_pdf(input_pdf, signature_image, output_pdf, position):
    """
    Menambahkan tanda tangan ke dokumen PDF pada posisi tertentu.
    """
    # Membaca PDF asli
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    # Membuat halaman baru dengan tanda tangan menggunakan ReportLab
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.drawImage(BytesIO(signature_image), position['x'], position['y'], width=200, height=100)  # Gunakan posisi
    can.save()

    # Gabungkan halaman tanda tangan dengan halaman PDF asli
    packet.seek(0)
    signature_page = PdfReader(packet).pages[0]
    for page in reader.pages:
        page.merge_page(signature_page)
        writer.add_page(page)

    # Simpan PDF hasil
    with open(output_pdf, 'wb') as output_file:
        writer.write(output_file)
