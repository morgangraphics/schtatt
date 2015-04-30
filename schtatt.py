import json
import argparse
from lxml import html
import requests
import csv
import gettext
import locale
import re
from datetime import datetime

def init_localization():
  '''prepare l10n'''
  locale.setlocale(locale.LC_ALL, '') # use user's preferred locale
  # take first two characters of country code
  loc = locale.getlocale()
  filename = "po/messages_%s.mo" % locale.getlocale()[0][0:2]
 
  try:
    #logging.debug( "Opening message file %s for locale %s", filename, loc[0] )
    trans = gettext.GNUTranslations(open( filename, "rb" ) )
  except IOError:
    #logging.debug( "Locale not found. Using default messages" )
    trans = gettext.NullTranslations()
 
  trans.install()
 
if __name__ == '__main__':
  init_localization()

# Open the config file - it's used in multiple spots
with open('config.json') as f:
    config = json.load(f)

#Set up our local variables - _() is the localization function
rows = []
dates = []		#List that we can sort on for comparison to the Dictonary that is generated
row = {}
srtd = []

statementMsg = _('Found Statement, Begin parsing...')
tripTableMsg = _('Found Trip tables, grabbing data...')
sortingMsg = _('Sorting Data by Date')
toJSONMsg = _('Creating JSON file')
surge = _("Surge")


#Parser information
parser = argparse.ArgumentParser(description='Output either JSON (default) or CSV file')

parser.add_argument('--json', nargs='?', default="json", help='create a JSON file - default')
parser.add_argument('--csv', nargs='?', default="json", help='create a csv file')
#parser.add_argument('--sum', dest='accumulate', action='store_const', const=sum, default=max, help='sum the integers (default: find the max)')

args = parser.parse_args()

#print args.json
#exit()


#JSON
def toJSON(rows):
	with open('data.json', 'w') as outfile:
		json.dump(rows, outfile, sort_keys=True, indent=4, separators=(',', ': '))

#CSV
def toCSV(rows):
	with open('data.csv', 'w') as outfile:
		wr = csv.writer(output, quoting=csv.QUOTE_ALL)
    	#rows.append(["Date", "UID", "Fare", "Time", "Mileage", "Surge Multiplier", "Additional Charges", "Rider Fee", 
	#"Rider Fee Deduction", "Uber Fee Deduction", "Earnings", "Week Of", "Trip Coords"])
    	#print("Writing Data to CSV file")
		#	rows.append([timestamp, weekOf, tripID, tripFare, tripTime, mileage, tripSurgeMultiplier, 
		#		tripAdditionalCharges, riderFee, riderFeeDeduction, uberFeeDeduction, earnings, tripsMapCoords])

    	#wr.writerows(rows)

#Login function attempts the login for the first time to retrieve the CSRFTOKEN, sets the session, then does it again
def login():
	#Start session recording
	loginURL = config.get("loginURL")
	s = requests.session()
	r = s.get(loginURL)

	#Parse Login Page Tree
	loginTree = html.fromstring(r.text)

	#Find the _csrf_token needed to appear Legit
	CSRFTOKEN = loginTree.xpath('//input[@name="_csrf_token"]/@value')[0]

	#Data needed for form Submission
	payload = {
	 	'email': config.get("email"), 
	 	'password': config.get("password"),
	 	'_csrf_token': CSRFTOKEN
	}

	s.post(loginURL, data=payload)

	return s

def tripDetails(tripURL):
	#Going to need to grab the Trip Data
	trip = {}

 	tripsPage = session.get(config.get("baseURL") + tripURL)
	tripsText = html.fromstring(tripsPage.text)

	tripsMapObj = tripsText.xpath('//script[contains(text(), "p2.map_trip")]/text()')
	tripsMapCoords = "" if len(tripsMapObj) == 0 else tripsMapObj[0].strip().replace("p2.map_trip", "").translate(None, '();')

	miles = tripsText.xpath('//strong[contains(text(), "'+_("Miles")+'")]/../following-sibling::div[1]/text()')[0]

	trip["tripCoords"] = tripsMapCoords
	trip["startCoords"] = re.findall('\[({.+?})', tripsMapCoords)
	trip["endCoords"] = re.findall('{(?=[^{]*$).+}', tripsMapCoords)
	trip["miles"] = miles

	return trip


#login to start session
session = login()

#Parse Satement Page Tree
statementsPage = session.get(config.get("baseURL") + '/statements/')
statementText = html.fromstring(statementsPage.text)

#Grab the HTML statement links - They have WAY more detail than the CSV version
statements = statementText.xpath('//a[text()="HTML"]')

#============================ TESTING ========================
cnt = 0
#============================ TESTING ========================

#Grab all the data
for detail in statements:
	print(statementMsg)

	#============================ TESTING ========================
	# if cnt > 0: 
	# 	break

	# cnt = cnt + 1
	#============================ TESTING ========================

	#Week Of - This is kind of dangerous but there is no real path to get this at this point
	weekOf = statementText.xpath('//table[2]/tbody/tr/td[2]/text()')

	url = detail.xpath('./@href')[0]

	#Parse Satement Page Tree
	statementsDetailPage = session.get(config.get("baseURL") + url)
	statementDetailText = html.fromstring(statementsDetailPage.text)

	#Grab all the trip related tables
	tripTables = statementDetailText.xpath('//table[contains(@class, "trips")]')

	
	#Iterate over all the Tables
	for table in tripTables:
		print(tripTableMsg)
		
		#Grab the date
		date = table.xpath(".//th/time/text()")
		date = "" if len(date) == 0 else date[0]
		
		#Start building the row Dictionary
		row[date] = []

		dates.append(date)


		#grab all the TR's we need to parse
		trs = table.xpath('.//tbody/tr')

		#Iterate over all the TR's and grab the info in the TD's directly
		for tr in trs: 
			
			rowData = {}

		 	#Grab all the TD's we need to parse
		 	td = tr.xpath('.//td')

		 	# Have to test for the number of TD's because of the Surge Multiplier & Information Hidden toggles
		 	# if there are only two, skip and keep going
		 	if len(td) == 2:
		 		continue

	 		#0 Dislays information Detail dropdown arrow

		 	#1 Time - There are two times associated in this TD - One is hidden and the other has a class of hidden but shown
		 	tripTime = td[1].xpath('.//a/time/text()')
		 	tripTime = "" if len(tripTime) == 0 else tripTime[0]
		 	rowData["tripTime"] = tripTime

		 	#WARNING - This is hidden by default and may be removed in the future
		 	timestamp = td[1].xpath('.//dl[1][@class = "trip-information"]//dd[1]/text()')
		 	timestamp = "" if len(timestamp) == 0 else timestamp[0]
		 	rowData["timestamp"] = timestamp
		 	
		 	#2 Trip UID/URL
		 	tripID = td[2].xpath('.//a/text()')
		 	tripID = "" if len(tripID) == 0 else tripID[0]
		 	rowData["tripID"] = tripID

		 	tripURL = td[2].xpath('.//a/@href')
		 	tripURL = "" if len(tripURL) == 0 else tripURL[0]
		 	rowData["tripURL"] = tripURL

		 	#Opens up the Details page and extracts GPS Coords
			tripsMap = tripDetails(tripURL)

			rowData["tripMapCoords"] = tripsMap['tripCoords']
			rowData["startCoords"] = tripsMap['startCoords']
			rowData["endCoords"] = tripsMap['endCoords']

			rowData["mileage"] = tripsMap['miles']

		 	#3 unused
		 	#td[3].xpath('')
			
		 	#4 Fare
		 	tripFare = td[4].xpath('.//text()')
		 	tripFare = "" if len(tripFare) == 0 else tripFare[0].replace("(", "-").replace(")","")
		 	rowData["tripFare"] = tripFare

			#5 Surge
		 	tripSurge = td[5].xpath('.//text()')
		 	tripSurgeText = tr.xpath('./following-sibling::tr//li[contains(text(), "'+surge+'")]/text()')
		 	
		 	tripSurgeMultiplier = "" if len(tripSurgeText) == 0 else tripSurgeText[0].strip('xSurgePricing: ')
		 	rowData["tripSurgeMultiplier"] = tripSurgeMultiplier

			#6 Surcharges & Tolls
			tripAdditionalCharges = td[6].xpath('.//text()')
			tripAdditionalCharges = "" if len(tripAdditionalCharges) == 0 else tripAdditionalCharges[0]
			rowData["tripAdditionalCharges"] = tripAdditionalCharges

			#7 Rider Fee
			riderFee = td[7].xpath('.//text()')
			riderFee = "" if len(riderFee) == 0 else riderFee[0]
			rowData["riderFee"] = riderFee

			#8 rider Fee Deduction
			riderFeeDeduction = td[8].xpath('.//text()')
			riderFeeDeduction = "" if len(riderFeeDeduction) == 0 else riderFeeDeduction[0].replace("(", "-").replace(")","")
			rowData["riderFeeDeduction"] = riderFeeDeduction
			
			#9 uber Fee Deduction 
			uberFeeDeduction = td[9].xpath('.//text()')
			uberFeeDeduction = "" if len(uberFeeDeduction) == 0 else uberFeeDeduction[0].replace("(", "-").replace(")","")
			rowData["uberFeeDeduction"] = uberFeeDeduction

			#10 Total Earnings
			earnings = td[10].xpath('.//text()')
			earnings = "" if len(earnings) == 0 else earnings[0]
			rowData["earnings"] = earnings

			row[date].append(rowData)


		#rows.append(row)


	
		#print rows

			# print date
			# print timestamp
			# print tripTime
			# print tripID
			# print tripURL
			# print tripsMapCoords
			# print mileage
			# print tripFare
			# print tripSurgeMultiplier
			# print tripAdditionalCharges
			# print riderFee
			# print riderFeeDeduction
			# print uberFeeDeduction
			# print earnings

srtedD = sorted(dates, key=lambda date: datetime.strptime(date, "%B %d, %Y"))


print(sortingMsg)
for day in srtedD:
	if day in row:
		srtd.append({day: row[day]})
		


if args.json is None or args.json == 'json':
	print(toJSONMsg)
	toJSON(srtd)

			




