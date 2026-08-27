from fastapi import FastAPI

app = FastAPI(title="File Analyzer")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
