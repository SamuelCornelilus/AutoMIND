# backend/build_index.py
"""
Modul sederhana untuk membangun TF-IDF index dan menyimpannya via joblib.

Versi ini aman untuk linting (tidak ada import tak terpakai, tidak ada lambda assignment).
"""

import json
import os
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer


def _no_tqdm(iterable):
    """
    Fallback sederhana jika tqdm tidak tersedia: kembalikan iterable apa adanya.
    Ditulis sebagai fungsi (bukan lambda) agar linter tidak mengeluh.
    """
    return iterable


def safe_tqdm():
    """
    Mengembalikan fungsi progres.
    Jika tqdm tersedia, gunakan tqdm asli, jika tidak gunakan dummy function.
    """
    try:
        from tqdm import tqdm  # type: ignore

        return tqdm
    except Exception:
        return _no_tqdm


tqdm = safe_tqdm()


def load_dataset(json_path: str) -> list[str]:
    """
    Memuat dataset JSON berisi list of question-answer.
    Format contoh:
    { "qa_pairs": [ {"question": "...", "answer": "..."}, ... ] }

    Mengembalikan list pertanyaan (questions).
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Dataset tidak ditemukan: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # format fleksibel
    if isinstance(data, dict) and "qa_pairs" in data:
        items = data.get("qa_pairs", [])
    elif isinstance(data, list):
        items = data
    else:
        items = data.get("questions", []) if isinstance(data, dict) else []

    questions = [
        item["question"]
        for item in items
        if isinstance(item, dict) and "question" in item
    ]

    return questions


def build_tfidf_index(questions: list[str], save_dir: str):
    """
    Membangun TF-IDF index dan menyimpannya ke folder save_dir.
    """
    if not questions:
        raise ValueError("Dataset pertanyaan kosong.")

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(tqdm(questions))

    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    joblib.dump(vectorizer, save_path / "tfidf_vectorizer.joblib")
    joblib.dump(tfidf_matrix, save_path / "tfidf_matrix.joblib")

    print(f"[OK] TF-IDF index saved to: {save_path}")


if __name__ == "__main__":
    dataset_path = "data/raw_dataset.json"
    output_dir = "backend/models"

    questions = load_dataset(dataset_path)
    build_tfidf_index(questions, output_dir)
