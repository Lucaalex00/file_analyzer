from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.responses import Response

from src.analyzer.document_analyzer import AnalysisError
from src.api.config import get_settings
from src.api.dependencies import get_pipeline
from src.extractors.base import ExtractionError
from src.extractors.factory import UnsupportedFileTypeError
from src.pipeline import DocumentAnalysisPipeline

app = FastAPI(title="File Analyzer")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(
    file: UploadFile,
    pipeline: DocumentAnalysisPipeline = Depends(get_pipeline),
) -> Response:
    settings = get_settings()

    # Fast path: reject oversized uploads before buffering the whole body.
    if file.size is not None and file.size > settings.max_file_size_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the maximum allowed size")

    file_bytes = await file.read()

    # Fallback for clients/servers that don't populate .size.
    if len(file_bytes) > settings.max_file_size_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the maximum allowed size")

    try:
        pdf_bytes = pipeline.run(
            file_bytes=file_bytes,
            filename=file.filename or "upload",
            content_type=file.content_type,
        )
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except ExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AnalysisError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return Response(content=pdf_bytes, media_type="application/pdf")
