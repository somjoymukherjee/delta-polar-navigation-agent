# DeLTa — Dynamic Environmental & Logistics/Navigation Intelligence Agent
**AI-Powered Antarctic Navigation & Cryosphere Hazard Intelligence Platform**

DeLTa is an operational decision-support AI ecosystem designed for extreme polar marine navigation and cryospheric risk management in the Antarctic Peninsula and Weddell Sea.

---

## ❄️ Architecture Overview

DeLTa couples three autonomous domain agents with a central multi-factor risk engine and an 8-stage operational loop:

```
                  USER / OPERATOR
                        │
                        ▼
                AI ORCHESTRATOR
   ┌────────────────────┼────────────────────┐
   ▼                    ▼                    ▼
POLAR NAVIGATION    SATELLITE/ENV.        GLACIER HAZARD
     AGENT         PERCEPTION AGENT       EARLY-WARNING
   └────────────────────┬────────────────────┘
                        │
                        ▼
               CENTRAL RISK ENGINE
              (0–100 Multi-Factor Grid)
                        │
                        ▼
           DECISION & ALERT ENGINE
          (Dynamic Rerouting & Warnings)
                        │
                        ▼
             OPERATOR HUD & AUDIT LOG
          (Human-in-the-Loop Signoff)
```

### 1. Three-Agent Ecosystem
- **Polar Navigation Agent**: A* and Dijkstra pathfinding over an Antarctic polar mesh with multi-objective trade-offs (`SAFETY_FIRST`, `BALANCED`, `TIME_FIRST`, `FUEL_EFFICIENCY`).
- **Satellite & Environmental Perception Agent**: Computer vision and feature extraction for SAR/optical imagery, sea-ice concentration tracking, iceberg detection, and temporal ice front change detection (T0, T1, T2, Current).
- **Glacier Hazard Early-Warning Agent**: Ice-shelf kinematics, flow acceleration, calving probability modeling, and downstream hazard projection (calving wave, iceberg field, meltwater outburst).

### 2. Autonomous 8-Stage Loop
```
OBSERVE ➔ PERCEIVE ➔ COMPARE ➔ REASON ➔ ASSESS RISK ➔ PLAN ➔ ACT/RECOMMEND ➔ MONITOR
```

### 3. Key Components
- **Unified Agent State**: Single central source of truth (`UnifiedAgentState`) persisting across cycles.
- **Normalized Observations**: Standardized observation schema with `mode` (`LIVE`, `HISTORICAL`, `DEMO`), `confidence`, `freshness`, and `quality`.
- **Explainable Risk Delta**: Explains risk point changes (e.g., `Risk 38 -> 84 (+18 Sea Ice, +7 Icebergs, +4 Weather)`).
- **Activity Stream**: Real-time event feed of the agent's internal cycle operations.
- **Human-in-the-Loop Audit Log**: Every recommendation, divergence, and operator decision is cryptographically signed and stored in SQLite (`delta_storage.db`).

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup & Run
```bash
# From workspace root:
pip install fastapi uvicorn pydantic numpy scipy pytest httpx

# Launch backend (port 8000)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
The backend serves both the REST API and the compiled frontend static dashboard.

### 2. Frontend Development (Optional)
```bash
cd frontend
npm install
npm run dev
```
For production build:
```bash
cd frontend
npm run build
```

### 3. Running Automated Test Suite
```bash
# Run all unit tests and full end-to-end autonomous cycle test
pytest tests/ -v
```

---

## 🕹️ Operational Demo Flow (SIH Pitch)

1. **Open Dashboard**: Navigate to `http://localhost:8000/`.
2. **Observe Baseline (T+0)**:
   - Vessel `R/V Polar Sentinel` anchored at Deception Island.
   - Recommended Route: **Route Bravo (Time-Optimized, Risk 38.2)**.
   - Freshness & Data Quality HUD: `91% confidence`, `18m age`, `High quality`.
3. **Inspect Satellite & Glacier State**:
   - Switch to **Satellite Imagery** tab: review SAR/Optical temporal changes.
   - Switch to **Glacier Kinematics** tab: review Larsen C & Pine Island retreat velocity and scenario projections (`BASELINE`, `ACCELERATED`, `HIGH_CHANGE`).
4. **Trigger Calving Event (T+12h)**:
   - Click the **T+12h Calving Event!** simulation button in the header.
   - **Loop executes**: `OBSERVE` -> `PERCEIVE` (8 bergs, 3 ice cells) -> `COMPARE` (front collapse -820m) -> `REASON` (Bravo risk 38 -> 84) -> `PLAN` (Route Alpha selected) -> `ACT` (Dynamic rerouting alert).
   - Dynamic Reroute Alert banner triggers: Route Alpha recommended (-46.7 pt risk reduction).
5. **Open Activity Stream**:
   - Click **Activity Stream** button in the header to view timestamped autonomous cycle steps.
6. **Open Audit Log (Human-in-the-Loop)**:
   - Click **Audit Log** button in the header to view immutable record of observations, rerouting decisions, and operator sign-offs.
7. **AI Command Center**:
   - Ask natural language questions: *"Is the current route safe?"* or *"Explain why Route Alpha is recommended over Route Bravo"*.
   - DeLTa calls backend tools and provides evidence-backed answers.

---

## 🔒 Security & Extensibility

- **No Secrets in Frontend**: All credentials and simulation controls managed server-side.
- **Pluggable Satellite Provider Interface**: Abstract satellite provider architecture ready for real NASA Earthdata / Sentinel-1 SAR ingestion without changing the agent logic.
- **Strict Demo Flagging**: Simulated data is explicitly flagged with `mode: "DEMO"` and never disguised as live data.
