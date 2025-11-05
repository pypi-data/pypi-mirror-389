# Video Examination API - Complete Documentation

## Overview
This document describes the **Video Examination API** endpoints that enable the frontend `VideoExaminationAnnotation.vue` component to manage patient examinations within video annotations.

## Issue 3 Resolution Summary

### Problem
The `VideoExaminationViewSet` was missing a `serializer_class` attribute, causing Django REST Framework to throw errors:
```
'VideoExaminationViewSet' should either include a `serializer_class` attribute
```

### Solution Implemented
✅ **Created comprehensive serializers:**
- `VideoExaminationSerializer` - Read-only serializer with nested data
- `VideoExaminationCreateSerializer` - Handles complex creation logic
- `VideoExaminationUpdateSerializer` - Handles partial updates

✅ **Fixed ViewSet:**
- Added `serializer_class = VideoExaminationSerializer`
- Implemented `get_serializer_class()` for action-specific serializers
- Added proper queryset with select_related/prefetch_related
- Implemented filtering by video_id, patient_id, examination_id

✅ **Added missing URL endpoint:**
- `GET /api/video/{video_id}/examinations/` (frontend expects this)
- Alternative: `GET /api/video-examinations/video/{video_id}/` (also works)

---

## API Endpoints

### 1. List All Video Examinations
**Endpoint:** `GET /api/video-examinations/`

**Query Parameters:**
- `video_id` (optional) - Filter by video ID
- `patient_id` (optional) - Filter by patient ID  
- `examination_id` (optional) - Filter by examination type ID

**Response:**
```json
[
  {
    "id": 123,
    "hash": "abc123def456",
    "examination_id": 5,
    "examination_name": "Colonoscopy",
    "video_id": 90,
    "patient_hash": "patient_hash_xyz",
    "date_start": "2024-01-15",
    "date_end": "2024-01-15",
    "findings": [
      {
        "id": 1,
        "finding_id": 42,
        "finding_name": "Polyp",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
]
```

**Example Usage:**
```bash
# Get all video examinations
curl "http://localhost:8000/api/video-examinations/"

# Get examinations for specific video
curl "http://localhost:8000/api/video-examinations/?video_id=90"

# Get examinations for specific patient
curl "http://localhost:8000/api/video-examinations/?patient_id=123"
```

---

### 2. Get Examinations for Specific Video (Frontend Expected)
**Endpoint:** `GET /api/video/{video_id}/examinations/`

This is the primary endpoint expected by `VideoExaminationAnnotation.vue`.

**Path Parameters:**
- `video_id` (required) - ID of the video

**Response:** Same as list endpoint

**Example Usage:**
```bash
# Get examinations for video 90 (frontend pattern)
curl "http://localhost:8000/api/video/90/examinations/"
```

**Alternative Endpoint:**
```bash
# Also works via router action
curl "http://localhost:8000/api/video-examinations/video/90/"
```

---

### 3. Get Single Examination
**Endpoint:** `GET /api/video-examinations/{id}/`

**Path Parameters:**
- `id` (required) - Examination ID

**Response:**
```json
{
  "id": 123,
  "hash": "abc123def456",
  "examination_id": 5,
  "examination_name": "Colonoscopy",
  "video_id": 90,
  "patient_hash": "patient_hash_xyz",
  "date_start": "2024-01-15",
  "date_end": "2024-01-15",
  "findings": []
}
```

**Example Usage:**
```bash
curl "http://localhost:8000/api/video-examinations/123/"
```

---

### 4. Create Video Examination
**Endpoint:** `POST /api/video-examinations/`

**Request Body:**
```json
{
  "video_id": 90,
  "examination_id": 5,
  "date_start": "2024-01-15",
  "date_end": "2024-01-15"
}
```

**Required Fields:**
- `video_id` - Must reference existing VideoFile
- `examination_id` - Must reference existing Examination type

**Optional Fields:**
- `date_start` - Examination start date
- `date_end` - Examination end date

**Response:** 201 Created
```json
{
  "id": 124,
  "hash": "newly_generated_hash",
  "examination_id": 5,
  "examination_name": "Colonoscopy",
  "video_id": 90,
  "patient_hash": "patient_hash_xyz",
  "date_start": "2024-01-15",
  "date_end": "2024-01-15",
  "findings": []
}
```

**Business Logic:**
1. Validates video exists
2. Validates examination type exists
3. Extracts patient from video's `SensitiveMeta.pseudo_patient`
4. Creates or updates PatientExamination linking patient, examination, and video
5. Auto-generates unique hash if not provided

**Error Responses:**
```json
// 400 - Video has no sensitive metadata
{
  "non_field_errors": [
    "Video must have sensitive metadata with patient information"
  ]
}

// 404 - Video not found
{
  "video_id": ["Video with id 999 does not exist"]
}

// 404 - Examination type not found
{
  "examination_id": ["Examination with id 999 does not exist"]
}
```

**Example Usage:**
```bash
curl -X POST "http://localhost:8000/api/video-examinations/" \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": 90,
    "examination_id": 5,
    "date_start": "2024-01-15"
  }'
```

---

### 5. Update Video Examination
**Endpoint:** `PATCH /api/video-examinations/{id}/`

**Path Parameters:**
- `id` (required) - Examination ID to update

**Request Body (all fields optional):**
```json
{
  "examination_id": 6,
  "date_start": "2024-01-16",
  "date_end": "2024-01-16"
}
```

**Response:** 200 OK (same structure as retrieve)

**Example Usage:**
```bash
curl -X PATCH "http://localhost:8000/api/video-examinations/123/" \
  -H "Content-Type: application/json" \
  -d '{
    "examination_id": 6,
    "date_start": "2024-01-16"
  }'
```

---

### 6. Delete Video Examination
**Endpoint:** `DELETE /api/video-examinations/{id}/`

**Path Parameters:**
- `id` (required) - Examination ID to delete

**Response:** 204 No Content
```json
{
  "message": "Examination 123 deleted successfully"
}
```

**Example Usage:**
```bash
curl -X DELETE "http://localhost:8000/api/video-examinations/123/"
```

---

## Database Models

### PatientExamination
```python
class PatientExamination(models.Model):
    patient = ForeignKey("Patient")          # From video.sensitive_meta.pseudo_patient
    examination = ForeignKey("Examination")   # Examination type (Colonoscopy, etc.)
    video = OneToOneField("VideoFile")       # Linked video
    date_start = DateField(null=True)
    date_end = DateField(null=True)
    hash = CharField(unique=True)            # Auto-generated unique identifier
```

### Relationships
```
VideoFile (90)
  └─> SensitiveMeta
       └─> pseudo_patient (Patient)
            └─> PatientExamination
                 ├─> examination (Examination type: Colonoscopy)
                 ├─> video (VideoFile 90) ← One-to-one back reference
                 └─> patient_findings (PatientFinding[])
```

---

## Frontend Integration

### VideoExaminationAnnotation.vue Expected Behavior

#### 1. Load Examinations on Video Selection
```javascript
// Frontend code (line 730)
const response = await axiosInstance.get(r(`video/${selectedVideoId.value}/examinations/`))

// Backend provides:
// GET /api/video/90/examinations/
// Returns: Array of PatientExamination with findings
```

#### 2. Create New Examination
```javascript
// When user annotates a new finding in video
await axiosInstance.post(r('video-examinations/'), {
  video_id: 90,
  examination_id: selectedExamType.value,
  date_start: new Date().toISOString().split('T')[0]
})
```

#### 3. Update Examination
```javascript
// When user modifies examination details
await axiosInstance.patch(r(`video-examinations/${examId}/`), {
  examination_id: newExamType.value
})
```

---

## Testing Commands

### Test with curl
```bash
# 1. Get examinations for video 90 (frontend pattern)
curl "http://localhost:8000/api/video/90/examinations/"

# 2. Get examinations for video 91 (alternative pattern)
curl "http://localhost:8000/api/video-examinations/?video_id=91"

# 3. Create examination for video 90
curl -X POST "http://localhost:8000/api/video-examinations/" \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": 90,
    "examination_id": 1,
    "date_start": "2024-11-04"
  }'

# 4. Update examination
curl -X PATCH "http://localhost:8000/api/video-examinations/1/" \
  -H "Content-Type: application/json" \
  -d '{"date_end": "2024-11-05"}'

# 5. Delete examination
curl -X DELETE "http://localhost:8000/api/video-examinations/1/"
```

### Test with Django shell
```python
from endoreg_db.models import VideoFile, Examination, PatientExamination

# Get video with patient
video = VideoFile.objects.get(id=90)
print(f"Video: {video.uuid}")
print(f"Patient: {video.sensitive_meta.pseudo_patient}")

# Get available examination types
exams = Examination.objects.all()
for exam in exams:
    print(f"ID: {exam.id}, Name: {exam.name}")

# Create examination
from endoreg_db.serializers import VideoExaminationCreateSerializer
serializer = VideoExaminationCreateSerializer(data={
    'video_id': 90,
    'examination_id': 1,
    'date_start': '2024-11-04'
})
if serializer.is_valid():
    patient_exam = serializer.save()
    print(f"Created: {patient_exam}")
else:
    print(f"Errors: {serializer.errors}")
```

---

## Error Handling

### Common Errors

#### 400 Bad Request - Missing video metadata
```json
{
  "non_field_errors": [
    "Video must have sensitive metadata with patient information"
  ]
}
```
**Fix:** Ensure video has been processed and has SensitiveMeta with pseudo_patient.

#### 404 Not Found - Video missing
```json
{
  "video_id": ["Video with id 999 does not exist"]
}
```
**Fix:** Verify video ID exists in database.

#### 404 Not Found - Examination type missing
```json
{
  "examination_id": ["Examination with id 999 does not exist"]
}
```
**Fix:** Use valid examination type ID from `/api/examinations/`.

---

## Migration Path

### For Existing Code Using Old Endpoint
If your code was trying to use `/api/video-examinations/` and failing, no changes needed!  
The endpoint now works correctly with proper serialization.

### For Code Using Custom Video Examination Logic
Replace custom logic with API calls:

**Before:**
```python
# Custom video examination creation
patient_exam = PatientExamination.objects.create(
    patient=video.sensitive_meta.pseudo_patient,
    examination=exam_type,
    video=video
)
```

**After:**
```python
# Use API endpoint
from rest_framework.test import APIClient
client = APIClient()
response = client.post('/api/video-examinations/', {
    'video_id': video.id,
    'examination_id': exam_type.id
})
patient_exam_data = response.json()
```

---

## Performance Considerations

### Optimized Queries
The ViewSet uses optimized querysets:
```python
queryset = PatientExamination.objects.select_related(
    'patient', 'examination', 'video'
).prefetch_related('patient_findings')
```

This prevents N+1 query problems when listing examinations.

### Recommended Pagination
For large datasets, add pagination:
```python
# In settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50
}
```

---

## Future Enhancements

### Planned Features
1. **Timestamp-based examinations** - Link findings to specific video timestamps
2. **Bulk operations** - Create multiple examinations in one request
3. **Export functionality** - Export examination data as CSV/JSON
4. **Filtering improvements** - Filter by date range, examination type, etc.

### API Versioning
Consider API versioning for backwards compatibility:
```
/api/v1/video-examinations/
/api/v2/video-examinations/  # Future version
```

---

## Summary

✅ **Issue 3 RESOLVED:**
- VideoExaminationViewSet now has proper `serializer_class`
- Frontend endpoint `/api/video/{id}/examinations/` works
- Comprehensive CRUD operations implemented
- Proper error handling and validation
- Optimized database queries

**Status:** Ready for production use with VideoExaminationAnnotation.vue frontend component.
