import requests

from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient


# Initialize shared components
client = None
db = None



def create_app():
    global client, db

    # Download the model
   

    # Initialize Flask app
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # MongoDB connection
    client = MongoClient("mongodb+srv://Kushan:Kus12NG*MDB@cluster0.vssd7k3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client['ResumeProjectDB']

    # Register Blueprints
    from app.routes.job_routes import job_routes
    from app.routes.candidate_routes import candidate_routes

    app.register_blueprint(job_routes)
    app.register_blueprint(candidate_routes)

    return app
