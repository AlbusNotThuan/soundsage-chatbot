import chromadb
import dotenv
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter

DATA_PATH = "data/"
CHROMA_PATH = "chroma_data/"

dotenv.load_dotenv()

documents = []
for file in os.listdir(DATA_PATH):
    if file.endswith('.pdf'):
        pdf_path = os.path.join(DATA_PATH, file)
        loader = PyPDFLoader(pdf_path)
        documents.extend(loader.load())


text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=10)
chunked_documents = text_splitter.split_documents(documents)


client = chromadb.Client()
if client.list_collections():
    consent_collection = client.create_collection("consent_collection")
else:
    print("Collection already exists")
vectordb = Chroma.from_documents(
    documents=chunked_documents,
    embedding=OpenAIEmbeddings(),
    persist_directory=CHROMA_PATH,
)
vectordb.persist()