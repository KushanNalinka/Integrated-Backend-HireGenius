from flask import Blueprint, request, jsonify, send_from_directory
from app.models.candidate_model import Candidate
import os
import json
import joblib
import pandas as pd
import numpy as np


from collections import Counter

from app.utils.chart_utils import get_and_display_chart

from app.models.job_model import Job

from app.services.linkedin_service import fetch_linkedin_data, calculate_score
from app.services.github_service import assign_marks, scaler, kmeans_model
from app.services.transcript_service import process_pdf, JOB_DICTIONARY
from werkzeug.utils import secure_filename


candidate_routes = Blueprint('candidates', __name__)

from app import db  # Import the shared db instance
candidates_collection = db["candidates"]  # Define candidates_collection

# Define folders for CV and transcripts
UPLOAD_FOLDER_CV = os.path.join(os.getcwd(), 'uploads/cv')
UPLOAD_FOLDER_TRANSCRIPTS = os.path.join(os.getcwd(), 'uploads/transcripts')
UPLOAD_FOLDER_TRANSCRIPT_EVALUATION = os.path.join(os.getcwd(), 'uploads/transcript_evaluation')

os.makedirs(UPLOAD_FOLDER_CV, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_TRANSCRIPTS, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_TRANSCRIPT_EVALUATION, exist_ok=True)

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

@candidate_routes.route('/candidates/by-email', methods=['GET'])
def get_candidate_by_email():
    email = request.args.get('email')

    if not email:
        return jsonify({"error": "Email query parameter is required"}), 400

    try:
        candidate = candidates_collection.find_one({"confirmEmail": email})
        if not candidate:
            return jsonify({"error": "Candidate not found"}), 404

        # Prepare customized response
        filtered_response = {
            "_id": str(candidate.get("_id")),
            "confirmEmail": candidate.get("confirmEmail"),
            "extractednoofprogramminglanguages": candidate.get("extractednoofprogramminglanguages", 0),
            "extractednoofprogrammingframeworks": candidate.get("extractednoofprogrammingframeworks", 0),
            "extractednoofwebtechnologies": candidate.get("extractednoofwebtechnologies", 0),
            "extractednoofdatabasetechnologies": candidate.get("extractednoofdatabasetechnologies", 0),
            "extractednoofsoftwaredevelopmentmethodologies": candidate.get("extractednoofsoftwaredevelopmentmethodologies", 0),
            "extractednoofversioncontroltechnologies": candidate.get("extractednoofversioncontroltechnologies", 0),
            "extractednoofdevopstools": candidate.get("extractednoofdevopstools", 0),
            "extractednoofcloudtechnologies": candidate.get("extractednoofcloudtechnologies", 0),
            "lastName": candidate.get("lastName"),
            "firstName": candidate.get("firstName"),
            "noofyearsofexperience": candidate.get("noofyearsofexperience"),
            "jobPosition": candidate.get("jobPosition"),
            "jobID": candidate.get("jobID"),
            "jobTitle": candidate.get("jobTitle"),
            "salaryRange": candidate.get("salaryRange"),
        }

        return jsonify(filtered_response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

###################
# Github Analysis
###################
@candidate_routes.route('/candidates/getCandidateGithubScore', methods=['POST'])
def get_candidate_github_score():
    try:
        # Parse input JSON data
        data = request.json
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        #Extract MArks from the request
        allocatedMarks = data.get('marks')
        
        # Extract features from the request
        features = data.get('features')  # Expecting a list of features
        if not features:
            return jsonify({"error": "Features missing in request"}), 400


        if(features[0]==0):
            response = {
                "prediction": 0,   
                "marks": 0
            }
            return jsonify(response), 200

        # Convert features to numpy array
        features = np.array(features).reshape(1, -1)  # Adjust shape if needed

        # Normalize the features
        features_normalized = scaler.transform(features)

        # Verify the normalized data (optional for debugging)
        print("Normalized Features:", features_normalized)

        # Make prediction
        prediction = kmeans_model.predict(features_normalized)  # Use the model's predict method
        print("Prediction:", prediction)

        # Convert the prediction to a native Python type (float)
        prediction = prediction[0] if isinstance(prediction, np.ndarray) else prediction

        # Assign marks based on the prediction (assuming it's a scalar output)
        marks = assign_marks(prediction, allocatedMarks)

        # Prepare response
        response = {
            "prediction": float(prediction),  # Ensure it's a native float
            "marks": marks
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



###################
# LinkedIn Profile Processing
###################
@candidate_routes.route('/candidates/getCandidateLinkedinScore', methods=['POST'])
def get_candidate_linkedin_score():
    data = request.get_json()
    username = data.get('username')
    job_data = data.get('job_data')
     
    try:
        linkedin_profile = fetch_linkedin_data(username)
         
        score = calculate_score(linkedin_profile, job_data)
         
        return jsonify({"candidate_score": score, "linkedin_profile": linkedin_profile})
    except Exception as e:
       
        return jsonify({"error": str(e)}), 500

####################
# Transcript Processing
####################
@candidate_routes.route('/candidates/getCandidateTranscriptScore', methods=['POST'])
def get_candidate_transcript_score():

    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected!"}), 400

    job_role = request.form.get('job_role')
    if not job_role:
        return jsonify({"success": False, "message": "No job role"}), 400

    
    if job_role not in JOB_DICTIONARY:
        return jsonify({"success": False, "message": "Invalid job role"}), 400
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER_TRANSCRIPT_EVALUATION, filename)
    file.save(file_path)
     
    score = process_pdf(file_path, job_role)
    return jsonify({"success": True, "score": score})





###################
# Update Candidate Table Marks After Github, LinkedIn, and Transcript Processing
###################

# Update candidate with GitHub marks
@candidate_routes.route('/candidates/<candidate_id>/github', methods=['PUT'])
def update_candidate_with_github_marks(candidate_id):
    data = request.json
    github_mark = data.get("githubMark")
    if github_mark is None:
        return jsonify({"error": "githubMark is required"}), 400
    
    try:
        object_id = ObjectId(candidate_id)
    except Exception as e:
        print("Invalid ObjectId:", e)
        return jsonify({"error": "Invalid candidate ID"}), 400

    result = candidates_collection.update_one({"_id": object_id}, {"$set": {"github_marks": github_mark}})

    if result.matched_count == 0:
        return jsonify({"error": "Candidate not found"}), 404

    return jsonify({"message": "GitHub marks updated successfully"})

# Update candidate with LinkedIn marks
@candidate_routes.route('/candidates/<candidate_id>/linkedin', methods=['PUT'])
def update_candidate_with_linkedin_marks(candidate_id):
    data = request.json
    linkedin_mark = data.get("linkedinMark")
    if linkedin_mark is None:
        return jsonify({"error": "linkedinMark is required"}), 400

    try:
        object_id = ObjectId(candidate_id)
    except Exception as e:
        print("Invalid ObjectId:", e)
        return jsonify({"error": "Invalid candidate ID"}), 400

    result = candidates_collection.update_one({"_id": object_id}, {"$set": {"linkedin_marks": linkedin_mark}})
    
    if result.matched_count == 0:
        return jsonify({"error": "Candidate not found"}), 404
    
    return jsonify({"message": "LinkedIn marks updated successfully"})

# Update candidate with Transcript marks
@candidate_routes.route('/candidates/<candidate_id>/transcript', methods=['PUT'])
def update_candidate_with_transcript_marks(candidate_id):
    data = request.json
    transcript_mark = data.get("transcriptMark")
    if transcript_mark is None:
        return jsonify({"error": "transcriptMark is required"}), 400
    
    try:
        object_id = ObjectId(candidate_id)
    except Exception as e:
        print("Invalid ObjectId:", e)
        return jsonify({"error": "Invalid candidate ID"}), 400  

    result = candidates_collection.update_one({"_id": object_id}, {"$set": {"transcript_marks": transcript_mark}})
    
    if result.matched_count == 0:
        return jsonify({"error": "Candidate not found"}), 404

    return jsonify({"message": "Transcript marks updated successfully"})