# backend/build_index.py
"""
Robust TF-IDF index builder for AutoMIND.

Features:
- Reads dataset from ../data/raw_dataset.json (project root /data/)
- Preprocessing: lowercasing, regex tokenization, stopword removal,
  optional stemming (uses NLTK Porter if available else simple fallback)
- Corpus = question + " " + answer (improves retrieval recall)
- Vectorizer: TF-IDF (ngram 1..2)
- Saves artifacts to backend/models/
- Portable: avoids NLTK downloads; uses fallback lists if NLTK not present.

Run:
  (.venv) C:\... \AutoMIND\backend> python build_index.py
"""

from pathlib import Path
import json
import joblib
import re
import sys
import argparse
from time import time

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.utils import check_random_state

# Optional progress printing
try:
    from tqdm import tqdm
except Exception:
    tqdm = lambda x: x  # noop


# ---------- Config ----------
BASE = Path(__file__).resolve().parent           # backend/
PROJECT_ROOT = BASE.parent                        # AutoMIND/
DATA_DIR = PROJECT_ROOT / "data"
DATASET_PATH = DATA_DIR / "raw_dataset.json"
MODEL_DIR = BASE / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_MAX_FEATURES = 50000
_TOKEN_PATTERN = re.compile(r"\b[a-zA-Z0-9]+\b")  # simple alnum tokenization

# ---------- Stopwords & Stemmer (try to use NLTK if available) ----------
USE_NLTK = False
try:
    import nltk
    from nltk.corpus import stopwords as _nltk_stopwords
    from nltk.stem import PorterStemmer as _NltkPorter
    # attempt to load stopwords (may raise LookupError if not downloaded)
    try:
        STOP_WORDS = set(_nltk_stopwords.words("english"))
        stemmer = _NltkPorter()
        USE_NLTK = True
    except Exception:
        # fallback if NLTK data not installed
        raise
except Exception:
    STOP_WORDS = {
        "a","an","the","and","or","is","are","was","were","in","on","of","for",
        "to","with","as","by","that","this","it","from","at","be","which","but",
        "has","have","had","will","would","can","could","should","may","might",
        "not","we","you","they","he","she","i","me","my","our","their","its"
    }
    # Simple lightweight suffix-stripping stemmer (fallback)
    class SimpleStemmer:
        def __init__(self):
            # ordered suffixes to remove (basic)
            self.sufs = ("ing","edly","edly","edly","edly","edly","edly","edly",
                         "edly","ed","es","s","ment","tion","ions","er","est","ly")
        def stem(self, w):
            if len(w) <= 3:
                return w
            for s in self.sufs:
                if w.endswith(s) and len(w) - len(s) >= 3:
                    return w[: -len(s)]
            return w
    stemmer = SimpleStemmer()

def _stem_token(tok: str) -> str:
    """Return stemmed token. Uses NLTK stemmer if available, else fallback."""
    if USE_NLTK:
        return stemmer.stem(tok)
    else:
        return stemmer.stem(tok)


# ---------- Preprocessing ----------
def preprocess_text(text: str) -> str:
    """
    Lowercase, tokenise on alphanumeric tokens, remove stopwords, stem tokens.
    Returns a single whitespace-joined string (ready for TF-IDF).
    """
    if not isinstance(text, str):
        return ""
    t = text.lower()
    tokens = _TOKEN_PATTERN.findall(t)
    tokens = [tok for tok in tokens if tok not in STOP_WORDS]
    tokens = [_stem_token(tok) for tok in tokens]
    return " ".join(tokens)


# ---------- Load dataset ----------
def load_dataset(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at: {path}")
    with path.open("r", encoding="utf8") as f:
        data = json.load(f)

    questions = []
    answers = []
    combined = []
    seen_q_norm = set()
    for idx, item in enumerate(data):
        q = item.get("question", "")
        a = item.get("answer", "")
        if not isinstance(q, str) or not isinstance(a, str):
            # skip invalid entries but warn
            print(f"[WARN] skipping non-string QA at index {idx}", file=sys.stderr)
            continue
        q_stripped = q.strip()
        a_stripped = a.strip()
        if not q_stripped or not a_stripped:
            print(f"[WARN] skipping empty QA at index {idx}", file=sys.stderr)
            continue
        # basic duplicate detection using normalized question
        qnorm = re.sub(r"\s+", " ", q_stripped.lower())
        if qnorm in seen_q_norm:
            # skip duplicate question (keep first)
            continue
        seen_q_norm.add(qnorm)
        questions.append(q_stripped)
        answers.append(a_stripped)
        combined.append(f"{q_stripped} {a_stripped}")
    return questions, answers, combined


# ---------- Build TF-IDF ----------
def build_index(dataset_path: Path, model_dir: Path, max_features: int = DEFAULT_MAX_FEATURES):
    start = time()
    print(f"Using dataset path: {dataset_path}")
    questions, answers, combined = load_dataset(dataset_path)
    n = len(combined)
    if n == 0:
        raise RuntimeError("No valid QA pairs found in dataset.")
    print(f"Loaded {n} QA pairs (unique questions kept)")

    # Preprocess corpus (tokenize, stopword remove, stem)
    print("Preprocessing text...")
    corpus = []
    for doc in tqdm(combined):
        corpus.append(preprocess_text(doc))

    print("Vectorizing TF-IDF...")
    vectorizer = TfidfVectorizer(ngram_range=(1,2),
                                 max_df=0.85,
                                 min_df=1,
                                 max_features=max_features,
                                 token_pattern=r"(?u)\b\w+\b")

    X = vectorizer.fit_transform(corpus)
    print(f"TF-IDF matrix shape: {X.shape}")

    # Save artifacts
    print("Saving artifacts to:", model_dir)
    joblib.dump(vectorizer, model_dir / "tfidf_vectorizer.joblib", compress=3)
    joblib.dump(questions, model_dir / "questions.joblib", compress=3)
    joblib.dump(answers, model_dir / "answers.joblib", compress=3)
    joblib.dump(X, model_dir / "tfidf_matrix.joblib", compress=3)

    meta = {
        "n_pairs": n,
        "matrix_shape": X.shape,
        "max_features": max_features,
        "use_nltk": bool(USE_NLTK)
    }
    with (model_dir / "meta.json").open("w", encoding="utf8") as mf:
        json.dump(meta, mf, indent=2)

    elapsed = time() - start
    print(f"Index built and saved in {elapsed:.2f} seconds.")
    print("Artifacts:")
    for p in ("tfidf_vectorizer.joblib","questions.joblib","answers.joblib","tfidf_matrix.joblib","meta.json"):
        print(" -", model_dir / p)


# ---------- CLI ----------
def parse_args():
    p = argparse.ArgumentParser(description="Build TF-IDF index for AutoMIND")
    p.add_argument("--data", "-d", type=str, default=str(DATASET_PATH), help="path to raw_dataset.json")
    p.add_argument("--out", "-o", type=str, default=str(MODEL_DIR), help="directory to save models")
    p.add_argument("--max-features", "-m", type=int, default=DEFAULT_MAX_FEATURES, help="max TF-IDF features")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_index(Path(args.data), Path(args.out), max_features=args.max_features)
