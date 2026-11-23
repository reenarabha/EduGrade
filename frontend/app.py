import streamlit as st
import requests

st.set_page_config(page_title="EduGrade", page_icon="📚")
st.title("EduGrade: Student Performance Prediction")
st.write("Student details daalo aur grade band + risk dekh lo")

with st.form("student_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        studytime = st.selectbox("Study Time", [1, 2, 3, 4], format_func=lambda x: f"{x} ({['<2h','2-5h','5-10h','>10h'][x-1]})")
        absences = st.number_input("Absences", min_value=0, max_value=93, value=5)
        failures = st.number_input("Past Failures", min_value=0, max_value=4, value=0)
        age = st.number_input("Age", min_value=15, max_value=22, value=16)
        Medu = st.selectbox("Mother's Education", [0,1,2,3,4])
        Fedu = st.selectbox("Father's Education", [0,1,2,3,4])
    
    with col2:
        schoolsup = st.selectbox("School Support", [0,1], format_func=lambda x: "Yes" if x else "No")
        famsup = st.selectbox("Family Support", [0,1], format_func=lambda x: "Yes" if x else "No")
        paid = st.selectbox("Paid Classes", [0,1], format_func=lambda x: "Yes" if x else "No")
        activities = st.selectbox("Activities", [0,1], format_func=lambda x: "Yes" if x else "No")
        internet = st.selectbox("Internet", [0,1], format_func=lambda x: "Yes" if x else "No")
        higher = st.selectbox("Wants Higher Education", [0,1], format_func=lambda x: "Yes" if x else "No")
        First_Term = st.number_input("First Term Grade", min_value=0, max_value=20, value=12)
        Second_Term = st.number_input("Second Term Grade", min_value=0, max_value=20, value=13)
    
    submitted = st.form_submit_button("Predict Grade & Risk")

if submitted:
    data = {
        "studytime": studytime,
        "absences": absences,
        "failures": failures,
        "age": age,
        "schoolsup": schoolsup,
        "famsup": famsup,
        "paid": paid,
        "activities": activities,
        "internet": internet,
        "higher": higher,
        "Medu": Medu,
        "Fedu": Fedu,
        "First_Term": First_Term,
        "Second_Term": Second_Term
    }
    
    try:
        
response = requests.post("http://172.18.160.33:8000/predict", json=data)
        if response.status_code == 200:
            result = response.json()
            st.success("Prediction Successful!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Predicted Grade Band", result["predicted_grade_band"])
            with col2:
                st.metric("Risk Level", result["risk_level"])
        else:
            st.error(f"Error: {response.text}")
    except Exception as e:
        st.error("Backend not running. Start server by Reena.")