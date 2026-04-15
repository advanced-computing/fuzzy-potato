# streamlit_app.py
# Streamlit app: load NYC OpenData (Socrata) and draw a line chart over time by police unit.
# Fix: use requests + params so spaces in $where/$order are URL-encoded properly.

import streamlit as st

main_page = st.Page("main_page.py", title="Home", icon="🎈")
proposal_page = st.Page("proposal_page.py", title="Project Proposal", icon="📄")
page_2 = st.Page("page_2.py", title="RQ1: Officer Complaint Distribution", icon="📊")
page_4 = st.Page("page_4.py", title="RQ2: Group Risk Patterns", icon="🧩")
page_3 = st.Page("page_3.py", title="RQ3: Precinct Crime and Misconduct", icon="🎉")

pg = st.navigation([main_page, proposal_page, page_2, page_4, page_3])
pg.run()
