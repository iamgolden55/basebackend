import re
import os

# Read the current email.py
with open('/Users/new/Newphb/basebackend/api/utils/email.py', 'r') as f:
    content = f.read()

# Find the certificate function
pattern = r'(def generate_hospital_certificate_pdf\(hospital\):.*?""".*?try:)'

replacement = r'''\1
        # Load signature image if available
        import base64
        signature_path = os.path.join(settings.BASE_DIR, 'media', 'signatures', 'admin_signature.png')
        signature_base64 = ''
        
        if os.path.exists(signature_path):
            with open(signature_path, 'rb') as sig_file:
                signature_base64 = base64.b64encode(sig_file.read()).decode('utf-8')
                logger.info(f"✍️ Admin signature loaded for certificate")
        else:
            logger.warning(f"⚠️ Signature not found at {signature_path}")
'''

# Apply the replacement
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open('/Users/new/Newphb/basebackend/api/utils/email.py', 'w') as f:
    f.write(new_content)

print('✅ Signature loading code added')
