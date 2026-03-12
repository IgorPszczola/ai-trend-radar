from fastapi import FastAPI
import httpx 

app = FastAPI()


@app.get("/api/trends/reddit")
async def fetch_reddit_trends():
    url = "https://www.reddit.com/r/streetwear/top.json?limit=30&t=week"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        data = response.json()
    
    trends = []
    for post in data["data"]["children"]:
        if len(post["data"]["title"]) > 3:
            trends.append({
                "title": post["data"]["title"],
                "url": "https://reddit.com" + post["data"]["permalink"],
                "score": post["data"]["score"]
            })
        else:
            continue
    
    return { 
        "source": "r/streetwear",
        "trends": trends
    }