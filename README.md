# Project_Squeegee
An open data search engine consisting of a web crawler, Elasticsearch domain hosted by AWS, and front end used for search queries.

Sourcing Operations employees within TomTom are tasked in finding geospatial data to be used in TomTom's digital maps. One of 
the common sources of this data are open data websites like www.data.gov. However, each open data website is unique and can have
a different layout. This means that the sourcing operations employee needs to be familiar with dozens of websites in order to 
search the sites in an efficient manner. However, that is usually not the case, and an employee can spend many valuable hours 
looking for data, sometimes without success.

The solution to this issue was to develop a web crawler that scrapes all the commonly used open data websites, collect information
from within the HTML content, and upload that information to an Elasticsearch domain hosted on AWS. Then, after creating a search
front-end, the sourcing operations employee can now go to one webpage and search for the data they desire, without having to be
familiar with dozens of different websites.

The web crawler was developed based on https://scrapy.org/, written in Python, and run on an AWS EC2 instance.

Due to an NDA with TomTom, I can't share any of the source code, but I have provided screenshots of the front end.

![Alt text](/screenshots/search.png)     ![Alt text](/screenshots/results.png)
![Alt text](/screenshots/results2.png)
