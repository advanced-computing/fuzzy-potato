import streamlit as st

# --- TITLE ---
st.markdown("# 🚔 Police Misconduct Analysis in NYC")
st.markdown("### Team: Emily Chu, Elsie Zhang 🎈")

st.divider()

# --- PROJECT OVERVIEW ---
st.markdown("## 📖 Project Overview")

st.write(
    "This project explores patterns in police misconduct across New York City "
    "using public data. We focus on three key questions to understand how "
    "complaints are distributed, which groups show higher complaint burden, "
    "and whether misconduct allegations are associated with the number of "
    "recorded crime incidents across precincts."
)

st.divider()

# --- NAVIGATION ---
st.markdown("## 🧭 Explore Our Research Questions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 RQ1\nDistribution of Complaints"):
        st.switch_page("page_2.py")

with col2:
    if st.button("🧩 RQ2\nGroup Risk Patterns"):
        st.switch_page("page_4.py")

with col3:
    if st.button("🚨 RQ3\nCrime vs Misconduct"):
        st.switch_page("page_3.py")

st.divider()

# --- KEY FINDINGS ---
st.markdown("## 🔍 Key Findings")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📊 RQ1")
    st.markdown("**Highly Concentrated**")
    st.caption("Complaints are concentrated among a small group of officers")

with col2:
    st.markdown("### 🧩 RQ2")
    st.markdown("**Group Disparities**")
    st.caption("Certain groups show higher complaint burden and substantiation rates")

with col3:
    st.markdown("### 🚨 RQ3")
    st.markdown("**Weak Relationship**")
    st.caption("Crime incidents are not strongly associated with misconduct")

st.caption(
    "These summaries highlight our main insights across the three research questions. "
    "Explore each section for detailed analysis."
)

st.divider()

# --- HOW TO USE ---
st.markdown("## ℹ️ How to Use This Dashboard")

st.write("""
- Use the buttons above or sidebar to navigate between research questions
- Each page includes interactive filters and visualizations
- Hover over charts to explore detailed data
""")
