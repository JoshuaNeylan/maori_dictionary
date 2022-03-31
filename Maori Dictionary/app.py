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
    category_list = list(set(category_list))
    for i in range(len(category_list)):
        category_list[i] = category_list[i][0].title()
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
    print(category_words)

    return render_template("category.html", category=category, words=category_words)



if __name__ == "__main__":
    app.run()

