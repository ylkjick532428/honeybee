# -*- coding: utf-8 -*-

import MySQLdb as mysql
import os, types, time, datetime
import urllib2
import re
from urllib import unquote

def filter_r_and_n(htmlstr):
	htmlstr = htmlstr.replace("\r", "")
	htmlstr = htmlstr.replace("\n", "")
	return htmlstr
	
def filter_tags(htmlstr):
	#先过滤CDATA
	re_cdata=re.compile('//<!\[CDATA\[[^>]*//\]\]>',re.I) #匹配CDATA
	re_script=re.compile('<\s*script[^>]*>[^<]*<\s*/\s*script\s*>',re.I)#Script
	re_style=re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>',re.I)#style
	re_br=re.compile('<br\s*?/?>')#处理换行
	re_h=re.compile('</?\w+[^>]*>')#HTML标签
	re_comment=re.compile('<!--[^>]*-->')#HTML注释
	s=re_cdata.sub('',htmlstr)#去掉CDATA
	s=re_script.sub('',s) #去掉SCRIPT
	s=re_style.sub('',s)#去掉style
	s=re_br.sub('\n',s)#将br转换为换行
	s=re_h.sub('',s) #去掉HTML 标签
	s=re_comment.sub('',s)#去掉HTML注释
	#去掉多余的空行
	blank_line=re.compile('\n+')
	s=blank_line.sub('\n',s)
	s=replaceCharEntity(s)#替换实体
	return s
	
##替换常用HTML字符实体.
#使用正常的字符替换HTML中特殊的字符实体.
#你可以添加新的实体字符到CHAR_ENTITIES中,处理更多HTML字符实体.
#@param htmlstr HTML字符串.
def replaceCharEntity(htmlstr):
	CHAR_ENTITIES={'nbsp':' ','160':' ',
				'lt':'<','60':'<',
				'gt':'>','62':'>',
				'amp':'&','38':'&',
				'quot':'"','34':'"',}
	
	re_charEntity=re.compile(r'&#?(?P<name>\w+);')
	sz=re_charEntity.search(htmlstr)
	while sz:
		entity=sz.group()#entity全称，如&gt;
		key=sz.group('name')#去除&;后entity,如&gt;为gt
		try:
			htmlstr=re_charEntity.sub(CHAR_ENTITIES[key],htmlstr,1)
			sz=re_charEntity.search(htmlstr)
		except KeyError:
			#以空串代替
			htmlstr=re_charEntity.sub('',htmlstr,1)
			sz=re_charEntity.search(htmlstr)
	return htmlstr

def str_repalce(s,re_exp,repl_string):
	return re_exp.sub(repl_string,s)


def url_decode(url):
	result={}
	tmp_array =url.split("?")
	params_str =  tmp_array[1]
	params_str =  params_str.split("&")
	for i in params_str:
		i=i.split("=")
		if len(i)==2:
			result[unquote(i[0])]=unquote(i[1])
	return result

#===============================================================================
# MySqlUtil : 链接数据库的工具类
#===============================================================================
class MySqlUtil(object):
	def __init__(self, db):
		self.db = db


	#==============================================================================
	# set_utf8 : 设置数据库连接的编码
	#==============================================================================
	def set_utf8(self, datebase_cursor):
		datebase_cursor.execute("SET NAMES utf8")
		datebase_cursor.execute("SET CHARACTER_SET_CLIENT=utf8")
		datebase_cursor.execute("SET CHARACTER_SET_RESULTS=utf8")

			
	def set_gbk(self, datebase_cursor):
		datebase_cursor.execute("SET NAMES gbk")
		datebase_cursor.execute("SET CHARACTER_SET_CLIENT=gbk")
		datebase_cursor.execute("SET CHARACTER_SET_RESULTS=gbk")

	
	def set_db(self, db):
		self.db = db

				
	def get_db_connection(self):
		self.db_connection = mysql.connect(host=self.db['HOST'], user=self.db['USER'], passwd=self.db['PASSWORD'], db=self.db['NAME'], charset='utf8')
		return self.db_connection
	
	
	def get_db_cursor(self):
		try:
			if self.db_connection:
				self.db_cursor = self.db_connection.cursor()
		except:
			self.db_cursor = self.get_db_connection().cursor()
		
		self.set_utf8(self.db_cursor)

		return self.db_cursor


	#==============================================================================
	# query : 执行查询语句, fields为查询自动的数组
	#==============================================================================
	def query(self, sql_str, fields):
		results = []

		db_cursor = self.get_db_cursor()
		db_conn = self.get_db_connection()
		
		db_cursor.execute(sql_str)
		query_results = db_cursor.fetchmany(10)
		
		while query_results:
			for row in query_results:
				result = {}
				i = 0
				for cel in row:
					key = fields[i]
					i = i + 1
					if key == "id":
						result[key] = int(cel)
					else:
						result[key] = cel
				results.append(result)
			query_results = db_cursor.fetchmany(10)
		return results


	#==============================================================================
	# update : 执行update语句
	#==============================================================================
	def update(self, sql_str):
		db_cursor = self.get_db_cursor()
		db_conn = self.get_db_connection()
		
		db_cursor.execute(sql_str)
		db_conn.commit()


	#==============================================================================
	# escape_string : 
	#==============================================================================
	def escape_string(self, str):
		return mysql.escape_string(str)


	#==============================================================================
	# close_db_connection : 关闭数据库连接
	#==============================================================================
	def close_db_connection(self):
		try:
			self.db_connection.close()
			print 'close db connection success'
		except:
			print 'close db connection failure'



g_adsl_account = {"name": "adsl",
				"username": "051262888698",
				"password": "630786"}

	
class Adsl(object):
	#==============================================================================
	# __init__ : name: adsl名称
	#==============================================================================
	def __init__(self):
		self.name = g_adsl_account["name"]
		self.username = g_adsl_account["username"]
		self.password = g_adsl_account["password"]

		
	#==============================================================================
	# set_adsl : 修改adsl设置
	#==============================================================================
	def set_adsl(self, account):
		self.name = account["name"]
		self.username = account["username"]
		self.password = account["password"]

	
	#==============================================================================
	# connect : 宽带拨号
	#==============================================================================
	def connect(self):
		cmd_str = "rasdial %s %s %s" % (self.name, self.username, self.password)
		os.system(cmd_str)
		time.sleep(5)

		
	#==============================================================================
	# disconnect : 断开宽带连接
	#==============================================================================
	def disconnect(self):
		cmd_str = "rasdial %s /disconnect" % self.name
		os.system(cmd_str)
		time.sleep(5)

	
	#==============================================================================
	# reconnect : 重新进行拨号
	#==============================================================================
	def reconnect(self):
		self.disconnect()
		self.connect()

class BookStore(object):
	def __init__(self):
		self.mysql = MySqlUtil(g_db_config_book_store_db)
		self.table = "book_store";


	def init_book_store(self):
		book_store = {}
		book_store['store_id'] = ''
		book_store['store_name'] = ''
		book_store['nick'] = ''
		book_store['open_time'] = ''
		book_store['credit'] = ''
		book_store['status'] = '0'
		book_store['good_reputation'] = ''
		book_store['level_name'] = ''
		book_store['authentication'] = 0
		book_store['bail'] = ''
		book_store['address'] = ''
		book_store['phone'] = ''
		book_store['homepage'] = ''
		book_store['store_notice'] = ''
		return book_store

	#==============================================================================
	# update : 执行update语句
	#==============================================================================
	def update(self, sql_str):
		db_cursor = self.mysql.get_db_cursor()
		db_conn = self.mysql.get_db_connection()
		
		db_cursor.execute(sql_str)
		db_conn.commit()

	
	#==============================================================================
	# query : 执行查询语句, fields为查询自动的数组
	#==============================================================================
	def query(self, sql_str, fields):
		results = []

		db_cursor = self.mysql.get_db_cursor()
		db_conn = self.mysql.get_db_connection()
		
		db_cursor.execute(sql_str)
		query_results = db_cursor.fetchmany(10)
		
		while query_results:
			for row in query_results:
				result = {}
				i = 0
				for cel in row:
					key = fields[i]
					i = i + 1
					if key == "id":
						result[key] = int(cel)
					else:
						result[key] = cel
				results.append(result)
			query_results = db_cursor.fetchmany(10)
		return results
	
	#==============================================================================
	# get_store_key_str : 把微博对象转换为字符串
	#==============================================================================
	def get_book_store_key_str(self):
		store = self.init_book_store()
	
		key_str = ""
		for key in store.keys():
			if key_str:
				key_str = "%s, %s"  % (key_str, key)
			else:
				key_str = "%s" % key
		
		key_str = "(%s)" % key_str
		
		return key_str
	
	
	def get_book_store_str(self, store):
		store_str = ""
		for key in store.keys():
			if store_str:
				if type(store[key]) is types.IntType or store[key] == "NULL":
					store_str = "%s, %s"  % (store_str, store[key])
				else:
					store_str = "%s, '%s'"  % (store_str, mysql.escape_string(store[key]))
					
			else:
				if type(store[key]) is types.IntType or store[key] == "NULL":
					store_str = "%s" % store[key]
				else:
					store_str = "'%s'" % mysql.escape_string(store[key])
		
		store_str = r"(%s)" % store_str
		
		return store_str
	
	
	#==============================================================================
	# get_book_store_id : 获得一个未抓取的书店store_id
	#==============================================================================
	def get_book_store_id(self):
		sql_str = "SELECT id, store_id FROM %s WHERE fetch_status=0 AND is_deleted=0 limit 1;" % 'province_has_book_store'
		
		query_result = self.query(sql_str, ["id", "store_id"])
		
		
		for result in query_result:
			return result["store_id"]
			
		return ""

	def update_fetch_status(self, store_id):
		sql_str = "UPDATE %s SET fetch_status=1 WHERE store_id=%s;" % ('province_has_book_store', store_id)
		print sql_str
		self.update(sql_str)
		
	def save_book_store(self, book_store):
		str1 = self.get_book_store_key_str()
		str2 = self.get_book_store_str(book_store)
					
		sql_str = "INSERT IGNORE %s%s VALUES %s;" % (self.table, str1, str2)
		self.update(sql_str)
		return True
	
	def save_booke_store_ids(self, prov_name, prov_id, ids):
		sql_str = "INSERT IGNORE %s(`province_name`, `province_code`,`store_id`, `category`) VALUES" % "province_has_book_store"
		tmp_str = ""
		for id in ids.keys():
			if tmp_str:
				tmp_str = "%s, ('%s', '%s', '%s', '%s')" % (tmp_str, prov_name, prov_id, id, ids[id])
			else:
				tmp_str = "('%s', '%s', '%s', '%s')" % (prov_name, prov_id, id, ids[id])
		
		if tmp_str:
			sql_str = "%s %s;" % (sql_str, tmp_str)
			self.update(sql_str)
			
	
	#==============================================================================
	# close : 关闭mysql数据库连接
	#==============================================================================
	def close(self):
		self.mysql.close_db_connection()
		
class CityUtil(object):
	def __init__(self):
		self.mysql = MySqlUtil(g_db_config_dispatch_db)
		
	
	#==============================================================================
	# query : 执行查询语句, fields为查询自动的数组
	#==============================================================================
	def query(self, sql_str, fields):
		results = []

		db_cursor = self.mysql.get_db_cursor()
		db_conn = self.mysql.get_db_connection()
		
		db_cursor.execute(sql_str)
		query_results = db_cursor.fetchmany(10)
		
		while query_results:
			for row in query_results:
				result = {}
				i = 0
				for cel in row:
					key = fields[i]
					i = i + 1
					result[key] = "%s" % cel
				results.append(result)
			query_results = db_cursor.fetchmany(10)
		return results

	
	def get_city_code(self, city_name):
		if city_name:
			sql_str = "select id from city where instr(aliases, '\$%s\$') order by id asc;" % city_name;
			query_result = self.query(sql_str, ["id"])
			
			for result in query_result:
				city_code = result["id"]
				city_code = city_code[:4]
				return city_code
			
		return "-1"

		
if __name__ == "__main__":
	url = "newbook_list.aspx?cate=80&sub=81&list=88"
	print url_decode(url)
	