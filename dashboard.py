import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("EMAIL_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Email Classifier", layout="wide")
st.title("Email Classifier")

try:
    stats = requests.get(f"{API_URL}/stats", timeout=5).json()
    emails = requests.get(f"{API_URL}/emails?limit=100", timeout=5).json()
except requests.RequestException as error:
    st.error(f"Cannot reach the API at {API_URL}: {error}")
    st.stop()

first, second = st.columns(2)
first.metric("Classified emails", stats["total_emails"])
second.metric("Need a response", stats["requires_response"])

st.subheader("Classifications")
if emails:
    table = pd.DataFrame(emails)[
        ["id", "sender", "subject", "category", "priority", "sentiment", "requires_response", "summary"]
    ]
    st.dataframe(table, use_container_width=True, hide_index=True)
else:
    st.info("No emails have been classified yet. Run main.py first.")

left, right = st.columns(2)
left.subheader("By category")
left.bar_chart(stats["by_category"])
right.subheader("By priority")
right.bar_chart(stats["by_priority"])
