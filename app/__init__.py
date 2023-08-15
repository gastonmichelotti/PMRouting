
from flask import Flask
from app.routes import setup_routes

app = Flask(__name__)
setup_routes(app)
