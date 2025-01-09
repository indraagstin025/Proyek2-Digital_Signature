import qrcode
import os

def generate_qr_code(data, output_folder, filename):
    """Generate QR Code dari data dan simpan sebagai file PNG."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)
    
    if len(data) > 1000:  # Contoh batas panjang
        raise ValueError("Data terlalu besar untuk QR Code.")


    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    output_path = os.path.join(output_folder, f"{filename}.png")
    img.save(output_path)
    return output_path
