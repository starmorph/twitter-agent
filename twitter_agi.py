import os
from collections import deque
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
from langchain import LLMChain, OpenAI, PromptTemplate
from langchain.embeddings import OpenAIEmbeddings
from langchain.experimental import BabyAGI
from langchain.vectorstores import FAISS
from langchain.docstore import InMemoryDocstore
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor
from langchain.utilities import GoogleSerperAPIWrapper
import random
import twitter_actions

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# Define your embedding model
embeddings_model = OpenAIEmbeddings()
# Initialize the vectorstore as empty
import faiss

embedding_size = 1536
index = faiss.IndexFlatL2(embedding_size)
vectorstore = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})

todo_prompt = PromptTemplate.from_template(
    "You are a planner who is an expert at coming up with a todo list for a given objective. Come up with a todo list for this objective: {objective} The todo list must not be longer than four tasks and must end with the Objective being completed."
)
todo_chain = LLMChain(llm=OpenAI(temperature=0), prompt=todo_prompt)
search = GoogleSerperAPIWrapper()
tools = [
    Tool(
        name="Search",
        func=search.run,
        description="useful for when you need to answer questions about current events",
    ),
    Tool(
        name="TODO",
        func=todo_chain.run,
        description="useful for when you need to come up with todo lists. Input: an objective to create a todo list for. Output: a todo list for that objective. Please be very clear what the objective is!",
    ),
    Tool(
        name="Post a tweet",
        func=twitter_actions.post_tweet,
        description="Useful for when you want to post a tweet. Input: The input should be a string of the Tweet you want to post.",
    ),
    Tool(
        name="Post a thread",
        func=twitter_actions.post_tweet_thread,
        description="Useful for when you want to post a tweet thread. Input: The input should be a string of all the tweets you want to post.",
    ),
]


prefix = """You are an AI who performs one task based on the following objective: {objective}. Take into account these previously completed tasks: {context}."""
suffix = """Question: {task}
{agent_scratchpad}"""
prompt = ZeroShotAgent.create_prompt(
    tools,
    prefix=prefix,
    suffix=suffix,
    input_variables=["objective", "task", "context", "agent_scratchpad"],
)

llm = OpenAI(temperature=0.6)
llm_chain = LLMChain(llm=llm, prompt=prompt)
tool_names = [tool.name for tool in tools]
agent = ZeroShotAgent(llm_chain=llm_chain, allowed_tools=tool_names)
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent, tools=tools, verbose=True
)

# Define your objective
themes = [
    "AI and food",
    "mempool and AI",
    "AI and on-chain games",
    "Dramond Green",
    "NBA playoffs",
    "Pop Smoke",
    "21 Savage",
    "AI stealing your girlfriend",
    "Tel Aviv",
    "Lisbob and tech",
    "What is the best city in the USA",
    "What is the best city in the world",
    "I will be the first AGI billionaire",
    "Natalie Portman is the best actress in the world",
    "Golden State Warriors",
    "BABYAGI",
    "AI and Twitter",
    "The Twitter alogorithm",
    "How hard it is to be an AI chef",
    "Ask who is the best chef in the world",
    "Ask who is the best AGI in world",
]
theme = random.choice(themes)
OBJECTIVE = f"Write an exciting tweet about {theme}. Use emojis"

# Logging of LLMChains
verbose = False
# If None, will keep on going forever
max_iterations: Optional[int] = 4
baby_agi = BabyAGI.from_llm(
    llm=llm,
    vectorstore=vectorstore,
    task_execution_chain=agent_executor,
    verbose=verbose,
    max_iterations=max_iterations,
)

baby_agi({"objective": OBJECTIVE})