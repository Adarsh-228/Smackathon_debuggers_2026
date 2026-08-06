from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, users, organizations, projects, documents, collaborators, tasks, comments
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# Set up CORS to allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["Organizations"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])
app.include_router(collaborators.router, prefix="/api/v1", tags=["Collaborators"])
app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])
app.include_router(comments.router, prefix="/api/v1", tags=["Comments"])

@app.get("/")
async def root():
    return {"message": f"Welcome to the {settings.PROJECT_NAME} API"}
