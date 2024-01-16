import os
import time
from config import *
from chromadb.utils import embedding_functions
import chromadb
from src.control.control import Chatbot
from src.tools.retriever import Retriever
from src.Llm.llm_factory import create_llm_agent
import logging
import logging.config


class CollectionManager:
    """
    A class to manage a collection of documents, including functionalities to list,
    upload, and query documents using a chatbot system. Aimed to be run in the terminal.

    Attributes:
        llm_agent (obj): An instance of a language model agent.
        client_db (obj): A database client for managing collections.
        chat (obj): An instance of a Chatbot for handling document retrieval and querying.
    """
    def __init__(self):
        """
        Initializes the CollectionManager with required components and configurations.
        """
        self.llm_agent = create_llm_agent(use_open_source_generation)
        if not os.path.exists("database_test/"):
            os.makedirs("database_test/")
        self.client_db = chromadb.PersistentClient("database_test/")
        self.chat = Chatbot(client_db=self.client_db, llm_agent=self.llm_agent, retriever=Retriever(llmagent=self.llm_agent))
        logging.config.fileConfig('/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Chatbot_llama2_questions/src/Logs/logging_config.ini')

    def list_collections(self):
        print("\nAvailable Collections:")
        for collection in self.chat.client_db.list_collections():
            print(f"- {collection.name}")

    def upload_document(self):
        filepath = input("\nEnter the path of the file to upload: ")
        if not os.path.exists(filepath):
            print("File not found. Please check the path and try again.")
            return

        include_images = input("Analyze text from images? (y/n): ").lower() == 'y'
        try:
            page_start = int(input("Enter the start page (default = 1): ") or "1")
        except ValueError:
            print("Invalid input for page start. Using default value 1.")
            page_start = 1

        with open(filepath, 'rb') as file:
            print("Uploading document...")
            start_time = time.time()
            try:
                result = self.chat.upload_doc(file, include_images, page_start)
                end_time = time.time()
                if result:
                    print(f"Document uploaded successfully. Time taken: {end_time - start_time} seconds")
                else:
                    print("Failed to upload document.")
            except Exception as e:
                print(f"An error occurred during upload: {e}")
                
    def query_collection(self):
        print("\nAvailable Collections:")
        collections = self.chat.client_db.list_collections()
        for idx, collection in enumerate(collections, start=1):
            print(f"{idx}. {collection.name}")

        collection_choice = input("\nChoose a collection to query (number): ")
        try:
            collection_index = int(collection_choice) - 1
            if collection_index < 0 or collection_index >= len(collections):
                print("Invalid collection number. Please try again.")
                return
        except ValueError:
            print("Invalid input. Please enter a number.")
            return

        selected_collection = collections[collection_index]
        open_ai_embedding = embedding_functions.OpenAIEmbeddingFunction(api_key=os.environ['OPENAI_API_KEY'], model_name="text-embedding-ada-002")
        self.chat.retriever.collection = self.chat.client_db.get_collection(selected_collection.name, embedding_function=open_ai_embedding)
        histo_text = []

        while True:
            query = input("\nEnter your query (or 'exit' to return): ")
            if query.lower() == 'exit':
                break

            histo_text.append((query, None))
            try:
                answer, sources = self.chat.get_response(query, histo_text)
                histo_text[-1] = (query, answer)
                print(f"\nAnswer: {answer}")

                print("\nSources:")
                shown_indices = set()
                for source in sources:
                    if source.index not in shown_indices:
                        shown_indices.add(source.index)
                        print(f" - {source.index} {source.title} (Score: {source.distance_str})")

                print("\nConversation History:")
                for q, a in histo_text:
                    print(f"Q: {q}")
                    if a:
                        print(f"A: {a}")
                    print("---")
            except Exception as e:
                print(f"An error occurred during querying: {e}")
                
    def run(self):
        """
        The main loop for user interaction. Provides different options and
        calls the respective methods based on user choice.
        """
        while True:
            print("\nOptions:")
            print("1. List Collections")
            print("2. Upload Document")
            print("3. Query Collection")
            print("4. Exit")
            choice = input("Choose an option: ")

            if choice == "1":
                self.list_collections()
            elif choice == "2":
                self.upload_document()
            elif choice == "3":
                self.query_collection()
            elif choice == "4":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")


def main():
    """
    The main function of the script. It sets up necessary configurations and
    starts the CollectionManager.
    """
    os.environ["TOKENIZERS_PARALLELISM"] = "true"
    if "OPENAI_API_KEY" not in os.environ:
        from config_key import OPENAI_API_KEY
        os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

    collection_manager = CollectionManager()
    collection_manager.run()


if __name__ == "__main__":
    main()
