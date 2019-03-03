import csv
import random
import re
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import sqlite3
import datetime
import os


conn = sqlite3.connect('products.db')       #Connect toDataBase
now=datetime.datetime.now()
currenttime = str(now.year)+'_'+str(now.month)+'_'+str(now.day)+'..'+str(now.hour)+'o\'clock'

with open('changes_at'+currenttime+'.txt', 'w') as file:    #initialize ChangeLog
    file.write(str(['SKU','price','rating','available','discount','oldprice','buybox','title','page','item','reviewsno','questionsno','Q1','Q2','Q3','Q4'])+'\n')

session = HTMLSession()

with open('proxies.txt', 'w') as file: # Get a list of daily Proxies
    r2 = str.replace((session.get('https://raw.githubusercontent.com/a2u/free-proxy-list/master/free-proxy-list.txt')
                      .html.text), ' ', '\n')
    r = session.get('http://proxy-daily.com/')
    dailyproxy = r.html.search('Free Http/Https Proxy List:</div><br><center><div style="border-radius:10px;'
                               'white-space:pre-line;border:solid 3px #ff4c3b;background:#fff;color:#666;padding:'
                               '4px;width:250px;height:400px;overflow:auto">{}<')
    if (dailyproxy is not None):
        dailyproxy = str(dailyproxy[0])
    else:
        dailyproxy = ''
    file.write(str(r2 + dailyproxy))

proxies = []
lines = open('proxies.txt', 'r') #store the proxies in a text file
for line in lines:
    proxies.append(line.strip('\n'))


def proximate():            #Get A random proxy address
    proxy = proxies[int(random.randint(0, len(proxies) - 1))]
    print({'http': proxy})
    return proxy


def scrape(file):#The Main Method, takes a csv file and calls all other helpers
                 #Returns a list of Results, where each element represents results of a product
    if(os.path.isfile('newReviews.txt')):
        os.remove('newReviews.txt')

    with open('newReviews.txt','w') as nr:      #Create a new file for newReviews
        nr.write('new Reviews for today :\n')

    with open(file) as csv_file:#Read the CSV file for the products info
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        results =[]
        for row in csv_reader:  #In everyrow, scrape the product represented
            proxy = proximate()
            print(f'SKU:{row[0]} ASIN:  {row[1]} keyword : {row[2]}.')
            sku = row[0]
            asin = row[1]
            keyword = row[2]
            try:
                results.append(search(asin, keyword, proxy,sku)) #Scrape the product, and append the returned results to the results list
            except:
                print('Internal Error')
            line_count += 1
        print(f'Processed {line_count} lines.')
        print(results)
        return results


def start(url, proxy, page, itemno,asin): #Takes info of a product, including url of product page and scrapes Price,rating and others
    if (not (url.startswith("https://www.amazon.com/"))): #Checks if it's a valid URL
        print("Not an Amazon URL")
    else:
        timeout = 1
        session = HTMLSession()
        header = {'User-agent': 'Mozilla/5.0'}
        r = session.get(url, headers=header, proxies={'http': proxy}) #Open URL of the product
        price = getprice(r)                 #Gets the price of the product
        while price is None and timeout < 5:#Retries 5 times in case the proxy isn't working
            proxy = proximate()             #Get a new proxy address
            r = session.get(url, headers=header, proxies={'http': proxy})
            price = getprice(r)
            timeout += 1
        price.replace(',','')   #Remove commas
        price =re.sub(r'[^\d^\.]+', '', price)#Get price without the dollar sign
        print(price)
        available = checkavailable(r)   #check if it's in stock
        rating = getrating(r)           #Get the ratinf
        discountlist = getdiscount(r)   #Get if there is a discount
        discount = discountlist[0]
        oldprice = discountlist[1]
        oldprice = oldprice.replace(',','')
        oldprice =re.sub(r'[^-^\d^\.]+', '', oldprice)
        buybox = getbuybox(r)           #Get Buy Box
        title = gettitle(r).replace(',',' ')  #
        print('attentionnnn' +title )
        reviewslist = getreviews(r,asin)
        reviewsno = reviewslist[0]
        reviewsno=reviewsno.replace(',','')
        reviews = reviewslist[1]
        questions = getquestions(r,asin)
        print(questions)
        questionsno = questions['noofquestions']
        questionsno = str(questionsno).replace(',','')
        with open(str(asin)+'reviews.txt', 'w') as file:    #Write The reviews in a unique file for every product
            for review in reviews:
                try:
                    file.write(str(review)+'\n')
                except:
                    print('writing error')



        return {            #Return the info of the product to be stored/displayed
            'price':float(price),
            'rating':float(rating),
            'available':available,
            'discount':discount,
            'oldprice':float(oldprice),
            'buybox':buybox,
            'title':title,
            'page': page-1,
            'itemno':itemno,
            'reviewsno':int(reviewsno),
            'questionsno': int(questionsno),
            'change':questions['change']
        }


def checkasin(asin, url):       #Checks if URL belongs to a certain product asin
    extracted = re.search('/dp/(.+)/', url)#extracts asin from url
    if(extracted is not None):
        extracted = extracted[1]
    return extracted == asin


def search(asin, keyword, proxy, sku):#Searches for the product in Amazon to know where it's located
    maxpages = None
    timeout=1
    while maxpages is None and timeout <=10 :   #Try to load the search results page 10 times
        page = 1
        found = False
        searchurl = 'https://www.amazon.com/s/ref=nb_sb_noss?url=search-alias%3Daps&field-keywords=' + keyword \
                    + '&rh=i%3Aaps%2Ck%3A12313'
        session = HTMLSession()
        header = {'User-agent': 'Mozilla/5.0'}
        r = session.get(searchurl, headers=header, proxies={'http': proxy})
        print(r.html.search('<span class="pagnDisabled">{}<'))
        maxpages = r.html.search('<span class="pagnDisabled">{}<')  #Get number of page results ( how many pages are the results)
        proxy = proximate()
        timeout+=1
    if maxpages is None:
        maxpages = 0
    maxpages = int(maxpages[0])
    while (not found and page <= 10 and page <= maxpages): # Search for product in the page, as long as it is one
                                                            # of the first 10 pages and is not the last results page
        if (page > 1):
            searchurl = 'https://www.amazon.com/s/ref=nb_sb_noss?url=search-alias%3Daps&field-keywords=' + keyword \
                        + '&rh=i%3Aaps%2Ck%3A12313&page=' + str(page)   #url of search page
        proxy = proximate()
        print(searchurl)
        itemno = 0
        header = {'User-agent': 'Mozilla/5.0'}
        r = session.get(searchurl, headers=header, proxies={'http': proxy})
        product = ''
        soup = BeautifulSoup(str(r.content))
        links = soup.find_all('a', attrs={'href': re.compile("^https://www.amazon.com/.+/.*dp/")})
        linksnew = []
        print(r.html)
        for href in links:  #Search for the product url in the page
            href = (href.attrs['href']).split('ref')[0]
            if (href not in linksnew):
                linksnew.append(href)
        for link in linksnew:
            itemno += 1
            if checkasin(asin, link):
                print(link)
                found = True
                print(linksnew)
                product = link
                break
        page += 1
    if not found:
        if page > 10:   #If the product is not in the first 10 results pages, return that it's after 10 pages
            results = {
                'price': 0,
                'rating': 0,
                'available': 0,
                'discount': 0,
                'oldprice': 0,
                'buybox': 'after more than 10 pages',
                'title': 'after more than 10 pages',
                'page': 0,
                'itemno': 0,
                'reviewsno': 0,
                'questionsno': 0,
                'change':['after more than 10 pages','after more than 10 pages','after more than 10 pages','after more than 10 pages']
            }
        else:# if the product is not found and there is no more results pages
            results = {
                'price': 0,
                'rating': 0,
                'available': 0,
                'discount': 0,
                'oldprice': 0,
                'buybox': 'Not Available, Try different keyword',
                'title': 'Not Available, Try different keyword',
                'page': 0,
                'itemno': 0,
                'reviewsno': 0,
                'questionsno': 0,
                'change':['Not Available, Try different keyword','Not Available, Try different keyword','Not Available, Try different keyword','Not Available, Try different keyword']
            }
    else:
        results = start(product, proxy, page, itemno,asin) #If the product is found, scrape its url for its price,rating,...

    #Update The DataBase
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    oldresults = c.execute('''SELECT * FROM Products WHERE SKU = ?''', [sku, ])
    row = c.fetchall()
    if(len(row) == 0):#If there is no product with the same SKU, Insert it in the database
        c.execute('''INSERT INTO Products VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',[sku,results['price'],results['rating'],
                  results['available'],results['discount'],results['oldprice'],results['buybox'],results['title'],
                  results['page'],results['itemno'],results['reviewsno'],results['questionsno']])
        conn.commit()
    else:#If there is a product in the database with same SKU, check for change
        change = False
        #changes = [False, False, False, False, False,False, False, False, False, False, False]
        newvalues=[sku,'No Change','No Change','No Change','No Change','No Change','No Change','No Change','No Change','No Change','No Change','No Change']
        print(results)
        newvalues += results['change']

        i=0 #Check every attribute for any changes
        for attribute, value in results.items():
            if(i+1 == len(row[0])):
                break
            if (row[0][i+1] != value):
                print(row[0][i+1])
                print(type(row[0][i+1]))
                print('different from')
                print(value)
                print(type(value))
                print('\n')
                change = True
                # changes[i-1]=True
                newvalues[i+1] = str(attribute)+' before' + str(row[0][i+1])+' after: '+str(value)
            i += 1
        if change:#If any changes are found, update the database
            print(sku,' change')
            #And write the changes in the changeLog

            with open('changes_at'+currenttime+'.txt', 'a') as file:
                file.write(str(newvalues)+'\n')
            c.execute('''UPDATE Products 
             SET price=?,rating=?,available=?,discount=?,oldprice=?,buybox=?,title=?,
            page=?,itemno=?,reviewsno=?,questionsno=?
            WHERE SKU=?''',
                      [results['price'], results['rating'],
                       results['available'], results['discount'], results['oldprice'], results['buybox'],
                       results['title'],
                       results['page'], results['itemno'], results['reviewsno'], results['questionsno'],sku])
            conn.commit()


        else:#If there is no change, don't update or write in the change log
            print(sku + ' no change')
    c.close()
    return results

def getprice(r):    #Get the price of the product from its url
    price = r.html.search('<span id="priceblock_ourprice" class="a-size-medium a-color-price">{}<')
    if price is not None:
        print(price[0])
        return price[0]
    else:
        price = r.html.search('<span id="price_inside_buybox" class="a-size-medium a-color-price">{}<')


def checkavailable(r): #Get the availability of the product from its url
    available = False
    if not 'Out Of Stock.' in r.html.text:
        available = True
    print(available)
    return available


def getrating(r):   #Get the rating of the product from its url
    rating = r.html.search('class="reviewCountTextLinkedHistogram noUnderline" title="{} out of 5')
    if rating is not None:
        print(rating[0])
        return (rating[0])


def getdiscount(r): #Get the discount of the product from its url, and the old price if there is a discount
    oldprice = r.html.search('<span class="a-text-strike"> {}</span>')
    if oldprice is not None:
        print('Old Price ', oldprice[0])
        return [True, oldprice[0]]
    else:
        print('No Discount')
        return [False, '-1']


def getbuybox(r):   #Get the buybox of the product from its url
    buybox = r.html.search('<span class="a-size-base a-color-secondary a-text-normal">Sold by {} and ships')
    if (buybox is not None):
        print(buybox[0])
        return (buybox[0])


def gettitle(r):    #Get the title of the product from its url
    title = r.html.search('<span id="productTitle" class="a-size-large">{}</span>')
    if (title is not None):
        print(title[0].strip())
        return (title[0].strip())


def getquestions(r,asin):#Get the top 4 questions of the product from its url
    noofquestions = re.search(r'(\d*\+?)\sanswered\squestion',r.html.text)
    if(noofquestions is not None):
        noofquestions = noofquestions[1] #Get the no of questions
    else:
        noofquestions= 0
    questionspage='https://www.amazon.com/ask/questions/asin/'+asin\
                  +'/1/ref=ask_dp_iaw_ql_hza?isAnswered=true#question-Tx1A2LT6IOB4OIY'
    timeout = 0
    r2 = session.get(questionspage, headers={'User-agent': 'Mozilla/5.0'},
                     proxies={'http': proximate()})

    while (r2.status_code != 200 and timeout < 5): #Try the questions page 5 times
        timeout += 1
        r2 = session.get(questionspage, headers={'User-agent': 'Mozilla/5.0'}, proxies={'http': proximate()})
    questions = r2.html.search_all(
        '<span class="a-declarative" data-action="ask-no-op" data-ask-no-op="{&quot;metricName&quot;:&quot;top-questio'
        'n-text-click&quot;}">{}</span>')
    oldquestions=['No change','No change','No change','No change']
                                                                        #Check changes of the top 4 questions
    if not (os.path.isfile(str(asin) + 'questions.txt')):   #If it's the first time to scrape this product don't check changes

        with open(str(asin) + 'questions.txt', 'w') as file:
            i = 0
            for question in questions:
                if i <4 :
                    file.write( str(question[0]) + '\n')
                    oldquestions[i]=str(question[0]).strip('\n')
                else:
                    break
                i+=1
    else:                                                   #Check changes in top 4 questions
        with open(str(asin) + 'questions.txt', 'w') as file:
            i = 0
            for question in questions:
                if i < 4:
                    if question[0] in open(str(asin) + 'questions.txt').read():#If it's not a new question
                        file.write( str(question[0]) + '\n')
                    else:   #If it's a new Questions
                        file.write(str(question[0]) + '\n')
                        oldquestions[i] = str(question[0]).strip('\n')

                else:
                    break
                i += 1

    return {'noofquestions':noofquestions,
    'change':oldquestions}

def getreviews(r,asin): #Get the reviews of the product from its url
    noofreviews = getreviewsno(r)
    reviewspage = r.html.search('see-all-reviews-link-foot" class="a-link-emphasis a-text-bold" href="{}">')[0]
    reviewspage = 'https://www.amazon.com' + reviewspage +'&pageNumber=1'
    if(reviewspage is not None):
        timeout=0
        r2 = session.get(reviewspage, headers={'User-agent': 'Mozilla/5.0'},
                         proxies={'http': proximate()})

        while(r2.status_code !=200 and timeout < 5):
            timeout+=1
            r2 = session.get(reviewspage, headers={'User-agent': 'Mozilla/5.0'}, proxies={'http': proximate()})
        new = True
        if(os.path.isfile(str(asin)+'reviews')): #Check if it's the first time to scrape this product
            new = False
        return (noofreviews,scrapereviews(r2,reviewspage,[],1,new)) #Get no of reviews and the reviews itself
    else:
        print('No reviews')
        return (noofreviews,[]) #If no Reviews found


def getreviewsno(r):    #Get no of reviews from product url
    noofreviews = re.search(r'([\d,]+\+?)\scustomer\sreviews', r.html.text)
    if (noofreviews is not None):
        return noofreviews[1]
    else:
        return 0


def scrapereviews(r,url,reviews,page,new): #Get all the reviews in the first 20 reviews pages
    if(page > 20):
        return reviews
    nextpage =re.search('.*pageNumber=',url)[0] # Get the url of the next page
    nextpage += str(page+1)
    print(nextpage)
    pagereviews =[]
    if re.search('Sorry, no reviews match your current selections.',r.html.text) is None: #If the page has reviews
        r = session.get(url,headers={'User-agent': 'Mozilla/5.0'}, proxies={'http': proximate()})
        reviewlisthtml = r.html.search(                         #HTML Of the reviews List
            '<div id="cm_cr-review_list"{}<div class="a-spinner-wrapper reviews-load-progess aok-hidden a-spacing-top-'
            'large"><span class="a-spinner a-spinner-medium"></span></div>')
        #Get the Required Data for every review
        profiles = re.findall(r'<span class="a-profile-name">(.*?)</span>',
                              reviewlisthtml[0])
        stars = re.findall(r'<span class="a-icon-alt">(.*?)out\sof\s5\sstars', str(reviewlisthtml))
        content = re.findall(r'<span data-hook="review-body" class="a-size-base review-text">(.*?)</span>',str(reviewlisthtml))
        date = re.findall(r'a-size-base a-color-secondary review-date">(.*?)</span>',str(reviewlisthtml))
        i = 0

        while(i<len(stars)):#Iterate on all the reviews
            reviewdate=date[i]
            monthWord = re.search('([a-zA-z]+).*',reviewdate)
            monthWord = monthWord[1]        #Get the month of the review as it's in Amazon
            print(monthWord)

            #convert monthWord to the corresponding month number
            if(monthWord == 'January'):
                month = 1
            elif (monthWord == 'February'):
                month = 2
            elif (monthWord == 'March'):
                month = 3
            elif (monthWord == 'April'):
                month = 4
            elif (monthWord == 'May'):
                month = 5
            elif (monthWord == 'June'):
                month = 6
            elif (monthWord == 'July'):
                month = 7
            elif (monthWord == 'August'):
                month = 8
            elif (monthWord == 'Septemeber'):
                month = 9
            elif (monthWord == 'October'):
                month = 10
            elif (monthWord == 'November'):
                month = 11
            elif (monthWord == 'Decemeber'):
                month = 12
            else:
                month = datetime.datetime.now().month - 1

            # Get day and year of the review
            day = re.search('.*(\d+),.*',reviewdate)
            day = day[1]
            year = re.search('.*,\s(\d+)',reviewdate)
            year = year[1]
            print(year + str(month)+day)

            content[i] = re.sub(r'<.*>', ' ', content[i])

            # Build a review instance
            review = [profiles[i],float(stars[i]),reviewdate,(content[i].replace('"', '\\"')).replace(',',' ')]
            if not new : #If it's not the first time to scrape the product, check if any review is newer than last review time
                if int(year) > datetime.datetime.now().year or ( int(year )== datetime.datetime.now().year and month > datetime.datetime.now().month) \
                        or ( int(year) == datetime.datetime.now().year and month == datetime.datetime.now().month and int(day )> datetime.datetime.now().day-1):
                    pagereviews.append(review)
                    with open('newReviews.txt','a') as file:
                        file.write(str(review).replace('\'','"')+',\n')
            else:# if it's the first time to scrape, don't check for new reviews
                pagereviews.append(str(review).replace('\'', '"') + ',')

            i+=1

    else:
        return reviews

    #Go to next reviews page and call the same function recursively
    timeout = 0
    r2 = session.get(nextpage, headers={'User-agent': 'Mozilla/5.0'},
                     proxies={'http': proximate()})

    while (r2.status_code != 200 and timeout < 5):
        timeout += 1
        r2 = session.get(nextpage, headers={'User-agent': 'Mozilla/5.0'},
                         proxies={'http': proximate()})
    reviews+=pagereviews
    return scrapereviews(r2,nextpage,reviews,page+1,new)


