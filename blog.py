from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List
from db import get_database
from bson import ObjectId
from auth import get_current_user

router = APIRouter(
    prefix="/blog",
    tags=["Blog Posts"],
    responses={404: {"description": "Not found"}},
)

class BlogPostIn(BaseModel):
    title: str = Field(..., title="Title of the blog post")
    content: str = Field(..., title="Content of the blog post")
    author: str = Field(..., title="Author of the blog post")
    owner_id: str = Field(..., title="Owner ID of the blog post")

class BlogPostOut(BlogPostIn):
    id: str  # Use string type for MongoDB ObjectId

# Helper function to parse MongoDB document to Pydantic model
def post_model(entity) -> BlogPostOut:
    return BlogPostOut(**entity, id=str(entity["_id"]))

@router.post("/posts/", response_model=BlogPostOut)
async def create_post(post: BlogPostIn, db=Depends(get_database), current_user=Depends(get_current_user)):
    post_dict = post.dict()
    post_dict["owner_id"] = current_user['_id']  # Set the owner_id to the current user's ID
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
async def update_post(post_id: str, updated_post: BlogPostIn, db=Depends(get_database), current_user=Depends(get_current_user)):
    post = await db["blogposts"].find_one({"_id": ObjectId(post_id)})
    if str(post['owner_id']) != str(current_user['_id']):
        raise HTTPException(status_code=403, detail="Not authorized to update this post")
    # Exclude owner_id from the update payload
    update_data = updated_post.dict(exclude_unset=True)
    result = await db["blogposts"].update_one({"_id": ObjectId(post_id)}, {"$set": update_data})
    if result.modified_count:
        updated_post = await db["blogposts"].find_one({"_id": ObjectId(post_id)})
        return post_model(updated_post)
    else:
        raise HTTPException(status_code=404, detail="Post not found")

@router.delete("/posts/{post_id}", response_model=BlogPostOut)
async def delete_post(post_id: str, db=Depends(get_database), current_user=Depends(get_current_user)):
    post = await db["blogposts"].find_one({"_id": ObjectId(post_id)})
    if str(post['owner_id']) != str(current_user['_id']):
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    result = await db["blogposts"].delete_one({"_id": ObjectId(post_id)})
    if result.deleted_count:
        return {"message": "Post deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Post not found")

