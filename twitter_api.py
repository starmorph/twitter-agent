from langchain.llms.openai import OpenAI
import os
import tweepy
import random
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.document_loaders import TwitterTweetLoader
from prompts import prompts
from langchain.chains import LLMChain

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ACTIVELOOP_TOKEN = os.getenv("ACTIVELOOP_TOKEN", "")

api_key = os.getenv("API_KEY", "")
api_secret_key = os.getenv("API_SECRET_KEY", "")
access_token = os.getenv("ACCESS_TOKEN", "")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET", "")

auth = tweepy.OAuth1UserHandler(
    api_key, api_secret_key, access_token, access_token_secret
)

api = tweepy.API(auth)

users = prompts["users"]
user = random.choice(users)

loader = TwitterTweetLoader.from_secrets(
    access_token=access_token,
    access_token_secret=access_token_secret,
    consumer_key=api_key,
    consumer_secret=api_secret_key,
    twitter_users=[user],
    number_tweets=50,  # Default value is 100
)
documents = loader.load()

# Fetch a tweet by ID
tweet_text = documents[0].page_content
tweet_id = documents[0].metadata['user_info']['status']['id']
tweet = api.get_status(tweet_id)

# Construct the tweet URL
tweet_url = f"https://twitter.com/{'zerohedge'}/status/{tweet.id}"

llm = OpenAI(temperature=0.9)

prompt = PromptTemplate(
    input_variables=["input_text"],
    template="You are a tweet reply agent.  You are replying to a tweet that says: {input_text}.  Make sure the reply is under 140 characters.  Be sassy, sarcastic, and over the top.  You want to make people cry laughing.  Always take the opposite position of the text",
)
quote_tweet_chain = LLMChain(llm=llm, prompt=prompt)
text = quote_tweet_chain.run(input_text=tweet_text)

# Quote it in a new status
api.update_status(text, attachment_url=tweet_url)