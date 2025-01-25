# fast API app
from fastapi import FastAPI, CORSMiddleware
from .database import Base, engine
from .routes import auth, chat, ticket

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(ticket.router)
