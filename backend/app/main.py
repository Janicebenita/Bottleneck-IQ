from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from .api import nexus_router, router, strands_router
from .enterprise import router as enterprise_router
from .config import settings
from .database import Base,SessionLocal,engine
from .models import Incident,NexusRun
from . import llm
from .tools.sandbox import get_sandbox
from .security import reset_rate_limits, security_middleware
from .integrations.antigravity import AntigravityStatus, get_antigravity_status
from .strands_runtime import runtime_status
from .strands_runtime.background import start_background_monitor, stop_background_monitor
@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.environment.lower() not in {"development", "test"} and settings.integration_token == "development-integration-token":
        raise RuntimeError("INTEGRATION_TOKEN must be configured outside development")
    reset_rate_limits()
    Base.metadata.create_all(engine)
    start_background_monitor()
    yield
    await stop_background_monitor()

app=FastAPI(title="Bottleneck IQ HumanGuard API",version="4.0.0",description="A Strands-powered autonomous reliability agent that investigates silently and surfaces verified human decisions",lifespan=lifespan)
app.middleware("http")(security_middleware)
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],allow_methods=["GET","POST"],allow_headers=["Content-Type"])
app.include_router(router)
app.include_router(nexus_router)
app.include_router(strands_router)
app.include_router(enterprise_router)
@app.get("/api/v1/integrations/antigravity/status", response_model=AntigravityStatus, tags=["Integrations"])
def antigravity_status() -> AntigravityStatus:
    return get_antigravity_status()
@app.get("/health")
def health():
    return {"status":"ok","backend":True,"provider":settings.llm_provider,"strands":runtime_status(),"production_action":"NOT_EXECUTED"}

@app.get("/readiness")
def readiness():
    database=False; seeded=False
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1")); database=True
            seeded=(db.scalar(select(NexusRun.id).limit(1)) is not None or db.scalar(select(Incident.id).limit(1)) is not None)
    except Exception: pass
    demo_app=True
    if settings.demo_app_url:
        try: demo_app=httpx.get(f"{settings.demo_app_url}/health",timeout=1).is_success
        except httpx.HTTPError: demo_app=False
    mode=get_sandbox(settings.sandbox_image).mode; actual=type(llm.get_provider(settings.llm_provider)).__name__.replace("LLMProvider","").replace("Provider","").lower()
    provider_ready=bool(actual)
    safety_ready=not settings.production_execution
    ready=database and demo_app and provider_ready and safety_ready and mode in {"docker","local"}
    return {"status":"ok" if ready else "degraded","ready":ready,"backend":True,"demo_app":demo_app,"database":database,"provider":actual,"configured_provider":settings.llm_provider,"provider_warning":llm.provider_warning,"mock_provider":actual=="mock","provider_ready":provider_ready,"seeded":seeded,"sandbox_mode":mode,"safety_ready":safety_ready,"strands":runtime_status(),"production_action":"NOT_EXECUTED","auto_deploy":False}
