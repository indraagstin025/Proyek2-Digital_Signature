from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import RectangleObject
from PIL import Image

def add_qr_to_pdf(pdf_path, qr_image_path, output_path):
    """
    Menambahkan QR Code ke sudut kanan bawah halaman terakhir dokumen PDF.
    :param pdf_path: Path dokumen PDF asli
    :param qr_image_path: Path file gambar QR Code
    :param output_path: Path untuk menyimpan PDF baru dengan QR Code
    """
    try:
        # Baca PDF asli
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # Baca QR Code sebagai gambar
        qr_image = Image.open(qr_image_path)

        # Konversi QR Code ke objek byte untuk ditambahkan ke PDF
        for page in reader.pages:
            writer.add_page(page)

        # Tentukan posisi QR Code (kanan bawah)
        qr_width = 100  # Lebar QR Code
        qr_height = 100  # Tinggi QR Code
        page_width = writer.pages[-1].media_box.width
        page_height = writer.pages[-1].media_box.height
        qr_position = RectangleObject([
            page_width - qr_width - 20,  # Posisi X (kanan bawah)
            20,                          # Posisi Y (bawah)
            page_width - 20,             # Lebar
            20 + qr_height               # Tinggi
        ])

        # Tambahkan QR Code ke halaman terakhir
        writer.pages[-1].add_annotation({
            "/Type": "/Annot",
            "/Subtype": "/Stamp",
            "/Rect": qr_position,
            "/NM": "QR Code",
            "/Contents": qr_image.tobytes()
        })

        # Simpan PDF baru dengan QR Code
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        print(f"PDF dengan QR Code berhasil disimpan di: {output_path}")
    except Exception as e:
        print(f"Gagal menambahkan QR Code ke PDF: {e}")
