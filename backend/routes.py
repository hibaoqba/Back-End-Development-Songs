from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from flask import Blueprint
from bson.objectid import ObjectId
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
routes = Blueprint("routes", __name__)
songs_collection = db["songs"]
@routes.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK"}), 200

@routes.route("/count", methods=["GET"])
def count():
    total = db.songs.count_documents({})
    return jsonify({"count": total}), 200

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK"}), 200

@app.route("/count")
def count():
    """Return the length of the documents in the collection"""
    count = collection.count_documents({})  # Empty filter to count all documents

    return jsonify({"count": count}), 200  # HTTP OK response code

if __name__ == "__main__":
    app.run(debug=True)

@app.route("/song", methods=["GET"])
def songs():
    """Fetch all songs from the database and return them"""
    try:
        songs_list = list(songs_collection.find({}))  # Get all documents from the songs collection
        # Convert MongoDB documents to JSON serializable format
        for song in songs_list:
            song["_id"] = str(song["_id"])  # Convert ObjectId to string
        return jsonify({"songs": songs_list}), 200  # Return the songs list with HTTP 200 OK
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Handle any errors


@app.route('/song/<int:id>', methods=["PUT"])
def update_song(id):
    try:
        data = request.get_json()

        song = db.songs.find_one({"id": id})

        if song:
            db.songs.update_one(
                {"id": id},
                {"$set": {
                    "title": data.get("title", song.get("title")),
                    "lyrics": data.get("lyrics", song.get("lyrics"))
                }}
            )
            updated_song = db.songs.find_one({"id": id})
            updated_song["_id"] = str(updated_song["_id"])  # Fix serialization error
            return jsonify(updated_song), 200
        else:
            return jsonify({"message": "song not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/song/<int:id>', methods=["DELETE"])
def delete_song(id):
    try:
        result = db.songs.delete_one({"id": id})
        if result.deleted_count == 0:
            return jsonify({"message": "song not found"}), 404
        return '', 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500
