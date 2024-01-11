import os
from chromadb.utils import embedding_functions

def create_embedding_model(use_open_source_embeddings: bool):
    """
    Factory function to create and return an embedding model.
    
    :param use_open_source: Boolean flag to determine which embedding model to use.
    :return: Instance of the chosen embedding model.
    """
    
    if use_open_source_embeddings:
        # Instantiate and return the open-source embedding model
        # return embedding_functions.InstructorEmbeddingFunction(
        #     model_name="hkunlp/instructor-base",
        #     device="cpu"
        # )
        
        return embedding_functions.SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-large-zh-v1.5")



    else:
        # Instantiate and return the OpenAI embedding model
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.environ['OPENAI_API_KEY'],
            model_name="text-embedding-ada-002"
        )