import os
from fastapi import FastAPI, HTTPException
import httpx
from database import collection
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()


app = FastAPI()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

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
        return {
            "UWAGA": "RapidAPI zwróciło coś innego niż posty. Oto surowe dane:",
            "DEBUG_RAW_DATA": data
        }

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

        trends.append({
            "text": text,
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