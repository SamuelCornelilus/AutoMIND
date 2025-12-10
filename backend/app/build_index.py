# build_index.py
"""
Simple index builder/loader for AutoMIND.
- If files exist in `models/` with names VECTORIZER_FILE, MATRIX_FILE, QUESTIONS_FILE, ANSWERS_FILE
  this script will try to load them and test a small query.
- If they don't exist, the script can build them from a plain text file at `data/docs.txt`
  where each line is one document (question+answer or text). The script will split each
  line into a 'question' and 'answer' automatically if it finds a delimiter '|||'.
  Format examples:
    Question text ||| Answer text
    Or a single line of text used as both question and answer.
- Output files are saved to models/ with the existing filenames your project uses.
"""

from pathlib import Path
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
import json
import sys

# File names used in your repo (match what you reported)
MODELS_DIR = Path("models")
VECTORIZER_FILE = MODELS_DIR / "VECTORIZER_FILE"
MATRIX_FILE = MODELS_DIR / "MATRIX_FILE"
QUESTIONS_FILE = MODELS_DIR / "QUESTIONS_FILE"
ANSWERS_FILE = MODELS_DIR / "ANSWERS_FILE"
META_FILE = MODELS_DIR / "meta.json"

# fallback input if we need to build
DATA_INPUT = Path("data") / "docs.txt"  # create this if you want to build from scratch

def ensure_nltk():
    # safe guard: download minimal resources if not present
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        print("Downloading NLTK punkt...")
        nltk.download("punkt", quiet=True)

def load_existing_models():
    """Try to load existing vectorizer/matrix/questions/answers. Returns tuple or raises."""
    if not MODELS_DIR.exists():
        raise FileNotFoundError(f"{MODELS_DIR} tidak ada. Buat folder models/ dan tempatkan file model Anda.")
    for p in (VECTORIZER_FILE, MATRIX_FILE, QUESTIONS_FILE, ANSWERS_FILE):
        if not p.exists():
            raise FileNotFoundError(f"Missing model file: {p}")
    print("Memuat model dari folder models/ ...")
    vectorizer = joblib.load(VECTORIZER_FILE)
    matrix = joblib.load(MATRIX_FILE)
    questions = joblib.load(QUESTIONS_FILE)
    answers = joblib.load(ANSWERS_FILE)
    meta = {}
    if META_FILE.exists():
        try:
            meta = json.loads(META_FILE.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    print("Model berhasil dimuat.")
    return vectorizer, matrix, questions, answers, meta

def build_from_input():
    """Build vectorizer+matrix from data/docs.txt. Each line is a doc.
       If a line contains '|||', split left=question, right=answer."""
    if not DATA_INPUT.exists():
        raise FileNotFoundError(f"Tidak menemukan {DATA_INPUT}. Siapkan file atau taruh model di folder models/ .")
    ensure_nltk()
    texts = []
    questions = []
    answers = []
    with DATA_INPUT.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            if "|||" in ln:
                q, a = [p.strip() for p in ln.split("|||", 1)]
            else:
                q, a = ln, ln
            questions.append(q)
            answers.append(a)
            texts.append(q)  # we index questions (you can change to index answers or both)
    print(f"Menemukan {len(texts)} dokumen di {DATA_INPUT}. Membuat TF-IDF vectorizer ...")
    vect = TfidfVectorizer(max_features=50000)
    matrix = vect.fit_transform(texts)
    # save to models/
    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(vect, VECTORIZER_FILE)
    joblib.dump(matrix, MATRIX_FILE)
    joblib.dump(questions, QUESTIONS_FILE)
    joblib.dump(answers, ANSWERS_FILE)
    meta = {"n_pairs": len(questions)}
    META_FILE.write_text(json.dumps(meta), encoding="utf-8")
    print("Selesai build. Model tersimpan di folder models/.")
    return vect, matrix, questions, answers, meta

def query_topk(vectorizer, matrix, questions, answers, query, top_k=3):
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, matrix).ravel()
    idx = np.argsort(-sims)[:top_k]
    results = []
    for i in idx:
        results.append({"id": int(i), "score": float(sims[i]), "question": questions[i], "answer": answers[i]})
    return results

def main():
    print("==== build_index.py ====")
    try:
        vect, matrix, questions, answers, meta = load_existing_models()
    except FileNotFoundError as e:
        print("Model tidak lengkap:", e)
        print("Mencoba membangun dari", DATA_INPUT)
        try:
            vect, matrix, questions, answers, meta = build_from_input()
        except Exception as e2:
            print("Gagal membangun index:", e2)
            sys.exit(1)

    # quick test query (interactive) - jika pengguna memberikan argumen, jalankan query itu
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print("Menjalankan query test:", query)
        results = query_topk(vect, matrix, questions, answers, query, top_k=3)
        print("Hasil:")
        for r in results:
            print(f"- id={r['id']} score={r['score']:.4f} question={r['question']!s}")
        return

    # jika tidak ada argumen, tampilkan contoh interaktif sederhana
    print("Index siap. Coba mengetik sebuah pertanyaan (ketik 'exit' untuk keluar):")
    while True:
        try:
            q = input(">> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nKeluar.")
            break
        if not q or q.lower() in ("exit", "quit"):
            print("Selesai.")
            break
        res = query_topk(vect, matrix, questions, answers, q, top_k=3)
        for r in res:
            print(f"[{r['id']}] (score {r['score']:.4f}) Q: {r['question']}")
            print(f"     A: {r['answer']}")
        print("-" * 40)

if __name__ == "__main__":
    main()
