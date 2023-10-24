from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    return render_template('home.html')


@app.route("/fri")
def fri():
    return render_template('fri.html')

@app.route("/fri/inf")
def inf():
    return render_template('INF.html')

@app.route("/fri/mat")
def mat():
    return render_template('MAT.html')

@app.route("/fri/anj")
def anj():
    return render_template('ANJ.html')


@app.route("/feit")
def feit():
    return render_template('feit.html')

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/register")
def register():
    return render_template('register.html')


if __name__ == '__main__':
    app.run(debug=True)
