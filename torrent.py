#!/usr/bin/python
from torrentfinders import BitSnoopTorrentFinder
import transmissionrpc
import sys, getopt, os
import ConfigParser

def main(argv):
	config = ConfigParser.RawConfigParser()
	config.read('torrent.cfg')
	hostname = config.get("Server", "host")
	password = config.get("Server", "password")

	isPaused, grep, isVerifiedOnly = False, None, True
	try:
		opts, args = getopt.getopt(argv,"hs:p:",["help=", "search=", "host=", "paused", "grep=", "verified=", "password="])
	except getopt.GetoptError:
		showHelpUse()
		sys.exit(2)
	for opt, arg in opts:
		if opt in [ "-h", "--help" ]:
			showHelpUse()
			sys.exit()
		elif opt in [ "-s", "--search" ]:
			searchTerm = arg
		elif opt in [ "--host" ]:
			hostname = arg
		elif opt in [ "--paused" ]:
			isPaused = True
		elif opt in [ "--grep" ]:
			grep = arg.lower()
		elif opt in [ "-p", "--password" ]:
			password = arg
		elif opt in [ "--verified" ]:
			isVerifiedOnly = parseBooleanArgument(arg)

	try:
		searchTerm
	except NameError:
		searchTerm = sys.argv[1]

	torrentFinder = BitSnoopTorrentFinder()
	torrentFinder.retrieveSearchResults(searchTerm)

	counter = 0
	torrents = []
	for torrent in torrentFinder:
		if grep:
			try:
				if not grep in torrent.filename.lower():
					continue
			except AttributeError:
				continue
		if isVerifiedOnly:
			try:
				if not torrent.verified:
					continue
			except AttributeError:
				continue
		torrents.append(torrent)
		print counter
		print torrent.filename
		print "Seeds", torrent.seeds
		print torrent.description
		print "-" * 20
		counter = counter + 1
		if (counter == 3):
			break

	if counter > 0:
		print "Select which torrent:"
		n = int(raw_input())
		transClient = transmissionrpc.Client(hostname, user='root', password=password, port=9091)
		transClient.add_torrent(torrents[n].magnet, None, paused=isPaused)

def showHelpUse():
	COLUMN_WIDTH = 25
	scriptName = os.path.basename(__file__)
	print scriptName, "-s <searchterm> [OPTION]"
	print ""
	print " " * 2, "-h, --help".ljust(COLUMN_WIDTH),          "show this help page"
	print " " * 2, "--grep".ljust(COLUMN_WIDTH),              "only torrents with grep in the filename"
	print " " * (COLUMN_WIDTH + 3),                           "case insensitive"
	print " " * 2, "--password".ljust(COLUMN_WIDTH),          "password for transmission"
	print " " * 2, "--verified [yes|no]".ljust(COLUMN_WIDTH), "only verified torrents"
	print " " * 2, "--paused".ljust(COLUMN_WIDTH),            "don't start the torrent after adding"
	print " " * 2, "--host".ljust(COLUMN_WIDTH),              "hostname of the transmission server"

def parseBooleanArgument(arg):
	if arg.lower() in ("1", "true", "yes"):
		result = True
	elif arg.lower() in ("0", "false", "no"):
		result = False
	else:
		showHelpUse()
		sys.exit(2)
	return result

if __name__ == "__main__":
   main(sys.argv[1:])

