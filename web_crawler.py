import scrapy
import scrapy_splash
from scrapy.selector import Selector
from w3lib.html import remove_tags, remove_tags_with_content
import re
from dateutil.parser import parse
from string import punctuation
import datetime
import os
import math
from scrapy.linkextractors import LinkExtractor
import urllib
from urllib.parse import urlparse
import json
import time
import sys

from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from squeegee.spiders.patterns import Description, Update, License, Title

class SqueegeeSpider(scrapy.Spider):
	name = 'squeegee'

	http_user = 'myersi'
	http_pass = 'splashdown'

	start_urls = []
	allowed_domains = []
	url_info = []
	start_urls_set = set()
	
	handle_httpstatus_list = [400, 403, 404, 408, 500, 502, 503, 504]
	bad_urls = {}
	
	description = Description()
	update = Update()
	licence = License()
	title = Title()

	page_queries = ['p', 'page', 'paged']
	filter_queries = ['q', 'add-to-cart', 'collection']
	dataset_queries = ['dataset', 'id', 'utitle']

	maxdepth = 0
	max_retries = 0
	retry = False
	uploading = False
	saving = False
	stats = False

	scraped_pages = 0
	start_time = 0
	timer = 0
	timer_length = 60
	uploads = 0
	failed_uploads = 0
	crawled_per_minute = {}

	IGNORED_EXTENSIONS = [
		# images
		'mng', 'pct', 'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pst', 'psp', 'tif',
		'tiff', 'ai', 'drw', 'dxf', 'eps', 'ps', 'svg',
		# audio
		'mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au', 'aiff',
		# video
		'3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt', 'rm', 'swf', 'wmv',
		'm4a', 'm4v', 'flv',
		# office suites
		'xls', 'xlsx', 'ppt', 'pptx', 'pps', 'doc', 'docx', 'odt', 'ods', 'odg',
		'odp', 'csv',
		# other
		'css', 'pdf', 'exe', 'bin', 'rss', 'zip', 'rar', 'kmz', 'rdf', 'json', 'xml',
		'kml',
	]

	extractor = LinkExtractor(allow=(),deny_extensions=IGNORED_EXTENSIONS)

	lua_script = """
	function main(splash)
		splash.private_mode_enabled = false
		splash.images_enabled = false
		splash.resource_timeout = 10.0
		assert(splash:go(splash.args.url))

		splash:wait(0.5)

		page = splash:html()
		prev_size = -1
		match_count = 0

		while match_count < 2 do
			prev_size = string.len(page)
			splash:wait(1.0)
			page = splash:html()

			if prev_size == string.len(page) then
				match_count = match_count + 1
			else
				match_count = 0
			end
		end

		return {html=splash:html()}
	end
	"""

	def __init__(self, JSON=None, DEPTH=math.inf, RETRY=False, RETRIES=3, UPLOAD=False, SAVE=False, STATS=False):
		dispatcher.connect(self.spider_closed, signals.spider_closed)
		
		if JSON != None:
			jason = json.load(open(JSON))
			for country in jason:
				for territory in jason[country]:
					for url in jason[country][territory]:
						if url[1] == 'source' or url[1] == 'dataset':
							self.start_urls.append(url[0])
							self.allowed_domains.append('{url.netloc}'.format(url=urlparse(url[0])))
							self.url_info.append({'country' : country, 'territory' : territory, 'type' : url[1]})
						else:
							sys.exit('ERROR: Invalid url type: "%s"  Valid types: "source", "dataset"' % (url[1]))
		else:
			sys.exit('ERROR: Must include a valid json input file with "-a JSON="')

		self.maxdepth = float(DEPTH)
		self.max_retries = int(RETRIES)
		self.retry = RETRY
		self.uploading = UPLOAD
		self.saving = SAVE
		self.stats = STATS

		if(not os.path.exists('../squeegee-output')):
			os.mkdir('../squeegee-output')

		open('../squeegee-output/bad_urls.out', 'a')
		if STATS:
			self.start_timer()
		print('Beginning scrape at: ' + str(datetime.datetime.now()), file=open('../squeegee-output/stats.out', 'a'))

	def spider_closed(self, spider):
		"""Timestamp the end of the scrape."""
		print('Ending scrape at: %s  Total uploads: %d' % (str(datetime.datetime.now()), self.uploads), file=open('../squeegee-output/stats.out', 'a'))
		if len(self.crawler.engine.slot.scheduler) == 0:
			self.store_bad_urls(spider)

	def store_bad_urls(self, spider):
		"""Convert the bad urls into a JSON input file."""
		spider.logger.info('Spider finished. Storing bad urls')

		lines = open('../squeegee-output/bad_urls.out').readlines()
		for line in lines:
			spl = line.strip().split()
			self.save_bad_url(spl[-1], spl[-2], spl[-3], spl[-4])

		json.dump(self.bad_urls, open('../squeegee-output/bad_urls.json', 'w'), indent=1)

	def start_requests(self):
		"""Create scrapy requests for start urls."""
		for x in range(len(self.start_urls)):
			url = self.start_urls[x]

			yield self.new_request(
				url=url,
				depth=0,
				retry=self.retry,
				pagelink=self.url_info[x]['type'] == 'source',
				country=self.url_info[x]['country'],
				territory=self.url_info[x]['territory'],
				retries=0
			)

	def start_timer(self):
		"""Begins timer used for outputting stats."""
		self.start_time = time.time()
		self.timer = self.start_time	

	def parse(self, response):
		"""Parse the response.
		* Scrapes last updated, description, title and licence information from dataset links
		* Skips scraping and follows all links on page links
		* Yields dictionary containing page and response info to pipelines.py
		"""
		if self.stats:
			self.output_stats(response)

		depth = response.meta['depth']
		page = {'url' : response.url, 'updated' : '', 'license' : '', 'title' : '', 'summary' : ''}

		# Handle bad urls
		if response.status in self.handle_httpstatus_list:
			bad_url = self.process_bad_url(response)
			yield bad_url if bad_url != None else {'page' : page, 'response' : response}
			return

		if not response.meta['pagelink']:
			# Remove all javascript and style content from html body
			response_plain = scrapy.Selector(text=remove_tags_with_content(response.text, ('script', 'style',)))

			page['updated'] = self.update.search_pattern(response_plain)
			page['license'] = self.licence.search_pattern(response_plain)
			page['summary'] = self.description.search_pattern(response_plain)
			page['title'] = self.title.search_pattern(response_plain)
		elif depth < self.maxdepth:
			# Get all links on the page
			links = self.extractor.extract_links(response)

			for link in links:
				yield self.new_request(
					url=link.url,
					depth=depth+1,
					retry=False,
					pagelink=self.is_pagelink(link.url),
					country=response.meta['country'],
					territory=response.meta['territory'],
					retries=0
				)

		# Print crawled information to file or upload
		yield {'page' : page, 'response' : response}

	def output_stats(self, response):
		"""Output information about the scrape.
		* Average number of pages fully processed
		* Number of uploads and failed uploads
		* Responses returned in the last minute
		"""
		if response.status not in self.crawled_per_minute:
			self.crawled_per_minute[response.status] = 1
		else:
			self.crawled_per_minute[response.status] += 1

		if time.time() - self.timer >= self.timer_length:
			pages_per_min = int(self.scraped_pages / ((time.time() - self.start_time) / 60.0))
			time_stamp = str(datetime.datetime.now())
			print('%s    %d pages per minute   uploaded: %d   failed uploads: %d' % (time_stamp, pages_per_min, self.uploads, self.failed_uploads), file=open('../squeegee-output/stats.out', 'a'))
			self.timer = time.time()

			message = 'Crawled in last %d seconds:  ' % (self.timer_length)
			for response_status in self.crawled_per_minute:
				message += '%d: %d   ' % (response_status, self.crawled_per_minute[response_status])
			print(message, file=open('../squeegee-output/stats.out', 'a'))
			self.crawled_per_minute = {} 

	def is_pagelink(self, url):
		"""Determine if a url contains a page query e.g. ?page=3"""
		parsed = urlparse(url)
		queries = urllib.parse.parse_qs(parsed.query)

		for q in queries:
			if q in self.page_queries:
				return True

		return self.is_directory_page_link(url)

	def is_directory_page_link(self, url):
		"""Determine if the url uses directories as page links e.g. /page/3"""
		return re.search(r'/page/\d+(/|$)', url) != None

	def process_bad_url(self, response):
		"""Retry bad urls a number of times equal to max_retries."""
		if response.meta['retries'] < self.max_retries:
			return self.new_request(
				url=response.url,
				depth=response.meta['depth'],
				retry=True,
				pagelink=response.meta['pagelink'],
				country=response.meta['country'],
				territory=response.meta['territory'],
				retries=response.meta['retries'] + 1
			)
		else:
			return None

	def save_bad_url(self, country, territory, source, url):
		"""Store bad urls that exceed the retry limit in a dictionary to be dumped to a json later."""
		if ('\\' in url):
			return
			
		if country not in self.bad_urls:
			self.bad_urls[country] = {}
		if territory not in self.bad_urls[country]:
			self.bad_urls[country][territory] = []

		self.bad_urls[country][territory].append([url, source])

	def new_request(self, url, depth, retry, pagelink, country, territory, retries, links=None):
		"""Return a new request object."""
		request = scrapy_splash.SplashRequest(url=self.get_next_page(url, pagelink), callback=self.parse, endpoint='execute', args={'lua_source':self.lua_script,'timeout':90})

		request.meta['depth'] = depth
		request.dont_filter = retry
		request.meta['pagelink'] = pagelink
		request.meta['country'] = country
		request.meta['territory'] = territory
		request.meta['retries'] = retries

		return request

	def get_next_page(self, url, pagelink):
		"""Generate the url for the new request.
		* Filters out problematic queries in page links or urls with dataset queries
		* Else return the url without queries
		"""
		parsed = urlparse(url)
		queries = urllib.parse.parse_qs(parsed.query)
		next_page = parsed.scheme + '://' + parsed.netloc + parsed.path

		if pagelink or self.has_dataset_queries(queries):
			i = 0
			for query in queries:
				if query not in self.filter_queries:
					next_page += '&' if i > 0 else '?'
					next_page += query + '=' + queries[query][0]
					i += 1

		return next_page

	def has_dataset_queries(self, queries):
		"""Check for dataset queries e.g. ?dataset="""
		for query in queries:
			if query in self.dataset_queries:
				return True
		return False
