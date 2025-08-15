# Media and Information Literacy (MIL) Content Analysis API Documentation

## Overview

This API allows you to analyze text content (such as articles, video titles, or transcribed audio) for potential misinformation or AI-generated markers. It is designed to help identify misleading content and provide explanations for its assessment.

---

## Base Endpoint

```
POST /api/v1/analyze
```

### Purpose

Analyzes a piece of text and determines if it is potentially misleading or AI-generated. Returns a confidence score and an explanation.

---

## Request

### Request Body (JSON)

-   **content** (string, required): The text to be analyzed. Must be between 10 and 10,000 characters.
    -   Example:
        ```json
        {
            "content": "This is a sample content to analyze."
        }
        ```

#### Schema: `AnalysisRequest`

| Field   | Type   | Description                                                       |
| ------- | ------ | ----------------------------------------------------------------- |
| content | string | The text content to be analyzed (article, title, transcript, etc) |

---

## Response

### Success (HTTP 200)

Returns a JSON object with the analysis results.

#### Schema: `AnalysisResponse`

| Field                     | Type    | Description                                                                 |
| ------------------------- | ------- | --------------------------------------------------------------------------- |
| is_potentially_misleading | boolean | `true` if the content is flagged as potentially misleading or AI-generated  |
| confidence_score          | number  | A score from 0.0 to 1.0 indicating the model's confidence in its assessment |
| explanation               | string  | A brief explanation of why the content was flagged                          |

-   Example Response:
    ```json
    {
        "is_potentially_misleading": true,
        "confidence_score": 0.87,
        "explanation": "Uses emotionally charged language."
    }
    ```

### Validation Error (HTTP 422)

If the request is invalid (e.g., missing or too short/long content), a validation error is returned.

#### Schema: `HTTPValidationError`

| Field  | Type  | Description               |
| ------ | ----- | ------------------------- |
| detail | array | List of validation errors |

Each item in `detail` is a `ValidationError` object:
| Field | Type | Description |
|-------|----------------|----------------------------|
| loc | array | Location of the error |
| msg | string | Error message |
| type | string | Type of validation error |

-   Example Error Response:
    ```json
    {
        "detail": [
            {
                "loc": ["body", "content"],
                "msg": "ensure this value has at least 10 characters",
                "type": "value_error"
            }
        ]
    }
    ```

---

## Summary for Frontend Developers

-   **Send a POST request** to `/api/v1/analyze` with a JSON body containing a `content` field.
-   **Receive a response** indicating if the content is potentially misleading, a confidence score, and an explanation.
-   **Handle validation errors** by checking for a 422 status and displaying the error messages to users.

This API is designed to be simple to integrate and provides clear, actionable feedback for content analysis tasks.
