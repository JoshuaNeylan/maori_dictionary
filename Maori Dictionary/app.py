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


# function executes when user goes to the signup page
@app.route('/signup', methods=["POST", "GET"])
def render_signup():
    # if the user is already logged in then redirect them to the homepage
    if is_logged_in():
        return redirect("/")

    # if the user attempts to sign up
    if request.method == "POST":
        # creates a variable for each of the inputs the user has filled in
        fname = request.form.get("fname").title().strip()
        lname = request.form.get("lname").title().strip()
        email = request.form.get("email").title().lower()
        password = request.form.get("password").strip()
        password2 = request.form.get("password2").strip()
        is_teacher_or_student = request.form.get("teacher_or_student")

        # creates a list of all the details the user had inputted in in the session storage
        session["sign up details"] = [fname, lname, email, password, password2]

        # a variable containing characters we don't the user to have their first or last name
        incorrect_characters_string = """<>{}[]\/,|"""

        # if the first name the user inputted is less than two characters redirect user to signup page with error
        # "first name needs to be at least 2 characters or more"
        if len(fname) < 2:
            return redirect("/signup?error=First+name+needs+at+least+2+characters+or+more")

        # if the last name the user inputted is less than two characters redirect user to signup page with error
        # "last name needs to be at least 2 characters or more"
        if len(lname) < 2:
            return redirect("/signup?error=Last+name+needs+at+least+2+characters+or+more")

        # checks if any characters we don't want in user's first or last names are present
        for char in incorrect_characters_string:

            # if any characters we don't want in user's first or last names are present
            if char in fname or char in lname:
                # redirect user to sign up page with error "Invalid characters in first or last name"
                return redirect("/signup?error=Invalid+characters+in+first+or+last+name")

        # if email is less than 6 characters
        if len(email) < 6:
            # redirect user to sign up page with error "Email must be at least 6 characters or more"
            return redirect("/signup?error=Email+must+be+at+least+6+characters+or+more")

        # if the user doesn't type the same password in the "confirm password" input as the password input
        if password != password2:
            # redirect the user to the signup page with the error message "password do not match"
            return redirect("/signup?error=Passwords+dont+match")

        # if the password is smaller than 8 characters
        if len(password) < 8:
            # redirect the user to the signup page with the error
            # "Password must be at least 8 characters or more"
            return redirect("/signup?error=Password+must+be+8+characters+or+more")

        # if the previous checks have been valid

        # creates a variable for the user's password after hashing
        hashed_password = bcrypt.generate_password_hash(password)

        # creates a connection to the database and creates a cursor that can be used for the connection
        con = create_connection(DB_NAME)
        cur = con.cursor()

        # creates a request to insert a set of account details into the user table in the database
        query = "INSERT INTO User(id, first_name, last_name, email, password) VALUES(Null, ?, ?, ?, ?)"

        # attempts to execute request by using the details the user put into the signup form
        # (with the hashed password instead of the un-hashed password)
        try:

            cur.execute(query, (fname, lname, email, hashed_password))

        except sqlite3.IntegrityError:
            # if the email the user put in the signup form has already been used before for an account
            # redirect user to the signup page with the error "Email is already used"
            return redirect(f"/signup?error=Email+is+already+used")

        # if all error checks have been passed

        # create request to get the id of the account the user has just created from the User table
        query = "SELECT id FROM User WHERE email = ?"

        # executes the request in the database using the email the user put in the signup form
        cur.execute(query, (email,))

        # creates a variable which stores the account id which was just fetched
        user_id = cur.fetchall()[0][0]

        # if the user selected for a teacher account when signing up
        if is_teacher_or_student == "teacher":
            # add the account id from the account that the user just created to the Teachers table in the database
            query = "INSERT INTO Teachers(id, user_id) VALUES(Null, ?)"
            cur.execute(query, (user_id,))

        # commit changes made to the database
        con.commit()

        # close the connection to the database
        con.close()

        # clears the session storage
        [session.pop(key) for key in list(session.keys())]

        # redirects user to the log in page
        return redirect("login")

    # creates a variable for the details the user has put in the signup form
    # this is used to keep the details filled in if the user gets an error or reloads the page
    signup_details = session.get("sign up details")

    # if the user hasn't filled in any details yet, leave the sign up form blank
    if signup_details is None:
        signup_details = ["", "", "", "", ""]

    # creates a variable for the error message which can be used in the html to display information more clearly
    # unless there is none
    error = request.args.get("error")

    if error is None:
        error = ""

    # renders the signup page for the user looking at the website
    return render_template("signup.html", error=error, logged_in=is_logged_in(), sign_up_details=signup_details)


# function executes when the user attempts to go to the login page
@app.route("/login", methods=["POST", "GET"])
def render_login():
    # if user is already logged in redirect them to the homepage
    if is_logged_in():
        return redirect("/")

    # if the user attempts to log in
    if request.method == "POST":

        # creates variables for the the email and password and a list containing both in session storage
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()
        session["log in details"] = [email, password]

        # creates a connection to the database and creates a cursor that can be used for the connection
        con = create_connection(DB_NAME)
        cur = con.cursor()

        # creates a request to select all the user's info (apart from email)
        # by using the email to search through the User table in the database
        query = """SELECT id, first_name, last_name, password FROM User WHERE email = ?"""

        # executes request with email that user put in log in input
        cur.execute(query, (email,))

        # creates a variable containing the details associated to the email the user put in
        # (whether there is any or not)
        user_data = cur.fetchall()

        # closes connection to the database
        con.close()

        # attempts to set a variable for each detail associated
        try:
            user_id = user_data[0][0]
            first_name = user_data[0][1]
            last_name = user_data[0][2]
            db_password = user_data[0][3]

        except IndexError:
            # if the email the user put in cannot be found in the User table
            # redirect them to the login page with the error "email cannot be found"
            return redirect("/login?error=Email+cannot+be+found")

        # if the password the user entered does not match the one associated with the email they typed in
        if not bcrypt.check_password_hash(db_password, password):
            # redirect user to the login page with error "email or password is incorrect"
            return redirect("/login?error=Email+or+password+is+incorrect")

        # removes login details from session storage and instead stores the user's id, email, first and last name
        session["email"] = email
        session["user_id"] = user_id
        session["first_name"] = first_name
        session["last_name"] = last_name
        session.pop("log in details")

        # redirects user to the homepage
        return redirect("/")

    # attempts to fill in log in detail inputs if the user has the page reloaded
    # if no details were put in by the user, the inputs will be left blank
    log_in_details = session.get("log in details")
    if log_in_details is None:
        log_in_details = ["", ""]

    # creates a variable for the error message which can be used in the html to display information more clearly
    # unless there is none
    error = request.args.get("error")

    if error is None:
        error = ""

    # renders the login page for the user looking at the website
    return render_template("login.html", error=error, logged_in=is_logged_in(), log_in_details=log_in_details)


# function executes when the user attempts to log out
@app.route("/logout")
def logout():
    # clears the session storage for the user
    [session.pop(key) for key in list(session.keys())]

    # redirects user to the homepage with message "See you next time!"
    return redirect("/?message=See+you+next+time!")


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
                           logged_in=is_logged_in(), error=error, new_word_details=new_word_details,
                           is_teacher=is_teacher())


# function executes when user attempts to save a word
@app.route("/saveword-<category>-<word_id>")
def save_word(category, word_id):
    # returns the user to the category they are looking at if they are not logged in with corresponding error
    if not is_logged_in():
        return redirect(f"/categories/{category}?error=not+logged+in")

    # checks if the word id from the word the user is trying to save is indeed an integer
    try:
        word_id = int(word_id)
    except ValueError:

        # if the word id is not an integer return them to the category they were looking at with corresponding error
        return redirect(f"/categories/{category}?error=Invalid+word+id")

    # if word id is an integer:

    # creates variables for the user's id and the current date to use when saving the word on their account
    user_id = session["user_id"]
    timestamp = date.today()

    # creates a connection to the database and creates a cursor that can be used for the connection
    con = create_connection(DB_NAME)
    cur = con.cursor()

    # checks if the word id is actually in dictionary by attempting to select a column from the saved word table where:
    # the word id matches the word id of the word the user is trying to save
    # and the user id matches that of the current user
    try:
        query = "SELECT word_id, user_id FROM Saved_words WHERE word_id = ? and user_id = ?"

        cur.execute(query, (word_id, user_id))

        # checks if the user has or hasn't saved the word already
        try:

            # creates variable which can be used to check if word has been saved
            saved_word_details = cur.fetchall()

            # if word has been saved by the user already
            # return them to the category they were looking at with corresponding error
            if len(saved_word_details[0]) != 0:
                return redirect(f"/categories/{category}?error=Word+has+already+been+saved")

        except IndexError:
            # if the word hasn't been saved before then save the word
            query = "INSERT INTO Saved_words (word_id, user_id, timestamp) VALUES (?, ?, ?)"
            cur.execute(query, (word_id, user_id, timestamp))

    # if the word id isn't actually in the dictionary:
    except sqlite3.IntegrityError as e:

        # prints error messages
        print(e)
        print("Problem Inserting into database - foreign key!")

        # closes connection to the database
        con.close()

        # returns them to the category they were looking at with the corresponding error
        return redirect(f"/categories/{category}?error=Invalid+word+id")

    # commit changes to the database
    con.commit()

    # closes connection to the database
    con.close()
    # return them to the category they were looking the message word has been successfully saved
    return redirect(f"/categories/{category}?message=word+saved")


# function executes when user trys to remove saved words
@app.route("/remove_saved_word-<category>-<word_id>")
def remove_saved_word(category, word_id):
    # if user is not logged in return them to the home page
    if not is_logged_in():
        return redirect("/")

    # checks if the word id from the word the user is trying to remove from saved is indeed an integer
    try:
        word_id = int(word_id)
    except ValueError:

        # if the word id isn't an integer print message stating that it isn't
        # then have the user returned to the homepage with corresponding error
        print(f"{word_id} isn't an integer")
        return redirect("/saved?error=Invalid+word+id")

    # create a variable for the user's id by getting the id from session storage
    user_id = session["user_id"]

    # creates a connection to the database and creates a cursor that can be used for the connection
    con = create_connection(DB_NAME)
    cur = con.cursor()

    # checks if the word id is actually in dictionary by attempting to select a column from the saved word table where:
    # the word id matches the word id of the word the user is trying to save
    # and the user id matches that of the current user
    try:

        query = "SELECT word_id, user_id FROM Saved_words WHERE word_id = ? and user_id = ?"
        cur.execute(query, (word_id, user_id))

        # checks if the user has or hasn't saved the word already
        try:

            # creates variable which can be used to check if word has been saved
            saved_word_details = cur.fetchall()

            # if word has been saved by the user remove word from saved words
            if len(saved_word_details[0]) != 0:
                query = "DELETE FROM Saved_words WHERE word_id = ? and user_id = ?"
                cur.execute(query, (word_id, user_id))

        except IndexError:
            # if word isnt saved return them to the saved words page with corresponding error
            return redirect(f"/saved?error=Word+isnt+saved")

    # if the word id isn't actually in the dictionary:
    except sqlite3.IntegrityError as e:

        # prints error messages
        print(e)
        print("Problem Inserting into database - foreign key!")

        # closes connection to the database
        con.close()

        # returns them to the saved words page with corresponding error
        return redirect(f"/saved?error=Invalid+word+id")

    # commit changes to the database
    con.commit()

    # closes connection to the database
    con.close()

    # return user to saved word page (reloads page)
    return redirect(f"/saved")


# function executes when user attempts clicks on a word on the category page
@app.route("/<category>/<word_id>", methods=["POST", "GET"])
def render_category_word_details(word_id, category):
    # creates a connection to the database and creates a cursor that can be used for the connection
    con = create_connection(DB_NAME)
    cur = con.cursor()

    # creates a request to get details of the word the user clicked on
    query = "SELECT maori, english, category, definition, year_level, image," \
            " timestamp, author, id FROM Dictionary WHERE id = ? and category = ?"

    # executes the request
    cur.execute(query, (word_id, category))

    # checks to see if word is in category
    try:
        word_details = cur.fetchall()[0]

    except IndexError:

        # if the word doesn't exist in category the user was previously looking at
        return redirect(f"/categories/{category}?error=word+not+in+category")

    # if word has an image set the image found variable (created below) to true otherwise set it to false
    if word_details[5]:

        image_found = True

    else:

        image_found = False

    # if the user is attempting to edit the word they are looking at
    if request.method == "POST":
        # creates a variable for each word detail and a list containing new word's details (that the user chooses)
        maori = request.form["maori"].lower()
        english = request.form["english"].lower()
        year_level = request.form["year_level"]
        definition = request.form["definition"]
        new_category = request.form["category"]
        session["new word details"] = [maori, english, year_level, definition]

        # creates a list with the names of all the categories in the dictionary
        category_list = category_setup()

        # if the category the user is trying to edit a word to doesn't exist in the dictionary
        if new_category not in category_list:
            # redirects the user to the word they were trying to edit's page with the error "Category not in dictionary"
            return redirect(f"/{category}/{word_details[8]}?error=Category+not+in+dictionary")

        # creates a string with characters that we don't want appearing in the url
        incorrect_characters_string = """<>{}[]\/,|"""

        # checks if any of the characters we don't want in the url are the maori part of the word
        for char in incorrect_characters_string:
            if char in maori:
                # if characters we don't want in the url are the maori part of the word then
                # return the user to the page for the word they were trying to edit with the corresponding error
                return redirect(f"/{category}/{word_details[8]}?error=Invalid+characters+in+maori")

        # creates a connection to the database and creates a cursor that can be used for the connection
        con = create_connection(DB_NAME)
        cur = con.cursor()

        # gets the first and last name of the user from the session data to create an author variable
        first_name, last_name = session.get("first_name"), session.get("last_name")
        author = f"{first_name} {last_name}"

        # creates a request to select the id's of words from the dictionary
        # that match the maori and english translation the user has put in
        query = "SELECT id FROM Dictionary WHERE maori = ? and english = ?"

        # executes request in database
        cur.execute(query, (maori, english))

        # checks if the new word details have the same english/maori translation as another word
        try:

            word_with_same_details_in_dictionary = cur.fetchall()[0][0]
            if word_with_same_details_in_dictionary != word_details[
                8] and word_with_same_details_in_dictionary is not None:
                # if the new word details do have the same english/maori translation as another word
                # redirect the user to the word they were trying to edit's page with the corresponding error
                return redirect(f"/{category}/{word_details[8]}?error=Word+already+in+dictionary")

        except IndexError:
            pass

        # if the new word details don't have the same english/maori translation as another word

        # create a request to update the current words details
        query = "UPDATE Dictionary SET maori = ?, english = ?, category = ?, year_level = ?," \
                " timestamp = ?, author = ?, definition = ? WHERE id = ?"

        # execute request using the new word details that the user just made
        cur.execute(query, (maori, english, new_category, year_level, date.today(), author, definition, word_details[8],))

        # commit changes to the database and close connection to database
        con.commit()
        con.close()

        # remove the new word details from the current session storage
        session.pop("new word details")

        # return the user to the word they were trying to edit's page with the message "word edited"
        return redirect(f"/{new_category}/{word_id}?message=Word+edited")

    # closes connection to the database
    con.close()

    # fills in the inputs to what the user put in if the page need to reload
    # if there is no details to fill in then leave blank
    new_word_details = session.get("new word details")
    if new_word_details is None:
        new_word_details = ["", "", "", ""]

    # creates a variable for the error message which can be used in the html to display information more clearly
    # unless there is none
    error = request.args.get("error")
    if error is None:
        error = ""

    # renders the word details page for the user looking at the website
    return render_template("word_details.html", word_details=word_details, category=category, image_found=image_found,
                           logged_in=is_logged_in(), error=error, is_teacher=is_teacher())


# function executes when the user goes to the saved words page
@app.route("/saved")
def render_saved():
    # if the user is not logged in redirect them to the homepage
    if not is_logged_in():
        return redirect("/")

    # creates a variable which stores the user's id
    user_id = session["user_id"]

    # creates a connection to the database and creates a cursor that can be used for the connection
    con = create_connection(DB_NAME)
    cur = con.cursor()

    # creates query to get word ids of words that a user has saved and when they were saved from the saved words table
    query = "SELECT word_id, timestamp FROM Saved_words WHERE user_id = ?;"

    # executes the request using the current user's id
    cur.execute(query, (user_id,))

    # creates a variable for all the word ids of words that the user has saved and when they were saved
    word_ids_with_timestamps = cur.fetchall()

    # cleans up variable to remove unnecessary nesting and overall make it easier to use
    for i in range(len(word_ids_with_timestamps)):
        word_ids_with_timestamps[i] = word_ids_with_timestamps[i][0], word_ids_with_timestamps[i][1]
    word_ids_with_timestamps = list(set(word_ids_with_timestamps))

    # creates a request to get the details from dictionary for a certain word id
    query = "SELECT maori, english, category, image, id FROM Dictionary WHERE id = ?;"

    # creates a list which will be used to store the users saved word's details
    saved_words_details_list = []

    for word_id_with_timestamp in word_ids_with_timestamps:

        # executes request (just previously mentioned) for each of the word ids
        # that are in the variable for all the word ids of words that the user has saved and when they were saved
        cur.execute(query, (word_id_with_timestamp[0],))

        # creates a variable for all the details from the current word id that has been requested
        word_details = cur.fetchall()

        # creates a list which will store the details without unnecessary nesting
        updated_word_details = []

        # puts all details of the current word into the updated word detail list
        for detail in word_details[0]:
            updated_word_details.append(detail)

        # if the current word does not have an image, give it the "noimage" image
        if updated_word_details[3] is None:
            updated_word_details[3] = "noimage.png"

        # add the current words details and matching timestamp to the list containing all the saved words details
        saved_words_details_list.append([updated_word_details, word_id_with_timestamp[1]])

    # renders the saved words' page for the user attempting to look at it
    return render_template("saved_words.html", logged_in=is_logged_in(),
                           saved_words_details_list=saved_words_details_list)


# function executes when user goes to the add category page
@app.route('/addcategory', methods=["POST", "GET"])
def render_add_category():
    # a variable containing characters we don't the user to have their first or last name
    incorrect_characters_string = """<>{}[]\/,|"""

    # creates a list which contains the name of all the currently existing categories in the dictionary
    category_list = category_setup()

    # if the user is not a teacher
    if not is_teacher():
        # redirects user to home page with the error "You do not have permission to add categories"
        return redirect(f"/?error=You+do+not+have+permission+to+add+categories")

    # if the user is attempting to add a category
    if request.method == "POST":

        # create a variable which stores the name of the new category the user wants to add in session storage
        session["new_category"] = request.form.get("category").title()

        # create a variable which stores the name of the new category the user wants to add outside of server storage
        new_category = session.get("new_category")

        # checks if any characters we don't want in a category name are present
        for char in incorrect_characters_string:

            # if any characters we don't want in a category name are present
            if char in new_category:
                # redirect user to add category page with error "Invalid characters in category name"
                return redirect("/addcategory?error=Invalid+characters+in+category+name")

        # checks if category name already exists in the dictionary
        for category in category_list:

            # if the category the user is trying to add already exists
            if new_category == category:

                # redirect user to the add category page with the error "This category already exists"
                return redirect("/addcategory?error=This+category+already+exists")

            # checks to see if category is similar to others that already exists
            # this is done by checking if the name of the category the user is trying to add
            # is contained within another category
            # or another category is contained within the name of the category the user is trying to add
            elif new_category in category or category in new_category:

                # if the user has already seen this error before let them continue to add the category
                if "category is similar" in f'{request.args.get("error")}':
                    pass

                # otherwise, if the user is not aware that the category they are trying to add is similar
                # to an already existing one, warn them
                else:
                    # redirects user to the add category page with the error
                    # "This category is similar to (whatever category was similar to the new category name).
                    # resubmit to add anyways"
                    return redirect(
                        f"/addcategory?error=This+category+is+similar+to+{category}.+resubmit+to+add+anyways")

        # clear the new category name from session storage
        session.pop("new_category")

        # creates a connection to the database and creates a cursor that can be used for the connection
        con = create_connection(DB_NAME)
        cur = con.cursor()

        # creates a requests to add a new category to the Categories list in the database
        query = "INSERT INTO Categories(category_name) VALUES(?)"

        # executes request using the category the user has inputed in the add category page
        cur.execute(query, (new_category,))

        # commit changes to the database
        con.commit()

        # close the connection to the database
        con.close()

        # redirects user to the add category page with the message "category added"
        return redirect("/addcategory?error=Category+added")

    # creates a variable for the details the user has put in the add category form
    # this is used to keep the details filled in if the user gets an error or reloads the page
    new_category = session.get("new_category")

    # if the user has typed nothing into the add category form, keep the input blank
    if new_category is None:
        new_category = ""

    # creates a variable for the error message which can be used in the html to display information more clearly
    # unless there is none
    error = request.args.get("error")

    if error is None:
        error = ""

    # renders the add category page for the user trying to look at it
    return render_template("addcategory.html", logged_in=is_logged_in(), new_category=new_category, error=error)


# function executes when user needs to confirm removing a category
@app.route("/confirmation/category-<category>")
def render_confirmation_category(category):
    # if user isn't a teacher
    if not is_teacher():
        # redirects them to the homepage with the error "You do not have permission to remove categories"
        return redirect(f"/?error=You+do+not+have+permission+to+remove+categories")

    # creates a list with the names of all the categories in the dictionary
    category_list = category_setup()

    # if the category the user is trying to delete doesn't exist in the dictionary
    if category not in category_list:
        # redirects the user to the homepage with the error "Category not in dictionary"
        return redirect(f"/?error=Category+not+in+dictionary")

    # renders the confirmation category page for the user looking at it
    return render_template("confirmation_category.html", logged_in=is_logged_in(), category=category)


# function executes when the user needs to confirm removing a word
@app.route("/confirmation/word-<word_in_maori>-<word_in_english>")
def render_confirmation_word(word_in_maori, word_in_english):
    # if the user is not a teacher
    if not is_teacher():
        # redirects user to the homepage with the error message
        # "You do not have permission to remove the word (word they were trying to remove)"
        return redirect(f"/?error=You+do+not+have+permission+to+remove+{word_in_maori}")

    # creates a connection to the database and creates a cursor that can be used for the connection
    con = create_connection(DB_NAME)
    cur = con.cursor()

    # creates request to get maori and english translation of a word from the dictionary Table
    query = "SELECT maori, english FROM Dictionary WHERE maori = ? and english = ?"

    # executes request to using the word that the user is trying to remove
    cur.execute(query, (word_in_maori, word_in_english))

    # checks if the word the user is trying to remove is in the dictionary
    try:
        word_details = cur.fetchall()[0]

    except IndexError:

        # if the word isn't in the dictionary

        # redirects user to the homepage with the error "Word not in dictionary"
        return redirect(f"/?error=Word+not+in+dictionary")

    # renders the remove word confirmation page for the user looking at it
    return render_template("confirmation_word.html", logged_in=is_logged_in(),
                           word_in_maori=word_in_maori, word_in_english=word_in_english)


# function executes when user attempts to delete a category
@app.route("/remove/category-<category>")
def remove_category(category):
    # if user isn't a teacher
    if not is_teacher():
        # redirects them to the homepage with the error
        # "You do not have permission to remove (category the user was trying to remove)"
        return redirect(f"/?error=You+do+not+have+permission+to+remove+{category}")

    # creates a connection to the database and creates a cursor that can be used for the connection
    con = create_connection(DB_NAME)
    cur = con.cursor()

    # creates a list with the names of all the categories in the dictionary
    category_list = category_setup()

    # if the category the user is trying to delete doesn't exist in the dictionary
    if category not in category_list:
        # redirects the user to the homepage with the error "Category"
        return redirect(f"/?error=Category+not+in+dictionary")

    # creates request to delete category from Categories table
    query = "DELETE FROM Categories WHERE category_name = ?"

    # executes request using the category the user is trying to remove
    cur.execute(query, (category,))

    # creates query to get ids of word which are in a certain category
    query = "SELECT id FROM Dictionary WHERE category = ?"

    # executes request with the category the user is trying to remove
    cur.execute(query, (category,))

    # attempts to remove words from the category the user is trying to delete
    try:

        # creates a list for words that need to be removed
        words_that_need_to_be_remove = cur.fetchall()

        # removes all words from the category
        for word in words_that_need_to_be_remove:
            query = "DELETE FROM Saved_words WHERE word_id = ?"

            cur.execute(query, (word[0],))

    except IndexError:
        # if there are noo words in the category don't attempt to remove any
        pass

    # creates a request to remove category from dictionary
    query = "DELETE FROM Dictionary WHERE category = ?"

    # executes request with the category the user is trying to remove
    cur.execute(query, (category,))

    # commit changes to the database
    con.commit()

    # closes connection to the database
    con.close()

    # redirects user to the homepage
    return redirect("/")


# function executes when user is attempting to remove word from dictionary
@app.route("/remove/word-<word_in_maori>-<word_in_english>")
def remove_word(word_in_maori, word_in_english):
    # if the user is not a teacher
    if not is_teacher():
        # redirects user to homepage with the error message
        # "You do not have permission to remove (word with maori translation user is attempting to remove)"
        return redirect(f"/?error=You+do+not+have+permission+to+remove+{word_in_maori}")

    # creates a connection to the database and creates a cursor that can be used for the connection
    con = create_connection(DB_NAME)
    cur = con.cursor()

    # creates request to get maori and english translation of a word from the dictionary Table
    query = "SELECT maori, english FROM Dictionary WHERE maori = ? and english = ?"

    # executes request to using the word that the user is trying to remove
    cur.execute(query, (word_in_maori, word_in_english))

    # checks if the word the user is trying to remove is in the dictionary
    # this is done by trying to get the word's id
    try:
        word_id = cur.fetchall()[0][0]

    except IndexError:

        # if the word isn't in the dictionary

        # redirects user to the homepage with the error "Word not in dictionary"
        return redirect(f"/?error=Word+not+in+dictionary")

    # creates a request to remove a word from the Saved word's table in the database
    query = "DELETE FROM Saved_words WHERE word_id = ?"

    # executes request with the word id of the word the user is trying to remove
    cur.execute(query, (word_id,))

    # creates a request to remove a word from the Dictionary table in the database
    query = "DELETE FROM Dictionary WHERE maori = ? and english = ?"

    # executes request using the maori and english translation of the word
    cur.execute(query, (word_in_maori, word_in_english))

    # commit changes made to the database
    con.commit()

    # close connection with database
    con.close()

    # redirects the user to the homepage
    return redirect("/")


# runs the application
if __name__ == "__main__":
    app.run()
