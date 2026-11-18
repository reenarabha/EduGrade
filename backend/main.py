from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import joblib
import pandas as pd
import os

app = FastAPI(title="EduGrade API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = "student_model.pkl"
if not os.path.exists(MODEL_PATH):
    print("Warning: student_model.pkl not found")
else:
    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully")

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

def get_risk_level(grade_band: str) -> str:
    if grade_band == "Low":
        return "High"
    elif grade_band == "Average":
        return "Medium"
    else:
        return "Low"

@app.get("/")
def home():
    return {"message": "EduGrade API is running"}

@app.post("/predict")
def predict(student: StudentInput):
    try:
        if 'model' not in globals():
            raise HTTPException(status_code=500, detail="Model not loaded")

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
            "Second_Term": student.Second_Term
        }])

        prediction = model.predict(data)[0]
        risk = get_risk_level(str(prediction))

        return {
            "predicted_grade_band": str(prediction),
            "risk_level": risk,
            "message": "Success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))