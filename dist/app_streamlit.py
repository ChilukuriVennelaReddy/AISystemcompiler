import streamlit as st
import requests
import os

st.set_page_config(layout="wide")

# Connect to compiled API backend
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")

st.title("Compiled App Runtime UI - General App")

st.sidebar.title("App Authentication Context")
user_role = st.sidebar.selectbox("Simulated User Role", ['Admin', 'Member', 'Guest'])

st.info(f"Viewing page as role: **{user_role}**")

# Generated views
st.write("---")
def render_main():

    st.subheader('COMP_PATIENT_LIST (TableList)')
    # Fetching from backend
    try:
        res = requests.get(f"{API_BASE_URL}/api/v1/users/{userId}/patients", headers={"role": user_role})
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data:
                st.dataframe(data, use_container_width=True)
            else:
                st.info("No records found in database table.")
        else:
            st.error(f"API Error ({res.status_code}): {res.json().get('detail', res.text)}")
    except Exception as e:
        st.warning(f"Could not connect to live API backend: {str(e)}. Showing mock sample data:")
        st.write([
            {"id": "1", "title": "Setup database tables", "status": "In Progress"},
            {"id": "2", "title": "Configure payments and auth", "status": "Todo"}
        ])

    st.subheader('COMP_PATIENT_FORM (Form)')
    with st.form('COMP_PATIENT_FORM_form'):
        first_name = st.text_input('First_name')
        last_name = st.text_input('Last_name')
        date_of_birth = st.text_input('Date_of_birth')
        submitted = st.form_submit_button('Submit Form')
        if submitted:
            payload = {'first_name': first_name, 'last_name': last_name, 'date_of_birth': date_of_birth}
            try:
                res = requests.post(f"{API_BASE_URL}/api/v1/users/{userId}/patients", json=payload, headers={"role": user_role})
                if res.status_code == 200:
                    st.success("Record created successfully in database!")
                    st.json(res.json())
                else:
                    st.error(f"Submission failed ({res.status_code}): {res.json().get('detail', res.text)}")
            except Exception as e:
                st.error(f"Could not connect to live API server: {str(e)}")

    st.subheader('COMP_DOCTOR_LIST (TableList)')
    # Fetching from backend
    try:
        res = requests.get(f"{API_BASE_URL}/api/v1/patients/{patientId}/doctors", headers={"role": user_role})
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data:
                st.dataframe(data, use_container_width=True)
            else:
                st.info("No records found in database table.")
        else:
            st.error(f"API Error ({res.status_code}): {res.json().get('detail', res.text)}")
    except Exception as e:
        st.warning(f"Could not connect to live API backend: {str(e)}. Showing mock sample data:")
        st.write([
            {"id": "1", "title": "Setup database tables", "status": "In Progress"},
            {"id": "2", "title": "Configure payments and auth", "status": "Todo"}
        ])

    st.subheader('COMP_DOCTOR_FORM (Form)')
    with st.form('COMP_DOCTOR_FORM_form'):
        first_name = st.text_input('First_name')
        last_name = st.text_input('Last_name')
        specialization = st.text_input('Specialization')
        submitted = st.form_submit_button('Submit Form')
        if submitted:
            payload = {'first_name': first_name, 'last_name': last_name, 'specialization': specialization}
            try:
                res = requests.post(f"{API_BASE_URL}/api/v1/patients/{patientId}/doctors", json=payload, headers={"role": user_role})
                if res.status_code == 200:
                    st.success("Record created successfully in database!")
                    st.json(res.json())
                else:
                    st.error(f"Submission failed ({res.status_code}): {res.json().get('detail', res.text)}")
            except Exception as e:
                st.error(f"Could not connect to live API server: {str(e)}")

    st.subheader('COMP_APPOINTMENT_LIST (KanbanBoard)')
    # Fetching from backend
    try:
        res = requests.get(f"{API_BASE_URL}/api/v1/doctors/{doctorId}/appointments", headers={"role": user_role})
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data:
                st.dataframe(data, use_container_width=True)
            else:
                st.info("No records found in database table.")
        else:
            st.error(f"API Error ({res.status_code}): {res.json().get('detail', res.text)}")
    except Exception as e:
        st.warning(f"Could not connect to live API backend: {str(e)}. Showing mock sample data:")
        st.write([
            {"id": "1", "title": "Setup database tables", "status": "In Progress"},
            {"id": "2", "title": "Configure payments and auth", "status": "Todo"}
        ])

    st.subheader('COMP_APPOINTMENT_FORM (Form)')
    with st.form('COMP_APPOINTMENT_FORM_form'):
        date_time = st.text_input('Date_time')
        reason = st.text_input('Reason')
        status = st.text_input('Status')
        submitted = st.form_submit_button('Submit Form')
        if submitted:
            payload = {'date_time': date_time, 'reason': reason, 'status': status}
            try:
                res = requests.post(f"{API_BASE_URL}/api/v1/doctors/{doctorId}/appointments", json=payload, headers={"role": user_role})
                if res.status_code == 200:
                    st.success("Record created successfully in database!")
                    st.json(res.json())
                else:
                    st.error(f"Submission failed ({res.status_code}): {res.json().get('detail', res.text)}")
            except Exception as e:
                st.error(f"Could not connect to live API server: {str(e)}")

    st.subheader('COMP_PRESCRIPTION_LIST (TableList)')
    # Fetching from backend
    try:
        res = requests.get(f"{API_BASE_URL}/api/v1/appointments/{appointmentId}/prescriptions", headers={"role": user_role})
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data:
                st.dataframe(data, use_container_width=True)
            else:
                st.info("No records found in database table.")
        else:
            st.error(f"API Error ({res.status_code}): {res.json().get('detail', res.text)}")
    except Exception as e:
        st.warning(f"Could not connect to live API backend: {str(e)}. Showing mock sample data:")
        st.write([
            {"id": "1", "title": "Setup database tables", "status": "In Progress"},
            {"id": "2", "title": "Configure payments and auth", "status": "Todo"}
        ])

    st.subheader('COMP_PRESCRIPTION_FORM (Form)')
    with st.form('COMP_PRESCRIPTION_FORM_form'):
        medication = st.text_input('Medication')
        dosage = st.text_input('Dosage')
        instructions = st.text_input('Instructions')
        submitted = st.form_submit_button('Submit Form')
        if submitted:
            payload = {'medication': medication, 'dosage': dosage, 'instructions': instructions}
            try:
                res = requests.post(f"{API_BASE_URL}/api/v1/appointments/{appointmentId}/prescriptions", json=payload, headers={"role": user_role})
                if res.status_code == 200:
                    st.success("Record created successfully in database!")
                    st.json(res.json())
                else:
                    st.error(f"Submission failed ({res.status_code}): {res.json().get('detail', res.text)}")
            except Exception as e:
                st.error(f"Could not connect to live API server: {str(e)}")


render_main()
