from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from src.config import BGE_MODEL_NAME, CHROMA_PERSIST_DIR, COLLECTION_NAME

def get_embedding_function():
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': True}  # normalise for cosine similarity

    embeddings = HuggingFaceEmbeddings(
        model_name=BGE_MODEL_NAME,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
    )
    return embeddings

def get_vectorstore():
    embeddings = get_embedding_function()
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR
    )
    return vectorstore
