from app import db
from bson.objectid import ObjectId

candidates_collection = db['candidates']

class Candidate:
    @staticmethod
    def create(data):
        result = candidates_collection.insert_one(data)
        candidate = candidates_collection.find_one({"_id": result.inserted_id})
        if candidate:
            candidate['_id'] = str(candidate['_id'])
        return candidate

    @staticmethod
    def get_all():
        candidates = list(candidates_collection.find())
        for candidate in candidates:
            candidate['_id'] = str(candidate['_id'])
        return candidates

    @staticmethod
    def delete(candidateID):
        candidates_collection.delete_one({"_id": ObjectId(candidateID)})

    @staticmethod
    def get_by_id(candidateID):
        candidate = candidates_collection.find_one({"_id": ObjectId(candidateID)})
        if candidate:
            candidate['_id'] = str(candidate['_id'])
        return candidate

    @staticmethod
    def update(candidateID, data):
        candidates_collection.update_one({"_id": ObjectId(candidateID)}, {"$set": data})
