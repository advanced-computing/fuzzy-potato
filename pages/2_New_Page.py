import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dataset 2: NYPD Complaint Data Historic", layout="wide")

st.title("Dataset 2: NYPD Complaint Data Historic")
st.write("Second relevant dataset")

df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [10, 14, 9, 18]})
fig = px.line(df, x="x", y="y")
st.plotly_chart(fig, use_container_width=True)
