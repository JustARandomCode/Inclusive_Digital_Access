from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import uuid
import httpx
from database import connect_to_mongo, close_mongo_connection
from routers import auth, voice, forms
from services.llm_service import llm_service
from services.stt_service import stt_service
from models import HealthResponse
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s [%(request_id)s] %(message)s"
    if False  # request_id injected per-request below
    else "%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting IDA backend...")

    await connect_to_mongo()

    # Load STT model at startup — blocks here intentionally so first requests are fast
    try:
        await stt_service.load_model()
    except Exception as e:
        logger.error(f"STT model failed to load: {e}")
        # Non-fatal: STT endpoints will return 500 until fixed

    # Pull LLM model if absent
    try:
        await llm_service.ensure_model_loaded()
    except Exception as e:
        logger.warning(f"LLM model check failed: {e}")

    logger.info("Startup complete")
    yield

    logger.info("Shutting down...")
    await llm_service.close()
    await close_mongo_connection()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Inclusive Digital Assistant",
    version="1.0.0",
    lifespan=lifespan,
    # Never expose internal error details in production responses
    docs_url="/docs",
    redoc_url=None,
)

# CORS: lock this down to your actual frontend origin in production
# e.g. allow_origins=["https://your-domain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # TODO: restrict before going to production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def attach_request_id(request: Request, call_next):
    """Attach a unique ID to every request for log correlation."""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(auth.router)
app.include_router(voice.router)
app.include_router(forms.router)


@app.get("/")
async def root():
    return {"service": "Inclusive Digital Assistant", "version": "1.0.0"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    services: dict[str, str] = {}

    try:
        from database import db_instance
        if db_instance.db is not None:
            await db_instance.client.admin.command("ping")
            services["mongodb"] = "healthy"
        else:
            services["mongodb"] = "disconnected"
    except Exception as e:
        services["mongodb"] = "unhealthy"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            services["ollama"] = "healthy" if r.status_code == 200 else "unhealthy"
    except Exception:
        services["ollama"] = "unhealthy"

    services["stt"] = "healthy" if stt_service.model is not None else "not_loaded"

    overall = (
        "healthy"
        if all(v == "healthy" for v in services.values())
        else "degraded"
    )
    return HealthResponse(status=overall, services=services)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.api_port)
