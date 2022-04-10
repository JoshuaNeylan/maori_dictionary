# do error control for editing when changing to an invalid category and others and change categorys to categories
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

    query = "SELECT category_name FROM Categories"

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
    print(session)
    return render_template("home.html", categorys=category_setup(), logged_in=is_logged_in())


@app.route("/categorys/<category>", methods=["POST", "GET"])
def render_category(category):
    con = create_connection(DB_NAME)
    cur = con.cursor()

    if request.method == "POST":

        maori = request.form["maori"].lower()
        english = request.form["english"].lower()
        year_level = request.form["year_level"]
        definition = request.form["definition"]
        session["new word details"] = [maori, english, year_level, definition]
        query = "SELECT id FROM Dictionary WHERE maori = ? and english = ?"
        cur.execute(query, (maori, english,))
        try:

            word_id = cur.fetchall()[0][0]
            return redirect(f"/categorys/{category}?error=Word+already+in+dictionary")

        except IndexError:

            session.pop("new word details")

            con = create_connection(DB_NAME)

            query = "INSERT INTO Dictionary(maori, english, category, year_level, timestamp, author, definition)" \
                    " VALUES(?, ?, ?, ?, ?, ?, ?)"

            cur = con.cursor()

            cur.execute(query, (maori, english, category, year_level, date.today(),
                                f"{session.get('first_name')} {session.get('last_name')}", definition))

            con.commit()

            con.close()

            return redirect(f"/categorys/{category}?error=Word+added")

    new_word_details = session.get("new word details")
    if new_word_details is None:
        new_word_details = ["", "", "", ""]

    query = "SELECT maori, english, image, id FROM Dictionary WHERE category = ?"

    cur.execute(query, (category,))
    category_words = cur.fetchall()
    updated_category_words = []

    for word_details in category_words:
        word_details_list = []

        for detail in word_details:
            word_details_list.append(detail)

        if word_details_list[2] is None:
            word_details_list[2] = "noimage.png"
        updated_category_words.append(word_details_list)

    con.close()

    error = request.args.get("error")

    if error is None:
        error = ""

    return render_template("category.html", category=category, words=updated_category_words,
                           logged_in=is_logged_in(), error=error, new_word_details=new_word_details)


@app.route("/saveword-<category>-<word_id>")
def save_word(category, word_id):
    if not is_logged_in():
        return redirect("/")

    try:
        word_id = int(word_id)
    except ValueError:

        print(f"{word_id} isn't an interger")

        return redirect("/categorys/<category>?error=Invalid+word+id")

    user_id = session["user_id"]
    print(f"user id is {user_id}", word_id)
    timestamp = date.today()
    con = create_connection(DB_NAME)
    cur = con.cursor()

    try:
        query = "SELECT word_id, user_id FROM Saved_words WHERE word_id = ? and user_id = ?"

        cur.execute(query, (word_id, user_id))
        try:

            saved_word_details = cur.fetchall()

            if len(saved_word_details[0]) != 0:
                return redirect(f"/categorys/{category}?error=Word+has+already+been+saved")

        except IndexError:

            query = "INSERT INTO Saved_words (word_id, user_id, timestamp) VALUES (?, ?, ?)"
            cur.execute(query, (word_id, user_id, timestamp))

    except sqlite3.IntegrityError as e:
        print(e)
        print("Problem Inserting into database - foreign key!")
        con.close()
        return redirect(f"/categorys/{category}?error=Invalid+word+id")

    con.commit()
    con.close()
    return redirect(f"/categorys/{category}")


@app.route("/unsaveword-<category>-<word_id>")
def remove_saved_word(category, word_id):
    if not is_logged_in():
        return redirect("/")

    try:
        word_id = int(word_id)
    except ValueError:

        print(f"{word_id} isn't an interger")

        return redirect("/saved?error=Invalid+word+id")

    user_id = session["user_id"]
    print(f"user id is {user_id}", word_id)
    con = create_connection(DB_NAME)
    cur = con.cursor()

    try:

        query = "SELECT word_id, user_id FROM Saved_words WHERE word_id = ? and user_id = ?"
        cur.execute(query, (word_id, user_id))

        try:

            saved_word_details = cur.fetchall()

            if len(saved_word_details[0]) != 0:
                query = "DELETE FROM Saved_words WHERE word_id = ? and user_id = ?"
                cur.execute(query, (word_id, user_id))

        except IndexError:

            return redirect(f"/saved?error=Word+isnt+saved")

    except sqlite3.IntegrityError as e:
        print(e)
        print("Problem Inserting into database - foreign key!")
        con.close()
        return redirect(f"/saved?error=Invalid+word+id")

    con.commit()
    con.close()
    return redirect(f"/saved")


@app.route("/<category>/<word>", methods=["POST", "GET"])
def render_category_word_details(word, category):
    con = create_connection(DB_NAME)

    query = "SELECT maori, english, category, definition, year_level, image," \
            " timestamp, author, id FROM Dictionary WHERE maori = ?"

    cur = con.cursor()
    cur.execute(query, (word,))
    word_details = cur.fetchall()[0]

    if word_details[5]:

        image_found = True

    else:

        image_found = False

    if request.method == "POST":
        maori = request.form["maori"].lower()
        english = request.form["english"].lower()
        year_level = request.form["year_level"]
        definition = request.form["definition"]
        category = request.form["category"].title()
        session["new word details"] = [maori, english, year_level, definition]

        session.pop("new word details")

        con = create_connection(DB_NAME)
        first_name, last_name = session.get("first_name"), session.get("last_name")
        author = f"{first_name} {last_name}"
        query = "UPDATE Dictionary SET maori = ?, english = ?, category = ?, year_level = ?," \
                " timestamp = ?, author = ?, definition = ? WHERE id = ?"

        cur = con.cursor()
        print(word_details[8])
        cur.execute(query, (maori, english, category, year_level, date.today(), author, definition, word_details[8],))

        con.commit()

        con.close()

        return redirect(f"/{category}/{maori}?error=Word+edited")

    con.close()
    new_word_details = session.get("new word details")
    if new_word_details is None:
        new_word_details = ["", "", "", ""]

    error = request.args.get("error")

    if error is None:
        error = ""

    return render_template("word_details.html", word_details=word_details, category=category, image_found=image_found,
                           logged_in=is_logged_in(), error=error)


@app.route("/login", methods=["POST", "GET"])
def render_login():
    if is_logged_in():
        return redirect("/")

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()
        session["log in details"] = [email, password]
        con = create_connection(DB_NAME)

        query = """SELECT id, first_name, last_name, password FROM User WHERE email = ?"""

        cur = con.cursor()

        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        try:
            user_id = user_data[0][0]
            first_name = user_data[0][1]
            last_name = user_data[0][2]
            db_password = user_data[0][3]

        except IndexError:
            return redirect("/login?error=Email+or+password+is+incorrect")

        if not bcrypt.check_password_hash(db_password, password):
            return redirect("/login?error=Email+or+password+is+incorrect")

        session["email"] = email
        session["user_id"] = user_id
        session["first_name"] = first_name
        session["last_name"] = last_name
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
            return redirect(f"/signup?error=Email+is+already+used")

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


@app.route("/saved")
def render_saved():
    if not is_logged_in():
        return redirect("/")

    user_id = session["user_id"]
    con = create_connection(DB_NAME)
    query = "SELECT word_id, timestamp FROM Saved_words WHERE user_id = ?;"

    cur = con.cursor()
    cur.execute(query, (user_id,))
    word_ids_with_timestamps = cur.fetchall()
    for i in range(len(word_ids_with_timestamps)):
        word_ids_with_timestamps[i] = word_ids_with_timestamps[i][0], word_ids_with_timestamps[i][1]

    word_ids_with_timestamps = list(set(word_ids_with_timestamps))

    query = "SELECT maori, english, category, image, id FROM Dictionary WHERE id = ?;"

    saved_words_details_list = []

    for word_id_with_timestamp in word_ids_with_timestamps:
        cur.execute(query, (word_id_with_timestamp[0],))
        word_details = cur.fetchall()
        updated_word_details = []

        for word in word_details[0]:
            updated_word_details.append(word)

        if updated_word_details[3] is None:
            updated_word_details[3] = "noimage.png"

        saved_words_details_list.append([updated_word_details, word_id_with_timestamp[1]])

    return render_template("saved_words.html", logged_in=is_logged_in(),
                           saved_words_details_list=saved_words_details_list)


@app.route('/addcategory', methods=["POST", "GET"])
def render_add_category():
    incorrect_characters_string = """<>{}[]\/,|"""

    category_list = category_setup()

    if not is_logged_in():
        return redirect("/")

    if request.method == "POST":
        session["new_category"] = request.form.get("category").title().replace(" ", "_")
        new_category = session.get("new_category")
        for char in incorrect_characters_string:
            if char in new_category:
                return redirect("/addcategory?error=Invalid+characters+in+category+name")

        for category in category_list:

            if new_category == category:
                return redirect("/addcategory?error=This+category+already+exists")

            elif new_category in category:

                if "category is similar" in f'{request.args.get("error")}':
                    pass

                else:
                    return redirect(
                        f"/addcategory?error=This+category+is+similar+to+{category}.+resubmit+to+add+anyways")

        session.pop("new_category")

        con = create_connection(DB_NAME)

        query = "INSERT INTO Categories(category_name) VALUES(?)"

        cur = con.cursor()

        cur.execute(query, (new_category,))

        con.commit()

        con.close()

        return redirect("/addcategory?error=Category+added")

    new_category = session.get("new_category")

    if new_category is None:
        new_category = ""

    error = request.args.get("error")

    if error is None:
        error = ""

    return render_template("addcategory.html", logged_in=is_logged_in(), new_category=new_category, error=error)


@app.route("/confirmation/category-<category>")
def render_confirmation_category(category):
    if not is_logged_in():
        return redirect("/")

    return render_template("confirmation_category.html", logged_in=is_logged_in(), category=category)


@app.route("/confirmation/word-<word_in_maori>-<word_in_english>")
def render_confirmation_word(word_in_maori, word_in_english):
    if not is_logged_in():
        return redirect("/")

    return render_template("confirmation_word.html", logged_in=is_logged_in(),
                           word_in_maori=word_in_maori, word_in_english=word_in_english)


@app.route("/remove/category-<category>")
def remove_category(category):
    if not is_logged_in():
        return redirect("/")

    con = create_connection(DB_NAME)

    query = "DELETE FROM Categories WHERE category_name = ?"

    cur = con.cursor()

    cur.execute(query, (category,))

    query = "SELECT id FROM Dictionary WHERE category = ?"

    cur.execute(query, (category,))

    try:

        words_that_need_to_be_remove = cur.fetchall()
        print(words_that_need_to_be_remove)

        for word in words_that_need_to_be_remove:
            query = "DELETE FROM Saved_words WHERE word_id = ?"

            cur.execute(query, (word[0],))

    except IndexError:
        pass

    query = "DELETE FROM Dictionary WHERE category = ?"

    cur.execute(query, (category,))

    con.commit()

    con.close()

    return redirect("/")


@app.route("/remove/word-<maori>-<english>")
def remove_word(maori, english):
    if not is_logged_in():
        return redirect("/")

    con = create_connection(DB_NAME)

    query = "SELECT id FROM Dictionary WHERE maori = ? and english = ?"

    cur = con.cursor()

    cur.execute(query, (maori, english))

    word_id = cur.fetchall()[0][0]

    query = "DELETE FROM Saved_words WHERE word_id = ?"

    cur.execute(query, (word_id,))

    query = "DELETE FROM Dictionary WHERE maori = ? and english = ?"

    cur.execute(query, (maori, english))

    con.commit()

    con.close()

    return redirect("/")


if __name__ == "__main__":
    app.run()
