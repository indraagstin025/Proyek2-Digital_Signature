import qrcode
import logging

def generate_qr_code(data, output_path):
    """
    Fungsi untuk membuat QR Code berdasarkan data yang diberikan.
    :param data: Data untuk QR Code
    :param output_path: Lokasi file untuk menyimpan QR Code
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Buat gambar QR Code dan simpan ke file
    img = qr.make_image(fill="black", back_color="white")
    img.save(output_path)
    logging.info(f"QR Code berhasil disimpan di: {output_path}")
