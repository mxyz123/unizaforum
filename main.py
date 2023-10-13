from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    return render_template('home.html')


@app.route("/fri")
def fri():
    return render_template('fri.html')


@app.route("/feit")
def feit():
    return render_template('feit.html')


if __name__ == '__main__':
    app.run(debug=True)
