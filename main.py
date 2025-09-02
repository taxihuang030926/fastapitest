# main.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World from pictunes.me"}

@app.get("/health")
async def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
