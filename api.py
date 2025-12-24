from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import os 
import shutil
from dotenv import load_dotenv
from llama_index.core import (
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    StorageContext, 
    load_index_from_storage,
    Settings
)
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

# load api key
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# setup models
Settings.llm = GoogleGenAI(model="models/gemini-3-pro-preview", api_key=GOOGLE_API_KEY)
Settings.embed_model = GoogleGenAIEmbedding(model_name="models/gemini-embedding-001", api_key=GOOGLE_API_KEY)

# directories
DATA_DIR = "./data"
PERSIST_DIR = "./storage"

os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI()

def get_chat_engine():
  """ Load the index and return a chat engine """
  if not os.path.exists(PERSIST_DIR):
    return None # index doesnt exist yet
  
  storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
  index = load_index_from_storage(storage_context)
  return index.as_chat_engine(chat_mode="context", prompt="You are a helpful expert.")

# API endpoints
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
  """ Endpoint 1: Frontend sends a PDF here. """
  try:
    # 1. save the file to disk
    file_path = os.path.join(DATA_DIR, file.filename)
    with open(file_path, "wb") as buffer:
      shutil.copyfileobj(file.file, buffer)
    
    # 2. Trigger Indexing immediately
    documents = SimpleDirectoryReader(DATA_DIR).load_data()
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=PERSIST_DIR)
    return {"status": "success", "filename": file.filename, "message": "File indexed successfully"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

class QueryRequest(BaseModel):
  question: str

@app.post("/query")
async def query_index(request: QueryRequest):
  """ Endpoint 2: Frontend asks a question """
  chat_engine = get_chat_engine()
  if not chat_engine:
    raise HTTPException(status_code=400, detail="No index found. Upload a file first.")

  response = await chat_engine.achat(request.question)

  # extract sources for the frontend
  sources = []
  for node in response.source_nodes:
    sources.append({
      "file": node.node.metadata.get('file_name', 'Unknown'),
      "page": node.node.metadata.get('page_label', 'N/A'),
      "text": node.node.get_content()[:200]
    })
  
  return {
    "answer": response.response,
    "sources": sources
  }