import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ..resources.starter import FrontendHander
from multiprocessing import Process

app = FastAPI()

# app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def client():
    return "Welcome to Kortecx"


def _init_backend():
    uvicorn.run(app, host="0.0.0.0", port=8000)


def start_components():
    backend = Process(target=_init_backend)
    backend.start()

    FrontendHander().init_frontend()
    backend.join()
