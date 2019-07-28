from flask import Flask
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

@app.route('/')
def hello_world():
    return 'hello world'
