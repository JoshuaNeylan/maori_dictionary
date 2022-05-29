# Imports modules needed for website and database
import sqlite3
from datetime import date
from sqlite3 import Error

from flask import Flask, render_template, request, redirect, session
from flask_bcrypt import Bcrypt

# creating a variable for database
DB_NAME = "maori_dictionary.db"

# list which holds input maximums for word details in this order:
# maori, english, definition, category name and year level
WORD_DETAILS_INPUT_MAXIMUMS = [85, 100, 200, 50, 10]

# list which holds input maximums for signup details in this order:
# first name, middle name/s, last name, email
SIGNUP_DETAILS_INPUT_MAXIMUMS = [30, 30, 30, 80]

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


# function for executing queries to the database
def query_executor(query, variable_used_to_execute_query, return_values):
    # creates connection to the database with a cursor to use
    con = create_connection(DB_NAME)
    cur = con.cursor()

    # if the query is using a variable to do a specific value request
    if variable_used_to_execute_query:

        # execute query using the variable given to the function
        cur.execute(query, variable_used_to_execute_query)

    # if the query isn't using a variable to do a specific value request
    elif not variable_used_to_execute_query:
        # execute query without a variable
        cur.execute(query)

    # if the user is trying to fetch values from the database
    if return_values:
        # close connection to database and return values
        values = cur.fetchall()
        con.close()
        return values

    # if the user is making changes to the database
    if not return_values:
        # commit changes to database that were made
        con.commit()

    # close connection to database
    con.close()


# function the checks if user is logged in
def is_logged_in():
    # returns value true if user is logged in otherwise returns false
    if session.get("email") is None:
        return False

    return True


# function that checks if user is a teacher
def is_teacher():
    # checks if user is logged in
    if session.get("email") is None:
        return False

    #  uses query executor to return a true or false value depending on whether the user is a teacher or not
    #  if the user is a teacher it will return true otherwise it returns false

    return len(query_executor("SELECT id FROM Teachers WHERE user_id = ?", (session.get("user_id"),), True))


# function executes when user is on the home page
@app.route('/')
def render_home():
    # uses the query executor to get an unsorted category list
    category_list = query_executor("SELECT category_name, id FROM Categories", None, True)

    category_list = sorted(list(category_list))
    # titles and sorts entries in list(alphabetical order) and returns the list
    for i in range(len(category_list)):
        category_list[i] = [category_list[i][1], category_list[i][0]]

    # renders the homepage for the user looking at the website
    return render_template("home.html", categories_with_ids=category_list, logged_in=is_logged_in(),
                           is_teacher=is_teacher(), first_name=session.get("first_name"))


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

        # checks if user has put a middle name in the middle name input
        if request.form.get("mname") is not None:
            mname = request.form.get("mname").title()
        else:
            # if the user hasn't make middle name a blank string
            mname = ""
        lname = request.form.get("lname").title().strip()
        email = request.form.get("email").title().lower()
        password = request.form.get("password").strip()
        password2 = request.form.get("password2").strip()
        is_teacher_or_student = request.form.get("teacher_or_student")

        # creates a list of all the details the user had inputted in the session storage
        session["sign up details"] = [fname, mname, lname, email, password, password2]

        # checks that the first name, last name and email the user put in the signup inputs
        # are less than the maximum amount of characters that have been set for each input
        if [i for i in range(3) if len([fname, mname, lname, email][i]) > SIGNUP_DETAILS_INPUT_MAXIMUMS[i]]:
            # if the user has gone over the maximum size for any of the signup detail inputs
            # redirect user to the signup page with the error message
            # "One or more of the fields of the fields were filled their limit"
            return redirect(f"/signup?error=One+or+more+of+the+fields+were+filled+over+their+limit")

        # a variable containing characters we don't want the user to have their first or last name
        incorrect_characters_string = """<>{}[]\/,|"""

        # if the first name the user inputted is less than two characters redirect user to signup page
        # with error message "first name needs to be at least 2 characters or more"
        if len(fname) < 2:
            return redirect("/signup?error=First+name+needs+at+least+2+characters+or+more")

        # if the last name the user inputted is less than two characters redirect user to signup page
        # with error message"last name needs to be at least 2 characters or more"
        if len(lname) < 2:
            return redirect("/signup?error=Last+name+needs+at+least+2+characters+or+more")

        # checks if any characters we don't want in user's first or last names are present
        for char in incorrect_characters_string:

            # if any characters we don't want in user's first, middle or last names are present
            if char in fname or char in lname or char in mname:
                # redirect user to sign up page with error message "Invalid characters in first or last name"
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
            # redirect the user to the signup page with the error message
            # "Password must be at least 8 characters or more"
            return redirect("/signup?error=Password+must+be+8+characters+or+more")

        # if the previous checks have been valid

        # creates a variable for the user's password after hashing
        hashed_password = bcrypt.generate_password_hash(password)

        # attempts to use the query executor to put the users details
        # (that they put into the signup form) and the hashed version of the password they inputted
        # into the Users table in the database

        try:

            query_executor(
                "INSERT INTO Users(id, first_name, middle_name, last_name, email, password) VALUES(Null, ?, ?, ?, ?, ?)",
                (fname, mname, lname, email, hashed_password), False)

        except sqlite3.IntegrityError:
            # if the email the user put in the signup form has already been used before for an account
            # redirect user to the signup page with the error message "Email is already used"
            return redirect(f"/signup?error=Email+is+already+used")

        # if all error checks have been passed

        # uses the query executor to get the user's new account id
        # using the email they put in the signup form
        user_id = query_executor("SELECT id FROM Users WHERE email = ?", (email,), True)[0][0]

        # if the user selected for a teacher account when signing up
        if is_teacher_or_student == "teacher":
            # add the account id from the account that the user just created to the Teachers table in the database
            # using the query executor
            query_executor("INSERT INTO Teachers(id, user_id) VALUES(Null, ?)", (user_id,), False)

        # clears the session storage
        [session.pop(key) for key in list(session.keys())]

        # redirects user to the log in page
        return redirect("login")

    # creates a variable for the details the user has put in the signup form
    # this is used to keep the details filled in if the user gets an error or reloads the page
    signup_details = session.get("sign up details")

    # if the user hasn't filled in any details yet, leave the sign up form blank
    if signup_details is None:
        signup_details = ["", "", "", "", "", ""]

    # creates a variable for the error message which can be used in the html to display information more clearly
    # unless there is none
    error = request.args.get("error")

    if error is None:
        error = ""

    # renders the sign up page for the user looking at the website
    return render_template("signup.html", error=error, logged_in=is_logged_in(), sign_up_details=signup_details)


# function executes when the user attempts to go to the login page
@app.route("/login", methods=["POST", "GET"])
def render_login():
    # if user is already logged in redirect them to the homepage
    if is_logged_in():
        return redirect("/")

    # if the user attempts to log in
    if request.method == "POST":

        # creates variables for the email and password and a list containing both in session storage
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()
        session["log in details"] = [email, password]

        # creates a request to select all the user's info (apart from email)
        # by using the email to search through the Users table in the database
        user_data = query_executor("SELECT id, first_name, middle_name, last_name, password FROM Users WHERE email = ?",
                                   (email,),
                                   True)

        # attempts to set a variable for each detail associated
        try:
            user_id = user_data[0][0]
            first_name = user_data[0][1]
            middle_name = user_data[0][2]
            last_name = user_data[0][3]
            db_password = user_data[0][4]

        except IndexError:
            # if the email the user put in cannot be found in the User table
            # redirect them to the login page with the error message "email cannot be found"
            return redirect("/login?error=Email+cannot+be+found")

        # if the password the user entered does not match the one associated with the email they typed in
        if not bcrypt.check_password_hash(db_password, password):
            # redirect user to the login page with error message "email or password is incorrect"
            return redirect("/login?error=Email+or+password+is+incorrect")

        # removes login details from session storage and instead stores the user's id, email, first middle and last name
        session["email"] = email
        session["user_id"] = user_id
        session["first_name"] = first_name
        session["middle_name"] = middle_name
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
@app.route("/category/<category_id>", methods=["POST", "GET"])
def render_category(category_id):
    # using the query executor
    # checks if the category the user is attempting to look at is in the dictionary
    try:
        category_name = query_executor("SELECT category_name FROM Categories WHERE id = ?", (category_id,),
                                       True)[0][0]
    except IndexError:
        # if the category dosen't exist return user to homepage with error message
        # "Category not in dictionary"
        return redirect("/?error=Category+not+in+dictionary")

    # keeps new category inputs fill if user made an error when adding new category
    new_word_details = session.get("new word details")
    if new_word_details is None:
        new_word_details = ["", "", "", ""]

    # uses query executor to get all words that are the category the user is looking at in the dictionary
    list_of_category_words = query_executor("SELECT maori, english, image, id FROM Dictionary WHERE category = ?",
                                            (category_name,), True)

    # creates variables for the current category words and updated(improved to be easier to work with) category words
    updated_list_of_category_words = []

    # improves the current list filled with category words by removing unnecessary nesting
    # and adding an image for words without them
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
    # if the user is attempting to add a word to the dictionary #
    #############################################################
    if request.method == "POST":

        # creates a variable for each word detail and a list containing new word's details
        maori = request.form["maori"].lower()
        english = request.form["english"].lower()
        year_level = request.form["year_level"]
        definition = request.form["definition"]

        # this word detail list is used to keep the details a user has typed if they got an error
        session["new word details"] = [maori, english, year_level, definition]

        # attempts to check if the user hasn't gone over the maximum size for any of the word detail inputs
        try:

            if [i for i in range(3) if len([maori, english, definition][i]) > WORD_DETAILS_INPUT_MAXIMUMS[i]] or int(
                    year_level) > WORD_DETAILS_INPUT_MAXIMUMS[4]:
                # if the user has gone over the maximum size for any of the word detail inputs
                # redirect user to the category they were trying to add a word to with the error message
                # "One or more of the fields of the fields were filled their limit"
                return redirect(f"/category/{category_id}?error=One+or+more+of+the+fields+were+filled+over+their+limit")

        except ValueError:
            # if a letter/s has been entered as the year level first encountered
            # redirect user to the category they were trying to add a word to with the error message
            # "Year level first encountered at must be a number"
            return redirect(f"/category/{category_id}?error=Year+level+first+encountered+at+must+be+number")

        # checks if any of the details the user inputted are blank
        for detail in session.get("new word details"):
            if not detail:
                # if one of the details the user entered in was empty
                # redirect them to the category they were trying to add the word to with the error message
                # "All fields must be filled to add word"
                return redirect(f"/category/{category_id}?error=All+fields+must+be+filled+to+add+word")
        # creates a string with characters that could be problematic being in a word's maori/english translation
        incorrect_characters_string = """<>{}[]\/,|"""

        # checks if any of the characters we don't want in the url are the maori/english part of the word
        for char in incorrect_characters_string:
            if char in maori or char in english:
                # if there are characters we don't want in the maori/english details of a word then
                # return the user to the category page with the error message
                # "Invalid characters in moari or english details"
                return redirect(f"/category/{category_id}?error=Invalid+characters+in+maori+or+english+details")

        # check if word is in dictionary already using query executor

        try:

            word_id = query_executor("SELECT id FROM Dictionary WHERE maori = ? and english = ?", (maori, english,),
                                     True)[0][0]

            # if word is in dictionary return them to the category page they were looking at with error message
            # "Word already in dictionary"
            return redirect(f"/category/{category_id}?error=Word+already+in+dictionary")

        except IndexError:

            # if word isn't in dictionary continue attempting to add the word

            # removes the word detail list from the users current session since word will be successfully added
            # (Clears the inputs incase the user wants to add another word)
            session.pop("new word details")

            # uses query executor to add the new word and its details to the dictionary table
            query_executor(
                "INSERT INTO Dictionary(maori, english, category, year_level, timestamp, author, definition)"
                " VALUES(?, ?, ?, ?, ?, ?, ?)",
                (maori, english, category_name, year_level, date.today(),
                 f"{session.get('first_name')} {session.get('middle_name')} {session.get('last_name')}", definition),
                False)

            # reloads page with message "Word added"
            return redirect(f"/category/{category_id}?error=Word+added")

    # renders the category page for the user looking at the website
    return render_template("category.html", category_name_with_id=[category_id, category_name],
                           words=updated_list_of_category_words,
                           logged_in=is_logged_in(), error=error, new_word_details=new_word_details,
                           is_teacher=is_teacher())


# function executes when user attempts to save a word
@app.route("/saveword-<category_id>-<word_id>")
def save_word(category_id, word_id):
    # returns the user to the category they are looking at if they are not logged in with error message
    # "not logged in"
    if not is_logged_in():
        return redirect(f"/category/{category_id}?error=not+logged+in")

    # checks if the word id from the word the user is trying to save is indeed an integer
    try:
        word_id = int(word_id)
    except ValueError:

        # if the word id is not an integer return them to the category they were looking at with error message
        # Invalid word id
        return redirect(f"/category/{category_id}?error=Invalid+word+id")

    # if word id is an integer:

    # creates variables for the user's id and the current date to use when saving the word on their account
    user_id = session["user_id"]
    timestamp = date.today()

    # creates a connection to the database and creates a cursor that can be used for the connection
    con = create_connection(DB_NAME)
    cur = con.cursor()

    # uses the query executor to check if the word the using is currently trying to save is already saved
    # and exists in the dictionary

    try:
        saved_word_details = query_executor(
            "SELECT word_id, user_id FROM Saved_words WHERE word_id = ? and user_id = ?",
            (word_id, user_id), True)
        try:

            # if word has been saved by the user already
            # return them to the category they were looking at with error message
            # "Word has already been saved"
            if len(saved_word_details[0]) != 0:
                return redirect(f"/category/{category_id}?error=Word+has+already+been+saved")

        except IndexError:
            # if the word hasn't been saved before then save the word using the query executor
            query_executor("INSERT INTO Saved_words (word_id, user_id, timestamp) VALUES (?, ?, ?)",
                           (word_id, user_id, timestamp), False)

    # if the word id isn't actually in the dictionary:
    except sqlite3.IntegrityError as e:

        # prints error messages
        print(e)
        print("Problem Inserting into database - foreign key!")
        # returns them to the category they were looking at with the error message
        # "Invalid word id"
        return redirect(f"/category/{category_id}?error=Invalid+word+id")

    # return them to the category they were looking the message word has been successfully saved
    return redirect(f"/category/{category_id}?message=word+saved")


# function executes when user trys to remove saved words
@app.route("/remove_saved_word-<word_id>")
def remove_saved_word(word_id):
    # if user is not logged in return them to the home page
    if not is_logged_in():
        return redirect("/")

    # checks if the word id from the word the user is trying to remove from saved is indeed an integer
    try:
        word_id = int(word_id)
    except ValueError:

        # if the word id isn't an integer print message stating that it isn't
        # then have the user returned to the homepage with error message
        # "(word id entered by user) isn't an integer"
        print(f"{word_id} isn't an integer")
        return redirect("/saved?error=Invalid+word+id")

    # create a variable for the user's id by getting the id from session storage
    user_id = session["user_id"]

    # uses the query executor to check if the word they are trying to remove from saved words
    # has been saved already and exists in the dictionary
    try:

        saved_word_details = query_executor(
            "SELECT word_id, user_id FROM Saved_words WHERE word_id = ? and user_id = ?",
            (word_id, user_id), True)

        # checks if the user has or hasn't saved the word already
        try:

            # if word has been saved by the user remove word from saved words
            # using the query executor
            if len(saved_word_details[0]) != 0:
                query_executor("DELETE FROM Saved_words WHERE word_id = ? and user_id = ?", (word_id, user_id), False)

        except IndexError:
            # if word isnt saved return them to the saved words page with the error message
            # "Word isnt saved"
            return redirect(f"/saved?error=Word+isnt+saved")

    # if the word id isn't actually in the dictionary:
    except sqlite3.IntegrityError as e:

        # prints error messages
        print(e)
        print("Problem Inserting into database - foreign key!")
        # returns them to the saved words page with error message
        # "Invalid word id"
        return redirect(f"/saved?error=Invalid+word+id")

    # return user to saved word page (reloads page)
    return redirect(f"/saved")


# function executes when user attempts clicks on a word on the category page
@app.route("/<category_id>/<word_id>", methods=["POST", "GET"])
def render_category_word_details(word_id, category_id):
    # using the query executor
    # attempts to get the name of the category for the word the user is trying to look at
    try:

        category_name = query_executor("SELECT category_name FROM categories WHERE id = ?",
                                       (category_id,), True)[0][0]
    except IndexError:
        # if the category for the word the user is trying to look at does not exist
        # redirect them to the homepage with the error message  "category not in dictionary"
        return redirect("/?error=category+not+in+dictionary")

    try:
        # uses query executor to get the details of the word the user is trying to look at
        word_details_list = query_executor("SELECT maori, english, category, definition, year_level, image,"
                                           " timestamp, author, id FROM Dictionary WHERE id = ? and category = ?",
                                           (word_id, category_name), True)[0]

    except IndexError:

        # if the word doesn't exist in category the user was previously looking at
        # redirect them to the category they thought the word was in with the error message
        #  "word not in category"
        return redirect(f"/category/{category_id}?error=word+not+in+category")

    # if word has an image set the image found variable (created below) to true otherwise set it to false
    if word_details_list[5]:

        image_found = True

    else:

        image_found = False

    ##################################################################
    # if the user is attempting to edit the word they are looking at #
    ##################################################################
    if request.method == "POST":
        # creates a variable for each word detail and a list containing new word's details (that the user chooses)
        maori = request.form["maori"].lower()
        english = request.form["english"].lower()
        year_level = request.form["year_level"]
        definition = request.form["definition"]
        new_category = request.form["category"]
        session["new word details"] = [maori, english, year_level, definition]
        # attempts to check if the user hasn't gone over the maximum size for any of the word detail inputs
        try:

            if [i for i in range(4) if
                len([maori, english, definition, new_category][i]) > WORD_DETAILS_INPUT_MAXIMUMS[i]] or int(
                year_level) > WORD_DETAILS_INPUT_MAXIMUMS[4]:
                # if the user has gone over the maximum size for any of the word detail inputs
                # redirect user to the page of the word they were trying to edit with the error message
                # "One or more of the fields of the fields were filled their limit"
                return redirect(
                    f"/{category_id}/{word_details_list[8]}?error=One+or+more+of+the+fields+were+filled+over+their+limit")

        except ValueError:
            # if a letter/s has been entered as the year level first encountered
            # redirect user to the page of the word they were trying to edit with the error message
            # "Year level first encountered at must be a number"
            return redirect(
                f"/{category_id}/{word_details_list[8]}?error=Year+level+first+encountered+at+must+be+number")

        # checks if any of the details the user inputted are blank
        for detail in session.get("new word details"):
            if not detail:
                # if one of the details the user entered in was empty
                # redirect them to the category they were trying to edit the word to with the error message
                # "All fields must be filled to edit word"
                return redirect(f"/{category_id}/{word_details_list[8]}?error=All+fields+must+be+filled+to+edit+word")
        # using the query executor
        # checks the categories table to see if new category exists in table
        try:
            new_category = query_executor("SELECT category_name FROM categories WHERE category_name = ?",
                                          (new_category,), True)[0][0]

        # if the category the user is trying to edit a word to doesn't exist in the dictionary
        except IndexError:

            # redirects the user to the word they were trying to edit's page with the error message
            # "Category not in dictionary"
            return redirect(f"/{category_id}/{word_details_list[8]}?error=Category+not+in+dictionary")

        # creates a string with characters that we don't want appearing in the url
        incorrect_characters_string = """<>{}[]\/,|"""

        # checks if any of the characters we don't want in the url are the maori part of the word
        for char in incorrect_characters_string:
            if char in maori or char in english:
                # if characters we don't want in the url are the maori/english part of the word then
                # return the user to the page for the word they were trying to edit with the error message
                # "Invalid characters in english or maori details"
                return redirect(f"/{category_id}/{word_details_list[8]}"
                                f"?error=Invalid+characters+in+english+or+maori+details")

        # gets the first and last name of the user from the session data to create an author variable
        author = f"{session.get('first_name')} {session.get('middle_name')} {session.get('last_name')}"

        # using the query executor
        # checks if the new word details have the same english/maori translation as another word
        try:

            word_with_same_details_in_dictionary = \
                query_executor("SELECT id FROM Dictionary WHERE maori = ? and english = ?",
                               (maori, english), True)[0][0]
            if word_with_same_details_in_dictionary != word_details_list[8] \
                    and word_with_same_details_in_dictionary is not None:
                # if the new word details do have the same english/maori translation as another word
                # redirect the user to the word they were trying to edit's page with the error message
                # "Word already in dictionary"
                return redirect(f"/{category_id}/{word_details_list[8]}?error=Word+already+in+dictionary")

        except IndexError:
            pass

        # if the new word details don't have the same english/maori translation as another word

        # uses query executor to update the current words details
        query_executor("UPDATE Dictionary SET maori = ?, english = ?, category = ?, year_level = ?,"
                       " timestamp = ?, author = ?, definition = ? WHERE id = ?",
                       (maori, english, new_category, year_level, date.today(), author, definition,
                        word_details_list[8],),
                       False)

        # remove the new word details from the current session storage
        session.pop("new word details")

        # uses query executor to get the id of the category the user put in the edit word details form
        new_category_id = query_executor("SELECT id FROM Categories WHERE category_name = ?",
                                         (new_category,), True)[0][0]
        # return the user to the word they were trying to edit's page with the message "word edited"
        return redirect(f"/{new_category_id}/{word_id}?message=Word+edited")

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
    return render_template("word_details.html", word_details=word_details_list, image_found=image_found,
                           logged_in=is_logged_in(), error=error, is_teacher=is_teacher(), category_id=category_id)


# function executes when the user goes to the saved words page
@app.route("/saved")
def render_saved():
    # if the user is not logged in redirect them to the homepage
    if not is_logged_in():
        return redirect("/")

    # creates a variable which stores the user's id
    user_id = session["user_id"]

    # uses query executor to get word ids of words that a user has saved
    # and when they were saved from the saved words table
    word_ids_with_timestamps = query_executor("SELECT word_id, timestamp FROM Saved_words WHERE user_id = ?",
                                              (user_id,), True)

    # cleans up variable to remove unnecessary nesting and overall make it easier to use
    for i in range(len(word_ids_with_timestamps)):
        word_ids_with_timestamps[i] = word_ids_with_timestamps[i][0], word_ids_with_timestamps[i][1]
    word_ids_with_timestamps = list(set(word_ids_with_timestamps))

    # creates a list which will be used to store the users saved word's details
    saved_words_details_list = []

    for word_id_with_timestamp in word_ids_with_timestamps:

        # uses query executor to select the details of each saved word
        # using their timestamp to identify them
        word_details = query_executor("SELECT maori, english, category, image, id FROM Dictionary WHERE id = ?",
                                      (word_id_with_timestamp[0],), True)

        # creates a list which will store the details without unnecessary nesting
        updated_word_details = []

        # puts all details of the current word into the updated word detail list along with
        # the id of the category the word is in (which is fetched using the query executor)
        for detail in word_details[0]:
            updated_word_details.append(detail)
        updated_word_details.append(query_executor("SELECT id FROM Categories WHERE category_name = ?",
                                                   (updated_word_details[2],), True)[0][0])
        # if the current word does not have an image, give it the "noimage" image
        if updated_word_details[3] is None:
            updated_word_details[3] = "noimage.png"

        # add the current words details and matching timestamp to the list containing all the saved words details
        saved_words_details_list.append([updated_word_details, word_id_with_timestamp[1]])

        # sorts saved words list
        saved_words_details_list = sorted(saved_words_details_list)

    # renders the saved words' page for the user attempting to look at it
    return render_template("saved_words.html", logged_in=is_logged_in(),
                           saved_words_details_list=saved_words_details_list)


# function executes when user goes to the add category page
@app.route('/addcategory', methods=["POST", "GET"])
def render_add_category():
    # a variable containing characters we don't the user to put in a category
    incorrect_characters_string = """<>{}[]\/,|"""

    # if the user is not a teacher
    if not is_teacher():
        # redirects user to home page with the error message "You do not have permission to add categories"
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
                # redirect user to add category page with error message "Invalid characters in category name"
                return redirect("/addcategory?error=Invalid+characters+in+category+name")

        # uses the query executor to get a list of all the categories
        category_list = query_executor("SELECT category_name FROM Categories", None, True)

        for category in category_list:

            # if the category the user is trying to add already exists
            if new_category == category[0]:

                # redirect user to the add category page with the error message "This category already exists"
                return redirect("/addcategory?error=This+category+already+exists")

            # checks to see if category is similar to others that already exists
            # this is done by checking if the name of the category the user is trying to add
            # is contained within another category
            # or another category is contained within the name of the category the user is trying to add
            elif new_category in category[0] or category[0] in new_category:

                # if the user has already seen this error before let them continue to add the category
                if "category is similar" in f'{request.args.get("error")}':
                    pass

                # otherwise, if the user is not aware that the category they are trying to add is similar
                # to an already existing one, warn them
                else:
                    # redirects user to the add category page with the error message
                    # "This category is similar to (whatever category was similar to the new category name).
                    # resubmit to add anyways"
                    return redirect(
                        f"/addcategory?error=This+category+is+similar+to+{category[0]}.+resubmit+to+add+anyways")

        # clear the new category name from session storage
        session.pop("new_category")

        # uses the query executor to add a new category to the Categories list in the database
        query_executor("INSERT INTO Categories(category_name) VALUES(?)", (new_category,), False)

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
@app.route("/confirmation/category-<category_id>")
def render_confirmation_category(category_id):
    # if user isn't a teacher
    if not is_teacher():
        # redirects them to the homepage with the error message "You do not have permission to remove categories"
        return redirect(f"/?error=You+do+not+have+permission+to+remove+categories")

    # uses query executor to check if the category the user is trying to delete exists
    try:
        category = query_executor("SELECT category_name FROM Categories WHERE id = ?", (category_id,), True)[0][
            0]

    except IndexError:
        # if the category the user is trying to delete doesn't exist in the dictionary
        # redirects the user to the homepage with the error message "Category not in dictionary"
        return redirect(f"/?error=Category+not+in+dictionary")

    # renders the confirmation category page for the user looking at it
    return render_template("confirmation_category.html", logged_in=is_logged_in(),
                           category_name_with_id=[category_id, category])


# function executes when the user needs to confirm removing a word
@app.route("/confirmation/word-<word_id>")
def render_confirmation_word(word_id):
    # if the user is not a teacher
    if not is_teacher():
        # redirects user to the homepage with the error message
        # "You do not have permission to remove words"
        return redirect("/?error=You+do+not+have+permission+to+remove+words")

    # checks if the word the user is trying to remove is in the dictionary using query executor
    try:
        word_details = query_executor("SELECT maori, english FROM Dictionary WHERE id = ?", (word_id,), True)

    except IndexError:

        # if the word isn't in the dictionary
        # redirects user to the homepage with the error message "Word not in dictionary"
        return redirect(f"/?error=Word+not+in+dictionary")

    # renders the remove word confirmation page for the user looking at it
    return render_template("confirmation_word.html", logged_in=is_logged_in(),
                           word_in_maori=word_details[0][0], word_in_english=word_details[0][1], word_id=word_id)


# function executes when user attempts to delete a category
@app.route("/remove/category-<category_id>")
def remove_category(category_id):
    # if user isn't a teacher
    if not is_teacher():
        # redirects them to the homepage with the error message
        # "You do not have permission to remove categories"
        return redirect(f"/?error=You+do+not+have+permission+to+remove+categories")

    # uses query executor to check if category exists in dictionary
    try:
        category = query_executor("SELECT category_name FROM Categories WHERE id = ?",
                                  (category_id,), True)[0][0]

    except IndexError:
        return redirect(f"/?error=Category+not+in+dictionary")

    # attempts to remove words from the category the user is trying to delete
    try:

        # creates a list for words that need to be removed using query executor
        words_that_need_to_be_remove = query_executor("SELECT id FROM Dictionary WHERE category = ?", (category,),
                                                      True)

        # removes all words from the category using query executor
        for word in words_that_need_to_be_remove:
            query_executor("DELETE FROM Saved_words WHERE word_id = ?", (word[0],), False)

    except IndexError:
        # if there are no words in the category don't attempt to remove any
        pass

    # uses the query executor to remove all instance of the category from the database
    query_executor("DELETE FROM Dictionary WHERE category = ?", (category,), False)
    query_executor("DELETE FROM Categories WHERE category_name = ?", (category,), False)

    # redirects user to the homepage
    return redirect("/")


# function executes when user is attempting to remove word from dictionary
@app.route("/remove/word-<word_id>")
def remove_word(word_id):
    # if the user is not a teacher
    if not is_teacher():
        # redirects user to homepage with the error message
        # "You do not have permission to remove words"
        return redirect(f"/?error=You+do+not+have+permission+to+remove+words")

    # checks if the word the user is trying to remove isd in the dictionary
    # this is done by trying to get the word's id using the query executor
    try:
        word_maori = query_executor("SELECT maori FROM Dictionary WHERE id=?",
                                    (word_id,), True)[0][0]

    except IndexError:

        # if the word isn't in the dictionary

        # redirects user to the homepage with the error message "Word not in dictionary"
        return redirect(f"/?error=Word+not+in+dictionary")

    # uses query executor to remove all instances of the word the user is trying to remove
    # from the database
    query_executor("DELETE FROM Saved_words WHERE word_id = ?", (word_id,), False)
    query_executor("DELETE FROM Dictionary WHERE id = ?", (word_id,), False)

    # redirects the user to the homepage
    return redirect("/")


# function executes when user goes to a page that has not got a function made for it
@app.errorhandler(404)
def unknown_page(error):
    # redirects user to homepage with error message
    # "Page not found"
    return redirect("/?error=Page+not+found")


# runs the application
if __name__ == "__main__":
    app.run()
