"""
DeLTa (Dynamic Environmental & Logistics/Navigation Intelligence Agent)
Main FastAPI Application Entrypoint
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.api.routes import router
from backend.agents.orchestrator import orchestrator

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run initial autonomous agent cycle
    print("[DeLTa System] Initializing Antarctic Intelligence Ecosystem...")
    orchestrator.run_autonomous_cycle(force_stage=0)
    print("[DeLTa System] Core agent loop initialized. Ready for operations.")
    yield
    print("[DeLTa System] Shutting down cleanly.")

app = FastAPI(
    title="DeLTa — Antarctic AI Navigation & Cryosphere Hazard Intelligence Agent",
    description="Operational decision-support system featuring continuous observation, satellite CV, dynamic rerouting, and early-warning alerts.",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for local and web frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from fastapi.staticfiles import StaticFiles

app.include_router(router)

dist_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "service": "DeLTa Polar Intelligence Platform",
            "status": "OPERATIONAL",
            "docs": "/docs",
            "mode": orchestrator.system_mode.value
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
