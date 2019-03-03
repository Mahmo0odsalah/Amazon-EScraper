import amazonscraper as scraper
from flask import Flask,request,flash
from flask import render_template, render_template_string
from flask_table import Table, Col
import json
import ast
import requests

#Flask app initialize

app = Flask(__name__)
app.config.update(
    SECRET_KEY=b'_5#y2L"F4Q8z\n\xec]/'
)

#Create table Class for the products
class ReviewTable(Table):
    profile = Col("Profile")
    rating = Col("Rating")
    content = Col("Content")

#Create Review Object
class Review(object):
    def __init__(self, profile, rating, content):
        self.profile = profile
        self.rating = rating
        self.content = content



#Create Table for the products
class ItemTable(Table):
    price = Col('Price')
    available = Col('available')
    rating = Col('rating')
    discount = Col(' discount')
    oldprice = Col('oldprice')
    buybox = Col('buybox')
    title = Col('title')
    page = Col('page')
    itemno = Col('itemno')
    questionsno = Col('noofquestions')
    reviewsno = Col('noofreviews')


#Create Item object
class Item(object):
    def __init__(self, price, available,rating,discount,oldprice,buybox,title,page,itemno,questionsno,reviewsno):
        self.price = price
        self.available = available
        self.rating = rating
        self.discount = discount
        self.oldprice = oldprice
        self.buybox = buybox
        self.title = title
        self.page = page
        self.itemno = itemno
        self.questionsno = questionsno
        self.reviewsno = reviewsno


#main page
@app.route('/', methods=['POST','GET'])
def index():
    #If post request, scrape the file with the name sent in the textbox
    if request.method == 'POST':
        path = request.form.get("fileToUpload")
        if not path.endswith('.csv'):
            path = path+'.csv'
        items = scraper.scrape(path)
        table = ItemTable(items)
        return render_template('index.html', path=table.__html__())
    #If get request, load the page
    else:
        return render_template('index.html', path='Please enter the name of the file')


#The reviews page
@app.route('/reviews', methods=['POST', 'GET'])
def reviews():
    #get reviews of the sku submitted in the textbox
    if request.method == 'POST':
        sku = request.form.get("sku")
        with open(sku + 'reviews.txt', 'r') as file:
            reviews = file.read()
            reviews = reviews.replace('\\"', "\'")
            reviews= reviews.strip('\n')
            reviews = json.loads(reviews.strip(',')+'}')
            print(reviews)
        labels = reviews
        return render_template_string('''


            <table>
                    <tr>
                        <td>  </td> 
                        <td> </td>
                        <td> </td>
                    </tr>


            {% for profile, rate in labels.items() %}

                    <tr>
                        <td>{{ profile }}</td> 
                        <td>{{ rate }}</td>
                        
                    </tr>

            {% endfor %}


            </table>
        ''', labels=labels)
    else:
        return render_template('reviews.html', sku='Please enter the SKU:')

app.run()