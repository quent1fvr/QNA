import os
import chromadb
from src.tools.retriever import Retriever
from src.tools.llm import LlmAgent
from src.tools.llm_opensource import LlmAgentOS
from src.model.block import Block
from src.model.doc import Doc
import gradio as gr
from src.tools.embedding_factory import create_embedding_model
from config import use_open_source_embeddings
import logging 
import time
class Chatbot:
    

    def __init__(self, retriever: Retriever = None, client_db=None, llm_agent : LlmAgent = None):
        self.llm = llm_agent
        self.retriever = retriever
        self.client_db = client_db

    def get_response(self, query, histo):
        
        timestart = time.time()
        histo_conversation, histo_queries = self._get_histo(histo)
        # language_of_query = self.llm.detect_language_v2(query).lower()
        #queries = self.llm.translate_v2(histo_queries)
        # if "en" in language_of_query:
        #     language_of_query = "en"
        # else:
        #     language_of_query = "fr"
        
        # block_sources = self.retriever.similarity_search(queries=queries)
        language_of_query = "en"
        block_sources = self.retriever.similarity_search(queries=query)
        block_sources = self._select_best_sources(block_sources)
        sources_contents = [f"Paragraph title : {s.title}\n-----\n{s.content}" if s.title else f"Paragraph {s.index}\n-----\n{s.content}" for s in block_sources]
        context = '\n'.join(sources_contents)
        i = 1
        while (len(context) + len(histo_conversation) > 15000) and i < len(sources_contents):
            context = "\n".join(sources_contents[:-i])
            i += 1
        answer = self.llm.generate_paragraph_v2(query=query, histo=histo_conversation, context=context, language=language_of_query)   
        answer = self._clean_chatgpt_answer(answer)
        timeend  = time.time()
        exec_time = timeend - timestart
        collection = self.retriever.collection
        logging.info(f"Collection: {collection.name}   , Query: {query} , Answer: {answer},  Sources: {sources_contents}", extra={'category': 'Query', 'elapsed_time':exec_time})

        return answer, block_sources

    

    @staticmethod
    def  _select_best_sources(sources: [Block], delta_1_2=0.15, delta_1_n=0.3, absolute=1.2, alpha=0.9) -> [Block]:
        """
        Select the best sources: not far from the very best, not far from the last selected, and not too bad per se
        """
        best_sources = []
        for idx, s in enumerate(sources):
            if idx == 0 \
                    or (s.distance - sources[idx - 1].distance < delta_1_2
                        and s.distance - sources[0].distance < delta_1_n) \
                    or s.distance < absolute:
                best_sources.append(s)
                delta_1_2 *= alpha
                delta_1_n *= alpha
                absolute *= alpha
            else:
                break
        return best_sources
    

    @staticmethod
    def _get_histo(histo: [(str, str)]) -> (str, str):
        histo_conversation = ""
        histo_queries = ""

        for (query, answer) in histo[-5:]:
            histo_conversation += f'user: {query} \n bot: {answer}\n'
            histo_queries += query + '\n'
        return histo_conversation[:-1], histo_queries
    

    @staticmethod
    def _clean_answer(answer: str) -> str:
        print(answer)
        answer = answer.strip('bot:')
        while answer and answer[-1] in {"'", '"', " ", "`"}:
            answer = answer[:-1]
        while answer and answer[0] in {"'", '"', " ", "`"}:
            answer = answer[1:]
        answer = answer.strip('bot:')
        if answer:
            if answer[-1] != ".":
                answer += "."
        return answer
    
    def _clean_chatgpt_answer(self,answer: str) -> str:
        answer = answer.strip('bot:')
        answer = answer.strip('Answer:')
        answer = answer.strip('Réponse:')
        while answer and answer[-1] in {"'", '"', " ", "`"}:
            answer = answer[:-1]
        return answer
    
    def upload_doc(self,input_doc,include_images_,actual_page_start):
        title = Doc.get_title(Doc,input_doc.name)
        extension = title.split('.')[-1]
        if extension and (extension == 'docx' or extension == 'pdf' or extension == 'html'):
                
            embedding_model = create_embedding_model(use_open_source_embeddings)

            coll_name = "".join([c if c.isalnum() else "_" for c in title])
            
            coll_name = coll_name
            
            collection = self.client_db.get_or_create_collection(name=coll_name, embedding_function=embedding_model)


            if collection.count() >=0:
                gr.Info("Please wait while your document is being analysed")
                print("Database is empty")
                doc = Doc(path=input_doc.name,include_images=include_images_,actual_first_page=actual_page_start)

                # for block in doc.blocks:  #DEBUG PART
                #     print(f"{block.index} : {block.content}")

                retriever = Retriever(doc.container, collection=collection,llmagent=self.llm)
            else:
                print("Database is not empty")
                retriever = Retriever(collection=collection,llmagent=self.llm)

            self.retriever = retriever
        else:
            
            return False
        return True
    
    def upload_docV2(self,input_doc,include_images_,actual_page_start):
        title = Doc.get_title(Doc,input_doc.name)
        extension = title.split('.')[-1]
        if extension and (extension == 'docx' or extension == 'pdf' or extension == 'html'):
            
            embedding_model = create_embedding_model(use_open_source_embeddings)

            coll_name = "".join([c if c.isalnum() else "_" for c in title])
            collection = self.client_db.get_or_create_collection(name=coll_name, embedding_function=embedding_model)


            if collection.count() == 0:
                gr.Info("Please wait while your document is being analysed")
                print("Database is empty")
                doc = Doc(path=input_doc.name,include_images=include_images_,actual_first_page=actual_page_start)

                # for block in doc.blocks:  #DEBUG PART
                #     print(f"{block.index} : {block.content}")

                retriever = Retriever(doc.container, collection=collection,llmagent=self.llm)
            else:
                print("Database is not empty")
                retriever = Retriever(collection=collection,llmagent=self.llm)

            self.retriever = retriever
        else:
            return False
        return True
    
    

    def list_models(self,model_dir):
        """
        List all files in the given directory.

        Args:
        model_dir (str): Directory containing model files.

        Returns:
        list: A list of filenames in the specified directory.
        """
        
        return [f for f in os.listdir(model_dir) if os.path.isfile(os.path.join(model_dir, f))]
    
    
    # def load_model(model_name):
    #     model_path = os.path.join(model_dir, model_name)
    #     return LlamaCpp(
    #         model_path=model_path,
    #         n_gpu_layers=n_gpu_layers,
    #         n_batch=n_batch,
    #         f16_kv=True,
    #         callback_manager=callback_manager,
    #         verbose=True,
    #         n_ctx=2200,
    #         temperature=0,
    #     )


