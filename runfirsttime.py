import sqlite3
conn = sqlite3.connect('products.db')
c = conn.cursor()
c.execute('''CREATE TABLE Products
                (SKU varchar PRIMARY KEY, price DECIMAL,rating DECIMAL, available BIT, discount BIT,oldprice DECIMAL,buybox VARCHAR,
                title VARCHAR, page INT, itemno INT, reviewsno INT, questionsno INT)''')
c.execute('''CREATE TABLE reviews
                (SKU VARCHAR PRIMARY KEY, reviews TEXT)''')
c.execute('''CREATE TABLE questions
                (SKU VARCHAR PRIMARY KEY, questions TEXT)''')
c.close()

