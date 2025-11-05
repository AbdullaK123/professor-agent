from dotenv import load_dotenv
from langchain_tavily import TavilySearch

# Ensure environment variables are loaded
load_dotenv()

search = TavilySearch(
    max_results=5,
    search_depth="advanced"
)