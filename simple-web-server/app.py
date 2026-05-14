from fastapi import FastAPI
import os

APP_NAME = os.getenv("APP_NAME", "Docker App")

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World", "APP_NAME": APP_NAME}
