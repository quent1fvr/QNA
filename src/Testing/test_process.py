import os
import pandas as pd
from langchain.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from src.control.control import Chatbot
from src.Llm.llm_opensource import LlmAgentOS
from src.tools.retriever import Retriever
from src.tools.embedding_factory import create_embedding_model
import chromadb
import sys

class ChatbotProcessor:
    """
    A class to process queries using a chatbot model.

    Attributes:
    - model_config (dict): Configuration for the LlamaCpp model.
    - client_db (chromadb.PersistentClient): The client for interacting with the database.
    - chatbot (Chatbot): An instance of the Chatbot class used for processing queries.
    """

    def __init__(self, model_config, client_db):
        """
        Initializes the ChatbotProcessor with the given model configuration and database client.

        Parameters:
        - model_config (dict): Configuration for the LlamaCpp model.
        - client_db (chromadb.PersistentClient): The client for interacting with the database.
        """
        self.model_config = model_config
        self.client_db = client_db
        self.chatbot = self.initialize_chatbot()
        
    def initialize_chatbot(self):
        """
        Initializes the chatbot with a language model and a retriever.

        Returns:
        - Chatbot: An instance of the Chatbot class.
        """
        embedding_model = create_embedding_model(False)
        collection = self.client_db.get_collection(name="Le_Petit_Prince_pdf", embedding_function=embedding_model)
        llm_model = LlamaCpp(**self.model_config)
        return Chatbot(llm_agent=LlmAgentOS(llm_model), retriever=Retriever(llmagent=LlmAgentOS(llm_model), collection=collection), client_db=self.client_db)


    def process_queries(self, input_excel_file, output_excel_file):
        """
        Processes queries from an Excel file and writes the responses to another Excel file.

        Parameters:
        - input_excel_file (str): The path to the input Excel file containing queries.
        - output_excel_file (str): The path to the output Excel file where responses will be saved.
        """
        df = pd.read_excel(input_excel_file)
        if 'Query' not in df.columns:
            raise ValueError("The Excel file must have a 'Query' column.")

        df['Answer'], df['Block Sources'] = zip(*df['Query'].apply(self.get_response))
        df.to_excel(output_excel_file, index=False)

    def get_response(self, query):
        """
        Gets the response for a single query using the chatbot.

        Parameters:
        - query (str): The query for which a response is needed.

        Returns:
        - tuple: A tuple containing the answer and block sources.
        """
        histo = []  # Define or get your histo here
        print(f"Query: {query}")
        answer, block_sources = self.chatbot.get_response(query, histo)
        return answer, block_sources

if __name__ == "__main__":

    # Add the specified path to the list of paths to search for modules.
    sys.path.append('/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Chatbot_llama2_questions')

    # Configure parallelism for tokenizers.
    os.environ["TOKENIZERS_PARALLELISM"] = "true"

    # Set the OpenAI API key from a configuration file if it's not already in the environment.
    if not "OPENAI_API_KEY" in os.environ:
        from Chatbot_llama2_questions.config_key import OPENAI_API_KEY
        os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

    # Initialize a callback manager with a streaming stdout handler.
    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

    # Connect to the ChromaDB database.
    client_db = chromadb.PersistentClient("database_structuredemo2/")

    # Configuration settings for each model.
    model_configs = {
        "model_1": {    
            "model_path": '/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Chatbot_llama2_questions/src/model/opensource_models/llama-2-13b-chat.Q5_K_S.gguf',
            "n_gpu_layers": 20,
            "n_batch": 256,
            "f16_kv": True,  
            "callback_manager": callback_manager,
            "verbose": True,  
            "n_ctx": 2200,
            "temperature": 0,
        },
        "model_2": {
            # Configuration details for model 2
        },
        # Additional models can be added here.
    }

    # Path to the input Excel file containing queries.
    input_excel_file = "/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Chatbot_llama2_questions/src/Testing/test_questions.xlsx"

    # Process each model and save the results to respective output files.
    for model_name, config in model_configs.items():
        processor = ChatbotProcessor(model_config=config, client_db=client_db)
        output_excel_file = f'output_{model_name}.xlsx'
        processor.process_queries(input_excel_file, output_excel_file)
        print(f"Processed {model_name}, results saved to {output_excel_file}")
        print(f'success oif l {model_name} alright 
              ')
