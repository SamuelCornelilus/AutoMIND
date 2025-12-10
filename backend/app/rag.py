# app/rag.py
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import joblib, os, json
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from .db import get_db
from .models_history import QueryHistory
from .models_auth import User
from .auth import get_current_user

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(ROOT, "models")

ANSWERS_FILE = os.path.join(MODELS_DIR, "ANSWERS_FILE")
VECTORIZER_FILE = os.path.join(MODELS_DIR, "VECTORIZER_FILE")
MATRIX_FILE = os.path.join(MODELS_DIR, "MATRIX_FILE")
QUESTIONS_FILE = os.path.join(MODELS_DIR, "QUESTIONS_FILE")

_vectorizer = None
_matrix = None
_answers = None
_questions = None
_load_error = None

def ensure_models_loaded():
    global _vectorizer, _matrix, _answers, _questions, _load_error
    if _load_error:
        raise RuntimeError("Model loading failed: " + _load_error)
    if _vectorizer is None:
        try:
            _vectorizer = joblib.load(VECTORIZER_FILE)
            _matrix = joblib.load(MATRIX_FILE)
            _answers = joblib.load(ANSWERS_FILE)
            _questions = joblib.load(QUESTIONS_FILE)
        except Exception as e:
            _load_error = str(e)
            raise

def retrieve(query: str, top_k: int = 3):
    ensure_models_loaded()
    q_vec = _vectorizer.transform([query])
    sims = cosine_similarity(q_vec, _matrix).flatten()
    idxs = np.argsort(-sims)[:top_k]

    results = []
    for i in idxs:
        results.append({
            "id": int(i),
            "score": float(sims[i]),
            "text": str(_answers[i])
        })
    return results


router = APIRouter(prefix="/rag/rag", tags=["rag"])

class RagQueryRequest(BaseModel):
    query: str
    top_k: int = 3

class RagDoc(BaseModel):
    id: int
    score: float
    text: str

class RagQueryResponse(BaseModel):
    query: str
    results: List[RagDoc]

class HistoryItem(BaseModel):
    id: int
    user_id: Optional[int]
    query: str
    results: List[RagDoc]
    created_at: str

class HistoryList(BaseModel):
    items: List[HistoryItem]
    total: int

@router.post("/query", response_model=RagQueryResponse)
def rag_query(
    req: RagQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieval API + menyimpan history ke database.
    Hanya bisa diakses jika user login (Bearer token).
    """
    try:
        results = retrieve(req.query, req.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {e}")

    # Save history (stringify results)
    try:
        history = QueryHistory(
            user_id=current_user.id,
            query=req.query,
            results=json.dumps(results, ensure_ascii=False)
        )
        db.add(history)
        db.commit()
    except Exception:
        db.rollback()

    return {"query": req.query, "results": results}


@router.get("/history", response_model=HistoryList)
def get_history(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ambil history query milik user yang sedang login.
    - Authorization: Bearer <token>
    - Query params: limit, offset
    """
    try:
        q = db.query(QueryHistory).filter(QueryHistory.user_id == current_user.id)
        total = q.count()
        rows = q.order_by(QueryHistory.created_at.desc()).limit(limit).offset(offset).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    items = []
    for r in rows:
        try:
            parsed_results = json.loads(r.results)
        except Exception:
            parsed_results = []
        # convert parsed_results items into RagDoc-like dicts
        docs = []
        for it in parsed_results:
            docs.append({
                "id": int(it.get("id", -1)),
                "score": float(it.get("score", 0.0)),
                "text": str(it.get("text", ""))
            })
        items.append({
            "id": r.id,
            "user_id": r.user_id,
            "query": r.query,
            "results": docs,
            "created_at": r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at)
        })

    return {"items": items, "total": total}
