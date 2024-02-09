import os
from config import *
import src.view.legacy_view as legacy_view
import src.view.view_user as view_user
#import src.view.view_admin as view_admin 
from src.view.new_admin_view import GradioInterface
from src.control.control import Chatbot
import chromadb
from src.tools.retriever import Retriever
from src.Llm.llm_factory import create_llm_agent  # Import the factory function
from config import use_open_source_generation
import logging
import logging.config
import streamlit as st

os.environ["TOKENIZERS_PARALLELISM"] = "true"

if not "OPENAI_API_KEY" in os.environ:
    from config_key import OPENAI_API_KEY
    os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

llm_agent = create_llm_agent(use_open_source_generation)

if not os.path.exists("database_demo/"): 
    os.makedirs("database_demo/")
    
client_db = chromadb.PersistentClient("database_demo/")

logging.config.fileConfig('/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Chatbot_llama2_questions/src/Logs/logging_config.ini')
#client_db.create_collection("tet")
 
chat = Chatbot(client_db=client_db, llm_agent=llm_agent, retriever=Retriever(llmagent=llm_agent)) # type: ignore
