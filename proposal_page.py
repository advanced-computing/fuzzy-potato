import streamlit as st

st.title("📄 Project Proposal")

st.info(
    """
This project analyzes patterns in **NYPD misconduct complaints** and compares them with
**crime levels across precincts** in New York City using NYC Open Data datasets.
"""
)

# ----------------------------------------------------
# DATA SOURCES
# ----------------------------------------------------

st.header("📂 Data Sources", divider="blue")

st.subheader("Dataset 1: CCRB Police Officer Complaints")

st.markdown("""
Source: NYC Open Data

https://data.cityofnewyork.us/Public-Safety/Civilian-Complaint-Review-Board-Police-Officers/2fir-qns4/about_data

This dataset contains officer-level complaint records from the
**Civilian Complaint Review Board (CCRB)**.

It includes information such as:

- officer demographics
- complaint counts
- allegation types
- investigation outcomes
""")

st.subheader("Dataset 2: NYPD Complaint Data Historic")

st.markdown("""
Source: NYC Open Data

https://data.cityofnewyork.us/Public-Safety/NYPD-Complaint-Data-Historic/qgea-i56i/about_data

This dataset contains historical complaint reports related to crimes in New York City.
It includes information such as:

- complaint type
- precinct location
- date and time of incidents
- crime classification
""")

# ----------------------------------------------------
# RESEARCH QUESTIONS
# ----------------------------------------------------

st.header("🔎 Research Questions", divider="green")

st.markdown("""
**RQ1**

Are complaints concentrated among a small subset of officers?

**RQ2**

Which groups show higher complaint burden and higher substantiation intensity?

**RQ3**

How do **crime levels across precincts** relate to **misconduct allegation patterns**?
""")

# ----------------------------------------------------
# RQ3 EXPLANATION
# ----------------------------------------------------

st.subheader("RQ3 Analytical Approach")

st.markdown("""
To address RQ3, we compare **crime counts by precinct** with **misconduct allegation counts**.

Key steps:

1. Use the **`addr_pct_cd`** column in Dataset 2 to identify precincts.

2. Aggregate crime incidents to calculate **crime_count by precinct**.

3. Merge this with Dataset 1's **misconduct_count by precinct** using
`precinct` (Dataset 1) and `addr_pct_cd` (Dataset 2).

4. Ensure both columns have matching types (both numeric or both string).

This allows us to explore whether precincts with **higher crime levels**
also show higher misconduct complaint levels**.
""")

# ----------------------------------------------------
# WHAT WE KNOW VS UNKNOWN
# ----------------------------------------------------

st.header("📊 What We Know vs Unknown", divider="orange")

col1, col2 = st.columns(2)

with col1:
    st.subheader("What We Know")

    st.markdown("""
- NYC provides open datasets on both **police misconduct complaints** and **crime incidents**.
- Complaint data includes officer-level allegations and outcomes.
- Crime data includes **precinct-level incident counts**.
- These datasets allow comparisons between **crime patterns and misconduct patterns**.
    """)

with col2:
    st.subheader("What We Do Not Know Yet")

    st.markdown("""
- Whether misconduct complaints are concentrated among a small number of officers.
- Whether some officer groups experience higher substantiated complaint rates.
- Whether precincts with higher crime levels also show higher misconduct allegations.
    """)

# ----------------------------------------------------
# CHALLENGES
# ----------------------------------------------------

st.header("⚠️ Anticipated Challenges", divider="red")

with st.expander("Click to view potential challenges"):
    st.markdown("""
**Data completeness**

Some records may contain missing values.

**Data merging**

Datasets use different column names (`precinct` vs `addr_pct_cd`).

**Interpretation challenges**

A complaint does not necessarily imply confirmed misconduct.

**Measurement bias**

Precincts with higher police activity may naturally generate more complaints.
""")

st.success("This proposal outlines the research questions and data sources for the project.")
