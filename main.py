from fastapi import FastAPI
from auth import router as auth_router
from blog import router as blog_router
app = FastAPI()


app.include_router(auth_router)
app.include_router(blog_router)

@app.get("/")
async def default_route():
    return {"message": "Welcome to your new app!"}