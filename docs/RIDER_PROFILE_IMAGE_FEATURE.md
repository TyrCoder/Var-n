# Rider Profile Image Feature

## Overview
Riders can now upload and manage their profile images directly from the dashboard.

## Features Added

### 1. Profile Image Upload
- **Location**: Profile section in Rider Dashboard
- **File Types**: PNG, JPG, JPEG, GIF, WEBP
- **Max Size**: 5MB
- **Storage**: `/static/images/riders/`

### 2. Display Locations
- **Topbar**: Small circular avatar (36x36px) - clickable to go to profile
- **Profile Section**: Large circular avatar (100x100px) with camera icon overlay

### 3. Database Changes
- **Table**: `riders`
- **New Column**: `profile_image` VARCHAR(500)
- **Migration File**: `migrations/add_rider_profile_image.sql`

## How to Use

### For Riders:
1. Log in to your Rider Dashboard
2. Click on "Profile" in the sidebar (or click your avatar in the topbar)
3. Hover over your profile picture
4. Click the camera icon (📷) at the bottom-right of the image
5. Select an image file from your device
6. The image will upload automatically and update immediately

### For Developers:

#### Run the Migration:
```sql
-- Execute in your MySQL database
SOURCE migrations/add_rider_profile_image.sql;

-- Or manually:
ALTER TABLE riders ADD COLUMN profile_image VARCHAR(500) AFTER service_area;
```

#### API Endpoint:
- **URL**: `/api/rider/upload-profile-image`
- **Method**: POST
- **Auth**: Requires rider session
- **Content-Type**: multipart/form-data
- **Parameters**: 
  - `profile_image` (file): Image file to upload

**Response**:
```json
{
  "success": true,
  "message": "Profile image uploaded successfully",
  "image_url": "/static/images/riders/rider_1_1234567890.jpg"
}
```

## Features

### Image Validation
- ✅ File type checking (only images allowed)
- ✅ File size limit (5MB max)
- ✅ Unique filename generation (prevents conflicts)
- ✅ Automatic directory creation

### User Experience
- ✅ Instant preview before upload
- ✅ Graceful error handling
- ✅ Default placeholder if no image
- ✅ Fallback SVG if image fails to load
- ✅ Success/error notifications

### Security
- ✅ Session authentication required
- ✅ Role verification (rider only)
- ✅ File extension validation
- ✅ Stored outside public root initially

## File Structure
```
static/
└── images/
    └── riders/
        ├── rider_1_1234567890.jpg
        ├── rider_2_1234567891.png
        └── ...
```

## Troubleshooting

### Image Not Uploading
1. Check file size (must be < 5MB)
2. Verify file type (PNG, JPG, JPEG, GIF, WEBP only)
3. Ensure `/static/images/riders/` directory exists and is writable
4. Check browser console for error messages

### Image Not Displaying
1. Verify the image path in the database
2. Check file exists in `/static/images/riders/`
3. Ensure proper file permissions
4. Clear browser cache

### Migration Issues
```sql
-- Check if column exists
DESCRIBE riders;

-- If column exists, skip migration
-- If not, run migration file
```

## Future Enhancements
- [ ] Image cropping before upload
- [ ] Multiple image size variants (thumbnail, medium, large)
- [ ] Image compression
- [ ] Remove old image when uploading new one
- [ ] Profile completion percentage
