import openai

class LlmAgent:

    def __init__(self, llm_model: str):
        self.llm = llm_model

    def generate_paragraph(self, query: str, context: {}, histo: [(str, str)], language='fr') -> str:
        """generates the  answer"""
        template = (f"You are a conversation bot designed to answer to the query from users."
                    f"Your answer is based on the context delimited by triple backticks :\n ``` {context} ```\n"
                    f"You are consistent and avoid redundancies with the rest of the initial conversation delimited by triple backticks :\n ``` {histo} ```\n"
                    f"Your response shall be in {language} and shall be concise."
                    f"You shall only provide the answer, nothing else before and after."
                    f"Here is the query you are given :\n"
                    f"``` {query} ```")
        generation = openai.ChatCompletion.create(model=self.llm, messages=[{"role":"user","content":template}])
        res = generation.choices[0].message.content
        print("****************")
        print(res)
        print("----")
        return str(res)
    
    def generate_paragraph_v2(self, query: str, context: {}, histo: [(str, str)], language='fr') -> str:
        """generates the  answer"""
        context_for_the_ai = (f"You are a conversation bot designed to answer to the query from users."
                    f"Your answer is based on the context delimited by triple backticks :\n ``` {context} ```\n"
                    f"You are consistent and avoid redundancies with the rest of the initial conversation delimited by triple backticks :\n ``` {histo} ```\n"
                    f"Your response shall be in {language} and shall be concise.")
        generation = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k", messages=[{"role":"system","content":context_for_the_ai},{"role":"user","content":query}])
        res = generation.choices[0].message.content
        print("****************")
        print(res)
        print("----")
        return str(res)

    def translate(self, text: str) -> str:
        """translates"""
        template = (f"Your task consists in translating in English the following text delimited by triple backticks: ``` {text} ```\n"
                    f"If the text is already in English, just return it !\n"
                    f"Your must not provide an answer to the text, just translate it.\n")
        generation = openai.ChatCompletion.create(model=self.llm, messages=[{"role":"user","content":template}])
        res = generation.choices[0].message.content
        print("****************")
        print(res)
        print("----TRANSLATE----")
        return res
    
    def translate_v2(self, text: str) -> str:
        """translates"""
        task = "Translate in english the text. If it is already in english, just return the text."
        generation = openai.ChatCompletion.create(model="gpt-4", messages=[{"role":"system","content":task},{"role":"user","content":text}])
        res = generation.choices[0].message.content
        print("****************")
        print(res)
        print("----TRANSLATE V2----")
        return res

    def generate_answer(self, query: str, answer: str, histo: str, context: str,language : str) -> str:
        """provides the final answer in {language} based on the initial query and the answer in english"""
        template = (f"Your task consists in translating the answer in {language}, if its not already the case, to the query "
                    f"delimited by triple backticks: ```{query}``` \n"
                    f"You don't add new content to the answer but: "
                    f"1 You can use some vocabulary from the context delimited by triple backticks:\n"
                    f"```{context}```\n"
                    f"2 You are consistent and avoid redundancies with the rest of the initial"
                    f"conversation delimited by triple backticks: ```{histo}```\n"
                    f"Your response shall respect the following format:<response>\n"
                    f"Here is the answer you are given in {language}:"
                    f"{answer}")
        generation = openai.ChatCompletion.create(model=self.llm, messages=[{"role":"user","content":template}])
        res = generation.choices[0].message.content
        print("****************")
        print(res)
        print("----")
        return str(res).strip()
    
    def summarize_paragraph(self, prompt : str, title_doc : str = '',title_para : str = ''):
        max_tokens = 700
        """summarizes the paragraph"""
        template = (f"Your task consists in summarizing the paragraph of the document untitled ```{title_doc}```."
                    f"The paragraph title is ```{title_para}```."
                    f"Your response shall be concise and shall respect the following format:"
                    f"<summary>"
                    f"If you see that the summary that you are creating will not respect ```{max_tokens}``` tokens, find a way to make it shorter."
                    f"The paragraph you need to summarize is the following :"
                    f"{prompt}")
        generation = openai.ChatCompletion.create(model=self.llm, messages=[{"role":"user","content":template}])
        res = generation.choices[0].message.content
        print("****************")
        print(res)
        print("----")
        return str(res).strip()
    
    def summarize_paragraph_v2(self, prompt : str, title_doc : str = '', title_para : str = ''):
        max_tokens = 850
        location_of_the_paragraph = prompt.split(" :")[0]
        """summarizes the paragraph"""
        task = (f"Your task consists in summarizing in English the paragraph of the document untitled ```{title_doc}``` located in the ```{location_of_the_paragraph}``` section of the document."
                    f"The paragraph title is ```{title_para}```."
                    f"Your response shall be concise and shall respect the following format:"
                    f"<summary>"
                    f"If you see that the summary that you are creating will not respect ```{max_tokens}``` tokens, find a way to make it shorter.")
        generation = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k", messages=[{"role":"system","content":task},{"role":"user","content":prompt}])
        res = generation.choices[0].message.content
        print("****************")
        print(res)
        print("----")
        return str(res).strip()
    
    def transform_paragraph_into_question(self, prompt : str, title_doc : str = '',title_para : str = '') -> (str, str):
        max_tokens = 150

        prompt_template=(f"Your job is to create two questions about a paragraph of a document untitled ```{title_doc}```."
        f"The paragraph title is ```{title_para}```."
        f"If you see that the questions that you are creating will not respect ```{max_tokens}``` tokens, find a way to make them shorter."
        f"If you can't create a question about the paragraph, just rephrase ```{title_para}``` so that it becomes a question."
        f"Your response shall contains two questions, shall be concise and shall respect the following format:"
        f"`<question1>!=;<question2>`"
        f"You should not answer to the questions, just create them. Moreover, you shall include the title of the paragraph in the questions."
        f"The paragraph you need to create questions about is the following :"
        f"{prompt}")
        generation = openai.ChatCompletion.create(model=self.llm, messages=[{"role":"user","content":prompt_template}])
        res = generation.choices[0].message.content
        print("****************")
        res = str(res).split("!=;")
        if len(res) == 1:
            return (res[0],"")
        elif len(res) == 2:
            return (res[0],res[1])
        else:
            return ("","")
  
    def detect_language(self, text: str) -> str:
        """detects the language"""
        template = (f"Your task consists in detecting the language of the last question or sentence of the text."
                    f"You should only give the two letters code of the language detected, nothing else."
                    f"Here is the text you are given delimited by triple backticks : ```{text}```")
        generation = openai.ChatCompletion.create(model=self.llm, messages=[{"role":"user","content":template}])
        res = generation.choices[0].message.content
        return str(res).strip()
    
    def detect_language_v2(self, text: str) -> str:
        """detects the language"""
        task = (f"Your task consists in detecting the language of the last question or sentence of the text."
                f"You should only give the two letters code of the language detected, nothing else.")
        generation = openai.ChatCompletion.create(model=self.llm, messages=[{"role":"system","content":task},{"role":"user","content":text}])
        res = generation.choices[0].message.content
        return str(res).strip()
