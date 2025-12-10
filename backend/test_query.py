# backend/test_query.py
import joblib
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parent
vec = joblib.load(BASE / "models" / "tfidf_vectorizer.joblib")
X = joblib.load(BASE / "models" / "tfidf_matrix.joblib")
questions = joblib.load(BASE / "models" / "questions.joblib")
answers = joblib.load(BASE / "models" / "answers.joblib")

def simple_query(q, top_k=3):
    v = vec.transform([q])
    sims = cosine_similarity(v, X).flatten()
    idx = np.argsort(-sims)[:top_k]
    out = []
    for i in idx:
        out.append((float(sims[i]), questions[i], answers[i]))
    return out

if __name__ == "__main__":
    q = "Apa fungsi sensor LiDAR pada AGV?"
    print(simple_query(q, top_k=5))
