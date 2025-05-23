# from app import create_app

# app = create_app()

# if __name__ == '__main__':
#     app.run(debug=True)
# app.py  – entry-point picked up by Gunicorn
from app import create_app

app = create_app()

if __name__ == "__main__":
    # NEVER enable debug in production
    app.run(host="0.0.0.0", port=5000)
