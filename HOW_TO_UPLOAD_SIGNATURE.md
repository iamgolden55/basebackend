# How to Upload Your Signature for Hospital Certificates

## Setup Complete ✅

The signature upload system is now ready! Here's how to use it:

### 1. Access Django Admin Panel
```
URL: http://localhost:8000/admin/
```
Login with your superuser credentials.

### 2. Navigate to Admin Signatures
- In the admin panel, look for "**ADMIN MODELS**" section
- Click on "**Admin Signatures**"

### 3. Add Your Signature
Click "**Add Admin Signature**" button and fill in:

- **Name**: PHB Administration (or your preferred name)
- **Signature image**: Click "Choose File" and upload your signature
  - Format: PNG with transparent background (recommended)
  - JPG also works
- **Is active**: ✓ Check this box (ensures this signature is used)

### 4. Save
Click the "**Save**" button

## Testing

After uploading, test by approving a hospital:
1. Go to admin panel → Hospitals
2. Approve a hospital
3. Check the certificate PDF - your signature will appear above "PHB Administration"

## Features

- ✅ Only one active signature at a time
- ✅ Preview your signature in the admin panel
- ✅ Easy to update or change
- ✅ Automatic integration with hospital approval certificates

## Certificate Design
- **Black "Certificate" title** ✓
- **Your signature** (once uploaded)
- **Elegant cursive fonts**
- **Professional layout**

## Need Help?

If the signature doesn't appear in the certificate:
1. Check that "Is active" is checked
2. Verify the image uploaded successfully
3. Check server logs for any errors

The signature will be embedded in every new hospital approval certificate automatically!
