import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.transformer import db
from src.routes.transformer import transformer_bp
from src.routes.templates import templates_bp
from src.routes.mappings import mappings_bp
from src.routes.intelligence import intelligence_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'transformer_secret_key_2025'

# Enable CORS for all routes
CORS(app)

# Register blueprints
app.register_blueprint(transformer_bp, url_prefix='/api/transformer')
app.register_blueprint(templates_bp, url_prefix='/api/templates')
app.register_blueprint(mappings_bp, url_prefix='/api/mappings')
app.register_blueprint(intelligence_bp, url_prefix='/api/intelligence')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
