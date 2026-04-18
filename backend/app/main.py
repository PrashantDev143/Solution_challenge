from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.explain import router as explain_router
from app.routes.report import router as report_router
from app.routes.scan import router as scan_router
from app.routes.simulate import router as simulate_router
from app.routes.upload import router as upload_router

app = FastAPI(title="BiasX-Ray API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(scan_router)
app.include_router(simulate_router)
app.include_router(explain_router)
app.include_router(report_router)

@app.get("/health")
def health():
    return {"status": "ok", "app": "BiasX-Ray"}