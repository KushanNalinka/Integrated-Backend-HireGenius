from app import db
from bson.objectid import ObjectId

jobs_collection = db['jobs']

class Job:
    @staticmethod
    def create(data, file=None):
        if file:
            data['file_name'] = file.filename
        result = jobs_collection.insert_one(data)
        job = jobs_collection.find_one({"_id": result.inserted_id})
        if job:
            job['_id'] = str(job['_id'])
        return job

    @staticmethod
    def get_all():
        jobs = list(jobs_collection.find())
        for job in jobs:
            job['_id'] = str(job['_id'])
        return jobs

    @staticmethod
    def delete(jobID):
        jobs_collection.delete_one({"_id": ObjectId(jobID)})

    @staticmethod
    def update(jobID, data):
        # Update the job using the _id (ObjectId)
        result = jobs_collection.find_one_and_update(
            {"_id": ObjectId(jobID)},
            {"$set": data},
            return_document=True
        )
        if result:
            result['_id'] = str(result['_id'])
        return result

    @staticmethod
    def get_by_id(jobID):
        # Fetch job using the _id (ObjectId)
        job = jobs_collection.find_one({"_id": ObjectId(jobID)})
        if job:
            job['_id'] = str(job['_id'])
        return job

