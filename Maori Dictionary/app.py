import sqlite3
from sqlite3 import Error
from flask import Flask, render_template, request, redirect, session

from flask_bcrypt import Bcrypt
from datetime import date

DB_NAME = "maori_dictionary.db"

app = Flask(__name__)
app.secret_key = "sdjfi3939j93@()@jJIDJijS)09"

bcrypt = Bcrypt(app)

def create_connection(db_file):
    try:

        connection = sqlite3.connect(db_file)
        connection.execute("pragma foreign_keys=ON")

        return connection

    except Error as e:
        print(e)

    return None


def category_setup():
    con = create_connection(DB_NAME)

    query = "SELECT category FROM Dictionary"

    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()
    con.close()
    for i in range(len(category_list)):
        category_list[i] = category_list[i][0].title()
    category_list = sorted(list(set(category_list)))

    return category_list


def is_logged_in():
    if session.get("email") is None:
        return False

    return True


@app.route('/')
def render_home():
    return render_template("home.html", categorys=category_setup(), logged_in=is_logged_in())


@app.route("/categorys/<category>")
def render_category(category):
    con = create_connection(DB_NAME)

    query = "SELECT maori, english, definition FROM Dictionary WHERE category = ?"

    cur = con.cursor()
    cur.execute(query, (category,))
    category_words = cur.fetchall()
    con.close()
    print(len(category_words))
    return render_template("category.html", category=category, words=category_words, logged_in=is_logged_in())


@app.route("/<category>/<word>")
def render_category_word_details(word, category):
    con = create_connection(DB_NAME)

    query = "SELECT maori, english, category, definition, year_level, image, timestamp, author FROM Dictionary WHERE maori = ?"

    cur = con.cursor()
    cur.execute(query, (word,))
    word_details = cur.fetchall()[0]
    con.close()

    if word_details[5]:

        image_found = True

    else:

        image_found = False

    return render_template("word_details.html", word_details=word_details, category=category, image_found=image_found, logged_in=is_logged_in())


@app.route("/login", methods=["POST", "GET"])
def render_login():

    if is_logged_in():
        return redirect("/")

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()
        session["log in details"] = [email, password]
        con = create_connection(DB_NAME)

        query = """SELECT id, first_name, password FROM User WHERE email = ?"""

        cur = con.cursor()

        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        try:
            user_id = user_data[0][0]
            first_name = user_data[0][1]
            db_password = user_data[0][2]

        except IndexError:
            return redirect("/login?error=Email+or+password+is+incorrect")

        if not bcrypt.check_password_hash(db_password, password):
            return redirect("/login?error=Email+or+password+is+incorrect")

        session["email"] = email
        session["user_id"] = user_id
        session["first_name"] = first_name
        session.pop("log in details")

        return redirect("/")

    log_in_details = session.get("log in details")
    if log_in_details is None:
        log_in_details = ["", ""]

    error = request.args.get("error")

    if error is None:
        error = ""

    return render_template("login.html", error=error, logged_in=is_logged_in(), log_in_details=log_in_details)

@app.route('/signup', methods=["POST", "GET"])
def render_signup():
    if is_logged_in():
        return redirect("/")

    if request.method == "POST":

        fname = request.form.get("fname").title().strip()
        lname = request.form.get("lname").title().strip()
        email = request.form.get("email").title().lower()
        password = request.form.get("password").strip()
        password2 = request.form.get("password2").strip()

        session["sign up details"] = [fname, lname, email, password, password2]

        incorrect_characters_string = """<>{}[]\/,|"""

        if len(fname) < 2:
            return redirect("/signup?error=First+name+needs+at+least+2+characters+or+more")

        if len(lname) < 2:
            return redirect("/signup?error=Last+name+needs+at+least+2+characters+or+more")

        for char in incorrect_characters_string:

            if char in fname or char in lname:
                return redirect("/signup?error=Invalid+characters+in+first+or+last+name")

        if len(email) < 6:
            return redirect("/signup?error=Email+must+be+at+least+6+characters+or+more")

        if password != password2:
            return redirect("/signup?error=Passwords+dont+match")

        if len(password) < 8:
            return redirect("/signup?error=Password+must+be+8+characters+or+more")

        hashed_password = bcrypt.generate_password_hash(password)

        con = create_connection(DB_NAME)

        query = "INSERT INTO User(id, first_name, last_name, email, password) VALUES(Null, ?, ?, ?, ?)"

        cur = con.cursor()

        try:

            cur.execute(query, (fname, lname, email, hashed_password))

        except sqlite3.IntegrityError:
            return redirect("/signup?error=Email+is+already+used?details={}")

        con.commit()

        con.close()

        [session.pop(key) for key in list(session.keys())]
        print(session)
        return redirect("login")
    signup_details = session.get("sign up details")

    if signup_details is None:
        signup_details = ["", "", "", "", ""]

    error = request.args.get("error")

    if error is None:
        error = ""

    return render_template("signup.html", error=error, logged_in=is_logged_in(), sign_up_details=signup_details)


@app.route("/logout")
def logout():
    [session.pop(key) for key in list(session.keys())]
    print(session)
    return redirect("/?message=See+you+next+time!")


if __name__ == "__main__":
    app.run()
