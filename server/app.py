from flask import Flask
from routes import register_routes
from config import Config

@app.route('/')
def hello_world():
    return 'Hello, World! This is the server of the application.'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    register_routes(app)

    return app

if __name__ == "__main__":
    app = create_app()
    # Start the development server
    # 0.0.0.0 makes it visible on your local network; change to "127.0.0.1" if you prefer localhost only.
    app.run(host="0.0.0.0", port=8080, debug=True)