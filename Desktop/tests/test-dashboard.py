import streamlit as st
from pymongo import MongoClient
import pandas as pd

# ------------------ MongoDB Connection ------------------ #
MONGO_URI = "mongodb+srv://shubhamgehlod_db_user:3HUdgGMZ10kMAvBa@languagetranscript.4hisuze.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)

db = client["LA_writing-database"]
col = db["evaluation-ai"]     # using this dataset


# ---------------- UI ---------------- #
st.set_page_config(page_title="Model Comparison Dashboard", layout="wide")
st.title("🧠 Semantic matching vs LLM ")
st.markdown("<h2 style='text-align:center;'>Model Evaluation Comparison</h2>", unsafe_allow_html=True)

data = list(col.find({}, {"_id":0}))
df = pd.DataFrame(data)


question_text = df.get("question", "No question found").iloc[0]

# Center alignment block
st.markdown("<p style='text-align:center; font-size:18px;'>QUESTION</p>", unsafe_allow_html=True)
st.markdown(
    f"""
    <div style="
        text-align:center;
        font-size:15px;
        font-weight:600;
        padding:18px;
        margin-top:10px;
        margin-bottom:25px;
        border-radius:10px;
        background:#f5f5f5;
        border:1px solid #ddd;
        width:80%;
        margin-left:auto;
        margin-right:auto;">
        {question_text}
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------- SCORE EXTRACTION ---------------- #

# Model-A
def extract_model_A(row):
    ev = row.get("evaluation")
    if isinstance(ev, dict):
        return ev.get("score") or ev.get("content_score")
    return None

df["model_A_score"] = df.apply(extract_model_A, axis=1)


# Model-B (Universal parser)
def extract_model_B(row):
    ev = row.get("evaluation_ai")

    # Format 1 -> list
    try:
        return ev[0]["output"][0]["output"].get("content_score")
    except:
        pass

    # Format 2 -> dict.output
    try:
        return ev["output"][0]["output"].get("content_score")
    except:
        pass

    # Format 3 -> fallback safety
    try:
        return ev.get("output", [{}])[0].get("output", {}).get("content_score")
    except:
        pass

    return None

df["model_B_score"] = df.apply(extract_model_B, axis=1)


# ---------------- FILTERS ---------------- #
st.sidebar.header("Filters")
min_A = st.sidebar.slider("Min Model-A Score",0,6,0)
min_B = st.sidebar.slider("Min Model-B Score",0,6,0)

filtered = df[
    (df["model_A_score"].fillna(-1) >= min_A) &
    (df["model_B_score"].fillna(-1) >= min_B)
]


# ---------------- OVERVIEW (Now Summary instead of Question) ---------------- #
st.subheader("📄 Summary View (A vs B Scores)")


summary_view = filtered[["answer","model_A_score","model_B_score"]].rename(
    columns={"answer":"summary"}
)
st.markdown(f"**Total Summaries: {len(summary_view)}**")
st.dataframe(summary_view, height=350)


# ---------------- CSV EXPORT ---------------- #
st.markdown("### 📥 Download CSV (Summary + Scores)")

csv = summary_view.to_csv(index=False).encode("utf-8")

st.download_button("⬇ Download CSV", csv, "summary_scores_model_comparison.csv")


# ---------------- Detailed Comparison ---------------- #
st.markdown("---")
st.subheader("🔍 Detailed Comparison | Evaluation Breakdown")

for row in filtered.to_dict("records"):
    A = row["model_A_score"]
    B = row["model_B_score"]

    with st.expander(f"📝 Summary Preview: {row['answer'][:60]}... | A:{A} vs B:{B}"):

        st.write("### 🧾 Question (for context)")
        st.write(row["question"])

        st.write("### ✍ Student Summary")
        st.write(row["answer"])

        colA, colB = st.columns(2)

        # ------------ MODEL A ------------ #
        with colA:
            st.subheader("🧠 Model-A Evaluation")
            evA = row.get("evaluation") or {}
            diag = evA.get("diagnostics") or {}

            st.write("Score:", evA.get("score"))
            st.write("Feedback:", evA.get("feedback"))
            st.write("Missing Ideas:", evA.get("missing_ideas"))
            st.write("Key Points:")
            st.json(diag.get("keypoints"))


        # ------------ MODEL B ------------ #
        with colB:
            st.subheader("🤖 Model-B Evaluation")

            ev = row.get("evaluation_ai")
            try:
                evB = (ev[0]["output"][0]["output"]
                       if isinstance(ev, list)
                       else ev["output"][0]["output"])

                st.write("Score:", evB.get("content_score"))
                st.write("Relevance:", evB.get("relevance_level"))
                st.write("Covered Ideas:")
                st.json(evB.get("covered_ideas"))
                st.write("Missing Ideas:")
                st.json(evB.get("missing_ideas"))
                st.write("Feedback:")
                st.write(evB.get("feedback"))

            except:
                st.warning("⚠ Model-B evaluation missing/invalid")

        st.info(f"📌 Score Difference → A:{A} | B:{B} | Δ = {A-B}")
