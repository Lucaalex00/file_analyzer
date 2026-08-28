import re
from contextlib import asynccontextmanager
from pathlib import Path, PurePosixPath

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from src.analyzer.document_analyzer import AnalysisError
from src.api.config import Settings, get_settings
from src.api.dependencies import get_extractor_factory, get_pipeline
from src.extractors.base import ExtractionError
from src.extractors.factory import ExtractorFactory, UnsupportedFileTypeError
from src.pipeline import DocumentAnalysisPipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings().validate()
    yield


app = FastAPI(title="File Analyzer", lifespan=lifespan)

_FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=_FRONTEND_DIR), name="static")

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_FRONTEND_DIR / "index.html")


def _report_filename(original_filename: str) -> str:
    stem = PurePosixPath(original_filename.replace("\\", "/")).stem
    safe_stem = _UNSAFE_FILENAME_CHARS.sub("_", stem) or "report"
    return f"{safe_stem}-report.pdf"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


async def _read_within_size_limit(file: UploadFile, settings: Settings) -> bytes:
    # Fast path: reject oversized uploads before buffering the whole body.
    if file.size is not None and file.size > settings.max_file_size_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the maximum allowed size")

    file_bytes = await file.read()

    # Fallback for clients/servers that don't populate .size.
    if len(file_bytes) > settings.max_file_size_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the maximum allowed size")

    return file_bytes


@app.post("/extract")
async def extract(
    file: UploadFile,
    factory: ExtractorFactory = Depends(get_extractor_factory),
) -> dict[str, str]:
    settings = get_settings()
    file_bytes = await _read_within_size_limit(file, settings)

    try:
        extractor = factory.get_extractor(file.filename or "upload", file.content_type)
        raw_text = extractor.extract(file_bytes, file.filename or "upload")
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except ExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {"text": raw_text.content}


@app.post("/analyze")
async def analyze(
    file: UploadFile,
    pipeline: DocumentAnalysisPipeline = Depends(get_pipeline),
) -> Response:
    settings = get_settings()
    file_bytes = await _read_within_size_limit(file, settings)

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

    report_filename = _report_filename(file.filename or "upload")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{report_filename}"'},
    )
