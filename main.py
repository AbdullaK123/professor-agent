from fastapi import FastAPI, Request
from langserve import add_routes
from pydantic import BaseModel
from app.graph import create_graph
from uuid import uuid4

def add_thread_id(config: dict, request: Request) -> dict:
    # Generate a unique thread_id for each request
    config["configurable"] = {"thread_id": str(uuid4())}
    return config


app = FastAPI()

graph = create_graph(checkpointer=None)

class LearningInput(BaseModel):
    topic: str
    background: str

add_routes(
    app,
    graph.with_types(input_type=LearningInput), 
    per_req_config_modifier=add_thread_id
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=4)
