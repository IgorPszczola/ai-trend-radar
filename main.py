import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse 
from fastapi.staticfiles import StaticFiles
import httpx
from database import collection
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

app = FastAPI()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = AsyncGroq(api_key=GROQ_API_KEY)

async def generate_pro_prompt(text: str, location: str, hashtags: list):
    system_prompt = """You are a professional AI Art Director and Midjourney v6 prompt engineer.
    Your task is to take an Instagram post's text, location, and hashtags, and convert them into a highly detailed, photorealistic image prompt.
    The main subject is ALWAYS a beautiful 25-year-old female model. 
    Extract the outfit, vibe, and environment from the provided text. If a location is provided, set the background there.
    Structure the prompt: subject description, outfit, environment/background, lighting, camera specs (e.g., shot on 35mm lens, DSLR, 8k, ultra-realistic, cinematic lighting).
    CRITICAL RULE: Output ONLY the raw prompt string. No conversational text, no quotes, no explanations. End the prompt with: --ar 4:5 --style raw"""

    user_content = f"Text: {text}\nLocation: {location}\nHashtags: {', '.join(hashtags)}"

    try:
        response = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating prompt: {str(e)}"


@app.get("/api/trends/instagram")
async def fetch_instagram_trends(username: str = "fit_aitana"):
    url = "https://instagram-scraper-20251.p.rapidapi.com/userposts/" 
    querystring = {"username_or_id": username}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "instagram-scraper-20251.p.rapidapi.com"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=querystring, timeout=20.0)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Błąd połączenia z RapidAPI: {str(exc)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Nieoczekiwany błąd: {str(e)}")

    items = data.get("data", {}).get("items", [])
    if not items:
        return {"UWAGA": "RapidAPI zwróciło coś innego niż posty.", "DEBUG_RAW_DATA": data}

    trends = []
    
    for item in items:
        caption_dict = item.get("caption") or {}
        text = caption_dict.get("text", "")
        
        if not text:
            continue

        hashtags = caption_dict.get("hashtags", [])
        location_dict = item.get("location") or {}
        location_name = location_dict.get("name", "")
        
        code = item.get("code", "")
        post_url = f"https://www.instagram.com/p/{code}/" if code else ""
        
        taken_at = item.get("taken_at")
        published_date = datetime.fromtimestamp(taken_at, timezone.utc) if taken_at else None

        ai_prompt = await generate_pro_prompt(text, location_name, hashtags)

        trends.append({
            "text": text,
            "ai_prompt": ai_prompt, 
            "hashtags": hashtags,
            "location": location_name,
            "url": post_url,
            "published_at": published_date,
            "fetched_at": datetime.now(timezone.utc)
        })

    granica = datetime.now(timezone.utc) - timedelta(hours=48)
    await collection.delete_many({"fetched_at": {"$lt": granica}})

    if trends:
        await collection.insert_many(trends)
        for post in trends:
            post["_id"] = str(post["_id"])

    return { 
        "source": f"instagram/{username}",
        "count": len(trends),
        "trends": trends
    }


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()