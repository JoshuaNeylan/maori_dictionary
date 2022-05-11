# Imports modules needed for website and database
import sqlite3
from sqlite3 import Error
from flask import Flask, render_template, request, redirect, session
from flask_bcrypt import Bcrypt
from datetime import date

# creating a variable for database
DB_NAME = "maori_dictionary.db"

# creates flask instance
app = Flask(__name__)

# sets the secret key which is used to help protect session cookies
app.secret_key = "sdjfi3939j93@()@jJIDJijS)09"

# creates a Bcrypt class container which can be used to hash and check hashed passwords
bcrypt = Bcrypt(app)


# function for creating a connection to the maori dictionary database
def create_connection(db_file):
    # connects to the database unless an error occurs where it will instead print the error and return nothing
    try:

        connection = sqlite3.connect(db_file)
        connection.execute("pragma foreign_keys=ON")

        return connection

    except Error as e:
        print(e)

    return None


# function for getting category names from Categories table, putting them into a sorted list and returning them

def category_setup():
    # connects to database
    con = create_connection(DB_NAME)

    # fetches category names from Categories table, puts them into a list then closes connection
    query = "SELECT category_name FROM Categories"
    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()
    con.close()

    # titles and sorts entries in list and returns the list
    for i in range(len(category_list)):
        category_list[i] = category_list[i][0].title()
    category_list = sorted(list(set(category_list)))
    return category_list


# function the checks if user is logged in
def is_logged_in():
    # returns true if user is logged in
    if session.get("email") is None:
        return False

    return True


# function that checks if user is a teacher
def is_teacher():
    # checks if user is logged in
    if session.get("email") is None:
        return False

    # connects to the database and checks if user id is in the teacher table
    con = create_connection(DB_NAME)
    cur = con.cursor()
    query = """SELECT id FROM Teachers WHERE user_id = ?"""
    cur.execute(query, (session.get("user_id"),))

    # if the user id is in the teacher table the function returns true otherwise it returns false
    if len(cur.fetchall()) == 1:
        # closes connection to database and returns true
        con.close()
        return True

    # closes connection to database and returns false
    con.close()
    return False


# function executes when user is on the home page
@app.route('/')
def render_home():
    # renders the homepage for the user looking at the website
    return render_template("home.html", categories=category_setup(), logged_in=is_logged_in(), is_teacher=is_teacher(),
                           first_name=session.get("first_name"))


# function executes when user attempts to look at a category
@app.route("/categories/<category>", methods=["POST", "GET"])
def render_category(category):
    # creates a connection to the database and creates a cursor that can be used for the connection
    con = create_connection(DB_NAME)
    cur = con.cursor()

    # checks if the category the user is attempting to look at is in the dictionary
    category_list = category_setup()

    # if the category is not in the dictionary the user is redirected to the homepage with a corresponding error
    if category not in category_list:
        return redirect(f"/?error=category+not+in+dictionary")

    # keeps new category inputs fill if user made an error when adding new category
    new_word_details = session.get("new word details")
    if new_word_details is None:
        new_word_details = ["", "", "", ""]

    # creates a request to get all words that are the category the user is looking at in the dictionary
    query = "SELECT maori, english, image, id FROM Dictionary WHERE category = ?"

    # executes the request
    cur.execute(query, (category,))

    # creates variables for the current category words and updated(improved to be easier to work with) category words
    list_of_category_words = cur.fetchall()
    updated_list_of_category_words = []

    # improves the current list filled with category words by removing unnecessary nesting and adding
    # an image for words without them
    for word_details in list_of_category_words:
        word_details_list = []

        for detail in word_details:
            word_details_list.append(detail)

        if word_details_list[2] is None:
            word_details_list[2] = "noimage.png"
        updated_list_of_category_words.append(word_details_list)

    # makes a variable to display the current error (if there is one) on the page
    error = request.args.get("error")

    if error is None:
        error = ""

    #############################################################
    # if the user is attempting to add a word to the dictionary:#
    #############################################################
    if request.method == "POST":

        # creates a variable for each word detail and a list containing new word's details
        maori = request.form["maori"].lower()
        english = request.form["english"].lower()
        year_level = request.form["year_level"]
        definition = request.form["definition"]

        # this word detail list is used to keep the details a user has typed if they got an error
        session["new word details"] = [maori, english, year_level, definition]

        # creates a string with characters that we don't want appearing in the url
        incorrect_characters_string = """<>{}[]\/,|"""

        # checks if any of the characters we don't want in the url are the maori part of the word
        for char in incorrect_characters_string:
            if char in maori:
                # if characters we don't want in the url are the maori part of the word then
                # return the to the category page with the corresponding error
                return redirect(f"/categories/{category}?error=Invalid+characters+in+maori")

        # check if word is in dictionary already
        query = "SELECT id FROM Dictionary WHERE maori = ? and english = ?"
        cur.execute(query, (maori, english,))
        try:

            word_id = cur.fetchall()[0][0]

            # if word is in dictionary return them to the category page they were looking at with corresponding error
            return redirect(f"/categories/{category}?error=Word+already+in+dictionary")

        except IndexError:

            # if word isn't in dictionary continue attempting to add the word

            # removes the word detail list from the users current session since word will be successfully added
            # (Clears the inputs incase the user wants to add another word)
            session.pop("new word details")

            # creates a connection to the database and creates a cursor that can be used for the connection
            con = create_connection(DB_NAME)
            cur = con.cursor()

            # creates a request to add the new word and its details to the dictionary table
            query = "INSERT INTO Dictionary(maori, english, category, year_level, timestamp, author, definition)" \
                    " VALUES(?, ?, ?, ?, ?, ?, ?)"

            # executes the request then commits request
            cur.execute(query, (maori, english, category, year_level, date.today(),
                                f"{session.get('first_name')} {session.get('last_name')}", definition))
            con.commit()

            # closes connection to database and shows them a word added message
            con.close()

            return redirect(f"/categories/{category}?error=Word+added")

    # closes connection to the database
    con.close()

    # renders the category page for the user looking at the website
    return render_template("category.html", category=category, words=updated_list_of_category_words,
                           logged_in=is_logged_in(), error=error, new_word_details=new_word_details
                           , is_teacher=is_teacher())


# function executes when user attempts to save a word
@app.route("/saveword-<category>-<word_id>")
def save_word(category, word_id):
    print(category)
    # returns the user to the homepage if they are not logg
    if not is_logged_in():
        return redirect(f"/categories/{category}?error=not+logged+in")

    try:
        word_id = int(word_id)
    except ValueError:

        print(f"{word_id} isn't an interger")
        return redirect(f"/categories/{category}?error=Invalid+word+id")

    user_id = session["user_id"]
    timestamp = date.today()
    con = create_connection(DB_NAME)
    cur = con.cursor()

    try:
        query = "SELECT word_id, user_id FROM Saved_words WHERE word_id = ? and user_id = ?"

        cur.execute(query, (word_id, user_id))
        try:

            saved_word_details = cur.fetchall()

            if len(saved_word_details[0]) != 0:
                return redirect(f"/categories/{category}?error=Word+has+already+been+saved")

        except IndexError:

            query = "INSERT INTO Saved_words (word_id, user_id, timestamp) VALUES (?, ?, ?)"
            cur.execute(query, (word_id, user_id, timestamp))

    except sqlite3.IntegrityError as e:
        print(e)
        print("Problem Inserting into database - foreign key!")
        con.close()
        return redirect(f"/categories/{category}?error=Invalid+word+id")

    con.commit()
    con.close()
    return redirect(f"/categories/{category}?message=word+saved")


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
    try:
        word_details = cur.fetchall()[0]

    except IndexError:
        return redirect(f"/categories/{category}?error=word+not+in+dictionary")

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

        # creates a string with characters that we don't want appearing in the url
        incorrect_characters_string = """<>{}[]\/,|"""

        # checks if any of the characters we don't want in the url are the maori part of the word
        for char in incorrect_characters_string:
            if char in maori:
                # if characters we don't want in the url are the maori part of the word then
                # return the to the page for the word they were trying to edit with the corresponding error
                return redirect(f"/{category}/{word_details[0]}?error=Invalid+characters+in+maori")

        category_list = category_setup()

        if category not in category_list:
            return redirect(f"/{category}/{word_details[0]}?error=category+not+in+dictionary")

        con = create_connection(DB_NAME)
        cur = con.cursor()
        first_name, last_name = session.get("first_name"), session.get("last_name")
        author = f"{first_name} {last_name}"

        query = "SELECT id FROM Dictionary WHERE maori = ? and english = ?"

        cur.execute(query, (maori, english))

        try:

            word_with_same_details_in_dictionary = cur.fetchall()[0][0]
            if word_with_same_details_in_dictionary != word_details[
                8] and word_with_same_details_in_dictionary is not None:
                return redirect(f"/{category}/{word_details[0]}?error=Word+already+in+dictionary")
        except IndexError:
            pass

        query = "UPDATE Dictionary SET maori = ?, english = ?, category = ?, year_level = ?," \
                " timestamp = ?, author = ?, definition = ? WHERE id = ?"

        cur.execute(query, (maori, english, category, year_level, date.today(), author, definition, word_details[8],))

        con.commit()

        con.close()

        session.pop("new word details")

        return redirect(f"/{category}/{maori}?error=Word+edited")

    con.close()
    new_word_details = session.get("new word details")
    if new_word_details is None:
        new_word_details = ["", "", "", ""]

    error = request.args.get("error")

    if error is None:
        error = ""

    return render_template("word_details.html", word_details=word_details, category=category, image_found=image_found,
                           logged_in=is_logged_in(), error=error, is_teacher=is_teacher())


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
        is_teacher_or_student = request.form.get("teacher_or_student")
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

        query = "SELECT id FROM User WHERE email = ?"
        cur.execute(query, (email,))
        user_id = cur.fetchall()[0][0]
        if is_teacher_or_student == "teacher":
            query = "INSERT INTO Teachers(id, user_id) VALUES(Null, ?)"
            cur.execute(query, (user_id,))
        con.commit()

        con.close()

        [session.pop(key) for key in list(session.keys())]

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

    if not is_logged_in() or not is_teacher():
        return redirect(f"/?error=You+do+not+have+permission+to+add+categories")

    if request.method == "POST":
        session["new_category"] = request.form.get("category").title()
        new_category = session.get("new_category")
        for char in incorrect_characters_string:
            if char in new_category:
                return redirect("/addcategory?error=Invalid+characters+in+category+name")

        for category in category_list:

            if new_category == category:
                return redirect("/addcategory?error=This+category+already+exists")

            elif new_category in category or category in new_category:

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
    if not is_logged_in() or not is_teacher():
        return redirect(f"/?error=You+do+not+have+permission+to+remove+categories")

    category_list = category_setup()
    if category not in category_list:
        return redirect(f"/?error=category+not+in+dictionary")

    return render_template("confirmation_category.html", logged_in=is_logged_in(), category=category)


@app.route("/confirmation/word-<word_in_maori>-<word_in_english>")
def render_confirmation_word(word_in_maori, word_in_english):
    if not is_logged_in() or not is_teacher():
        return redirect(f"/?error=You+do+not+have+permission+to+remove+{word_in_maori}")

    query = "SELECT maori, english FROM Dictionary WHERE maori = ? and english = ?"
    con = create_connection(DB_NAME)
    cur = con.cursor()
    cur.execute(query, (word_in_maori, word_in_english))
    try:
        word_details = cur.fetchall()[0]

    except IndexError:
        return redirect(f"/?error=word+not+in+dictionary")

    return render_template("confirmation_word.html", logged_in=is_logged_in(),
                           word_in_maori=word_in_maori, word_in_english=word_in_english)


@app.route("/remove/category-<category>")
def remove_category(category):
    if not is_logged_in() or not is_teacher():
        return redirect(f"/?error=You+do+not+have+permission+to+remove+{category}")

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
    if not is_logged_in() or not is_teacher():
        return redirect(f"/?error=You+do+not+have+permission+to+remove+{maori}")

    con = create_connection(DB_NAME)

    query = "SELECT id FROM Dictionary WHERE maori = ? and english = ?"

    cur = con.cursor()

    cur.execute(query, (maori, english))
    try:

        word_id = cur.fetchall()[0][0]

    except IndexError:
        return redirect(f"/?error=word+not+in+dictionary")

    query = "DELETE FROM Saved_words WHERE word_id = ?"

    cur.execute(query, (word_id,))

    query = "DELETE FROM Dictionary WHERE maori = ? and english = ?"

    cur.execute(query, (maori, english))

    con.commit()

    con.close()

    return redirect("/")


if __name__ == "__main__":
    app.run()
