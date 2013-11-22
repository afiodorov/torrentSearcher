from HTMLParser import HTMLParser
import parsers
from parsers import HTMLParserTag
from parsers import HTMLParserTagWithAttribute
from parsers import HTMLParserBetweenTags
from collections import namedtuple
import urllib, urllib2, logging, locale

Torrent = namedtuple("Torrent", "filename url magnet torrentFile torrentsite description seeds verified")

LOGGER = logging.getLogger('torrentfinders')
LOGGER.setLevel(logging.ERROR)
handler = logging.FileHandler('/tmp/torrentfinders.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
LOGGER.addHandler(handler)

class PageOpener(object):
    def __init__(self):
        self._userAgent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/28.0.1500.71 Chrome/28.0.1500.71 Safari/537.36'

    def addUserAgent(self):
        urlhandler = urllib2.HTTPHandler(debuglevel=0)
        opener = urllib2.build_opener(urlhandler)
        opener.addheaders = [('User-agent', self._userAgent)]
        urllib2.install_opener(opener)

    def retrievePage(self, request):
        result = None
        try:
            LOGGER.info("Retrieving: " + str( request.get_full_url ))
            result = urllib2.urlopen(request)
            LOGGER.info("Returned status: " + str( result.getcode() ) )
        except (urllib2.URLError, urllib2.HTTPError) as e:
            LOGGER.exception(e)
        return result

class BitSnoopTorrentFinder(object):
    """Finds torrents in bitsnoop.com website"""
    torrentUrl = "http://bitsnoopproxy.in"
    searchUrl = torrentUrl + "/search/all"

    class BitSnoopFrontPageParser(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)
            self._isPrecededBySpanTag = False
            self._linksToTorrents = []

        def handle_starttag(self, tag, attrs):
            if (tag == "span"):
                for (attrName, attrVal) in attrs:
                    if attrName == "class" and attrVal == "icon cat_tv":
                        self._isPrecededBySpanTag = True
                        break

            elif (self._isPrecededBySpanTag == True):
                self._isPrecededBySpanTag = False
                if (tag == "a"):
                    self._linksToTorrents.extend(filter(lambda x: x[0] == 'href', attrs))

        def finiliseParsing(self):
            self._linksToTorrents = map(lambda x: BitSnoopTorrentFinder.torrentUrl + x[1], self._linksToTorrents)

        @property
        def linksToTorrents(self):
            return self._linksToTorrents

    def __init__(self):
        self._pageOpener = PageOpener()
        self._pageOpener.addUserAgent()

    def __iter__(self):
        if hasattr(self, '_htmlParser'):
            for torrentLink in self._htmlParser.linksToTorrents:
                yield self.buildTorrent(torrentLink)
        else:
            raise StopIteration


    def retrieveSearchResults(self, searchTerm):
        request = self.__buildRequest(searchTerm)
        self.__searchResults = self._pageOpener.retrievePage(request)
        self._htmlParser = self.BitSnoopFrontPageParser()
        self._htmlParser.feed(self.__searchResults.read())
        self._htmlParser.finiliseParsing()

    def buildTorrent(self, link):
        request = urllib2.Request(link)
        torrentPage = self._pageOpener.retrievePage(request)
        encoding = torrentPage.headers.getparam('charset')
        encoding = encoding[:encoding.find(",")]
        return self._buildTorrentFromPage(link, torrentPage.read().decode(encoding))

    def __buildRequest(self, searchTerm):
        urlWithSearch = BitSnoopTorrentFinder.searchUrl + "/" + urllib.quote_plus(searchTerm)
        return urllib2.Request(urlWithSearch)

    def _buildTorrentFromPage(self, torrentLink, torrentPage):
        description = self._getTorrentDescription(torrentPage)
        seeds       = self._getTorrentSeeds(torrentPage)
        links       = self._getTorrentLinks(torrentPage)
        fileName    = self._getTorrentFileName(torrentPage)
        isVerified  = self._getIsTorrentVerified(torrentPage)

        #namedtuple("Torrent", "filename url magnet torrentFile torrentsite description seeds verified")
        torrent = Torrent(fileName, torrentLink, links.magnet, links.file, "bitsnoop", description, seeds, isVerified)
        return torrent

    def _getTorrentDescription(self, torrentPage):
        torrentHTMLParser = HTMLParserTagWithAttribute("meta", "name", "description", "content")
        torrentHTMLParser.feed(torrentPage)
        if torrentHTMLParser.data:
            return torrentHTMLParser.data[0]
        else:
            return None

    def _getTorrentSeeds(self, torrentPage):
        torrentHTMLParser = HTMLParserBetweenTags("span", "title", "Seeders")
        torrentHTMLParser.feed(torrentPage)
        if torrentHTMLParser.data:
            #locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )
            #seeds = locale.atoi(torrentHTMLParser.data[0])
            return torrentHTMLParser.data[0]
        else:
            return None

    def _getTorrentFileName(self, torrentPage):
        torrentHTMLParser = HTMLParserBetweenTags("i", "style", "color:#AAA;font-size:0.8em;font-weight:normal;")
        torrentHTMLParser.feed(torrentPage)
        if torrentHTMLParser.data:
            return torrentHTMLParser.data[0].lstrip("(").rstrip(")")
        else:
            return None

    def _getIsTorrentVerified(self, torrentPage):
        torrentHTMLParser = HTMLParserBetweenTags("span", "class", "good")
        torrentHTMLParser.feed(torrentPage)
        torrentVerified = False
        for tagContent in torrentHTMLParser.data:
            if tagContent == "Verified":
                torrentVerified = True
                break
        return torrentVerified

    def _getTorrentLinks(self, torrentPage):
        torrentHTMLParser = HTMLParserTag("a", "href")
        torrentHTMLParser.feed(torrentPage)
        magnet = filter(parsers.isMagnetLink, torrentHTMLParser.data)
        if magnet:
            magnet = min(magnet, key=len)
        else:
            magnet = None

        file = filter(parsers.isTorrentLink, torrentHTMLParser.data)
        if file:
            file = file[0]
        else:
            file = None
        Links = namedtuple('Links', "magnet file")
        links = Links(magnet, file)
        return links
