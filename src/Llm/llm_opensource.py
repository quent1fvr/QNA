from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


class LlmAgentOS:

    def __init__(self, llm_model):        
        self.llm = llm_model

    def generate_paragraph(self, query: str, context: {}, histo: [(str, str)], language='fr') -> str:
        template = (
            "<s>[INST] You are a conversation bot designed to answer users' queries. "
            "Answer the query while considering the context and avoiding redundancies with the conversation history. "
            "Your response should be in {language} and concise. [/INST]</s>"
            "Query: ```{query}```"
            "Context: ```{context}``` "
            "History: ```{histo}``` "
        )
        prompt = PromptTemplate(template=template, input_variables=["query", "context", "histo", "language"])
        llm_chain = LLMChain(prompt=prompt, llm=self.llm)
        response = llm_chain.run({"query": query, "context": context, "histo": histo, "language": language})
        res = response.choices[0].message.content
        return str(res)

    def generate_paragraph_v2(self, query: str, context: {}, histo: [(str, str)], language='en') -> str:
        template = (
            "Query: ```{query}```"
            "Context: ```{context}``` "
            "History: ```{histo}``` "
        )
        prompt = PromptTemplate(template=template, input_variables=["query", "context", "histo"])
        llm_chain = LLMChain(prompt=prompt, llm=self.llm, verbose= True)
        response = llm_chain.run({"query": query, "context": context, "histo": histo})
        return str(response)



    def translate(self, text: str) -> str:
        template = (
            "<s>[INST] Translate the following text into English. If it's already in English, return it as is. [/INST]</s>"
            "Text: ```{text}```"
        )
        prompt_template = PromptTemplate(template=template, input_variables=["text"])
        llm_chain = LLMChain(prompt=prompt_template, llm=self.llm)
        response = llm_chain.run({"text": text})
        res = response.choices[0].message.content
        return str(res)

    def translate_v2(self, text: str) -> str:
        template = (
            "<s>[INST] Translate the text into English. Return the text as is if it's already in English. [/INST]</s>"
            "Text: ```{text}```"
        )
        prompt_template = PromptTemplate(template=template, input_variables=["text"])
        llm_chain = LLMChain(prompt=prompt_template, llm=self.llm)
        response = llm_chain.run({"text": text})
        return str(response)

    # Continuing from the previous functions....

    def generate_answer(self, query: str, answer: str, histo: str, context: str, language: str) -> str:
        template = (
            "<s>[INST] Translate the provided answer into {language}, ensuring it's consistent with the query, context, and history. [/INST]</s>"
            "Query: ```{query}``` "
            "Answer: ```{answer}``` "
            "History: ```{histo}``` "
            "Context: ```{context}```"
        )
        prompt_template = PromptTemplate(template=template, input_variables=["query", "answer", "histo", "context", "language"])
        llm_chain = LLMChain(prompt=prompt_template, llm=self.llm)
        response = llm_chain.run({"query": query, "answer": answer, "histo": histo, "context": context, "language": language})
        res = response.choices[0].message.content
        return str(res).strip()

    def summarize_paragraph_v2(self, prompt: str, title_doc: str = '', title_para: str = ''):
        max_tokens = 850
        location_of_the_paragraph = prompt.split(" :")[0]
        template = (
            "<s>[INST] Summarize the paragraph from the document titled {title_doc}, located in {location_of_the_paragraph} "
            "section. Keep the summary within {max_tokens} tokens. [/INST]</s>"
            "Title of Paragraph: ```{title_para}``` "
            "Prompt: ```{prompt}```"
        )
        prompt_template = PromptTemplate(template=template, input_variables=["title_doc", "location_of_the_paragraph", "title_para", "max_tokens", "prompt"])
        llm_chain = LLMChain(llm=self.llm, prompt=prompt_template, verbose=True)
        response = llm_chain.run({"prompt": prompt, "title_doc": title_doc, "location_of_the_paragraph": location_of_the_paragraph, "title_para": title_para, "max_tokens": max_tokens})
        return str(response).strip()

    def transform_paragraph_into_question(self, prompt: str, title_doc: str = '', title_para: str = '') -> (str, str):
        max_tokens = 150
        template = (
            "<s>[INST] Create two questions based on the given paragraph titled {title_para} from the document {title_doc}. "
            "Keep the questions within {max_tokens} tokens. [/INST]</s>"
            "Paragraph: ```{prompt}```"
        )
        prompt_template = PromptTemplate(template=template, input_variables=["title_doc", "title_para", "max_tokens", "prompt"])
        llm_chain = LLMChain(prompt=prompt_template, llm=self.llm)
        response = llm_chain.run({"prompt": prompt, "title_doc": title_doc, "title_para": title_para})
        res = response.choices[0].message.content.split("!=;")
        return res[0].strip(), res[1].strip() if len(res) > 1 else ""

    def detect_language(self, text: str) -> str:
        template = (
            "<s>[INST] Detect the language of the last sentence or question in the text and provide its two-letter code. [/INST]</s>"
            "Text: ```{text}```"
        )
        prompt_template = PromptTemplate(template=template, input_variables=["text"])
        llm_chain = LLMChain(prompt=prompt_template, llm=self.llm)
        response = llm_chain.run({"text": text})
        return str(response).strip()

    def detect_language_v2(self, text: str) -> str:
        template = (
            "<s>[INST] Identify the language of the final sentence or question in the given text using its two-letter code. [/INST]</s>"
            "Text: ```{text}```"
        )
        prompt_template = PromptTemplate(template=template, input_variables=["text"])
        llm_chain = LLMChain(prompt=prompt_template, llm=self.llm)
        response = llm_chain.run({"text": text})
        return str(response).strip()