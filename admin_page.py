import streamlit as st

def show():
     st.title('This is the admin page')
     st.status('UNDER CONSTRUCTION', state='running', expanded=False)
     st.write(st.session_state)

     if st.button("Logout"):
           st.session_state['role'] = None
           st.session_state['user_key'] = None
           st.rerun()