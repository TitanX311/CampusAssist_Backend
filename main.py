"""
FastAPI – India Colleges & Institutes Directory
Data source: combined_institutes.csv  (1 104 institutes, 33 states)

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload

Swagger UI: http://localhost:8000/docs
"""

import csv
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Load data from CSV at startup
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "combined_institutes.csv"

def load_data() -> List[dict]:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found at {CSV_PATH}")
    records = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), start=1):
            records.append({
                "id":           i,
                "institute_id": row["Institute Id"].strip(),
                "name":         row["Institute Name"].strip(),
                "city":         row["City"].strip(),
                "state":        row["State"].strip(),
            })
    return records

DATA: List[dict] = load_data()

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="India Colleges & Institutes API",
    description=(
        "Search 1 100+ colleges and institutes across India.\n\n"
        "Filter by **state**, **city**, or **name**. All filters support partial/case-insensitive matching."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class Institute(BaseModel):
    id:           int
    institute_id: str
    name:         str
    city:         str
    state:        str

class PaginatedResponse(BaseModel):
    total:     int
    page:      int
    page_size: int
    results:   List[Institute]

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _apply_filters(
    data:  List[dict],
    state: Optional[str],
    city:  Optional[str],
    name:  Optional[str],
    query: Optional[str],
) -> List[dict]:
    out = data
    if state:
        s = state.lower()
        out = [d for d in out if s in d["state"].lower()]
    if city:
        c = city.lower()
        out = [d for d in out if c in d["city"].lower()]
    if name:
        n = name.lower()
        out = [d for d in out if n in d["name"].lower()]
    if query:
        ABBR = {
            "nit":   "national institute of technology",
            "iit":   "indian institute of technology",
            "iiit":  "indian institute of information technology",
            "iim":   "indian institute of management",
            "iiser": "indian institute of science education and research",
            "iisc":  "indian institute of science",
            "aiims": "all india institute of medical sciences",
            "bits":  "birla institute of technology",
            "nls":   "national law school",
            "nlu":   "national law university",
            "jnu":   "jawaharlal nehru university",
        }
        expanded = []
        for tok in query.lower().split():
            if tok in ABBR:
                expanded.extend(ABBR[tok].split())
            else:
                expanded.append(tok)

        def matches(d: dict) -> bool:
            haystack = f"{d['name']} {d['city']} {d['state']} {d['institute_id']}".lower()
            return all(tok in haystack for tok in expanded)

        out = [d for d in out if matches(d)]
    return out

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", tags=["Info"])
def root():
    return {
        "message":   "Welcome to the India Colleges & Institutes API",
        "total":     len(DATA),
        "docs":      "/docs",
        "endpoints": ["/institutes", "/institutes/{id}", "/states", "/cities", "/stats"],
    }


@app.get("/institutes", response_model=PaginatedResponse, tags=["Institutes"])
def list_institutes(
    state:     Optional[str] = Query(None, description="Filter by state (partial match). E.g. Kerala, Tamil Nadu"),
    city:      Optional[str] = Query(None, description="Filter by city (partial match). E.g. Mumbai, Bengaluru"),
    name:      Optional[str] = Query(None, description="Search by institute name (partial match). E.g. IIT, Medical"),
    query:     Optional[str] = Query(None, description="Global search across name, city, and state"),
    page:      int           = Query(1,  ge=1,         description="Page number"),
    page_size: int           = Query(20, ge=1, le=200, description="Results per page (max 200)"),
):
    """
    List institutes with optional filters.

    ### Examples
    - `?state=Maharashtra`
    - `?city=Chennai`
    - `?name=Engineering`
    - `?query=Delhi` – searches name + city + state
    - `?state=Karnataka&city=Bengaluru`
    """
    filtered = _apply_filters(DATA, state, city, name, query)
    total    = len(filtered)
    start    = (page - 1) * page_size
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        results=[Institute(**d) for d in filtered[start : start + page_size]],
    )


@app.get("/institutes/{institute_id}", response_model=Institute, tags=["Institutes"])
def get_institute(institute_id: int):
    """Fetch a single institute by its numeric row ID."""
    for d in DATA:
        if d["id"] == institute_id:
            return Institute(**d)
    raise HTTPException(status_code=404, detail=f"Institute with id {institute_id} not found.")


@app.get("/states", tags=["Metadata"])
def list_states():
    """All unique states in the dataset."""
    states = sorted({d["state"] for d in DATA})
    return {"total": len(states), "states": states}


@app.get("/cities", tags=["Metadata"])
def list_cities(
    state: Optional[str] = Query(None, description="Filter cities by state (partial match)"),
):
    """All unique cities, optionally filtered by state."""
    data = DATA
    if state:
        data = [d for d in data if state.lower() in d["state"].lower()]
    cities = sorted({d["city"] for d in data})
    return {"total": len(cities), "cities": cities}


@app.get("/stats", tags=["Metadata"])
def stats():
    """Summary statistics — total institutes, states, cities, breakdown by state."""
    from collections import Counter
    state_counts = Counter(d["state"] for d in DATA)
    return {
        "total_institutes": len(DATA),
        "total_states":     len(state_counts),
        "total_cities":     len({d["city"] for d in DATA}),
        "institutes_by_state": dict(sorted(state_counts.items(), key=lambda x: -x[1])),
    }