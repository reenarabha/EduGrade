import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

app = FastAPI(title="EduGrade API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WEIGHTS_PATH = Path(__file__).resolve().parent / "model_weights.json"
MODEL_WEIGHTS: dict[str, Any] | None = None
if WEIGHTS_PATH.exists():
    with WEIGHTS_PATH.open("r", encoding="utf-8") as f:
        MODEL_WEIGHTS = json.load(f)


class StudentInput(BaseModel):
    studytime: int = Field(..., ge=1, le=4)
    absences: int = Field(..., ge=0, le=93)
    failures: int = Field(..., ge=0, le=4)
    age: int = Field(..., ge=15, le=22)
    schoolsup: int = Field(..., ge=0, le=1)
    famsup: int = Field(..., ge=0, le=1)
    paid: int = Field(..., ge=0, le=1)
    activities: int = Field(..., ge=0, le=1)
    internet: int = Field(..., ge=0, le=1)
    higher: int = Field(..., ge=0, le=1)
    Medu: int = Field(..., ge=0, le=4)
    Fedu: int = Field(..., ge=0, le=4)
    First_Term: int = Field(..., ge=0, le=20)
    Second_Term: int = Field(..., ge=0, le=20)

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_grade_keys(cls, data: Any) -> Any:
        """Accept G1/G2 aliases in addition to First_Term/Second_Term."""
        if isinstance(data, dict):
            normalized = dict(data)
            if "First_Term" not in normalized and "G1" in normalized:
                normalized["First_Term"] = normalized["G1"]
            if "Second_Term" not in normalized and "G2" in normalized:
                normalized["Second_Term"] = normalized["G2"]
            return normalized
        return data


def get_risk_level(grade_band: str) -> str:
    """Map predicted grade band to academic risk level."""
    if grade_band == "Low":
        return "High"
    if grade_band == "Average":
        return "Medium"
    return "Low"


def predict_linear_svc(student: StudentInput, weights: dict[str, Any]) -> str:
    """Run exact StandardScaler + one-vs-one Linear SVC inference without heavy ML deps."""
    payload = student.model_dump()
    features: list[str] = weights["features"]
    means: list[float] = weights["mean"]
    scales: list[float] = weights["scale"]
    classes: list[str] = weights["classes"]
    coefs: list[list[float]] = weights["coef"]
    intercepts: list[float] = weights["intercept"]

    scaled = [
        (payload[feat] - means[idx]) / scales[idx]
        for idx, feat in enumerate(features)
    ]

    n_classes = len(classes)
    votes = [0] * n_classes
    pair_idx = 0
    for i in range(n_classes):
        for j in range(i + 1, n_classes):
            decision = (
                sum(coefs[pair_idx][d] * scaled[d] for d in range(len(scaled)))
                + intercepts[pair_idx]
            )
            if decision > 0:
                votes[i] += 1
            else:
                votes[j] += 1
            pair_idx += 1

    best_idx = max(range(n_classes), key=lambda idx: votes[idx])
    return classes[best_idx]


@app.get("/")
@app.get("/api")
@app.get("/api/")
def home():
    return {"message": "EduGrade API is running"}


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok" if MODEL_WEIGHTS else "error", "model_loaded": MODEL_WEIGHTS is not None}


@app.post("/predict")
@app.post("/api/predict")
def predict(student: StudentInput):
    if MODEL_WEIGHTS is None:
        raise HTTPException(status_code=500, detail="Model weights not loaded")

    prediction = predict_linear_svc(student, MODEL_WEIGHTS)
    risk = get_risk_level(prediction)
    return {
        "predicted_grade_band": prediction,
        "risk_level": risk,
        "grade_band": prediction,
        "risk": risk,
        "message": "Success",
    }
