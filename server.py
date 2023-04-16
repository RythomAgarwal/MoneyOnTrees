import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from pymongo import MongoClient
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, request
import urllib

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)



app = Flask(__name__)
client = MongoClient("mongodb+srv://rythom:" + urllib.parse.quote("Rhythm@123") + "@gtcl.3dqqy7u.mongodb.net/test")
app.db = client.gt

app.secret_key = env.get("APP_SECRET_KEY")

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)

# Controllers API
@app.route("/")
def home():
    return render_template(
        "index.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/dash")

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@app.route('/shop')
def index():
    return render_template('shop.html')

@app.route('/buy', methods=["GET", "POST"])
def buy_coins():
    # get amount of coins to purchase from form
    if request.method == "POST":
        name = session.get("user")["userinfo"]["nickname"]
        coins = request.form.get("shop_input")

        user_exists = app.db.holding.find_one({'name': name})

        if user_exists:
            new_coins = int(user_exists['balance']) + int(coins)
            app.db.holding.update_one({'name': name}, {'$set': {'balance': int(new_coins)}})
            return redirect(url_for('dashboard'))
        else:
            # Create new document
            app.db.holding.insert_one({'name': name, 'balance': coins})
            return redirect(url_for('dashboard'))

        return render_template("shop.html")

@app.route('/donate')
def donate():
    name = session.get("user")["userinfo"]["nickname"]
    user_exists_hold = app.db.holding.find_one({'name': name})
    user_exists_don = app.db.donation.find_one({'name': name})
    if user_exists_don:
        donation = user_exists_don['donated']
    else:
        app.db.donation.insert_one({'name': name, 'donated': 0})

    if user_exists_hold:
        holding = user_exists_hold['balance']
    else:
        app.db.holding.insert_one({'name': name, 'balance': 0})

    return render_template("donate.html", coin_balance=holding, dona=donation)

@app.route('/don', methods=["GET", "POST"])
def don_coins():
    name = session.get("user")["userinfo"]["nickname"]
    user_exists = app.db.donation.find_one({'name': name})
    # get amount of coins to purchase from form
    if request.method == "POST":
        name = session.get("user")["userinfo"]["nickname"]
        don_amount = request.form.get("don_input")
        user_exists_hold = app.db.holding.find_one({'name': name})
        user_exists = app.db.donation.find_one({'name': name})

        if user_exists:
            new_coins = int(user_exists['donated']) + int(don_amount)
            app.db.donation.update_one({'name': name}, {'$set': {'donated': int(new_coins)}})
            print(user_exists_hold["balance"])
            hold = int(user_exists_hold["balance"]) - int(don_amount)
            app.db.holding.update_one({'name': name}, {'$set': {'balance': int(hold)}})
            return redirect(url_for('dashboard'))
        else:
            # Create new document
            app.db.donation.insert_one({'name': name, 'donated': don_amount})
            return redirect(url_for('dashboard'))

    return render_template("donate.html")

@app.route('/challenges')
def challenge():
    return render_template('challenge.html')

@app.route('/dash')
def dashboard():
    global holding, donation
    name = session.get("user")["userinfo"]["nickname"]
    user_exists_hold = app.db.holding.find_one({'name': name})
    user_exists_don = app.db.donation.find_one({'name': name})
    if user_exists_don:
        donation = user_exists_don['donated']
    else:
        app.db.donation.insert_one({'name': name, 'donated': 0})

    if user_exists_hold:
        holding = user_exists_hold['balance']
    else:
        app.db.holding.insert_one({'name': name, 'balance': 0})

    return render_template("dashboard.html", coin_balance=holding,
                        donated_coins=donation)


if __name__ == '__main__':
 
    # run() method of Flask class runs the application
    # on the local development server.
    app.run()
