"""
Clean certificate PDF generation function for PHB hospital approval
This is the updated elegant design with ornate decorative corners
"""

from io import BytesIO
from xhtml2pdf import pisa
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def generate_hospital_certificate_pdf(hospital):
    """
    Generate a PDF certificate for hospital approval with elegant professional design

    Args:
        hospital: Hospital model instance

    Returns:
        BytesIO: PDF file in memory, or None if generation fails
    """
    try:
        # Create elegant certificate HTML template with ornate decorative corners
        certificate_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PHB Hospital Certificate of Approval</title>
    <style>
        @page {{
            size: A4 landscape;
            margin: 0;
        }}

        body {{
            font-family: Georgia, 'Times New Roman', serif;
            margin: 0;
            padding: 0;
            background-color: #f0f0f0;
        }}

        .certificate {{
            width: 1000px;
            height: 700px;
            background-color: #fdfaf7;
            border: 10px solid #1a5c3a;
            position: relative;
            margin: 0 auto;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
        }}

        .inner-border {{
            position: absolute;
            top: 30px;
            left: 30px;
            right: 30px;
            bottom: 30px;
            border: 2px solid #d4af37;
            padding: 40px;
            box-sizing: border-box;
        }}

        /* Decorative ornate corners */
        .corner {{
            position: absolute;
            width: 100px;
            height: 100px;
        }}

        .corner.top-left {{
            top: 15px;
            left: 15px;
            border-top: 4px solid #d4af37;
            border-left: 4px solid #d4af37;
        }}

        .corner.top-left::before {{
            content: '✤';
            position: absolute;
            top: -8px;
            left: -8px;
            font-size: 24px;
            color: #d4af37;
        }}

        .corner.top-right {{
            top: 15px;
            right: 15px;
            border-top: 4px solid #d4af37;
            border-right: 4px solid #d4af37;
        }}

        .corner.top-right::before {{
            content: '✤';
            position: absolute;
            top: -8px;
            right: -8px;
            font-size: 24px;
            color: #d4af37;
        }}

        .corner.bottom-left {{
            bottom: 15px;
            left: 15px;
            border-bottom: 4px solid #d4af37;
            border-left: 4px solid #d4af37;
        }}

        .corner.bottom-left::before {{
            content: '✤';
            position: absolute;
            bottom: -8px;
            left: -8px;
            font-size: 24px;
            color: #d4af37;
        }}

        .corner.bottom-right {{
            bottom: 15px;
            right: 15px;
            border-bottom: 4px solid #d4af37;
            border-right: 4px solid #d4af37;
        }}

        .corner.bottom-right::before {{
            content: '✤';
            position: absolute;
            bottom: -8px;
            right: -8px;
            font-size: 24px;
            color: #d4af37;
        }}

        /* Header section */
        .header {{
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #d4af37;
        }}

        .seal-container {{
            margin: 0 auto 12px;
            width: 80px;
            height: 80px;
            border: 4px solid #1a5c3a;
            border-radius: 50%;
            background: linear-gradient(135deg, #2d5f3d 0%, #1a5c3a 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}

        .medical-symbol {{
            font-size: 36px;
            color: #d4af37;
        }}

        .org-name {{
            font-size: 20px;
            font-weight: bold;
            color: #1a5c3a;
            letter-spacing: 4px;
            text-transform: uppercase;
            margin: 8px 0 5px;
        }}

        .org-subtitle {{
            font-size: 11px;
            color: #555;
            font-style: italic;
            letter-spacing: 1px;
        }}

        /* Certificate title */
        .cert-title {{
            font-family: 'Brush Script MT', cursive, Georgia, serif;
            font-size: 72px;
            color: #1a5c3a;
            text-align: center;
            margin: 15px 0 5px;
            line-height: 1;
            font-weight: normal;
        }}

        .cert-subtitle {{
            font-size: 14px;
            color: #666;
            text-align: center;
            font-style: italic;
            margin-bottom: 20px;
            letter-spacing: 3px;
            text-transform: uppercase;
        }}

        /* Body content */
        .body {{
            text-align: center;
            padding: 0 50px;
        }}

        .presented-to {{
            font-size: 13px;
            color: #666;
            font-style: italic;
            margin-bottom: 12px;
        }}

        .recipient-name {{
            font-family: 'Brush Script MT', cursive, Georgia, serif;
            font-size: 42px;
            font-weight: normal;
            color: #1a5c3a;
            margin: 12px 0;
            padding: 8px 25px;
            border-bottom: 2px solid #d4af37;
            display: inline-block;
            max-width: 85%;
        }}

        .description {{
            font-size: 12px;
            color: #444;
            line-height: 1.6;
            margin: 18px auto;
            max-width: 700px;
        }}

        .verification-stamp {{
            background: linear-gradient(135deg, #1a5c3a 0%, #2d5f3d 100%);
            color: #d4af37;
            padding: 6px 18px;
            border-radius: 25px;
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 2px;
            text-transform: uppercase;
            display: inline-block;
            margin: 12px 0;
            box-shadow: 0 3px 8px rgba(0,0,0,0.2);
        }}

        /* Details grid */
        .details-grid {{
            margin: 18px auto;
            max-width: 650px;
            border: 1px solid #e0e0e0;
            background: #fafafa;
        }}

        .detail-row {{
            display: flex;
            border-bottom: 1px solid #e0e0e0;
        }}

        .detail-row:last-child {{
            border-bottom: none;
        }}

        .detail-label {{
            flex: 0 0 40%;
            padding: 6px 12px;
            font-size: 10px;
            font-weight: bold;
            color: #555;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            text-align: right;
            background: #f0f0f0;
        }}

        .detail-value {{
            flex: 1;
            padding: 6px 12px;
            font-size: 11px;
            color: #333;
            border-left: 1px solid #e0e0e0;
        }}

        /* Footer signatures */
        .footer {{
            margin-top: 25px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            padding: 0 40px;
        }}

        .signature-block {{
            text-align: center;
            flex: 1;
        }}

        .signature-line {{
            width: 160px;
            height: 1px;
            background: #888;
            margin: 25px auto 6px;
        }}

        .signature-title {{
            font-size: 10px;
            font-weight: bold;
            color: #333;
            margin: 4px 0;
        }}

        .signature-name {{
            font-size: 9px;
            color: #666;
        }}

        /* Certificate number */
        .cert-number {{
            position: absolute;
            bottom: 20px;
            right: 40px;
            font-size: 8px;
            color: #999;
            text-align: right;
            line-height: 1.4;
        }}
    </style>
</head>
<body>
    <div class="certificate">
        <div class="inner-border">
            <!-- Decorative ornate corners -->
            <div class="corner top-left"></div>
            <div class="corner top-right"></div>
            <div class="corner bottom-left"></div>
            <div class="corner bottom-right"></div>

            <!-- Header -->
            <div class="header">
                <div class="seal-container">
                    <div class="medical-symbol">⚕</div>
                </div>
                <div class="org-name">PHB</div>
                <div class="org-subtitle">Public Health Bureau - Federal Republic of Nigeria</div>
            </div>

            <!-- Certificate Title -->
            <div class="cert-title">Certificate</div>
            <div class="cert-subtitle">of Approval</div>

            <!-- Body -->
            <div class="body">
                <div class="presented-to">This certificate is proudly presented to</div>

                <div class="recipient-name">{hospital.name}</div>

                <div class="description">
                    In recognition of successfully completing the comprehensive registration and verification
                    process with the Public Health Bureau (PHB). This hospital has met all required standards
                    and is hereby authorized as a verified member of the PHB Healthcare Network, with full
                    access to the Electronic Health Records System, Electronic Prescription Service, and all
                    integrated healthcare platform services.
                </div>

                <div class="verification-stamp">✓ Verified & Approved</div>

                <!-- Hospital Details -->
                <div class="details-grid">
                    <div class="detail-row">
                        <div class="detail-label">Registration Number:</div>
                        <div class="detail-value">{hospital.registration_number}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Facility Type:</div>
                        <div class="detail-value">{hospital.get_hospital_type_display()}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Location:</div>
                        <div class="detail-value">{hospital.city}, {hospital.state}, {hospital.country}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Approval Date:</div>
                        <div class="detail-value">{timezone.now().strftime('%B %d, %Y')}</div>
                    </div>
                </div>
            </div>

            <!-- Footer Signatures -->
            <div class="footer">
                <div class="signature-block">
                    <div class="signature-line"></div>
                    <div class="signature-title">Authorized Signature</div>
                    <div class="signature-name">PHB Administration Team</div>
                </div>

                <div class="signature-block">
                    <div class="signature-line"></div>
                    <div class="signature-title">Date of Issue</div>
                    <div class="signature-name">{timezone.now().strftime('%d %B %Y')}</div>
                </div>
            </div>

            <div class="cert-number">
                Certificate ID: PHB-CERT-{hospital.id:04d}-{timezone.now().strftime('%Y%m%d')}<br/>
                Verify at: https://phb.ng/verify/{hospital.registration_number}
            </div>
        </div>
    </div>
</body>
</html>
"""

        # Generate PDF
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(
            certificate_html,
            dest=pdf_buffer
        )

        if pisa_status.err:
            logger.error(f"PDF generation failed for hospital {hospital.name}")
            return None

        pdf_buffer.seek(0)
        logger.info(f"✅ PDF certificate generated for {hospital.name}")
        return pdf_buffer

    except Exception as e:
        logger.error(f"❌ Failed to generate PDF certificate: {str(e)}")
        return None
