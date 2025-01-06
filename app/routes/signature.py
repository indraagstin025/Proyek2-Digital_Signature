from flask import Blueprint, request, jsonify
import pyseto
from pyseto import Key
import datetime
from app.models import db, Signature

# Blueprint untuk rute tanda tangan digital
signature_bp = Blueprint('signature', __name__, url_prefix='/signature')

# Kunci privat dan publik (seharusnya disimpan dengan aman)
PRIVATE_KEY = b"""-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEILTL+0PfTOIQcn2VPkpxMwf6Gbt9n4UEFDjZ4RuUKjd0
-----END PRIVATE KEY-----"""
PUBLIC_KEY = b"""-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAHrnbu7wEfAP9cGBOAHHwmH4Wsot1ciXBHwBBXQ4gsaI=
-----END PUBLIC KEY-----"""

private_key = Key.new(version=4, purpose="public", key=PRIVATE_KEY)
public_key = Key.new(version=4, purpose="public", key=PUBLIC_KEY)

@signature_bp.route('/create', methods=['POST'])
def create_signature():
    try:
        data = request.json
        if not data or 'document' not in data:
            return jsonify({'error': 'Document data is required'}), 400

        # Buat payload dengan timestamp
        payload = {
            'document': data['document'],
            'timestamp': datetime.datetime.utcnow().isoformat()
        }

        # Encode payload menjadi token PASETO
        token = pyseto.encode(private_key, payload)
        
        new_signature = Signature(document=data['document'], token=token)
        db.session.add(new_signature)
        db.session.commit()

        return jsonify({'token': token}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@signature_bp.route('/verify', methods=['POST'])
def verify_signature():
    try:
        data = request.json
        if not data or 'token' not in data:
            return jsonify({'error': 'Token is required'}), 400

        # Decode dan verifikasi token PASETO
        decoded = pyseto.decode(public_key, data['token'])
        payload = decoded.payload

        return jsonify({'verified': True, 'payload': payload}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
    

