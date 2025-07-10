from flask import Flask, request, render_template,redirect


app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the Flask App!"


if __name__ == '__main__':
    app.run(debug=True ,port=2108)