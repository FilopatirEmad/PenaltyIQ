# API Documentation

The PenaltyIQ backend exposes a set of RESTful endpoints built with FastAPI. This document outlines the primary analysis endpoint utilized by the Flutter application.

## Core Endpoint

### `POST /api/v1/analyze`

Processes an uploaded video payload, extracting biomechanical features and generating a structured coaching report.

**Content-Type:** `multipart/form-data`

#### Request Parameters
| Name | Type | Description |
| :--- | :--- | :--- |
| `video` | `File` | The raw `.mp4` or `.mov` byte stream captured by the user. |
| `zone_id` | `String` | The target area of the goal the player was aiming for (e.g., `"T1"`, `"B4"`). Used to select the correct IK priors. |

#### Response Format (JSON)
The endpoint returns a structured `AnalysisResponse` object containing the overall technique score, status levels, and a breakdown of coaching cues per joint.

```json
{
  "success": true,
  "data": {
    "score": 85,
    "level": "Pro",
    "breakdown": {
      "trunk_inclination": 92,
      "support_knee": 88,
      "hip_flexion": 80,
      "knee_flexion": 75
    },
    "coaching_items": [
      {
        "variable": "trunk_inclination",
        "label": "Trunk Inclination at Contact",
        "measured_deg": 12.4,
        "target_deg": 10.0,
        "delta_deg": 2.4,
        "status": "OPTIMAL",
        "cue": "Trunk inclination at contact is optimal for this zone. Your body lean is correctly positioned for the target height."
      },
      {
        "variable": "hip_flexion",
        "label": "Hip Extension (Backswing)",
        "measured_deg": -15.2,
        "target_deg": -25.0,
        "delta_deg": 9.8,
        "status": "NEEDS_WORK",
        "cue": "Your hip backswing is insufficient. Drive your kicking thigh further back during the wind-up to generate more foot speed."
      }
    ]
  }
}
```

## System Endpoints

### `GET /health`
Standard health check used by the Flutter frontend to confirm server connectivity before uploading large payloads.

**Response:**
```json
{
  "status": "ok",
  "service": "PenaltyIQ API v1.1.0",
  "auth_required": false
}
```
