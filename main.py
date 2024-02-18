from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
from blog import router as blog_router
app = FastAPI()

# Define a list of allowed origins for CORS
# You can use ["*"] to allow all origins
allowed_origins = ["*"]

# Add CORSMiddleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Specify the allowed origins
    allow_credentials=True,  # Allow cookies to be included in cross-origin requests
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


app.include_router(auth_router)
app.include_router(blog_router)

@app.get("/")
async def default_route():
    return {"message": "Welcome to your new app!"}