# API Documentation

## Overview

The Adaptive SRS API provides endpoints for spaced repetition learning, adaptive placement testing, and AI-powered content generation.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

Currently, the API uses username-based identification. All endpoints accept a `username` parameter or field.

## Endpoints

### Core Learning

#### Get Next Cards for Study Session

```http
POST /v1/sessions/next
```

**Request Body:**
```json
{
  "count": 20,
  "username": "user123"
}
```

**Response:**
```json
{
  "cards": [
    {
      "id": "card_123",
      "front": "Привет",
      "back": "Hello",
      "cefr_level": "A1",
      "due_date": "2024-01-15",
      "interval_days": 1,
      "stability": 0.5,
      "difficulty": 0.3
    }
  ],
  "total_available": 45
}
```

#### Submit Review Results

```http
POST /v1/reviews
```

**Request Body:**
```json
[
  {
    "card_id": "card_123",
    "rating": 3,
    "response_time_ms": 2500,
    "username": "user123"
  }
]
```

**Response:**
```json
{
  "updated_cards": 1,
  "next_review_date": "2024-01-17"
}
```

### Placement Testing

#### Start Placement Test

```http
POST /v1/placement/start
```

**Request Body:**
```json
{
  "username": "user123",
  "language": "ru",
  "claimed_level": "B1"
}
```

**Response:**
```json
{
  "session_id": "placement_456",
  "first_card": {
    "id": "card_789",
    "front": "Как дела?",
    "back": "How are you?",
    "cefr_level": "A2"
  },
  "estimated_level": "B1"
}
```

#### Submit Placement Answer

```http
POST /v1/placement/answer
```

**Request Body:**
```json
{
  "session_id": "placement_456",
  "card_id": "card_789",
  "user_answer": "How are you?",
  "response_time_ms": 5000
}
```

**Response:**
```json
{
  "next_card": {
    "id": "card_101",
    "front": "Где ты работаешь?",
    "back": "Where do you work?",
    "cefr_level": "B1"
  },
  "current_estimate": "B1",
  "confidence": 0.75,
  "is_complete": false
}
```

### User Statistics

#### Get User Statistics

```http
GET /v1/stats/{username}
```

**Response:**
```json
{
  "username": "user123",
  "cefr_level": "B1",
  "total_cards": 150,
  "cards_reviewed": 120,
  "cards_due": 25,
  "streak_days": 7,
  "accuracy_rate": 0.85,
  "total_study_time_minutes": 180
}
```

#### Get User Profile

```http
GET /v1/user/{username}
```

**Response:**
```json
{
  "username": "user123",
  "cefr_level": "B1",
  "language": "ru",
  "created_at": "2024-01-01T00:00:00Z",
  "last_active": "2024-01-15T10:30:00Z",
  "total_study_sessions": 25
}
```

### Content Generation

#### Generate Single Content

```http
POST /v1/generate/content
```

**Request Body:**
```json
{
  "lexeme_id": "lex_123",
  "target_cefr": "B1",
  "user_id": "user123",
  "context": "business conversation"
}
```

**Response:**
```json
{
  "job_id": "gen_456",
  "status": "queued",
  "estimated_completion": "2024-01-15T11:00:00Z"
}
```

#### Generate Batch Content

```http
POST /v1/generate/batch
```

**Request Body:**
```json
{
  "lexemes": [
    {
      "lexeme_id": "lex_123",
      "target_cefr": "B1"
    },
    {
      "lexeme_id": "lex_456",
      "target_cefr": "A2"
    }
  ],
  "user_id": "user123"
}
```

**Response:**
```json
{
  "job_id": "batch_789",
  "status": "processing",
  "total_items": 2,
  "completed_items": 0
}
```

#### Get Generation Suggestions

```http
GET /v1/generate/suggestions/{user_cefr}
```

**Query Parameters:**
- `user_id`: User identifier
- `limit`: Maximum number of suggestions (default: 10)

**Response:**
```json
{
  "suggestions": [
    {
      "lexeme_id": "lex_123",
      "lemma": "работать",
      "pos": "verb",
      "frequency_rank": 150,
      "difficulty_score": 0.6
    }
  ]
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200` - Success
- `400` - Bad Request (validation error)
- `404` - Not Found
- `422` - Unprocessable Entity
- `500` - Internal Server Error

**Error Response Format:**
```json
{
  "detail": "Error message description",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limiting

- **Content Generation**: 10 requests per minute per user
- **Review Submissions**: 100 requests per minute per user
- **Placement Testing**: 20 requests per minute per user

## CORS

The API supports CORS for the following origins:
- `http://localhost:3000` (development)
- `https://your-domain.com` (production)

## Data Models

### Card
```json
{
  "id": "string",
  "front": "string",
  "back": "string",
  "cefr_level": "string",
  "lexeme_id": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### UserCard
```json
{
  "id": "string",
  "user_id": "string",
  "card_id": "string",
  "stability": "float",
  "difficulty": "float",
  "interval_days": "integer",
  "due_date": "date",
  "reps": "integer",
  "lapses": "integer",
  "last_review": "datetime"
}
```

### ReviewLog
```json
{
  "id": "string",
  "user_id": "string",
  "card_id": "string",
  "rating": "integer",
  "response_time_ms": "integer",
  "reviewed_at": "datetime"
}
```

## Testing

You can test the API using the interactive documentation at `/docs` (Swagger UI) or `/redoc`.
