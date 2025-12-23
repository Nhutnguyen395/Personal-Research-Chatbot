import os
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

# 1. load the google api key
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# 2. configure LlamaIndex to use Gemini
# use "Gemini 1.5 Flash" because its fast and free
Settings.llm = GoogleGenAI(model="models/gemini-3-pro-preview", api_key=GOOGLE_API_KEY)

# use google embedding model
Settings.embed_model = GoogleGenAIEmbedding(model_name="models/gemini-embedding-001", api_key=GOOGLE_API_KEY)

DATA_DIR = "./data"
PERSIST_DIR = "./storage"

def main():
  if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    print(f"Created {DATA_DIR}. Please put a PDF inside it and run again.")
    return
  
  # check if we already have an index on disk
  if not os.path.exists(PERSIST_DIR):
    print("Indexing documents wth Gemini... (this might take few seconds)")
    documents = SimpleDirectoryReader(DATA_DIR).load_data()

    # this will now use Gemini for both Embeddings and LLM
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=PERSIST_DIR)
    print("Saved index to storage.")
  else:
    print("Loading index from storage...")
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)

  # ask the question
  query_engine = index.as_query_engine()

  print("\n--- Ask Gemini a question about your pdf ---")
  while True:
    user_q = input("Question (or 'q' to quit): ")
    if user_q.lower() == 'q':
      break

    response = query_engine.query(user_q)
    print(f"\nAnswer: {response}\n")

if __name__ == "__main__":
    main()