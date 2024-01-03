# llm_factory.py
#from src.tools.llm_opensource_mistral import LlmAgentOSMistral


def create_llm_agent(use_open_source: bool):
    """
    Factory function to create and return an LLM agent.
    
    :param use_open_source: Boolean flag to determine which LLM agent to use.
    :return: Instance of either LlmAgentOS or LlmAgent.
    """
    if use_open_source:
        from src.tools.llm_opensource import LlmAgentOS
        from config import llm_opensource

        return LlmAgentOS(llm_model=llm_opensource)  # Instantiate the open-source agent
    
    else:
        from src.tools.llm import LlmAgent
        from config import llm_openai
        return LlmAgent(llm_model=llm_openai)    # Instantiate the proprietary agent
