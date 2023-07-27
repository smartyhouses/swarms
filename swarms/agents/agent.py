#base toolset
from swarms.agents.tools.agent_tools import *
from langchain.tools import BaseTool

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from typing import List, Any, Dict, Optional, Type
from langchain.memory.chat_message_histories import FileChatMessageHistory

import logging
from pydantic import BaseModel, Extra

from swarms.agents.models.hf import HuggingFaceLLM

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AgentNodeInitializer:
    """Useful for when you need to spawn an autonomous agent instance as a agent to accomplish complex tasks, it can search the internet or spawn child multi-modality models to process and generate images and text or audio and so on"""

    def __init__(self, 
    llm, 
    tools, 
    vectorstore, 
    temperature, 
    model_type: str=None, 
    human_in_the_loop=True,
    model_id: str = None,
    embedding_size: int = 8192,
    system_prompt: str = None,
    max_iterations: int = None):
        if not llm or not tools or not vectorstore:
            logging.error("llm, tools, and vectorstore cannot be None.")
            raise ValueError("llm, tools, and vectorstore cannot be None.")
        
        self.llm = llm
        self.tools = tools
        self.vectorstore = vectorstore
        
        self.agent = None
        self.temperature = temperature
        self.model_type = model_type
        
        self.human_in_the_loop = human_in_the_loop
        self.prompt = prompt
        self.model_id = model_id

        self.embedding_size = embedding_size
        self.system_prompt system_prompt





    def create_agent(self, ai_name="Swarm Agent AI Assistant", ai_role="Assistant", human_in_the_loop=True, search_kwargs={}, verbose=False):
        logging.info("Creating agent in AgentNode")
        try:
            self.agent = AutoGPT.from_llm_and_tools(
                ai_name=ai_name,
                ai_role=ai_role,
                tools=self.tools,
                llm=self.llm,
                memory=self.vectorstore.as_retriever(search_kwargs=search_kwargs),
                human_in_the_loop=human_in_the_loop,
                chat_history_memory=FileChatMessageHistory("chat_history.txt"),
            )
            # self.agent.chain.verbose = verbose
        except Exception as e:
            logging.error(f"Error while creating agent: {str(e)}")
            raise e

    def add_tool(self, tool: Tool):
        if not isinstance(tool, Tool):
            logging.error("Tool must be an instance of Tool.")
            raise TypeError("Tool must be an instance of Tool.")
        
        self.tools.append(tool)

    def run(self, prompt: str) -> str:
        if not isinstance(prompt, str):
            logging.error("Prompt must be a string.")
            raise TypeError("Prompt must be a string.")
        
        if not prompt:
            logging.error("Prompt is empty.")
            raise ValueError("Prompt is empty.")
        
        try:
            self.agent.run([f"{prompt}"])
            return "Task completed by AgentNode"
        except Exception as e:
            logging.error(f"While running the agent: {str(e)}")
            raise e


class AgentNode:
    def __init__(self, openai_api_key):
        if not openai_api_key:
            logging.error("OpenAI API key is not provided")
            raise ValueError("openai_api_key cannot be None")
        
        self.openai_api_key = openai_api_key

    def initialize_llm(self, llm_class):
        """
        Init LLM 

        Params:
            llm_class(class): The Language model class. Default is OpenAI.
            temperature (float): The Temperature for the language model. Default is 0.5
        """
        try: 
            # Initialize language model
            if self.llm_class == 'openai' or OpenAI:
                return llm_class(openai_api_key=self.openai_api_key, temperature=self.temperature)
            elif self.model_type == "huggingface":
                return HuggingFaceLLM(model_id=self.model_id, temperature=self.temperature)
        except Exception as e:
            logging.error(f"Failed to initialize language model: {e}")


    def initialize_tools(self, llm_class):
        if not llm_class:
            logging.error("llm_class not cannot be none")
            raise ValueError("llm_class cannot be none")
        try:
                
            logging.info('Creating AgentNode')
            llm = self.initialize_llm(llm_class)
            web_search = DuckDuckGoSearchRun()

            tools = [
                web_search,
                WriteFileTool(root_dir=ROOT_DIR),
                ReadFileTool(root_dir=ROOT_DIR),
                process_csv,
                WebpageQATool(qa_chain=load_qa_with_sources_chain(llm)),
            ]
            if not tools:
                logging.error("Tools are not initialized")
                raise ValueError("Tools are not initialized")
            return tools
        except Exception as e:
            logging.error(f"Failed to initialize tools: {e}")

    def initialize_vectorstore(self):
        try:
            embeddings_model = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
            index = faiss.IndexFlatL2(self.embedding_size)
            return FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})
        except Exception as e:
            logging.error(f"Failed to initialize vector store: {e}")
            raise

    def create_agent(self, llm_class=ChatOpenAI, ai_name="Swarm Agent AI Assistant", ai_role="Assistant", human_in_the_loop=False, search_kwargs={}, verbose=False):
        if not llm_class:
            logging.error("llm_class cannot be None.")
            raise ValueError("llm_class cannot be None.")
        try:
            agent_tools = self.initialize_tools(llm_class)
            vectorstore = self.initialize_vectorstore()
            agent = AgentNode(llm=self.initialize_llm(llm_class), tools=agent_tools, vectorstore=vectorstore)
            agent.create_agent(ai_name=ai_name, ai_role=ai_role, human_in_the_loop=human_in_the_loop, search_kwargs=search_kwargs, verbose=verbose)
            return agent
        except Exception as e:
            logging.error(f"Failed to create agent node: {e}")
            raise

def agent(openai_api_key, ojective, model_type, model_id):
    if not objective or not isinstance(objective, str):
        logging.error("Invalid objective")
        raise ValueError("A valid objective is required")

    if not openai_api_key:
        logging.error("OpenAI API key is not provided")
        raise ValueError("OpenAI API key is required")
    try:
        initializer = AgentNodeInitializer(openai_api_key)
        agent = initializer.create_agent()
        return agent
    except Exception as e:
        logging.error(f"An error occured in agent: {e}")
        raise
