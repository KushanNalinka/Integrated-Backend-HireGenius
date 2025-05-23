from flask import Blueprint, request, jsonify, send_from_directory
from app.models.candidate_model import Candidate
import os
import json
import joblib
import pandas as pd


from collections import Counter

from app.utils.chart_utils import get_and_display_chart

from app.models.job_model import Job


candidate_routes = Blueprint('candidates', __name__)

from app import db  # Import the shared db instance
candidates_collection = db["candidates"]  # Define candidates_collection

# Define folders for CV and transcripts
UPLOAD_FOLDER_CV = os.path.join(os.getcwd(), 'uploads/cv')
UPLOAD_FOLDER_TRANSCRIPTS = os.path.join(os.getcwd(), 'uploads/transcripts')

os.makedirs(UPLOAD_FOLDER_CV, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_TRANSCRIPTS, exist_ok=True)

# Load the trained stacked model
model_path = os.path.join(os.getcwd(), "local_model", "stacked_model_new.joblib")
model = joblib.load(model_path)



@candidate_routes.route('/candidates/predict/<candidate_id>', methods=['GET'])
def predict_matching_percentage(candidate_id):
    """Predicts the candidate's matching percentage using an ML model."""
    candidate = Candidate.get_by_id(candidate_id)
    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404

    input_data = {
        "No of Tools and Technologies": candidate.get("num_of_tools_technologies", 0),
        "Courses & Certifications Matching": candidate.get("coursesAndCertificationMatchingSimilarity", 0),
        "Achievements Matching": candidate.get("achievements_similarity",0),  # Assuming static value for achievements
        "Work Experience Matching": candidate.get("workExperienceMatchingSimilarity", 0),
        "Projects Matching": candidate.get("projectsMatchingSimilarity", 0)
    }

    input_df = pd.DataFrame([input_data])

    try:
        predicted_matching_percentage = model.predict(input_df)[0]
    except Exception as e:
        return jsonify({"error": f"Prediction error: {str(e)}"}), 500

    # Update candidate record with prediction
    Candidate.update(candidate_id, {
        "predicted_matching_percentage": round(predicted_matching_percentage, 2)
    })

    return jsonify({
        "predicted_matching_percentage": round(predicted_matching_percentage, 2)
    }), 200



@candidate_routes.route('/candidates/predicted_percentage/<candidate_id>', methods=['GET'])
def get_predicted_percentage(candidate_id):
    candidate = candidates_collection.find_one({"_id": candidate_id}, {"predicted_matching_percentage": 1})
    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404
    return jsonify({"predicted_matching_percentage": candidate.get("predicted_matching_percentage", "N/A")}), 200


    

    return jsonify({"message": "Candidate processing triggered successfully"}), 200


    

@candidate_routes.route('/candidates', methods=['GET'])
def get_candidates():
    candidates = Candidate.get_all()
    return jsonify(candidates), 200

@candidate_routes.route('/candidates/<candidateID>', methods=['DELETE'])
def delete_candidate(candidateID):
    Candidate.delete(candidateID)
    return jsonify({"message": "Candidate deleted"}), 200

@candidate_routes.route('/candidates/<candidateID>', methods=['GET'])
def get_candidate(candidateID):
    candidate = Candidate.get_by_id(candidateID)
    if candidate:
        return jsonify(candidate), 200
    else:
        return jsonify({"error": "Candidate not found"}), 404
    
@candidate_routes.route('/candidates/candidatesByGeneratedId/<generatedCandidateID>', methods=['GET'])
def get_candidate_by_generated_id(generatedCandidateID):
    
        # Find the candidate using the generated candidate ID
        genCandidate = candidates_collection.find_one({"candidateId": generatedCandidateID})

        if not genCandidate:
            return jsonify({"error": "Candidate not found"}), 404

        # Extract the MongoDB ObjectId
        candidateID = genCandidate.get('_id')

        # Fetch the full candidate details using the ObjectId
        candidate = Candidate.get_by_id(candidateID)

        if candidate:
          
            return jsonify(candidate), 200
        else:
            return jsonify({"error": "Candidate not found"}), 404
        
@candidate_routes.route('/candidates/job/<jobId>', methods=['GET'])
def get_candidates_by_job(jobId):
    try:
        # Find candidates using jobId (make sure jobId is stored as a string in MongoDB)
        candidates = list(candidates_collection.find({"jobID": jobId}))

        if not candidates:
            return jsonify({"error": "No candidates found for this job"}), 404

        # Convert ObjectId to string before returning the response
        for candidate in candidates:
            candidate['_id'] = str(candidate['_id'])  # Convert ObjectId to string

        return jsonify(candidates), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


  

        
      

@candidate_routes.route('/uploads/cv/<filename>', methods=['GET'])
def serve_cv(filename):
    return send_from_directory(UPLOAD_FOLDER_CV, filename)

@candidate_routes.route('/uploads/transcripts/<filename>', methods=['GET'])
def serve_transcript(filename):
    return send_from_directory(UPLOAD_FOLDER_TRANSCRIPTS, filename)

@candidate_routes.route('/candidates/<candidateID>/chart', methods=['GET'])
def display_candidate_chart(candidateID):
    get_and_display_chart(candidateID)
    return jsonify({"message": "Chart displayed successfully"}), 200


    
    return jsonify({"message": "Charts generated successfully", "charts": charts}), 200

@candidate_routes.route('/candidates/charts/<candidateID>', methods=['GET'])
def get_all_charts(candidateID):
    candidate = Candidate.get_by_id(candidateID)
    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404

    charts = candidate.get('charts', {})
    return jsonify({"charts": charts}), 200

@candidate_routes.route('/candidates/finalized_score/<candidate_id>', methods=['POST'])
def calculate_finalized_score(candidate_id):
    """Calculates and updates the candidate's finalized score."""
    
    # Fetch the candidate from the database
    candidate = Candidate.get_by_id(candidate_id)
    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404

    # Extract necessary fields
    predicted_matching_percentage = candidate.get("predicted_matching_percentage", 0)
    github_marks = candidate.get("github_marks", 0)
    linkedin_marks = candidate.get("linkedin_marks", 0)
    transcript_marks = candidate.get("transcript_marks", 0)

    # Calculate the average of github, linkedin, and transcript marks
    non_empty_marks = [github_marks, linkedin_marks, transcript_marks]
    avg_marks = sum(non_empty_marks) / len(non_empty_marks) if len(non_empty_marks) > 0 else 0

    # Calculate finalized score
    finalized_score = round((0.6 * predicted_matching_percentage) + (0.4 * avg_marks), 2)

    # Update candidate record with the finalized score
    Candidate.update(candidate_id, {"finalized_score": finalized_score})

    return jsonify({
        "message": "Finalized score calculated and updated successfully",
        "finalized_score": finalized_score
    }), 200

