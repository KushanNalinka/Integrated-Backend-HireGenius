from PIL import Image
import io
import base64
from app.models.candidate_model import Candidate

def get_and_display_chart(candidate_id):
    # Fetch the candidate data from the database
    candidate = Candidate.get_by_id(candidate_id)
    if not candidate or 'skills_chart_image' not in candidate:
        print("Chart not found.")
        return

    # Decode the base64 image
    chart_base64 = candidate['skills_chart_image']
    chart_data = base64.b64decode(chart_base64)

    # Open and display the image
    image = Image.open(io.BytesIO(chart_data))
    image.show()
