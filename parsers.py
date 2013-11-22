from HTMLParser import HTMLParser
import re

class DataWrapper(object):
	def __init__(self):
		self._data = []

	@property
	def data(self):
		return self._data

class HTMLParserBetweenTags(HTMLParser, DataWrapper):
	def __init__(self, tag, attname, attvalue):
		HTMLParser.__init__(self)
		DataWrapper.__init__(self)

		self.numOfNestedTags = 0
		self.tag = tag
		self.attname = attname
		self.attvalue = attvalue

	def handle_starttag(self, tag, attributes):
		if tag != self.tag:
			return
		if self.numOfNestedTags:
			self.numOfNestedTags =+ 1
			return
		if not (self.attname, self.attvalue) in attributes:
			return
		self.numOfNestedTags = 1

	def handle_endtag(self, tag):
		if tag == self.tag and self.numOfNestedTags:
			self.numOfNestedTags -= 1

	def handle_data(self, data):
			if self.numOfNestedTags:
				self._data.append(data)

class HTMLParserTagWithAttribute(HTMLParser, DataWrapper):
	def __init__(self, tag, attname, attvalue, attneeded):
		HTMLParser.__init__(self)
		DataWrapper.__init__(self)

		self.tag = tag
		self.attname = attname
		self.attvalue = attvalue
		self.attneeded = attneeded

	def handle_starttag(self, tag, attributes):
		if tag == self.tag:
			isAttrfound = (self.attname, self.attvalue) in attributes
			if(isAttrfound):
				data = filter(lambda (x,y): x == self.attneeded, attributes)
				data = map(lambda (x,y): y, data)
				self._data.extend(data)

class HTMLParserTag(HTMLParser, DataWrapper):
	def __init__(self, tag, attneeded):
		HTMLParser.__init__(self)
		DataWrapper.__init__(self)

		self.tag = tag
		self.attneeded = attneeded

	def handle_starttag(self, tag, attributes):
		if tag == self.tag:
			data = filter(lambda (x,y): x == self.attneeded, attributes)
			data = map(lambda (x,y): y, data)
			self._data.extend(data)

def isMagnetLink(link):
	magnetPattern = r'^magnet:'
	prog = re.compile(magnetPattern)
	result = prog.match(link)
	if result:
		return True
	else:
		return False
def isTorrentLink(link):
	torrentPattern = r'.*\.torrent$'
	prog = re.compile(torrentPattern)
	result = prog.match(link)
	if result:
		return True
	else:
		return False
