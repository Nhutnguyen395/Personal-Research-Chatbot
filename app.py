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
# choosing to use gemini 3 pro
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

  # instead of as_query_engine, use as_chat_engine
  # chat_mode = "context" to look at the documents and the chat history
  chat_engine = index.as_chat_engine(chat_mode="context", system_prompt="You are a helpful research assistant. Always cite your sources.")

  print("\n--- Ask Gemini (Now with Memory!) ---")
  print("Type 'q' to quit.\n")
  while True:
    user_q = input("You: ")
    if user_q.lower() == 'q':
      break
    
    response = chat_engine.stream_chat(user_q)
    print("\nAI: ", end="")
    
    # loops through the token as they arrive like ChatGPT typing out
    for token in response.response_gen:
      print(token, end="", flush=True)

    # Cite Sourse: the 'source_nodes' lists the exact chunks the AI used
    print("--- Sources Used ---")
    for node in response.source_nodes:
      # get metadata (page number, filename)
      meta = node.node.metadata
      # get snippet of the text it read
      snippet = node.node.get_content()[:50].replace("\n", " ")
      print(f"File: {meta.get('file_name', 'Unknown')} | Page: {meta.get('page_label', 'N/A')}")
      print(F"Snippet: \"{snippet}...\"\n")

if __name__ == "__main__":
    main()