import streamlit as st
from pymongo import MongoClient
import pandas as pd

# ------------------ MongoDB Connection ------------------ #
MONGO_URI = "mongodb+srv://shubhamgehlod_db_user:3HUdgGMZ10kMAvBa@languagetranscript.4hisuze.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)

db = client["LA_writing-database"]
col = db["evaluation-ai"]     # <- dataset confirmed


# ---------------- UI ---------------- #
st.set_page_config(page_title="Model Comparison Dashboard", layout="wide")
st.title("🧠 Model-A vs Model-B Evaluation Comparison Dashboard")

data = list(col.find({}, {"_id":0}))
df = pd.DataFrame(data)

st.write("📦 Total Records Loaded:", len(df))


# ---------------- SCORE EXTRACTION ---------------- #

# Model-A extraction
def extract_model_A(row):
    ev = row.get("evaluation")
    if isinstance(ev, dict):
        return ev.get("score") or ev.get("content_score")
    return None

df["model_A_score"] = df.apply(extract_model_A, axis=1)


# Model-B extraction (UNIVERSAL HANDLER)
def extract_model_B(row):
    ev = row.get("evaluation_ai")

    # Format 1 -> evaluation_ai[0].output[0].output (12 docs)
    try:
        return ev[0]["output"][0]["output"].get("content_score")
    except:
        pass

    # Format 2 -> evaluation_ai.output[0].output (major docs)
    try:
        return ev["output"][0]["output"].get("content_score")
    except:
        pass

    # Format 3 -> fallback if direct dict
    try:
        return ev.get("output", [{}])[0].get("output", {}).get("content_score")
    except:
        pass

    return None

df["model_B_score"] = df.apply(extract_model_B, axis=1)


# Sanity Check Display
st.write("🟢 Model-A Score Extracted:", df["model_A_score"].notna().sum())
st.write("🟢 Model-B Score Extracted:", df["model_B_score"].notna().sum())


# ---------------- FILTERS ---------------- #
st.sidebar.header("Filters")
min_A = st.sidebar.slider("Min Model-A Score",0,6,0)
min_B = st.sidebar.slider("Min Model-B Score",0,6,0)

filtered = df[
    (df["model_A_score"].fillna(-1) >= min_A) &
    (df["model_B_score"].fillna(-1) >= min_B)
]


# ---------------- OVERVIEW TABLE ---------------- #
st.subheader("📄 Overview (A vs B Scores)")
st.dataframe(filtered[["question","model_A_score","model_B_score"]], height=350)


# ---------------- CSV EXPORT ---------------- #
st.markdown("### 📥 Export CSV")

export_df = filtered[["question","answer","model_A_score","model_B_score"]].copy()
export_df["question_short"] = export_df["question"].apply(
    lambda x: x[:60]+"..." if isinstance(x,str) and len(x)>60 else x
)

csv = export_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇ Download CSV", csv, "model_comparison_results.csv")


# ---------------- DETAILED SIDE-BY-SIDE VIEW ---------------- #
st.markdown("---")
st.subheader("🔍 Detailed Side-by-Side Comparison")

for row in filtered.to_dict("records"):
    A = row["model_A_score"]
    B = row["model_B_score"]

    with st.expander(f"📝 {row['question'][:70]}... | A:{A} vs B:{B}"):

        st.write("### 🔎 Question")
        st.write(row["question"])

        st.write("### ✍ Student Answer")
        st.write(row["answer"])

        colA,colB = st.columns(2)

        # -------- Model A -------- #
        with colA:
            st.markdown("### 🧠 Model-A Evaluation")

            evA = row.get("evaluation") or {}
            diag = evA.get("diagnostics") or {}

            st.write("**Score:**", evA.get("score"))
            st.write("**Feedback:**", evA.get("feedback"))
            st.write("**Missing Ideas:**", evA.get("missing_ideas"))
            st.write("**Keypoints:**")
            st.json(diag.get("keypoints"))


        # -------- Model B -------- #
        with colB:
            st.markdown("### 🤖 Model-B Evaluation")

            ev = row.get("evaluation_ai")

            try:
                # auto detect format to display full block
                evB = (ev[0]["output"][0]["output"]
                       if isinstance(ev, list)
                       else ev["output"][0]["output"])

                st.write("**Score:**", evB.get("content_score"))
                st.write("**Relevance:**", evB.get("relevance_level"))
                st.write("**Covered Ideas:**")
                st.json(evB.get("covered_ideas"))
                st.write("**Missing Ideas:**")
                st.json(evB.get("missing_ideas"))
                st.write("**Feedback:**")
                st.write(evB.get("feedback"))

            except:
                st.warning("⚠ Model-B evaluation missing/invalid")


        st.info(f"📌 Score Difference → A:{A} | B:{B} | Δ = {A-B}")
