from lib.Config import Config
import MySQLdb
from warnings import filterwarnings

class Database:
	conn = None
	filterwarnings('ignore', category = MySQLdb.Warning)

	def connect(self):
		config = Config()

		self.conn = MySQLdb.connect(
			host=config.getConfig()['mysql']['host'],
			port=config.getConfig()['mysql']['port'],
			user=config.getConfig()['mysql']['user'],
			passwd=config.getConfig()['mysql']['pass'],
			db=config.getConfig()['mysql']['db']
			)
		self.conn.autocommit(True)
		self.conn.set_character_set('utf8')

	def query(self, sql, args=None):
		try:
			cursor = self.conn.cursor()
			cursor.execute(sql,args)
		except:
			self.connect()
			cursor = self.conn.cursor()
			try:
				cursor.execute(sql,args)
			except MySQLdb.Error as e:
				print("-------")
				print(e)
				print("-------")
				cursor.close()
				self.connect()
				cursor = self.conn.cursor()
				try:
					cursor.execute(sql, args)
				except MySQLdb.Error as e:
					print("NONONONO")
					
		return cursor

	def queryMany(self, sql, args=None):
		try:
			cursor = self.conn.cursor()
			cursor.executemany(sql,args)
		except:
			self.connect()
			cursor = self.conn.cursor()
			cursor.executemany(sql,args)
		return cursor