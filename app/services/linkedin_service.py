import spacy
from fuzzywuzzy import fuzz
import spacy
import requests
import json
import os

nlp = spacy.load('en_core_web_md')
 

def load_cache(cache_file='cache.json'):
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache, cache_file='cache.json'):
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=4)

def fetch_linkedin_data(username):
    print("Fetching data from LinkedIn API")
    cache = load_cache()

    print("Checking cache")
    if username in cache:
        print("Loading from cache")
        return cache[username]

    url = "https://linkedin-data-api.p.rapidapi.com/"
    querystring = {"username": username}
    headers = {
        "x-rapidapi-key": "ad440e2882mshd6f9b0aed9a84e0p19f8d9jsnccf873cb409e",
        #"x-rapidapi-key": "d8c96f55e5mshed0fafa54c1f119p14056djsn58663d192484",
        "x-rapidapi-host": "linkedin-data-api.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        data = response.json()
        cache[username] = data
        save_cache(cache)
        return data
    else:
        raise Exception("API request failed with status code: {}".format(response.status_code))


def calculate_score(linkedin_profile, job_data):
     
    total_score = 0
    max_score = 100
    categories = 5

    
    # Experience Calculation
    required_exp = job_data['experienceYears']
    experience_score = 0
    if('position' not in linkedin_profile):
        experience_score = 0
    else:
        profile_exp_years = sum([
            (2024 - pos['start']['year']) if pos['end']['year'] == 0 else (pos['end']['year'] - pos['start']['year'])
            for pos in linkedin_profile['position']
        ])

        if profile_exp_years >= required_exp:
            experience_score = 2
            
        elif profile_exp_years >= required_exp / 2:
            experience_score = 1
            
        else:
            experience_score = 0
    
    total_score += experience_score

    # Education Score
    education_score = 0
    if 'educations' not in linkedin_profile:
        education_score = 0
    else: 
        for edu in linkedin_profile['educations']:
            if fuzz.partial_ratio(edu['degree'].lower(), job_data['education'].lower()) > 80:
                education_score = 2
                break
            elif fuzz.partial_ratio(edu['degree'].lower(), job_data['education'].lower()) > 50:
                education_score = 1
                break
            else:
                education_score = 0
    

    # Education Score with NLP
    education_score_nlp = 0
    if 'educations' not in linkedin_profile:
        education_score_nlp = 0
    else:    
        for edu in linkedin_profile['educations']:
            doc1 = nlp(job_data['education'].lower())
            doc2 = nlp(edu['degree'].lower())
            similarity = doc1.similarity(doc2)
            if similarity > 0.8:
                education_score_nlp = 2
                break
            elif similarity > 0.5:
                education_score_nlp = 1
                break
            else:
                education_score_nlp = 0

    total_score += (education_score + education_score_nlp)/2 

    # Skill Matching
    skill_score = 0
    if 'skills' not in linkedin_profile:
        skill_score = 0
    else:   
        for required_skill in job_data['skills']:
            match = max([fuzz.partial_ratio(skill['name'].lower(), required_skill.lower()) for skill in linkedin_profile['skills']])
            if match > 80:
                skill_score += 2
                break
            elif match > 50:
                skill_score += 1
                break
            else:
                skill_score += 0
    

    # Skill Matching with NLP
    skill_score_nlp = 0
    if 'skills' not in linkedin_profile:
        skill_score_nlp = 0
    else:    
        for skill in linkedin_profile['skills']:
            for required_skill in job_data['skills']:
                doc1 = nlp(skill['name'].lower())
                doc2 = nlp(required_skill.lower())
                similarity = doc1.similarity(doc2)
                if similarity > 0.8:
                    skill_score_nlp += 2
                elif similarity > 0.5:
                    skill_score_nlp += 1
                else:
                    skill_score_nlp += 0

    
    if 'skills' not in linkedin_profile:
        total_score += 0
    else:
        total_score += skill_score +  skill_score_nlp/len(linkedin_profile['skills'])


    # Projects 
    project_score = 0
    
    if 'projects' not in linkedin_profile:
        project_score = 0
    else:  
        if 'projects' in linkedin_profile and isinstance(linkedin_profile['projects'], dict) and 'items' in linkedin_profile['projects']:
            if any(fuzz.partial_ratio(proj['title'].lower(), job_data['job_description'].lower()) > 80 for proj in linkedin_profile['projects']['items']):
                project_score = 2
                
            elif any(fuzz.partial_ratio(proj['title'].lower(), job_data['job_description'].lower()) > 50 for proj in linkedin_profile['projects']['items']):
                project_score = 1
                
            else:
                project_score = 0


    # Projects with NLP
    project_score_nlp = 0

    if 'projects' in linkedin_profile and 'items' in linkedin_profile['projects']:
        if len(linkedin_profile['projects']['items']) > 0:
            for proj in linkedin_profile['projects']['items']:
                doc1 = nlp(proj['title'].lower())
                doc2 = nlp(job_data['job_description'].lower())
                similarity = doc1.similarity(doc2)
                if similarity > 0.8:
                    project_score_nlp += 2
                elif similarity > 0.5:
                    project_score_nlp += 1

            project_score_nlp = project_score_nlp / len(linkedin_profile['projects']['items'])
        else:
            project_score_nlp = 0
            

    total_score += project_score + project_score_nlp
   

    # Volunteering
    volunteer_score = 0
    if 'volunteering' in linkedin_profile:
        volunteer_score = 2 if linkedin_profile['volunteering'] else 0

    total_score +=   volunteer_score

    final_score = (total_score / (categories * 2)) * 100
    return min(final_score, max_score)

 



