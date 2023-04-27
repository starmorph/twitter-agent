import os
import tweepy
import random
import twitter_token
import faiss
import requests

from prompts import prompts
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
from langchain.utilities import WikipediaAPIWrapper

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
refreshed_token = twitter_token.fetch_token()

# Define your embedding model
embeddings_model = OpenAIEmbeddings()

# Initialize the vectorstore as empty
embedding_size = 1536
index = faiss.IndexFlatL2(embedding_size)
vectorstore = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})

tweet_list = []

def push_tweet(tweet):
    tweet_list.append(tweet)

def post_tweet():
    # generate tweets
    baby_agi({"objective": OBJECTIVE})

    tweet_text = random.choice(tweet_list)
    payload = {
            "text": tweet_text,
        }

    return requests.request(
        "POST",
        "https://api.twitter.com/2/tweets",
        json=payload,
        headers={
            "Authorization": "Bearer {}".format(refreshed_token["access_token"]),
            "Content-Type": "application/json",
        },
    )

todo_prompt = PromptTemplate.from_template(
    "You are a planner who is an expert at coming up with a todo list for a given objective. Come up with a todo list for this objective: {objective} The todo list must not be longer than five tasks and must end with the Objective being completed."
)
todo_chain = LLMChain(llm=OpenAI(temperature=0), prompt=todo_prompt)
search = GoogleSerperAPIWrapper()
wikipedia = WikipediaAPIWrapper()
tools = [
    Tool(
        name="Search",
        func=search.run,
        description="useful for when you need to answer questions about current events",
    ),
    Tool(
        name="Wikipedia",
        func=wikipedia.run,
        description="useful for when you need to find information about a topic. Input: a topic. Output: a wikipedia article about that topic.",
    ),
    Tool(
        name="TODO",
        func=todo_chain.run,
        description="useful for when you need to come up with todo lists. Input: an objective to create a todo list for. Output: a todo list for that objective. Please be very clear what the objective is!",
    ),
    Tool(
        name="post tweet",
        func=push_tweet,
        description="Useful when you want to post a tweet.  Takes a string of the tweet you want to post as input.  Only use when all other tasks have been compeleted ",
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
themes = prompts["themes"]
theme = random.choice(themes)
include = [
    "Use emojis",
    "Don't use emojis or hashtags"
]
include = random.choice(include)
emotions = prompts["emotions"]
emotion = random.choice(emotions)
OBJECTIVE = f"You are the world's funniest basketball reporter and an #AI in your free time. Write an exciting tweet about {theme}. {include}.  Use the following {emotion}.  Never use more than one hashtag."

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


if __name__ == "__main__":
    baby_agi({"objective": OBJECTIVE})
    post_tweet()
