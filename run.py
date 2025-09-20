"""
Application entry point
"""

from app import create_app

# Create Flask application
app = create_app('development')

if __name__ == "__main__":
    app.run(debug=True, port=8080)
