# streamlit_app.py
# Streamlit app: load NYC OpenData (Socrata) and draw a line chart over time by police unit.
# Fix: use requests + params so spaces in $where/$order are URL-encoded properly.

import streamlit as st

# Define the pages
main_page = st.Page("main_page.py", title="Team: Emily Chu, Elsie Zhang", icon="🎈")
proposal_page = st.Page("proposal.py",title="Project Proposal",icon="📄")
page_2 = st.Page("page_2.py", title="Dataset 1: NYC OpenData – Allegations Over Time", icon="❄️")
page_3 = st.Page("page_3.py", title="Dataset 2: NYPD Complaint Data Historic", icon="🎉")

# Set up navigation
pg = st.navigation([main_page, proposal_page, page_2, page_3])

# Run the selected page
pg.run()
    