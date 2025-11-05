# import os
# import threading
# from pathlib import Path
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import FileResponse
# from fastapi.staticfiles import StaticFiles
# from pydantic import BaseModel
# import uvicorn
#
#
# from LocalSearch.backend.engine import SearchEngine
# from LocalSearch.backend.directory.embedding_processor import generate_embeddings
# FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
# FRONTEND_PATH = FRONTEND_DIR / "index.html"
#
# app = FastAPI(title="Local AI Search Backend")
# app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR.resolve())), name="frontend")
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# # Models
# class ProcessRequest(BaseModel):
#     path: str
#     force: bool = False
#
# class AskRequest(BaseModel):
#     path: str
#     question: str
#
# # Engines storage
# _engines = {}
#
# @app.get("/")
# def index():
#     return FileResponse(str(FRONTEND_PATH.resolve()))
#
# @app.post("/process")
# def process_folder(req: ProcessRequest):
#     folder_path = req.path
#     force = req.force
#
#     if not os.path.exists(folder_path):
#         return {"status": "error", "message": "Folder does not exist."}
#
#     generate_embeddings(folder_path, force=force)
#     _engines[folder_path] = SearchEngine(folder_path)
#     return {"status": "done"}
#
# @app.post("/ask")
# def ask_question(req: AskRequest):
#     folder_path = req.path
#     question = req.question
#
#     if folder_path not in _engines:
#         _engines[folder_path] = SearchEngine(folder_path)
#
#     engine = _engines[folder_path]
#     answer = engine.search(question)
#     return {"answer": answer}
#
#
# # Helper to run FastAPI in a thread
#
