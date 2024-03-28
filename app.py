from flask import Flask
app = Flask(__name__)
@app.route('/')
def hello_world():
    return 'movies 1782 User Bot'
if __name__ == "__main__":
    app.run()
