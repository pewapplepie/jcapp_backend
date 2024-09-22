from flask import Flask, request, jsonify
from pymongo import MongoClient
import json
import os
from bson import ObjectId  # Import to handle ObjectId
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fetch sensitive data from environment variables
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_CLUSTER_URL = os.getenv("MONGO_CLUSTER_URL")
MONGO_DATABASE = os.getenv("MONGO_DATABASE")

# MongoDB Atlas connection string (with environment variables)
client = MongoClient(
    f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_CLUSTER_URL}/{MONGO_DATABASE}?retryWrites=true&w=majority&appName=Cluster36147"
)
db = client[MONGO_DATABASE]
posts_collection = db["posts"]

app = Flask(__name__)


# Function to generate posts.json file
def update_posts_file():
    posts = list(
        posts_collection.find({}, {"_id": 0})
    )  # Exclude MongoDB's _id field from JSON
    with open(os.path.join(os.path.dirname(__file__), "posts.json"), "w") as file:
        json.dump(posts, file, indent=2)


# Function to convert MongoDB documents to JSON-friendly format
def serialize_post(post):
    post["_id"] = str(post["_id"])  # Convert ObjectId to string
    return post


# Route to create a new blog post
@app.route("/posts", methods=["POST"])
def create_post():
    data = request.get_json()
    post = {
        "title": data["title"],
        "content": data["content"],
        "publishDate": data.get("publishDate", None),
    }
    result = posts_collection.insert_one(post)

    # Convert ObjectId to string and add it to the post
    post["_id"] = str(result.inserted_id)

    # Generate the JSON file after new post creation
    update_posts_file()

    return jsonify(post), 201


# Route to get all blog posts
@app.route("/posts", methods=["GET"])
def get_posts():
    posts = list(posts_collection.find())
    # Serialize all posts to convert ObjectId to string
    posts = [serialize_post(post) for post in posts]
    return jsonify(posts)


# Route to delete a post (optional)
@app.route("/posts/<string:title>", methods=["DELETE"])
def delete_post(title):
    result = posts_collection.delete_one({"title": title})

    if result.deleted_count > 0:
        update_posts_file()
        return jsonify({"message": "Post deleted"}), 204
    else:
        return jsonify({"message": "Post not found"}), 404


# Start the server
if __name__ == "__main__":
    app.run(debug=True, port=5000)
