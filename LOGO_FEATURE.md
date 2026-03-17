# Dynamic Logo Feature

## Overview
The dynamic logo feature allows administrators to upload and manage the store logo through the admin panel. The logo is displayed consistently across the entire website.

## Backend Implementation

### API Endpoints

#### Upload Logo
```http
POST /api/v1/settings/store/logo
Authorization: Bearer {admin_token}
Content-Type: multipart/form-data

Form Data:
- logo: File (PNG, JPG, JPEG, WEBP)
```

**Response:**
```json
{
  "message": "Logo uploaded successfully",
  "logo_url": "/uploads/logos/logo_uuid.png"
}
```

#### Delete Logo
```http
DELETE /api/v1/settings/store/logo
Authorization: Bearer {admin_token}
```

**Response:**
```json
{
  "message": "Logo deleted successfully"
}
```

### File Storage

#### Directory Structure
```
backend/uploads/
├── products/          # Product images
└── logos/            # Store logos
    └── logo_*.{ext}  # Uploaded logo files
```

#### Logo Processing
- **Max dimensions:** 400x200px (optimized for headers)
- **Supported formats:** PNG, JPG, JPEG, WEBP
- **Max file size:** 5MB
- **Transparency:** Preserved for PNG files
- **Compression:** JPEG quality 90%, PNG optimized

### Database Storage
Logo URLs are stored in the `settings` table:
```sql
INSERT INTO settings (category, key, value, data_type) 
VALUES ('store', 'store_logo_url', '/uploads/logos/logo_uuid.png', 'string');
```

## Frontend Integration

### Usage in Components
```tsx
// Header Component
{settings?.store_logo_url ? (
  <img src={settings.store_logo_url} alt="Store Logo" />
) : (
  <div>Default Logo Placeholder</div>
)}
```

### Admin Interface
- Location: Admin Settings → Store Settings
- Features:
  - File upload with preview
  - Current logo display
  - Remove logo option
  - File validation feedback

## File Management

### Automatic Cleanup
- Old logo files are automatically deleted when new logos are uploaded
- File deletion is handled when logo settings are removed

### URL Generation
```javascript
// Logo URLs are served as static files
const logoUrl = "/uploads/logos/logo_uuid.png"
// Full URL: https://your-domain.com/uploads/logos/logo_uuid.png
```

## Security Features

### Admin-Only Access
- Upload/delete operations require admin authentication
- Public endpoints only return logo URLs, not upload functionality

### File Validation
- File type validation (image files only)
- File size limits (5MB max)
- Image processing validation
- Automatic directory creation with proper permissions

## Testing

### Manual Testing
1. Login as admin
2. Go to Admin Settings → Store Settings
3. Upload a logo file
4. Verify logo appears in header/footer
5. Test logo removal

### API Testing
Use the provided `test_logo_endpoints.py` script:
```bash
python test_logo_endpoints.py
```

## Troubleshooting

### Common Issues

#### Logo not appearing
- Check file permissions in `/uploads/logos/`
- Verify logo URL in settings database
- Check browser cache

#### Upload failures
- Verify file size is under 5MB
- Check file format is supported
- Ensure admin authentication

#### File not found errors
- Check uploads directory exists
- Verify Railway mount path configuration
- Check file path in database matches actual file

### Development Tips
- Logo files are served as static files via FastAPI
- URLs are relative to the uploads mount point
- Frontend components handle logo fallbacks gracefully 