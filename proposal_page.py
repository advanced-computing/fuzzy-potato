import streamlit as st

st.title("📄 Project Proposal")

st.info(
    """
This project analyzes patterns in **NYPD misconduct complaints** and compares them with
**crime levels across precincts** in New York City using two NYC Open Data datasets.
"""
)

# ----------------------------------------------------
# DATA SOURCES
# ----------------------------------------------------

st.header("📂 Data Sources", divider="blue")

st.subheader("Dataset 1: CCRB Police Officer Complaints")

st.markdown("""
**Source:** NYC Open Data

Civilian Complaint Review Board: Police Officers
https://data.cityofnewyork.us/Public-Safety/Civilian-Complaint-Review-Board-Police-Officers/2fir-qns4/about_data

This dataset contains officer-level misconduct complaint information from the
**Civilian Complaint Review Board (CCRB)**.

It includes variables such as:

- officer demographics
- current command and current rank
- total complaints
- substantiated complaints
- officer status and reporting dates
""")

st.subheader("Dataset 2: NYPD Complaint Data Historic")

st.markdown("""
**Source:** NYC Open Data

NYPD Complaint Data Historic
https://data.cityofnewyork.us/Public-Safety/NYPD-Complaint-Data-Historic/qgea-i56i/about_data

This dataset contains historical crime complaint records in New York City.

It includes variables such as:

- offense category and description
- precinct identifier
- borough
- report date
- crime classification
""")

# ----------------------------------------------------
# RESEARCH QUESTIONS
# ----------------------------------------------------

st.header("🔎 Research Questions", divider="green")

st.markdown("""
**RQ1**
How extreme are the highest-complaint officers relative to the overall distribution?

**RQ2**
Which groups show the highest complaint burden and substantiation intensity?

**RQ3**
Is crime volume associated with misconduct allegations across precincts?
""")

# ----------------------------------------------------
# ANALYTICAL APPROACH
# ----------------------------------------------------

st.header("🧠 Analytical Approach", divider="violet")

st.subheader("RQ1 Approach")

st.markdown("""
For **RQ1**, we study how the most complained-about officers compare with the overall
officer population.

We use Dataset 1 to:

1. Rank officers by **Total Complaints**.
2. Show the **top officers** with the highest complaint counts.
3. Compare them with the **overall distribution** of complaints across all officers.
4. Summarize the distribution using metrics such as:
   - mean complaints per officer
   - median complaints per officer
   - share of officers with zero complaints
   - extreme high-end complaint values

This helps us determine whether the highest-complaint officers are simply above average
or whether they are true outliers relative to the full distribution.
""")

st.subheader("RQ2 Approach")

st.markdown("""
For **RQ2**, we compare officer groups rather than individual officers.

Using Dataset 1, we group officers by variables such as:

- **Current Command**
- **Current Rank**

We then compute two group-level indicators:

- **Complaint burden** = average complaints per officer in the group
- **Substantiation intensity** = substantiated complaints per 100 complaints

To visualize these patterns, we use:

1. A **quadrant bubble chart** to show how groups compare across both dimensions.
2. A ranked chart for **complaint burden**.
3. A ranked chart for **substantiation intensity**.

This helps identify which groups appear most exposed to complaints and which groups
have relatively higher substantiation rates.
""")

st.subheader("RQ3 Approach")

st.markdown("""
For **RQ3**, we compare **crime counts by precinct** with
**misconduct allegation counts by precinct**.

Key steps:

1. Use the **`addr_pct_cd`** column in Dataset 2 to identify precincts.
2. Aggregate Dataset 2 into **crime_count by precinct**.
3. Aggregate Dataset 1 into **misconduct_count by precinct**.
4. Merge the two datasets using matching precinct identifiers.
5. Analyze whether precincts with higher crime volume also tend to have
higher misconduct complaint counts.

This allows us to study whether there is a broader precinct-level relationship
between local crime volume and police misconduct allegations.
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
- Dataset 1 supports **officer-level** analysis.
- Dataset 1 also supports **group-level** analysis using command and rank variables.
- Dataset 2 supports **precinct-level** crime aggregation.
- Together, the datasets allow us to compare:
  - individual officer complaint patterns
  - group-level risk patterns
  - precinct-level crime and misconduct patterns
    """)

with col2:
    st.subheader("What We Do Not Know Yet")

    st.markdown("""
- Whether the highest-complaint officers are truly extreme
  relative to the full officer distribution.
- Which officer groups show the highest complaint burden.
- Which officer groups show the highest substantiation intensity.
- Whether precincts with higher crime levels also show more misconduct allegations.
    """)

# ----------------------------------------------------
# CHALLENGES
# ----------------------------------------------------

st.header("⚠️ Anticipated Challenges", divider="red")

with st.expander("Click to view potential challenges"):
    st.markdown("""
**Data completeness**
Some records may contain missing values or unknown categories.

**Group interpretation**
High complaint burden and high substantiation intensity do not mean the same thing,
so both need to be interpreted carefully.

**Precinct matching**
Datasets use different column names for precinct-related variables,
so merging requires careful type cleaning and validation.
**Measurement bias**
Higher police activity or reporting intensity may generate more complaints,
which can affect interpretation.

**Substantiation limits**
A substantiated complaint is a stronger outcome than a raw complaint count, but
it still does not fully capture all dimensions of misconduct.
""")

st.success(
    "This proposal reflects the current project structure, research questions, "
    "and planned analytical workflow."
)
