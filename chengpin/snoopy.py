# -*- coding: utf-8 -*-

import HTMLParser
import urlparse
import urllib
import urllib2
import cookielib
import string
import re
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from urllib2 import urlopen, Request

class Snoopy(object):
	def __init__(self):
		self.host		=	"www.eslite.com"	# host name we are connecting to
		self.port			=	80					# port we are connecting to
		self.proxy_host		=	""					# proxy host to use
		self.proxy_port		=	""					# proxy port to use
		self.proxy_user		=	""					# proxy user to use
		self.proxy_pass		=	""					# proxy password to use
		self.params		  =   {}
		self.agent			=	"Mozilla/5.0 (Windows NT 6.1 WOW64 rv:14.0) Gecko/20100101 Firefox/14.0.1"#"Snoopy v1.2.3"	# agent we masquerade as
		self.referer		=	""					# referer info to pass
		self.cookies		=	{}			# array of cookies to pass
													# $cookies["username"]="joe"
		self.rawheaders		=	{}			# array of raw headers to send
													# $rawheaders["Content-type"]="text/html"
	
		self.maxredirs		=	5					# http redirection depth maximum. 0 = disallow
		self.lastredirectaddr	=	""				# contains address of last redirected address
		self.offsiteok		=	True				# allows redirection off-site
		self.maxframes		=	0					# frame content depth maximum. 0 = disallow
		self.expandlinks	=	True				# expand links to fully qualified URLs.
													# this only applies to fetchlinks()
													# submitlinks(), and submittext()
		self.passcookies	=	True				# pass set cookies back through redirects
													# NOTE: this currently does not respect
													# dates, domains or paths.
		
		self.user			=	""					# user for http authentication
		self.pass_auth		=	""					# password for http authentication
		
		# http accept types
		self.accept			=	"text/html, application/xhtml+xml, */*"
		
		self.results		=	""					# where the content is put
			
		self.error			=	""					# error messages sent here
		self.response_code	=	""					# response code returned from server
		self.headers		=	{}			# headers returned from server sent here
		self.maxlength		=	2000000				# max return data length (body)
		self.read_timeout	=	0					# timeout on read operations, in seconds
													# supported only since PHP 4 Beta 4
													# set to 0 to disallow timeouts
		self.timed_out		=	False				# if a read operation timed out
		self.status			=	0					# http request status
	
		self.temp_dir		=	"/tmp"				# temporary directory that the webserver
													# has permission to write to.
													# under Windows, this should be C:\temp
	
		self.curl_path		=	"/usr/local/bin/curl"
													# Snoopy will use cURL for fetching
													# SSL content if a full system path to
													# the cURL binary is supplied here.
													# set to False if you do not have
													# cURL installed. See http:#curl.haxx.se
													# for details on installing cURL.
													# Snoopy does *not* use the cURL
													# library functions built into php,
													# as these functions are not stable
													# as of this Snoopy release.
		
		#**** Private variables ****
		
		self._maxlinelen	=	40960				# max line length (headers)
		
		self._httpmethod	=	"GET"				# default http request method
		self._httpversion	=	"HTTP/1.0"			# default http request version
		self._submit_method	=	"POST"				# default submit method
		self._submit_type	=	"application/x-www-form-urlencoded"	# default submit type
		self._mime_boundary	=   ""					# MIME boundary for multipart/form-data submit type
		self._redirectaddr	=	False				# will be set if page fetched is a redirect
		self._redirectdepth	=	0					# increments on an http redirect
		self._frameurls		= 	{}			# frame src urls
		self._framedepth	=	0					# increments on frame depth
		
		self._isproxy		=	False				# set if using a proxy server
		self._fp_timeout	=	30					# timeout for socket connection
	
	

	#==============================================================================
	# setCookies 设置cookies字典
	#==============================================================================
	def setCookies(self, cookies):
		self.cookies = cookies
		
	#==============================================================================
	# getCookies : 获得cookies字典
	#==============================================================================
	def getCookies(self, cookies):
		return self.cookies
		
	#==============================================================================
	# getCookiesStr : 获得cookies字典, 已经转换为字符串
	#==============================================================================
	def getCookiesStr(self):
		cookies_str = ""
		for key in self.cookies.keys():
			cookies_str = "%s %s=%s" % (cookies_str, key, self.cookies[key])
		return cookies_str
	
	#==============================================================================
	# setCookiesStr : 通过cookiesz字符串设置cookie
	#==============================================================================
	def setCookiesStr(self, cookies_str):
		cookies = {}
		cookies_str = cookies_str.replace(" ", "");
		cookies_array = cookies_str.split(";");
		
		for cookie in cookies_array:
			if cookie:
				cookie = cookie.split("=")
				cookie_key = cookie[0]
				cookie_value = cookie[1]
				cookies[cookie_key] =  cookie_value
		
		self.cookies = cookies
		 
	#==============================================================================
	# getheaders : 获得请求头
	#==============================================================================
	def getheaders(self):
		headers = {'User-Agent' : self.agent,
				   'Referer' : 'http://shop.kongfz.com',
				   'Host': self.host,
				   'Accept-Language': 'zh-CN',
				   'Accept': self.accept}
		
		headers["Cookie"] = 'shoppingCartSessionId=b5be7924b4ef53a28bafe38d73e88ca1; __utma=141829104.1947170551.1350538661.1350613206.1350622177.6; __utmz=141829104.1350613206.5.3.utmcsr=kongfz.com|utmccn=(referral)|utmcmd=referral|utmcct=/; __utma=141829104.1947170551.1350538661.1350613206.1350622177.6; __utmz=141829104.1350613206.5.3.utmcsr=kongfz.com|utmccn=(referral)|utmcmd=referral|utmcct=/; PHPSESSID=1c1fa6ce9cb79e4d9c43c147e9b964cf; __utmc=141829104; __utmc=141829104; __utmb=141829104.1.10.1350622177; __utmb=141829104.2.10.1350622177'
		return headers
	
	
	#==============================================================================
	# fetch : 获得网页内容
	#==============================================================================
	def fetch(self, url, driver=""):
		if driver == "":
			params = ""
			headers = self.getheaders()
			request = urllib2.Request(url, params, headers)
			response = urllib2.urlopen(request)
			response_text = response.read()
			self.results = response_text
			self.response_code = 200
			
		else:
			driver.get(url)
			time.sleep(5)
			self.results = driver.page_source
			self.response_code = 200
			return True
	

def chengpin_test():
	snoopy = Snoopy()
	
	snoopy.fetch("http://www.eslite.com/newbook_list.aspx?cate=156&sub=157&list=167&page=2")
	print snoopy.results
	
#===============================================================================
# snoopy_test : Snoopy类测试
#===============================================================================
def snoopy_test():
	chengpin_test()
	
		
if __name__ == "__main__":
	snoopy_test()
