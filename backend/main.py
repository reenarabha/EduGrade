from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator
import joblib
import pandas as pd

app = FastAPI(title="EduGrade API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
CANDIDATE_MODEL_PATHS = [
    BASE_DIR / "student_model.pkl",
    BASE_DIR.parent / "student_model.pkl",
]
MODEL_PATH = next((p for p in CANDIDATE_MODEL_PATHS if p.exists()), CANDIDATE_MODEL_PATHS[0])

model = None
if not MODEL_PATH.exists():
    print(f"Warning: {MODEL_PATH} not found")
else:
    model = joblib.load(MODEL_PATH)
    print(f"Model loaded successfully from {MODEL_PATH}")


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


@app.get("/")
@app.get("/api")
@app.get("/api/")
def home():
    return {"message": "EduGrade API is running"}


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok" if model is not None else "error", "model_loaded": model is not None}


@app.post("/predict")
@app.post("/api/predict")
def predict(student: StudentInput):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    try:
        data = pd.DataFrame([{
            "studytime": student.studytime,
            "absences": student.absences,
            "failures": student.failures,
            "age": student.age,
            "schoolsup": student.schoolsup,
            "famsup": student.famsup,
            "paid": student.paid,
            "activities": student.activities,
            "internet": student.internet,
            "higher": student.higher,
            "Medu": student.Medu,
            "Fedu": student.Fedu,
            "First_Term": student.First_Term,
            "Second_Term": student.Second_Term,
        }])

        prediction = str(model.predict(data)[0])
        risk = get_risk_level(prediction)

        return {
            "predicted_grade_band": prediction,
            "risk_level": risk,
            "grade_band": prediction,
            "risk": risk,
            "message": "Success",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
