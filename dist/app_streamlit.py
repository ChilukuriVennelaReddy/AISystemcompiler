import streamlit as st
import requests

st.set_page_config(layout="wide")

st.title("Compiled App Runtime UI - General App")

st.sidebar.title("App Authentication Context")
user_role = st.sidebar.selectbox("Simulated User Role", ['Admin', 'Member', 'Guest'])

st.info(f"Viewing page as role: **{user_role}**")

# Generated views
st.write("---")
def render_main():

    st.subheader('COMP_CONTACTS_LIST (TableList)')
    # Fetching from backend
    try:
        res = requests.get(f"http://127.0.0.1:8001/api/v1/contacts", headers={"role": user_role})
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data:
                st.dataframe(data, use_container_width=True)
            else:
                st.info("No records found in database table.")
        else:
            st.error(f"API Error ({res.status_code}): {res.json().get('detail', res.text)}")
    except Exception as e:
        st.warning(f"Could not connect to live API backend on port 8001: {str(e)}. Showing mock sample data:")
        st.write([
            {"id": "1", "title": "Setup database tables", "status": "In Progress"},
            {"id": "2", "title": "Configure payments and auth", "status": "Todo"}
        ])

    st.subheader('COMP_CONTACT_FORM (Form)')
    with st.form('COMP_CONTACT_FORM_form'):
        first_name = st.text_input('First_name')
        last_name = st.text_input('Last_name')
        phone = st.text_input('Phone')
        submitted = st.form_submit_button('Submit Form')
        if submitted:
            payload = {'first_name': first_name, 'last_name': last_name, 'phone': phone}
            try:
                res = requests.post(f"http://127.0.0.1:8001/api/v1/contacts", json=payload, headers={"role": user_role})
                if res.status_code == 200:
                    st.success("Record created successfully in database!")
                    st.json(res.json())
                else:
                    st.error(f"Submission failed ({res.status_code}): {res.json().get('detail', res.text)}")
            except Exception as e:
                st.error(f"Could not connect to live API server on port 8001: {str(e)}")


render_main()
