from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root() -> dict:
    return {"message": "Hello from FastAPI!!"}

@app.post("/query")
async def query():
    return {}