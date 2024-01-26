from langchain_community.llms import LlamaCpp 
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import os
content_language = 'en'
plan_language = 'en'
content_en_path_real = "data/Illumio_Core_REST_API_Developer_Guide_23.3.pdf"
content_test = "data/Test/Illumio_product_brief.pdf"
content_python = "data/cours-python_crop.docx"
content_html = "data/Test/list.html"
content_data_analyst = "data\Test\Data_Analyst_chez_Stockly.pdf"
content_test_epita = "data\Test\Test_epita.pdf"


# Configuration Settings

# ----- Language Model Selection -----
# Choose whether to use open-source language model for generation
# Setting this to False will use OpenAI's model specified by `llm_openai`
use_open_source_generation = False

# OpenAI Language Model Configuration
# `llm_openai`: Specifies the version of OpenAI's GPT model to use for text generation

######## OPENAI ########

llm_openai = "gpt-3.5-turbo"

# Open-Source Language Model Configuration
# `llm_opensource`: Configuration for the open-source LLaMA model
# `n_gpu_layers`: Number of layers to run on GPU, set to 1 for efficient performance
# `n_batch`: Batch size for processing, dependent on the available RAM
# `f16_kv`: Set to True for efficient memory usage
# `n_ctx`: The maximum number of tokens to consider for a single request
# `temperature`: Controls randomness in generation, lower values make responses more deterministic


######## OPEN SOURCE ########


# n_gpu_layers = 20
# n_batch = 256  
# callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
# llm_opensource = LlamaCpp(
#     model_path="/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Chatbot_llama2_questions/src/model/opensource_models/llama-2-13b-chat.Q5_K_S.gguf",
#     n_gpu_layers=n_gpu_layers,
#     n_batch=n_batch,
#     f16_kv=True,  
#     callback_manager=callback_manager,
#     verbose=True,  
#     n_ctx=2200,
#     temperature=0,
# )


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

# ----- Embeddings Configuration -----
# Choose whether to use open-source embeddings


use_open_source_embeddings = False  





 
examples = {"Question_1": "What is the max_results parameter for async traffic queries ?",
            "Question_2": "How can I use the Public Experimental Provisioning API to determine if a specific set of objects can be provisioned?",
            "Question_3": "Explain the potential challenges and workarounds when using json-query with the curl -i option. Why might this combination lead to errors?",
}


view_config = {
    'title': """
    <h1 style="
        text-align: center;
        font-size: 4.5em;
        background-image: linear-gradient(45deg, #f3ec78, #af4261);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        -moz-background-clip: text;
        -moz-text-fill-color: transparent;
        font-weight: bold;
        margin-top: 4%;
        padding-bottom: 1%;
    ">Eurêka</h1>
    """,
    'examples': examples,
}
