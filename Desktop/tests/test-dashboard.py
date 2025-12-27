import streamlit as st
from pymongo import MongoClient
import pandas as pd

# ------------------ MongoDB Connection ------------------ #
MONGO_URI = "mongodb+srv://shubhamgehlod_db_user:3HUdgGMZ10kMAvBa@languagetranscript.4hisuze.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)

db = client["LA_writing-database"]
col = db["evaluation-dataset1"]

# ---------------- UI ---------------- #
st.set_page_config(page_title="Model Comparison Dashboard", layout="wide")
st.title("🧠 Model-A vs Model-B Evaluation Comparison Dashboard")

# Fetch Data
data = list(col.find({}, {"_id":0}))
df = pd.DataFrame(data)

# Extract Model-A Score
df["model_A_score"] = df["evaluation"].apply(lambda x: x.get("score") if x else None)

# Extract Model-B Score (n8n nested)
def get_model_B_score(x):
    try:
        return x[0]["output"][0]["output"]["content_score"]
    except:
        return None

df["model_B_score"] = df["evaluation_from_n8n"].apply(get_model_B_score)

# Sidebar Filters
st.sidebar.header("Filters")
min_A = st.sidebar.slider("Min Model-A Score",0,6,0)
min_B = st.sidebar.slider("Min Model-B Score",0,6,0)

filtered = df[(df.model_A_score>=min_A) & (df.model_B_score>=min_B)]

# Overview Table
st.subheader("📄 Overview")
st.dataframe(filtered[["question","model_A_score","model_B_score"]],height=350)

st.markdown("---")
st.subheader("🔍 Detailed Side-by-Side Comparison")

# Loop through each result
for row in filtered.to_dict("records"):
    colA,colB = st.columns([1,1])

    with st.expander(f"📝 {row['question'][:80]}...  | A:{row['model_A_score']}  vs  B:{row['model_B_score']}"):

        st.write("### 🔎 Question:")
        st.write(row["question"])

        st.write("### ✍ Student Summary:")
        st.write(row["answer"])

        # ---------------- LEFT: Model A ---------------- #
        with colA:
            st.markdown("### 🧠 Model-A Evaluation (FastAPI)")
            st.write("**Score:**",row["evaluation"].get("score"))
            st.write("**Feedback:**",row["evaluation"].get("feedback"))
            st.write("**Missing Ideas:**",row["evaluation"].get("missing_ideas"))
            st.write("**Keypoints Covered:**")
            st.json(row["evaluation"].get("diagnostics").get("keypoints"))
        
        # ---------------- RIGHT: Model B ---------------- #
        with colB:
            st.markdown("### 🤖 Model-B Evaluation (n8n LLM)")
            try:
                evB = row["evaluation_from_n8n"][0]["output"][0]["output"]

                st.write("**Score:**",evB.get("content_score"))
                st.write("**Relevance:**",evB.get("relevance_level"))
                st.write("**Covered Ideas:**")
                st.json(evB.get("covered_ideas"))
                st.write("**Missing Ideas:**")
                st.json(evB.get("missing_ideas"))
                st.write("**Feedback:**")
                st.write(evB.get("feedback"))

            except:
                st.warning("⚠ No Model-B evaluation available")

        # Summary Card
        st.markdown("---")
        diff = (row["model_A_score"] or 0) - (row["model_B_score"] or 0)
        st.info(f"📌 Score Difference → **Model-A: {row['model_A_score']} | Model-B: {row['model_B_score']} | Δ = {diff}**")

