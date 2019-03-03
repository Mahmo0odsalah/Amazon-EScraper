AmazonEscraper is a custom made webscraper for products on Amazon. With its smart and creative methods to overcome 
Amazon's strict anti-scraping policies and its simple web interface, it's a real piece of art.
first, the user enters the name of a .csv file that is located in the root folder. Which contains: SKU,ASIN and keywords for
each product. The scraper then takes the file. Calls the function scrape() that iterates on the csv file, and gets the 
entries of each products. Then it calls the function search(), which generates the url of the search page. And starts
searching for the product with the keyword given untill it finds it, or reaches the end of the search results, or 
exceeds 10 results pages. If it finds the product it stores the page number and the product order in this page. And
then calls the function start(). Which takes the url of the product itself and gets all the information about it. 
Including price, rating, avialability, and many others.

One of the most complex helper methods is getreviews(). Which is called in start and is divided into 2 parts: 
getreviewsno() the number of reviews of the product. And scrapereviews() which is a recursive function that 
scrapes the reviews pages and calls itself on the next review page untill it reaches the end of the ratings pages.

After start() returns the results of scraping the product, the function search() uses these results. It first looks
for a product with the same SKU in the database. If it's not found it simply enters a new entry. If it finds a
product with the same SKU, it compares between the results it gets and the results in the database and looks for
any difference between them. If any is found, it updates the database and stores the change in the changelog file.
If none is found it simply ignores the results and doesn't write anything in the changelog.
