# import requests

# from flask import Flask
# from flask_cors import CORS
# from pymongo import MongoClient


# # Initialize shared components
# client = None
# db = None



# def create_app():
#     global client, db

#     # Download the model
   

#     # Initialize Flask app
#     app = Flask(__name__)
#     CORS(app, resources={r"/*": {"origins": "*"}})

#     # MongoDB connection
#     client = MongoClient("mongodb+srv://Kushan:Kus12NG*MDB@cluster0.vssd7k3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
#     db = client['ResumeProjectDB']

#     # Register Blueprints
#     from app.routes.job_routes import job_routes
#     from app.routes.candidate_routes import candidate_routes

#     app.register_blueprint(job_routes)
#     app.register_blueprint(candidate_routes)

#     return app


# import os
# import requests
# from flask import Flask
# from flask_cors import CORS
# from pymongo import MongoClient

# client = None
# db     = None

# def create_app():
#     global client, db

#     app = Flask(__name__)
#     CORS(app, resources={r"/*": {"origins": "*"}})

#     # MongoDB (read from env at runtime)
#     mongo_uri = os.getenv("MONGO_URI")         # <── pulled from EC2 env
#     client    = MongoClient(mongo_uri)
#     db        = client["ResearchProjectNewDB"]

#     # Blueprints
#     from app.routes.job_routes       import job_routes
#     from app.routes.candidate_routes import candidate_routes
#     app.register_blueprint(job_routes)
#     app.register_blueprint(candidate_routes)

#     return app


import os
from pathlib import Path
from dotenv import load_dotenv        # ← new
from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient

# ---------- load .env when running locally ----------
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path, override=False)   # ignored if the file is absent

client = None
db     = None

def create_app():
    global client, db

    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Get Mongo URI from env – fail fast if missing
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise RuntimeError("MONGO_URI not set. Add it to .env (local) "
                           "or pass it as an environment variable in production.")

    client = MongoClient(mongo_uri)
    db     = client["ResearchProjectNewDB"]

    from app.routes.job_routes       import job_routes
    from app.routes.candidate_routes import candidate_routes
    app.register_blueprint(job_routes)
    app.register_blueprint(candidate_routes)

    return app
