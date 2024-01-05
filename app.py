import os
from config import *
import src.view.legacy_view as legacy_view
import src.view.view_user2 as view_user2
from src.control.control import Chatbot
import chromadb
from src.tools.retriever import Retriever
from src.tools.llm_factory import create_llm_agent  # Import the factory function
from config import use_open_source_generation
import logging
import logging.config
from src.view.new_view import merge_dash_admin as view_admin

os.environ["TOKENIZERS_PARALLELISM"] = "true"

if not "OPENAI_API_KEY" in os.environ:
    from config_key import OPENAI_API_KEY
    os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

llm_agent = create_llm_agent(use_open_source_generation)

if not os.path.exists("database_test/"): 
    os.makedirs("database_test/")
    
client_db = chromadb.PersistentClient("database_test/")

logging.config.fileConfig('logging_config.ini')


chat = Chatbot(client_db=client_db, llm_agent=llm_agent, retriever=Retriever(llmagent=llm_agent))

ilumio_qna_admin = view_admin.run(ctrl=chat, config=view_config)

ilumio_qna_admin.queue().launch()
