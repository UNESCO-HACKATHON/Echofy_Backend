# UNESCO-HACKATHON/Echofy_Backend

Echofy Backend is a FastAPI-based content analysis API built for Media and Information Literacy (MIL).  
It is designed to evaluate text, audio, and image content and generate structured analysis that helps identify potentially misleading, emotional, or low-trust information.

The project also includes background task support for file processing, simple task tracking endpoints, and a test suite for the core text-analysis flow.

---

## Overview

Echofy Backend provides a unified analysis pipeline for multiple content types:

- **Text analysis** — analyze raw text for reliability and misleading signals
- **Audio analysis** — transcribe audio, then run the text analysis pipeline
- **Image analysis** — extract text from images, then run the text analysis pipeline
- **Task tracking** — inspect processing tasks and their status
- **Root health check** — verify the API is running

The API is structured to support modular services and future expansion into deeper multimedia verification workflows.

---

## Features Implemented

### 1. FastAPI application
- FastAPI application with metadata configured in `main.py`
- CORS enabled for all origins, methods, and headers
- Root endpoint for a quick service check

### 2. Content analysis endpoints
The API exposes analysis routes under `/api`:

- `POST /api/analyze/audio/`
- `POST /api/analyze/image/`
- `POST /api/analyze/video/` *(currently a placeholder endpoint)*
- text analysis routes are included through the text service router

### 3. Audio processing
- Accepts uploaded audio files
- Saves file temporarily
- Transcribes audio using the audio service
- Passes the transcript through the text analysis pipeline
- Returns a structured analysis response

### 4. Image processing
- Accepts uploaded image files
- Saves file temporarily
- Extracts text from the image using the image service
- Passes extracted text through the text analysis pipeline
- Returns a structured analysis response

### 5. Text analysis pipeline
The text pipeline is organized into modular steps such as:
- ingestion and parsing
- claim extraction
- claim verification
- sentiment and tone analysis
- score aggregation
- response formatting

### 6. Background task support
The project includes task processor utilities for:
- saving uploaded files to temporary storage
- starting background processing jobs
- tracking task status
- cleaning up temporary files after processing

### 7. Task endpoints
- `GET /api/tasks`
- `GET /api/tasks/{task_id}`

These allow clients to inspect job progress and results.

### 8. Automated tests
A test file is included for the text analysis endpoint behavior, covering:
- reliable content
- misleading content
- missing content
- too-short content validation

---

## API Endpoints

### Root
#### `GET /`
Returns a simple message confirming the API is running.

Example response:
```json
{
  "message": "Welcome to the MIL Content Analysis API!"
}
```

### Audio Analysis
#### `POST /api/analyze/audio/`
Accepts an uploaded audio file and returns a trust-oriented analysis after transcription and text processing.

### Image Analysis
#### `POST /api/analyze/image/`
Accepts an uploaded image file, extracts text, and returns a trust-oriented analysis.

### Video Analysis
#### `POST /api/analyze/video/`
Placeholder endpoint currently returning a basic response.

### Task Listing
#### `GET /api/tasks`
Returns all stored background task statuses.

### Task Status
#### `GET /api/tasks/{task_id}`
Returns the status/result of a specific background task.

---

## Analysis Workflow

The content analysis flow is designed around a shared pipeline:

1. **Input intake**
   - raw text
   - audio file
   - image file

2. **Preprocessing**
   - transcription for audio
   - OCR/text extraction for image
   - parsing and cleaning

3. **Claim extraction**
   - identify factual claims in the content

4. **Claim verification**
   - verify each extracted claim
   - produce status, reasoning, evidence, and sources

5. **Sentiment analysis**
   - assess tone
   - detect emotionally charged or warning-type language

6. **Score aggregation**
   - combine verification and sentiment signals
   - produce a final trust score

7. **Structured response**
   - summary
   - breakdown of claim extraction
   - source analysis
   - sentiment analysis
   - flags if needed

---

## Project Structure

```text
Echofy_Backend/
├── app/
│   ├── routes/
│   │   ├── audio.py
│   │   ├── image.py
│   │   ├── tasks.py
│   │   ├── text.py
│   │   └── __init__.py
│   ├── services/
│   │   ├── audio/
│   │   ├── image/
│   │   ├── text/
│   │   ├── deepfake/
│   │   └── video/
│   ├── tasks/
│   │   └── processors.py
│   └── __init__.py
├── tests/
│   └── test_analysis.py
├── main.py
├── requirements.txt
├── Pipfile
├── .env.example
└── README.md
```

---

## Technologies Used

- **Python**
- **FastAPI**
- **Uvicorn**
- **Pydantic**
- **python-multipart**
- **python-dotenv**
- **Pillow**
- **pytesseract**
- **pytest**
- plus many NLP, AI, OCR, and data-processing libraries listed in `requirements.txt`

---

## Environment Variables

Create a `.env` file based on `.env.example`.

```env
NEWSAPI_ORG=
NEWSDATA_IO=
GOOGLE_FACT=
SERPER_API=
GEMINI_API=
TAVILY_API=
REDDIT_CLIENT_ID=
REDDIT_SECRET_KEY=
```

Some of these keys appear to support external information retrieval, fact-checking, and research integrations.

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/UNESCO-HACKATHON/Echofy_Backend.git
cd Echofy_Backend
```

### 2. Create and activate a virtual environment
Using `pipenv`:
```bash
pipenv install
pipenv shell
```

Or using `venv`:
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
If you are not using `pipenv`, install with:
```bash
pip install -r requirements.txt
```

### 4. Add environment variables
Create a `.env` file:
```bash
cp .env.example .env
```

Then fill in the required keys.

---

## Running the Application

Start the API with Uvicorn:

```bash
uvicorn main:app --reload
```

By default, the API should be available at:

- http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## Running Tests

Run the test suite with:

```bash
pytest
```

The existing tests validate the content analysis behavior for expected edge cases and normal cases.

---

## Notes

- The project is currently set up with a strong backend foundation for multimodal analysis.
- Some routes, especially video analysis, are still placeholder implementations.
- The codebase already suggests future expansion into:
  - deepfake detection
  - richer source credibility checks
  - stronger fact-checking workflows
  - additional multimedia analysis capabilities

---

## License

This project is licensed under the MIT License.
```

