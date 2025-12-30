from fastapi import FastAPI
from routes.base import base_router 
# from routes import base
app = FastAPI()

app.include_router(base_router) 
# app.include_router(base.base_router) # analyse la deference 