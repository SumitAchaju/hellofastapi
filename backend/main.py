from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.middlewares.auth import BearerTokenAuthBackend, AuthenticationMiddleware
from app.db.postgres.session import sessionmanager
from app.db.mango.session import mango_sessionmanager
from app.api.v1.router import v1_router
import json


@asynccontextmanager
async def lifespan(application: FastAPI):
    # on startup code

    yield

    # on shutdown code
    if sessionmanager.get_engine() is not None:
        # Close the DB connection
        await sessionmanager.close()

    if mango_sessionmanager.client is not None:
        await mango_sessionmanager.close()


app = FastAPI(lifespan=lifespan)

app.mount("/files", StaticFiles(directory="files"), "files")


@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(json.loads(exc.json()), status_code=422)


app.include_router(v1_router)

origins = ["http://localhost:5173", "http://127.0.0.1:8000", "http://localhost:3000"]
# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# noinspection PyTypeChecker
app.add_middleware(
    AuthenticationMiddleware,
    backend=BearerTokenAuthBackend(),
)


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>FastAPI</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                }
                h1 {
                    color: #1a73e8;
                }
                a {
                    color: #1a73e8;
                }
                .container {
                    margin: 100px 0;
                }
                .container > div {
                    text-align: center;
                    padding-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div>
                    <h1>FastAPI Hello Chat Application</h1>
                    <div>
                        <a href="/docs">API Docs</a>
                    </div>
                </div>
            </div>
        </body>
    </html>
    """
