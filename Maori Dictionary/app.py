import sqlite3
from sqlite3 import Error
from flask import Flask, render_template, request, redirect, session

from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
DB_NAME = "maori_dictionary.db"

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





@app.route('/')
def render_home():
    return render_template("home.html", categorys=category_setup())

@app.route("/categorys/<category>")
def render_category(category):

    con = create_connection(DB_NAME)

    query = "SELECT maori, english, definition FROM Dictionary WHERE category = ?"

    cur = con.cursor()
    cur.execute(query, (category,))
    category_words = cur.fetchall()
    con.close()
    print(len(category_words))
    return render_template("category.html", category=category, words=category_words)

@app.route("/categorys/<category>/<word>")
def render_category_word_details(word, category):

    con = create_connection(DB_NAME)

    query = "SELECT maori, english, category, definition, year_level, image, image_type, timestamp, author FROM Dictionary WHERE maori = ?"

    cur = con.cursor()
    cur.execute(query, (word,))
    word_details = cur.fetchall()
    improved_word_details = []
    for i in range(len(word_details[0])):
        improved_word_details.append(word_details[0][i])
    con.close()
    print(improved_word_details)
    return render_template("word_details.html", word_details=improved_word_details, category=category)



if __name__ == "__main__":
    app.run()

