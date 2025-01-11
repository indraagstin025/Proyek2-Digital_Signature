import qrcode
import logging
import os

def generate_qr_code(data, output_path, base_url=None):
    """
    Membuat QR Code berdasarkan data yang diberikan.
    :param data: Data atau token untuk QR Code
    :param output_path: Lokasi penyimpanan QR Code
    :param base_url: URL dasar untuk validasi QR Code
    """
    try:
        # Validasi input
        if not isinstance(data, str) or not data.strip():
            raise ValueError("Data untuk QR Code harus berupa string yang valid.")
        if base_url and not base_url.startswith("http"):
            raise ValueError("Base URL harus berupa URL yang valid.")

        # Jika base_url diberikan, buat URL untuk QR Code
        if base_url:
            data = f"{base_url}?token={data}"
            logging.info(f"URL QR Code yang dibuat: {data}")
        
        # Validasi output_path
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logging.info(f"Folder untuk QR Code dibuat: {output_dir}")

        # Membuat QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Simpan gambar QR Code
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_path)
        logging.info(f"QR Code berhasil disimpan di: {output_path}")
        logging.info(f"Data QR Code: {data}")
    except Exception as e:
        logging.error(f"Gagal membuat QR Code: {e}")
        raise
