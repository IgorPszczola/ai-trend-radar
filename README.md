# AI Trend Radar

AI Trend Radar is a full-stack portfolio project that collects Instagram post data through a RapidAPI integration, enriches each post with an AI-generated visual prompt using Llama on Groq, stores results in MongoDB, and serves a lightweight frontend for exporting prompts to TXT.

This project was built to demonstrate practical backend engineering skills:
- API integration and data extraction
- Async Python service development
- LLM integration in a real workflow
- NoSQL data modeling with MongoDB
- Simple product-oriented frontend for end users

## Why This Project

Many AI image workflows start from weak prompts. This app turns social media trends into structured, production-ready prompt drafts.

Pipeline:
1. Fetch Instagram posts for a selected profile.
2. Extract text, hashtags, location, URL, and publication time.
3. Generate a professional image prompt with Llama (via Groq).
4. Save enriched records in MongoDB.
5. Let the user download all prompts as a TXT file.

## Tech Stack

### Backend
- FastAPI: asynchronous API framework used to expose endpoints and serve the app.
- Python 3: core language for data processing and integration logic.
- httpx (AsyncClient): non-blocking HTTP requests to RapidAPI.
- python-dotenv: environment variable management from .env.

### Data Layer
- MongoDB Atlas: cloud NoSQL database for storing extracted and generated trend documents.
- Motor (AsyncIOMotorClient): async MongoDB driver for high-throughput, non-blocking DB operations.

### AI Layer
- Groq API: ultra-fast inference endpoint for LLM calls.
- Llama 3.1 8B Instant: model used to transform raw Instagram context into professional prompt output.

### Frontend
- HTML + JavaScript: lightweight UI logic for user interaction and file generation.
- Tailwind CSS (CDN): quick and modern styling.

## Core Features

- Instagram trend extraction from RapidAPI endpoint
- Filtering posts without useful text
- Prompt generation for each post with structured art-direction style
- MongoDB persistence of enriched trends
- Auto-cleanup of stale records older than 48 hours
- Browser download of generated prompts as .txt

## Architecture Overview

1. User enters an Instagram username in the frontend.
2. Frontend calls GET /api/trends/instagram?username=... .
3. Backend requests user posts from RapidAPI.
4. For each valid post, backend sends context to Groq Llama.
5. Backend stores final trend objects in MongoDB.
6. Backend returns trends; frontend builds and downloads TXT output.

## Project Structure

- main.py: FastAPI app, RapidAPI fetch, Groq prompt generation, endpoint logic, frontend serving.
- database.py: MongoDB client and collection setup.
- index.html: UI for profile input, loading states, error handling, and TXT export.
- tests/test_main.py: unit tests for API behavior with mocked RapidAPI, MongoDB, and prompt generation.
- pytest.ini: pytest configuration for async tests.

## Environment Variables

Create a .env file in the root:

```env
MONGODB_URL=your_mongodb_connection_string
RAPIDAPI_KEY=your_rapidapi_key
GROQ_API_KEY=your_groq_api_key
```

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install fastapi uvicorn httpx motor python-dotenv groq
```

3. Run the API server:

```bash
uvicorn main:app --reload
```

4. Open in browser:
- http://127.0.0.1:8000

## Testing

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the test suite:

```bash
python -m pytest -q
```

Current test coverage includes:
- Successful extraction and transformation flow
- Handling of unexpected upstream response schema
- Mapping upstream HTTP failures to API 502 response
- Root endpoint HTML response check

## API Endpoint

### GET /api/trends/instagram

Query parameters:
- username: Instagram username (default: fit_aitana)

Response includes:
- source
- count
- trends[] containing text, ai_prompt, hashtags, location, url, published_at, fetched_at

## Example Stored Document (MongoDB)

```json
{
  "text": "Post caption...",
  "ai_prompt": "ultra-realistic portrait... --ar 4:5 --style raw",
  "hashtags": ["fashion", "editorial"],
  "location": "Milan",
  "url": "https://www.instagram.com/p/ABC123/",
  "published_at": "2026-03-15T20:10:00Z",
  "fetched_at": "2026-03-16T09:42:00Z"
}
```

## Engineering Decisions

- Async everywhere: both HTTP and Mongo operations are asynchronous to reduce waiting time.
- Lightweight frontend: no heavy framework required for this use case.
- Prompt generation at ingestion time: each stored trend is immediately usable.
- Time-based cleanup: avoids unlimited growth of temporary trend data.

## Skills Demonstrated

- Building production-style REST APIs with FastAPI
- Integrating third-party APIs with robust error handling
- Working with cloud-hosted NoSQL databases
- Integrating LLMs into business workflows
- Designing end-to-end features from data ingestion to user download
- Managing secrets and environment configuration

## Potential Next Improvements

- Add response validation with Pydantic models
- Add retries and circuit-breaker logic for external APIs
- Add caching and rate-limit protection
- Add unit and integration tests (pytest + httpx test client)
- Containerize with Docker for easier deployment
- Add authentication and per-user project history

## Notes

- Never commit real API keys or database credentials.

---
This project demonstrates practical integration of APIs, AI tooling, async Python services, and cloud data storage in one coherent product workflow.
