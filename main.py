from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def check_health():
    return {"status": "ok",
            "message": "API is healthy"}