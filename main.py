from flask_sqlalchemy import SQLAlchemy
import uuid
from flask_mysqldb import MySQL
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import MySQLdb.cursors  
import re
import json
from json2html import json2html
import pandas as pd
#######################################################################################################################################################################
app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345678'
app.config['MYSQL_DB'] = 'bookstore'

mysql=MySQL(app)
app.secret_key = 'lulsecintern'

#######################################################################################################################################################################

@app.route('/tempcheck',methods=['GET','POST'])
def tempchecking():
    try:
        sort_option = request.form.get('sort_option')
        if sort_option == 'asc_bname':
            query = "SELECT * FROM booksinstore ORDER BY BookName ASC"
        elif sort_option=='desc_bname':
            query = "SELECT * FROM booksinstore ORDER BY BookName DESC"
        elif sort_option=='asc_auth':
            query = "SELECT * FROM booksinstore ORDER BY Author ASC"
        elif sort_option=='desc_auth':
            query= "SELECT * FROM booksinstore ORDER BY Author DESC"
        # Execute your query here
        cursor = mysql.connection.cursor()
        #getting all the books
        cursor.execute(query)
        data=cursor.fetchall() 
        
        columns = [desc[0] for desc in cursor.description]
        # Initialize an empty list to store the dictionary entries
        data_as_dict = []
        # Fetch all rows and convert them into dictionaries
        for row in data:
            row_dict = {}
            for i, value in enumerate(row):
                row_dict[columns[i]] = value
            data_as_dict.append(row_dict)
        #return jsonify({'Book status': data})

        return render_template('bookcollectionsort.html', collection=data_as_dict)
    except Exception as e:
       return jsonify({'error': str(e)})

#######################################################################################################################################################################
@app.route('/books', methods=['GET'])
def get_books():
    try:
        #establishing connection with mysql server
        user_id = session['id']
        cursor = mysql.connection.cursor()
        #getting all the books
        cursor.execute("SELECT * FROM books WHERE id = %s", (user_id,))
        books_data = cursor.fetchall()
        # Get the column names from the table
        columns = [desc[0] for desc in cursor.description]
        # Initialize an empty list to store the dictionary entries
        data_as_dict = []
        # Fetch all rows and convert them into dictionaries
        for row in books_data:
            row_dict = {}
            for i, value in enumerate(row):
                row_dict[columns[i]] = value
            data_as_dict.append(row_dict)
        return render_template('bookcollection.html ',collection=data_as_dict )
    except Exception as e:
       return jsonify({'error': str(e)})

@app.route('/allbooksjson', methods=['GET'])
def jsonofbooks():
    try:
       #establishing connection with mysql server
       cursor = mysql.connection.cursor()
       #getting all the books
       cursor.execute("SELECT * FROM books")  
       books_data = cursor.fetchall()
       cursor.close()
       return jsonify({'Books': books_data})
    except Exception as e:
       return jsonify({'error': str(e)})

@app.route('/bookstatus', methods=['GET'])
def get_statusofbooks():
    try:
       #establishing connection with mysql server
       cursor = mysql.connection.cursor()
       #getting all the books
       cursor.execute("SELECT book_name,status FROM books")  
       books_data = cursor.fetchall()
       cursor.close()
       return jsonify({'Book status': books_data})
    except Exception as e:
       return jsonify({'error': str(e)})
    
@app.route("/remove", methods=["GET", "POST"])
def remove():
    msg=''
    if request.method == 'POST' and 'name_book' in request.form:
        user_id = session['id']
        name = request.form["name_book"]
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM books WHERE book_name= % s and id= % s",(name,user_id))
        mysql.connection.commit()
        if cursor.rowcount > 0:
            flash(f"Book '{name}' removed successfully", 'success')
        else:
            flash(f"Book '{name}' not found", 'error')
        cursor.close()
        msg = 'Removed Successfully'
    return render_template("remove.html",msg=msg)
    
@app.route("/update", methods=["GET", "POST"])
def update():
    msg=''
    if request.method == 'POST' and 'name_book' in request.form and 'genre_book' in request.form and 'book_status' in request.form and 'links' in request.form:
        user_id = session['id']
        name = request.form["name_book"]
        genre = request.form["genre_book"]
        status =request.form["book_status"]
        links=request.form["links"]
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO books (id,book_name,Genre,Status,links) VALUES (% s,% s, % s ,% s,% s)",(user_id,name, genre,status,links))
        mysql.connection.commit()
        msg = 'Updated successfully!'
    return render_template("update.html",msg=msg)

@app.route('/bookname', methods=['GET'])
def get_bookname():
    try:
       #establishing connection with mysql server
       cursor = mysql.connection.cursor()
       #getting all the books
       cursor.execute("SELECT book_name FROM books")  
       books_data = cursor.fetchall()
       cursor.close()
       return jsonify({'Book Name': books_data})
    except Exception as e:
       return jsonify({'error': str(e)})

###############################################################################################################################################

@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM accounts WHERE username = % s AND password=% s",(username,password))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = 'Logged in successfully !'
            return redirect(url_for('index'))
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)
 
@app.route('/index', methods =['GET', 'POST'])
def index():
    uname=session['username']
    return render_template('index.html',message=uname)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not username or not password:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO accounts(username,password) VALUES ( % s, % s)', (username, password))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)


if __name__ == '__main__':
    app.run(debug=True, port=5050)
