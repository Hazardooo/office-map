from fastapi import FastAPI

app = FastAPI(title="Office Map API", version="0.1.0")

@app.get("/")
def read_root():
    return {"message": "Welcome to Office Map API"}

@app.get("/docs", include_in_schema=False)
async def custom_docs():
    # This matches the healthcheck URL
    return {"status": "ok"}
