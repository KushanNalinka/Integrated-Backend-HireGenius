from flask import Blueprint, request, jsonify, send_from_directory
from app.models.job_model import Job
import os

job_routes = Blueprint('jobs', __name__)

# Define folder for general job uploads
UPLOAD_FOLDER_GENERAL = os.path.join(os.getcwd(), 'uploads/general')  
os.makedirs(UPLOAD_FOLDER_GENERAL, exist_ok=True)

@job_routes.route('/jobs', methods=['POST'])
def create_job():
    data = request.form.to_dict()
    file = request.files.get('file')
    if file:
        file.save(os.path.join(UPLOAD_FOLDER_GENERAL, file.filename))
    job = Job.create(data, file)
    return jsonify(job), 201

@job_routes.route('/jobs', methods=['GET'])
def get_jobs():
    jobs = Job.get_all()
    return jsonify(jobs), 200

@job_routes.route('/jobs/<jobID>', methods=['DELETE'])
def delete_job(jobID):
    Job.delete(jobID)
    return jsonify({"message": "Job deleted"}), 200

@job_routes.route('/jobs/<jobID>', methods=['GET'])
def get_job(jobID):
    job = Job.get_by_id(jobID)
    if job:
        return jsonify(job), 200
    else:
        return jsonify({"error": "Job not found"}), 404

@job_routes.route('/jobs/<jobID>', methods=['PUT'])
def update_job(jobID):
    data = request.form.to_dict()
    file = request.files.get('file')
    if file:
        file.save(os.path.join(UPLOAD_FOLDER_GENERAL, file.filename))
        data['file_name'] = file.filename  # Update the file_name field if a new file is uploaded
    updated_job = Job.update(jobID, data)
    if updated_job:
        return jsonify(updated_job), 200
    else:
        return jsonify({"error": "Job not found"}), 404

@job_routes.route('/uploads/general/<filename>', methods=['GET'])
def serve_general_file(filename):
    return send_from_directory(UPLOAD_FOLDER_GENERAL, filename)
