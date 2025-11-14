import re

# Read template and escape all CSS curly braces for f-string
with open('certificate_template_final.txt', 'r') as f:
    template = f.read()

# Escape all { and } in CSS but preserve the placeholders
template_escaped = template.replace('{', '{{').replace('}', '}}')

# Restore the placeholders
template_escaped = template_escaped.replace('{{HOSPITAL_NAME}}', '{hospital.name}')
template_escaped = template_escaped.replace('{{DATE_UPPER}}', "{timezone.now().strftime('%d %B %Y').upper()}")
template_escaped = template_escaped.replace('{{CERT_ID}}', "PHB-CERT-{hospital.id:04d}-{timezone.now().strftime('%Y%m%d')}")
template_escaped = template_escaped.replace('{{REG_NUM}}', '{hospital.registration_number}')
template_escaped = template_escaped.replace('{{LOCATION}}', '{hospital.city}, {hospital.state}')

# Create the new function
new_function = '''def generate_hospital_certificate_pdf(hospital):
    """
    Generate a PDF certificate for hospital approval with elegant professional design

    Args:
        hospital: Hospital model instance

    Returns:
        BytesIO: PDF file in memory, or None if generation fails
    """
    try:
        # Create elegant certificate HTML template with Google Fonts for beautiful cursive
        certificate_html = f"""''' + template_escaped + '''"""

        # Generate PDF using WeasyPrint for better font support
        pdf_buffer = BytesIO()
        HTML(string=certificate_html).write_pdf(pdf_buffer)
        
        pdf_buffer.seek(0)
        logger.info(f"✅ PDF certificate generated for {hospital.name}")
        return pdf_buffer

    except Exception as e:
        logger.error(f"❌ Failed to generate PDF certificate: {str(e)}")
        return None

'''

# Read email.py
with open('api/utils/email.py', 'r') as f:
    content = f.read()

# Replace the function
pattern = r'def generate_hospital_certificate_pdf\(hospital\):.*?(?=\ndef [a-z_]|\Z)'
new_content = re.sub(pattern, new_function, content, flags=re.DOTALL)

# Write back
with open('api/utils/email.py', 'w') as f:
    f.write(new_content)

print('✅ Certificate function fixed with properly escaped CSS!')
