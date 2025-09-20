# LEGACY - Use run.py instead
# But keeping this for deployment compatibility
import os
from app import create_app

# Create Flask application with proper environment detection
config_name = os.getenv('FLASK_ENV', 'production')
app = create_app(config_name)

if __name__ == '__main__': 
    app.run(debug=True, port=8080)
