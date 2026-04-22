import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.explain import router as explain_router
from app.routes.report import router as report_router
from app.routes.scan import router as scan_router
from app.routes.simulate import router as simulate_router
from app.routes.upload import router as upload_router
from app.routes.analyze import router as analyze_router

app = FastAPI(
    title="BiasX-Ray API",
    description="AI fairness auditing platform that detects hidden discrimination in ML systems",
    version="1.0.0"
)

# CORS configuration with environment variable support
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
allowed_origins = [origin.strip() for origin in allowed_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(scan_router)
app.include_router(simulate_router)
app.include_router(explain_router)
app.include_router(report_router)
app.include_router(analyze_router)

@app.get("/health")
def health():
    return {"status": "ok", "app": "BiasX-Ray"}