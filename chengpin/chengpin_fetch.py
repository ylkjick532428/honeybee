# -*- coding: utf-8 -*-

import HTMLParser
import urlparse
import urllib
import urllib2
import cookielib
import string
import re
import time
import sys


#from selenium import webdriver
#from selenium.webdriver.common.keys import Keys
from urllib2 import urlopen, Request

from utils import MySqlUtil, Adsl, filter_tags, url_decode, str_repalce, filter_r_and_n
from snoopy import Snoopy

#数据库配置
chengpin_db = {'NAME': 'chengpin',
'USER': 'weibo',
'PASSWORD': '3c38f920d8bf11c96c09023fe49c8917',
'HOST': 'localhost',
'PORT': "3306"}


def urldecode(query):
	d = {}
	a = query.split('&')
	for s in a:
		if s.find('='):
			k,v = map(urllib.unquote, s.split('='))
			try:
				d[k].append(v)
			except KeyError:
				d[k] = [v]

	return d


class Chengpin(object):
	def __init__(self):
		self.snoopy = Snoopy()
		self.mysql = MySqlUtil(chengpin_db)

	#设置抓起客户端的编号，为了方便多个进程同时运行		
	def set_client(self, client_count, client_id):
		try:
			self.client_count = int(client_count)
			self.client_id = int(client_id)
		except:
			self.client_count = 1
			self.client_id = 1
	
	def init_category_format(self):
		category = {}
		category["cate"] = ""
		category["sub"] = ""
		category["list"] = ""
		category["page"] = "1"
		category["text"] = ""
		category["status"] = "0"
		return category
		
		
	#==============================================================================
	# fetch_categorys : 抓取诚品书店的类别
	#==============================================================================
	def fetch_categorys(self):
		category_urls = [
		"http://www.eslite.com/category.aspx?cate=80",	#中文
		"http://www.eslite.com/category.aspx?cate=156",	#外文
		"http://www.eslite.com/category.aspx?cate=44"	#儿童
		]
		
		categorys = []
		
		for category_url in category_urls:
			self.snoopy.fetch(category_url)
			html =  self.snoopy.results
			reg_pattern = re.compile("\r")
			html = str_repalce(html, reg_pattern, "")
			reg_pattern = re.compile("\n")
			html = str_repalce(html, reg_pattern, "")
			reg_pattern = re.compile(r'<a href="(newbook_list.aspx?.*?)">(.*?)</a>')
			category_strs = reg_pattern.findall(html)
			
			for category_str in category_strs:
				try:
					category = self.init_category_format()
					params = url_decode(category_str[0])
					category["cate"] = params["cate"]
					category["sub"] = params["sub"]
					category["list"] =  params["list"]
					category["text"] =  category_str[1].strip().decode("utf8")
					categorys.append(category)
				except:
					pass
		return	categorys
			
	def save_categorys(self, categorys):
		categorys_str = ""
		for category in categorys:
			if categorys_str:
				categorys_str = "%s , ('%s', '%s', '%s', '%s', '%s', '%s')" % (categorys_str, category["cate"], category["sub"], category["list"], category["page"], category["text"], category["status"])
			else:
				categorys_str = "('%s', '%s', '%s', '%s', '%s', '%s')" % (category["cate"], category["sub"], category["list"], category["page"], category["text"], category["status"])
		
		if categorys_str:
			sql_str = "INSERT IGNORE category(`cate`, `sub`, `list`, `page`, `text`, `status`) VALUES %s;" % categorys_str
			print sql_str
			self.mysql.update(sql_str)
	
	def get_category(self):
		client_count = self.client_count
		client_id = self.client_id - 1
		
		sql_str = "SELECT `cate`, `sub`, `list`, `page`, `text` FROM `category` WHERE `status`=0 AND id%s%s=%s ORDER BY `id` ASC LIMIT 1;"  %  ("%", str(client_count), str(client_id))
		
		rows = self.mysql.query(sql_str, ["cate","sub","list","page", "text"])
		
		for row in rows:
			row["page"] = int(row["page"])
			return row
		
		return False
	
	
	def update_category_status(self, category, status):
		sql_str = "update category set `page`='%s', `status`='%s' where `cate`='%s' and `sub`='%s' and `list`='%s';" \
			% (category["page"], str(status), category["cate"], category["sub"], category["list"])
		print sql_str
		self.mysql.update(sql_str)
		
	#==============================================================================
	# fetch_book_id : 抓取某个小分类的图书的id
	#==============================================================================
	def fetch_books_id(self, category):
		for page in range(category["page"], 26, 1):
			category_url = "http://www.eslite.com/newbook_list.aspx?cate=%s&sub=%s&list=%s&page=%s" \
				% (category["cate"], category["sub"], category["list"], str(category["page"]))
			
			self.snoopy.fetch(category_url)
			html = self.snoopy.results
			reg_pattern = re.compile(r'pgid=(\d+)')
			books_id = reg_pattern.findall(html)
			books_id = {}.fromkeys(books_id).keys()
			self.save_books_id(books_id, category)
			print u"%s %s页:%s" % (category["text"], str(category["page"]), str(len(books_id)))
			category["page"] = page
			self.update_category_status(category, 0)
			if len(books_id) < 10:
				break
		self.update_category_status(category, 1)
		
	def save_books_id(self, books_id, category):
		books_str = ""
		for book_id in books_id:
			if books_str:
				books_str = "%s, ('%s', '%s', '%s', '%s', '')" % (books_str, book_id, category["cate"], category["sub"], category["list"])
			else:
				books_str = "('%s', '%s', '%s', '%s', '')" % (book_id, category["cate"], category["sub"], category["list"])
			
		if books_str:
			sql_str = "INSERT IGNORE book_abs(`book_id`, `cate`, `sub`, `list`, `html`) VALUES %s;" % books_str
			print sql_str
			self.mysql.update(sql_str)
	
	def get_book_url(self, book_abs):
		return ""
	
	def update_fetch_status_fail(self, name, year):
		status = 2
		sql_str = "UPDATE `publisher` SET  `status`=%s WHERE `name`='%s' AND `year`=%s;" % \
		(status, self.db.escape_string(name), str(year))
		print sql_str
		self.db.update(sql_str)
		
	def get_book_html(self, book_abs):
		sql_str = "select html from book_abs where book_id='%s';" % (book_abs["book_id"])
		
		rows = self.mysql.query(sql_str, ["html"])
		for row in rows:
			return filter_r_and_n(row["html"])
		return False
		
	def fetch_book(self, book_abs):
		book = self.init_book()
		book["url"] = "http://www.eslite.com/product.aspx?pgid=%s" % book_abs["book_id"]
		book["book_id"] = book_abs["book_id"]
		
		html = self.get_book_html(book_abs)
		if html:
			book = self.prase_book(book, html)
			self.save_book(book)
			self.update_book_abs_status(book_abs)
	
	#==============================================================================
	# prase_books_abstract : 从html中匹配书简介
	#==============================================================================
	def prase_books_abstract(self, html):
		books = []
		reg_pattern = re.compile(r"makeDetailUrl\(this, '/search/showDocDetails\?', '(.*?)', '(.*?)', '(.*?)'\);")
		book_matchs = reg_pattern.findall(html)
		
		for book_match in book_matchs:
			book = self.init_book_abstract()
			book["book_id"] = book_match[0]
			book["src"] = book_match[1]
			book["publisher"] = book_match[2]
			books.append(book)
			print book["book_id"], book["src"], book["publisher"]
			
		return books
			
	
	def prase_book(self, book, html):
		reg_pattern = re.compile(u'<h1>(.*?)</h1>')
		match = reg_pattern.search(html)
		if match:
			book["name"] = match.group(1)
			book["name"] = filter_tags(book["name"])
			book["name"] = filter_r_and_n(book["name"])
		
		reg_pattern = re.compile(u'<div class="PI_info">(.*?)</div>')
		match = reg_pattern.search(html)
		if match:
			book_info_str = match.group(1)
			
			#作者
			reg_pattern = re.compile(u'<h3 class="PI_item">作者(.*?)</h3>')
			match = reg_pattern.search(book_info_str)
			if match:
				book["author"] = match.group(1)
				book["author"] = filter_tags(book["author"])
				book["author"] = filter_r_and_n(book["author"])
				book["author"] = book["author"].replace(" ／ ", "")
				
			#出版社
			reg_pattern = re.compile(u'<h3 class="PI_item">出版社(.*?)</h3>')
			match = reg_pattern.search(book_info_str)
			if match:
				book["press"] = match.group(1)
				book["press"] = filter_tags(book["press"])
				book["press"] = filter_r_and_n(book["press"])
				book["press"] = book["press"].replace(" ／ ", "")
				
			#出版日期
			reg_pattern = re.compile(u'<h3 class="PI_item">出版日期(.*?)</h3>')
			match = reg_pattern.search(book_info_str)
			if match:
				book["publictime"] = match.group(1)
				book["publictime"] = filter_tags(book["publictime"])
				book["publictime"] = filter_r_and_n(book["publictime"])
				book["publictime"] = book["publictime"].replace(" ／ ", "")
			
			#定价
			reg_pattern = re.compile(u'<h3 class="PI_item">定價(.*?)</h3>')
			match = reg_pattern.search(book_info_str)
			if match:
				book["price"] = match.group(1)
				book["price"] = filter_tags(book["price"])
				book["price"] = filter_r_and_n(book["price"])
				book["price"] = book["price"].replace(" ／ ", "")
			
			#售价
			reg_pattern = re.compile(u'<h3 class="PI_item">售價(.*?)</h3>')
			match = reg_pattern.search(book_info_str)
			if match:
				book["sell_price"] = match.group(1)
				book["sell_price"] = filter_tags(book["sell_price"])
				book["sell_price"] = filter_r_and_n(book["sell_price"])
				book["sell_price"] = book["sell_price"].replace(" ／ ", "")
			
			#裝訂
			reg_pattern = re.compile(u'class="PI_item">裝訂(.*?)<')
			match = reg_pattern.search(book_info_str)
			if match:
				book["print"] = match.group(1)
				book["print"] = filter_tags(book["print"])
				book["print"] = filter_r_and_n(book["print"])
				book["print"] = book["print"].replace(" ／ ", "")
				
			#商品語言
			reg_pattern = re.compile(u'class="PI_item">商品語言(.*?)<')
			match = reg_pattern.search(book_info_str)
			if match:
				book["language"] = match.group(1)
				book["language"] = filter_tags(book["language"])
				book["language"] = filter_r_and_n(book["language"])
				book["language"] = book["language"].replace(" ／ ", "")
		
		#詳細資料
		
		reg_pattern = re.compile(u'<div class="C_box"><h2>詳細資料</h2>(.*?)</div>')
		match = reg_pattern.search(html)
		if match:
			book_info_str = match.group(1)
			book_info_str = filter_tags(book_info_str)
			book_info_str = book_info_str.replace("\t", "")
		
			reg_pattern = re.compile(u'ISBN 13 ／(\d+)')
			match = reg_pattern.search(book_info_str)
			if match:
				book["isbn"] = match.group(1)
				
			reg_pattern = re.compile(u'頁數／(\d+)')
			match = reg_pattern.search(book_info_str)
			if match:
				book["pagecnt"] = match.group(1)
				
			
		#目录
		reg_pattern = re.compile(u'<div id="ctl00_ContentPlaceHolder1_Product_info_more1_catelog" class="C_box" style="display:none;">(.*?)</div>')
		match = reg_pattern.search(html)
		if match:
			book["menu"] =  filter_tags(match.group(1))
			book["menu"] = book["menu"].replace("本書目錄", "")
		return book
	
		#作者介绍
		reg_pattern = re.compile(u'<div id="ctl00_ContentPlaceHolder1_Product_info_more1_all_character" class="C_box" style="display:none;">(.*?)</div>')
		match = reg_pattern.search(html)
		if match:
			book["authordesc"] =  filter_tags(match.group(1))
			book["authordesc"] = book["authordesc"].replace("作者介紹", "")
		
		#内容接受	
		reg_pattern = re.compile(u'<div id="ctl00_ContentPlaceHolder1_Product_info_more1_introduction" class="C_box" style="display:block;">(.*?)</div>')
		match = reg_pattern.search(html)
		if match:
			book["desc"] =  filter_tags(match.group(1))
			book["desc"] = book["desc"].replace("內容簡介", "")
		
		#媒体推荐	
		reg_pattern = re.compile(u'<div id="ctl00_ContentPlaceHolder1_Product_info_more1_medium" class="C_box" style="display:none;">(.*?)</div>')
		match = reg_pattern.search(html)
		if match:
			book["meidum"] =  filter_tags(match.group(1))
			book["meidum"] = book["meidum"].replace("媒體推薦", "")
		
		#得獎紀錄
		reg_pattern = re.compile(u'<div id="ctl00_ContentPlaceHolder1_Product_info_more1_award" class="C_box" style="display:none;">(.*?)</div>')
		match = reg_pattern.search(html)
		if match:
			book["award"] =  filter_tags(match.group(1))
			book["award"] = book["award"].replace("得獎紀錄", "")
		
		return book
	
			
	#==============================================================================
	# update_fetch_status : 保存抓取进度
	#==============================================================================
	def update_fetch_status(self, name, year, page=1, success=False):
		if success:
			status = 1
		else:
			status = 0
		sql_str = "UPDATE `publisher` SET `page`=%s, `status`=%s WHERE `name`='%s' AND `year`=%s;" % \
		(str(page), status, self.db.escape_string(name), str(year))
		print sql_str
		self.db.update(sql_str)
	
	
	#==============================================================================
	# get_publister : 获得一个出版社
	#==============================================================================
	def get_publisher(self):
		client_count = self.client_count
		client_id = self.client_id - 1
		
		sql_str = "SELECT `id`, `name`, `year`, `page` from `publisher` WHERE `status`=0 AND id%s%s=%s ORDER BY `year` ASC LIMIT 1;"  %  ("%", str(client_count), str(client_id))
		
		rows = self.db.query(sql_str, ["id","name","year","page"])
		
		for row in rows:
			print row["id"]
			publisher = {}
			publisher["name"] = row["name"]
			publisher["year"] = int(row["year"])
			publisher["page"] = int(row["page"])
			return publisher
		
		return False
	
	def get_publisher_by_id(self, id):
		sql_str = "SELECT `name`, `year`, `page` from `publisher` WHERE `status`=0 AND `id`=%s;" % (str(id))
		
		rows = self.db.query(sql_str, ["name","year","page"])
		
		for row in rows:
			publisher = {}
			publisher["name"] = row["name"]
			publisher["year"] = int(row["year"])
			publisher["page"] = int(row["page"])
			return publisher
		
		return False
	
	def init_publisher(self):
		return
		for id in range(27, 2351, 1):
			publisher = self.get_publisher_by_id(id)
			
			year_str = ""
			for year in range(1971, 2013, 1):
				if year_str:
					year_str = "%s, ('%s', %s)" % (year_str, self.db.escape_string(publisher["name"]), str(year))
				else:
					year_str = "('%s', %s)" % (self.db.escape_string(publisher["name"]), str(year))
			print id
			if year_str:
				sql_str = "INSERT IGNORE publisher(`name`, `year`) VALUES %s;" % (year_str)
				self.db.update(sql_str)
				
				
	def get_book_abs(self, status):
		client_count = self.client_count
		client_id = self.client_id - 1
		sql_str = "SELECT book_id FROM `book_abs` WHERE `status`=%s  AND id%s%s = %s LIMIT 1;" % (str(status), "%",str(client_count), str(client_id))
		rows = self.mysql.query(sql_str, ["book_id"])
		for row in rows:
			return row
		
		return False
	
	def fetch_book_html(self, book_abs):
		book_url = "http://www.eslite.com/product.aspx?pgid=%s" % book_abs["book_id"]
		print book_url
		self.snoopy.fetch(book_url)
		html = self.snoopy.results
		self.save_book_html(book_abs, html)
	
	def save_book_html(self, book_abs, html):
		html = self.mysql.escape_string(html)
		sql_str = "update book_abs set html='%s', status=1 where book_id='%s';" % (html, book_abs["book_id"])
		self.mysql.update(sql_str)
	
	def init_book(self):
		book = {}
		book["book_id"] = ""	#book_id
		book["isbn"] = ""		#isbn
		book["category"] = ""	
		book["shortCategory"] = ""	#分类
		book["ztCategory"] = ""	#中图分类号
		book["name"] = ""		#书名
		book["author"] = ""		#作者
		book["authordesc"] = ""		#介绍
		book["price"] = ""		#定价
		book["sell_price"] = "" #售价
		book["language"] = "" #语言
		book["press"] = ""		#出版社
		book["print"] = ""		#装订
		book["publictime"] = ""	#出版时间
		book["pagecnt"] = 0		#页数
		book["version"] = 0		#版本
		book["printversion"] = 0#版本
		book["desc"] = ""		#摘要
		book["url"] = ""		#url
		book["img"] = ""	#图片
		book["meidum"] = ""  #媒体推荐
		book["award"] = "" #得奖记录
		book["menu"] = "" #目录
		
		return book
	
	def save_book(self, book):
		for key in book.keys():
			print key, book[key]

		values_str = ""
		keys_str = ""
		for key in book.keys():
			if book[key]:
				if values_str:
					values_str = "%s, '%s'" % (values_str, self.mysql.escape_string(str(book[key])))
					keys_str = "%s, `%s`" % (keys_str, key)
				else:
					values_str = "'%s'" % (self.mysql.escape_string(str(book[key])))
					keys_str = "`%s`" % (key)
		
		sql_str = "INSERT IGNORE book(%s) VALUES (%s)  on duplicate key update `isbn`='%s';" % (keys_str, values_str, book["isbn"])
		print sql_str
		self.mysql.update(sql_str)
	
	def update_book_abs_status(self, book_abs):
		sql_str = "UPDATE book_abs SET `status`=2 WHERE book_id='%s';" % \
		(book_abs["book_id"])
		self.mysql.update(sql_str)
		


if __name__ == "__main__":
	try:
		type = sys.argv[1]
	except:
		type = ""
	
	type = "book_html"
	
	client_count = 1
	client_id = 1
	try:
		client_count = int(argvs[1])
	except:
		pass
	
	try:
		client_id = int(argvs[2])
	except:
		pass
	
	if type in ["init", "book_id", "book_html", "publisher", "book"]:
		chengpin = Chengpin()
		chengpin.set_client(client_count, client_id)
		
		#初始化诚品书店的类别信息
		if type == "init":
			categorys = chengpin.fetch_categorys()
			chengpin.save_categorys(categorys)
		
		#抓取诚品的图书的id
		elif type == "book_id":
			while True:
				try:
					category = chengpin.get_category()
					print category
					if category:
						books_id = chengpin.fetch_books_id(category)
					else:
						break
				except:
					print "exception sleep(5)"
					time.sleep(5)
				
		#获得图书页面的html
		elif type == "book_html":
			while True:
				try:
					book_abs = chengpin.get_book_abs(0)
					if book_abs:
						chengpin.fetch_book_html(book_abs)
					else:
						break
				except:
					print "exception sleep(5)"
					time.sleep(5)
		
		#抓取图书的详情
		elif type == "book":
			while True:
				book_abs = chengpin.get_book_abs(1)
				if book_abs:
					chengpin.fetch_book(book_abs)
				else:
					break
	else:
		print "python chengpin_fetch.py init"
		print "python chengpin_fetch.py book_id"
		print "python chengpin_fetch.py book"
		print "init 抓取类别"
		print "book_id 抓取诚品图书的id"
		print "book 抓取同城书店的图书信息"
