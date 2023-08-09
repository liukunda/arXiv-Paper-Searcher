
from langchain.callbacks import StdOutCallbackHandler
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.chains.base import Chain
from langchain.document_loaders import PyPDFLoader

class Chain():
    def __init__(self,pdf_path) -> None:
        self.pdf_path = pdf_path
        self.loader = PyPDFLoader(self.pdf_path.strip())
        self.documents = self.loader.load_and_split()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            add_start_index=True,
        )

        self.paragraphs = text_splitter.create_documents(
            [d.page_content for d in self.documents])
        self.embeddings = OpenAIEmbeddings(model='text-embedding-ada-002')
        self.db = FAISS.from_documents(self.paragraphs, self.embeddings)
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(temperature=0),
            chain_type="stuff",
            retriever=self.db.as_retriever(),
            verbose=True
        )

    def get_answer(self,ask):
        result = self.qa_chain(ask)
        return result