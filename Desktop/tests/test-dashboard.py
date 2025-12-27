import streamlit as st
from pymongo import MongoClient
import pandas as pd

# ------------------ MongoDB Connection ------------------ #
MONGO_URI = "mongodb+srv://shubhamgehlod_db_user:3HUdgGMZ10kMAvBa@languagetranscript.4hisuze.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)

db = client["LA_writing-database"]
col = db["evaluation-dataset1"]

# --------------- Page Layout ---------------- #
st.set_page_config(page_title="Evaluation Dashboard", layout="wide")
st.title("📊 Student Writing Evaluation Dashboard")

# Load data
data = list(col.find({}, {"_id": 0}))
df = pd.DataFrame(data)

# Extract score inside evaluation
df["score"] = df["evaluation"].apply(lambda x: x.get("score") if isinstance(x, dict) else None)

# ------------------ Search Filters ------------------ #
st.sidebar.title("🔍 Filters")

text_query = st.sidebar.text_input("Search in Question or Answer")

score_filter = st.sidebar.number_input("Minimum Score Filter", min_value=0, max_value=9, value=0)

score_exact = st.sidebar.text_input("Search Exact Score (optional)")

# Apply Filters
filtered_df = df.copy()

if text_query:
    filtered_df = filtered_df[
        filtered_df["question"].str.contains(text_query, case=False, na=False) |
        filtered_df["answer"].str.contains(text_query, case=False, na=False)
    ]

# Score range filter
filtered_df = filtered_df[filtered_df['score'] >= score_filter]

# Exact score search
if score_exact.isdigit():
    filtered_df = filtered_df[filtered_df['score'] == int(score_exact)]

st.subheader("Evaluation Records")
st.dataframe(filtered_df[["question", "answer", "score"]], height=400)

# ------------------ Detailed Viewer ------------------ #
st.subheader("Detailed Evaluation View")

for row in filtered_df.to_dict("records"):
    with st.expander(f"📝 {row['question'][:80]}...  | Score: {row['score']}"):
        st.write("### Question:")
        st.write(row["question"])
        
        st.write("### Student Answer:")
        st.write(row["answer"])

        st.write("### Evaluation Result")
        st.write(f"**Score:** {row['score']}")
        st.write(f"**Feedback:** {row['evaluation'].get('feedback')}")
        st.write("**Missing Ideas:**", row['evaluation'].get("missing_ideas"))
        st.write("**Diagnostics (raw):**")
        st.json(row["evaluation"].get("diagnostics"))
