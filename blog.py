from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from db import get_database
from bson import ObjectId

router = APIRouter(
    prefix="/blog",
    tags=["Blog Posts"],
    responses={404: {"description": "Not found"}},
)

class BlogPostIn(BaseModel):
    title: str = Field(..., title="Title of the blog post")
    content: str = Field(..., title="Content of the blog post")
    author: str = Field(..., title="Author of the blog post")

class BlogPostOut(BlogPostIn):
    id: str  # Use string type for MongoDB ObjectId

# Helper function to parse MongoDB document to Pydantic model
def post_model(entity) -> BlogPostOut:
    return BlogPostOut(**entity, id=str(entity["_id"]))

@router.post("/posts/", response_model=BlogPostOut)
async def create_post(post: BlogPostIn, db=Depends(get_database)):
    post_dict = post.dict()
    result = await db["blogposts"].insert_one(post_dict)
    new_post = await db["blogposts"].find_one({"_id": result.inserted_id})
    return post_model(new_post)

@router.get("/posts/", response_model=List[BlogPostOut])
async def read_posts(db=Depends(get_database)):
    posts = await db["blogposts"].find().to_list(100)
    return [post_model(post) for post in posts]

@router.get("/posts/{post_id}", response_model=BlogPostOut)
async def read_post(post_id: str, db=Depends(get_database)):
    post = await db["blogposts"].find_one({"_id": ObjectId(post_id)})
    if post:
        return post_model(post)
    raise HTTPException(status_code=404, detail="Post not found")

@router.put("/posts/{post_id}", response_model=BlogPostOut)
async def update_post(post_id: str, updated_post: BlogPostIn, db=Depends(get_database)):
    result = await db["blogposts"].update_one({"_id": ObjectId(post_id)}, {"$set": updated_post.dict()})
    if result.modified_count:
        updated_post = await db["blogposts"].find_one({"_id": ObjectId(post_id)})
        return post_model(updated_post)
    raise HTTPException(status_code=404, detail="Post not found")

@router.delete("/posts/{post_id}", response_model=BlogPostOut)
async def delete_post(post_id: str, db=Depends(get_database)):
    result = await db["blogposts"].delete_one({"_id": ObjectId(post_id)})
    if result.deleted_count:
        return {"message": "Post deleted successfully"}
    raise HTTPException(status_code=404, detail="Post not found")
