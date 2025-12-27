import requests
from pymongo import MongoClient

# ------------------ MongoDB Connection ------------------ #
MONGO_URI = "mongodb+srv://shubhamgehlod_db_user:3HUdgGMZ10kMAvBa@languagetranscript.4hisuze.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)

db = client["LA_writing-database"]
test_col = db["evaluation-dataset1"]      
API_URL = "http://127.0.0.1:8000/score/content"  

# ------------------ Evaluation Runner ------------------ #
def evaluate_all():
    print("🔍 Fetching documents without evaluation...")

    # ⚡ Only pick docs which don't have evaluation yet
    docs = test_col.find({"evaluation": {"$exists": False}}, {"question":1, "answer":1})

    pending = test_col.count_documents({"evaluation": {"$exists": False}})
    print(f"🚀 Total pending evaluations: {pending}\n")

    for doc in docs:
        print(f"➡ Evaluating: {doc['_id']}")

        payload = {
            "passage": doc.get("question", ""),
            "summary": doc.get("answer", "")
        }

        res = requests.post(API_URL, json=payload)
        print("📡 Status:", res.status_code)

        if res.status_code != 200:
            print(f"❌ API Failed for {doc['_id']}\n")
            continue

        data = res.json()

        # 🔥 updating the same document (no duplicate collection)
        test_col.update_one(
            {"_id": doc["_id"]},
            {"$set": {"evaluation": data}}
        )

        print(f"✔ Saved → {doc['_id']} Score={data['score']}\n")

    print("🎉 All pending documents evaluated successfully!")


# ------------------ Execute ------------------ #
if __name__ == "__main__":
    print("📌 Running Evaluation Script...\n")
    evaluate_all()
