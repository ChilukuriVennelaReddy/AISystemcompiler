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

    st.subheader('COMP_ORDER_LIST (KanbanBoard)')
    # Fetching from backend
    try:
        res = requests.get(f"{API_BASE_URL}/api/v1/users/{userId}/orders", headers={"role": user_role})
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

    st.subheader('COMP_ORDER_FORM (Form)')
    with st.form('COMP_ORDER_FORM_form'):
        order_number = st.text_input('Order_number')
        total = st.text_input('Total')
        status = st.text_input('Status')
        submitted = st.form_submit_button('Submit Form')
        if submitted:
            payload = {'order_number': order_number, 'total': total, 'status': status}
            try:
                res = requests.post(f"{API_BASE_URL}/api/v1/users/{userId}/orders", json=payload, headers={"role": user_role})
                if res.status_code == 200:
                    st.success("Record created successfully in database!")
                    st.json(res.json())
                else:
                    st.error(f"Submission failed ({res.status_code}): {res.json().get('detail', res.text)}")
            except Exception as e:
                st.error(f"Could not connect to live API server: {str(e)}")


render_main()
