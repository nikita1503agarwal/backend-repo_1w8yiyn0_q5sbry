import os
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Worksheet, Reflection, QuizSubmission, QuizQuestion

app = FastAPI(title="Network Topology Learning API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Network Topology Learning Backend"}


# ---- Static quiz bank (can be extended or moved to DB later) ----
QUIZ_BANK: Dict[str, Dict[str, Any]] = {
    "network-topologies": {
        "title": "Computer Network Topologies",
        "questions": [
            {
                "id": "q1",
                "question": "Which topology uses a central hub/switch to connect all nodes?",
                "options": ["Bus", "Star", "Ring", "Mesh"],
                "answer": 1,
            },
            {
                "id": "q2",
                "question": "In which topology does data travel in one direction around a closed loop?",
                "options": ["Ring", "Tree", "Hybrid", "Bus"],
                "answer": 0,
            },
            {
                "id": "q3",
                "question": "Which topology provides multiple redundant paths between nodes?",
                "options": ["Mesh", "Bus", "Star", "Tree"],
                "answer": 0,
            },
            {
                "id": "q4",
                "question": "A backbone cable with terminators at both ends describes which topology?",
                "options": ["Bus", "Star", "Tree", "Hybrid"],
                "answer": 0,
            },
            {
                "id": "q5",
                "question": "Which topology is a hierarchical combination of star topologies?",
                "options": ["Mesh", "Tree", "Ring", "Bus"],
                "answer": 1,
            },
            {
                "id": "q6",
                "question": "A network combining multiple topology types is called?",
                "options": ["Composite", "Mixed", "Hybrid", "Aggregate"],
                "answer": 2,
            },
        ],
    }
}


# ---- Models for responses ----
class QuizDefinition(BaseModel):
    title: str
    questions: List[QuizQuestion]


# ---- Database helpers ----

def collection_name(model_cls) -> str:
    return model_cls.__name__.lower()


# ---- Worksheet Endpoints ----
@app.post("/api/worksheets")
def submit_worksheet(payload: Worksheet):
    try:
        inserted_id = create_document(collection_name(Worksheet), payload)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/worksheets")
def list_worksheets():
    try:
        docs = get_documents(collection_name(Worksheet))
        # Convert ObjectId to string
        for d in docs:
            d["_id"] = str(d["_id"]) if "_id" in d else None
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Reflection Endpoints ----
@app.post("/api/reflections")
def submit_reflection(payload: Reflection):
    # Validate worksheet_id is a valid ObjectId
    try:
        _ = ObjectId(payload.worksheet_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid worksheet_id")

    try:
        inserted_id = create_document(collection_name(Reflection), payload)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Quiz Endpoints ----
@app.get("/api/quizzes/{quiz_key}", response_model=QuizDefinition)
def get_quiz(quiz_key: str):
    data = QUIZ_BANK.get(quiz_key)
    if not data:
        raise HTTPException(status_code=404, detail="Quiz not found")
    questions = [QuizQuestion.model_validate({"id": q["id"], "question": q["question"], "options": q["options"]}) for q in data["questions"]]
    return QuizDefinition(title=data["title"], questions=questions)


@app.post("/api/quizzes/{quiz_key}/submit")
def submit_quiz(quiz_key: str, payload: QuizSubmission):
    data = QUIZ_BANK.get(quiz_key)
    if not data:
        raise HTTPException(status_code=404, detail="Quiz not found")
    correct = 0
    details = []
    total = len(data["questions"])
    for q in data["questions"]:
        qid = q["id"]
        selected = payload.answers.get(qid, -1)
        is_correct = int(selected) == int(q["answer"])  # be tolerant of types
        if is_correct:
            correct += 1
        details.append({
            "id": qid,
            "question": q["question"],
            "selected": selected,
            "correct_answer": q["answer"],
            "is_correct": is_correct,
        })
    score = correct
    result = {
        "student_name": payload.student_name,
        "quiz_key": quiz_key,
        "score": score,
        "total": total,
        "details": details,
    }
    # Persist quiz result
    try:
        create_document("quizsubmission", result)
    except Exception:
        pass
    return result


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
