import os
import sys
import urllib.request
import urllib.error

try:
	from PIL import Image
except ImportError:
	import Image
import pytesseract
from wand.image import Image as Img
import pprint
from PyPDF2 import PdfFileReader, PdfFileWriter
from bs4 import BeautifulSoup
import requests
from pymongo import MongoClient

db_name = sys.argv[1]

client = MongoClient("mongodb+srv://zach:G8GqPsUgP6b9VUvc"
        "@cluster0-svcn3.gcp.mongodb.net/test?retryWrites=true")
db = client[db_name]

CURRENT_YEARS = ["2013", "2014", "2015", "2016", "2017", "2018"]
SEMESTERS = {"Spring": 20, "Summer": 30, "Fall": 10}
BUG_CITY = ["_", "-", '—', "=", '__', "--", "==", '_—', '——'] # See line 217...


def pdf_splitter(path, col, term):
	# This will take a pdf and split it into individual pages, saving them to directory pdfs/split
	fname = os.path.splitext(os.path.basename(path))[0]
	pnum = 0
	pdf = PdfFileReader(path)
	for page in range(pdf.getNumPages()):
		pdf_writer = PdfFileWriter()
		pdf_writer.addPage(pdf.getPage(page))
 
		output_filename = str(page+1) + col + term + ".pdf"
 		
		try:
			with open(path.split("/", 1)[0] + "split/" + output_filename, 'xb') as out:
				pdf_writer.write(out)
				print('Created: {}'.format(output_filename))
		except FileExistsError:
			print(output_filename + " ALREADY EXISTS!")

		pnum += 1
		
	return pnum


def web_crawl(url):
	# This function will crawl the given url, and download specific pdfs
	urls = []
	names = []
	page = requests.get(url, timeout=5)
	soup = BeautifulSoup(page.text, "html.parser")
	for i, link in enumerate(soup.findAll('a')):
		full_url = url + link.get('href')
		if full_url.endswith('.pdf'):
			sel = soup.select('a')[i].attrs['href']
			# Now to aptly name these files... finna get ugly here
			for year in CURRENT_YEARS:
				if year in sel:
					for semester in SEMESTERS.keys():
						if semester in sel:

							if "Sciences" in sel:
								col = "artsn"

							elif "Architecture" in sel:
								col = "arc"

							elif "Atmospheric" in sel:
								col = "geo"

							# Aviation
							elif "Business" in sel:
								col = "bus"

							elif "Energy" in sel:
								col = "nrg"

							elif "Education" in sel:
								col = "edu"

							elif "Engineering" in sel:
								col = "engr"

							elif "Fine" in sel:
								col = "farts" #hahaha

							elif "International" in sel:
								col = "ints"

							elif "Journalism" in sel:
								col = "jrnl"

							elif "Professional" in sel:
								col = "prof"
							else:
								continue


							# We are only saving the urls/names of current years and desired colleges
							# Gotta git rid of some unnecessary characters in the url
							pdf_url = full_url[:18] + full_url[49:]
							if pdf_url not in urls:
								urls.append(pdf_url)
								names.append(str(col) + str(year) + str(SEMESTERS[semester]))
								print("Adding %s to Write Queue..." % (str(col) + str(year) + str(SEMESTERS[semester])))
								print(pdf_url + "\n")
							continue

	names_urls = zip(names, urls)
	# Now we "download" the pdfs by writing to pdf files
	for name, url in names_urls:
		try:
			print("Attempting to open: " + url)
			resp = urllib.request.urlopen(url)

			try:
				pdf = open("pdfs/" + name + ".pdf", 'xb')
				print("Writing " + name + "\n")
				pdf.write(resp.read())
				pdf.close()
			except FileExistsError:
				print(name + " ALREADY EXISTS IN DIRECTORY!!\n")

		except urllib.error.HTTPError:
			print("404 Error on this page... This PDF may not exist yet.\n")

	return names_urls
		



def parse_files(directory):
	for file in os.listdir(directory):
		f = os.fsdecode(file)
		#f = '136bus201410.pdf'
		if f.endswith(".pdf"):
			print("Running: " + f)
			dbdict =   {}
			instructor2 = {} # In case there is a second instructor

			# Can't read from pdfs, so we need to convert each one to a jpg
			with Img(filename='pdfs/split/' + f, resolution=300) as img:
				img.compression_quality = 99
				img.save(filename='pdfs/jpgs/' + f.rstrip(".pdf") + '.jpg')

			# Now that we have a jpg, we can read it into text -  just a massive wall of text
			img = Image.open('pdfs/jpgs/' + f.rstrip(".pdf") + '.jpg')
			text = pytesseract.image_to_string(img)

			# list of the dbdictionaries that will be added to the DataBase
			db_objects = []

			lines = text.splitlines()
			i = 0
			while i < len(lines):			
				if "Question" in lines[i]:
					i += 1
					while "Response" not in lines[i]:
						if len(lines[i]) >= 3:
							tokens = lines[i].split(" ")
							i += 1
							# This is to handle wrapping text
							if len(lines[i]) >= 3:
								lines[i-1] += " " + lines[i]
							db_objects.append({"Question": lines[i-1][3:].lstrip(" "), 
												"Question Number": int(tokens[0].strip('.'))})
							i += 1
						else:
							i += 1
				else:
					i += 1
			
			# Need to iterate twice bc sometimes it reads out of order
			i = 0
			while i < len(lines):
				#print(lines[i])
				if "College of" in lines[i]:
					tokens = lines[i].split(" ")

					if tokens[2] == "Business":
						dbdict["College Code"] = "BUS"

					elif tokens[2] == "Architecture":
						dbdict["College Code"] = "ARC"

					elif tokens[2] == "Arts":
						dbdict["College Code"] = "ARTSN"

					elif tokens[2] == "Atmospheric":
						dbdict["College Code"] = "GEO"

					#Aviation

					elif tokens[2] == "Earth":
						dbdict["College Code"] = "NRG"

					elif tokens[2] == "Education":
						dbdict["College Code"] = "EDU"

					elif tokens[2] == "Engineering":
						dbdict["College Code"] = "ENGR"

					elif tokens[2] == "Fine":
						dbdict["College Code"] = "FARTS" # haha

					# Honors College

					elif tokens[2] == "International":
						dbdict["College Code"] = "INTS"

					elif tokens[2] == "Journalism":
						dbdict["College Code"] = "JRNL"

					elif tokens[2] == "Professional":
						dbdict["College Code"] = "PROF"

					#University College

					#Center for Independent and Distant Learning

					#Expository Writing

					#ROTC

				elif "Deviation" in lines[i]:
					i += 1
					# x is to keep track of which db object we are adding data to
					x = 0
					while x < len(db_objects):
						if len(lines[i]) > 2:
							tokens = lines[i].split(" ")

							# Welcome to Bug City
							# Weird OCR bug here, its seeing something that I dont on random files
							for n in range(0, len(tokens) - 1):
								if tokens[n] in BUG_CITY:
									tokens.pop(n)
								# Dude I dont even know...
								if tokens[n] == 'FE':
									tokens[n] = 5

							try:
								if "INDIVIDUAL" in lines[i]:
									db_objects[x]["Mean"] = float(tokens[1])
									db_objects[x]["Median"] = int(tokens[2])
									db_objects[x]["Standard Deviation"] = float(tokens[3])
									db_objects[x]["Percent Rank - Department"] = float(tokens[-2])
									db_objects[x]["Percent Rank - College"] = float(tokens[-1])
								elif "DEPARTMENT" in lines[i]:
									db_objects[x]["Department Mean"] = float(tokens[1])
									db_objects[x]["Department Median"] = int(tokens[2])
									db_objects[x]["Department Standard Deviation"] = float(tokens[3])
								elif "SIMILAR" in lines[i]:
									db_objects[x]["Similar College Mean"] = float(tokens[1])
									db_objects[x]["Similar College Median"] = int(tokens[2])
								elif "COLLEGE" in lines[i]:
									db_objects[x]["College Mean"] = float(tokens[1])
									db_objects[x]["College Median"] = int(tokens[2])
									x += 1
							except ValueError:
								print("Bad Data! Going to need manual input for this document...")
								print(tokens)
						i += 1

				elif "Total Enrollment" in lines[i]:
					tokens = lines[i].split(" ")
					for n in range(0, len(tokens)):
						if 'Enrollment' in tokens[n]:
							dbdict["Instructor Enrollment"] = int(tokens[n+1])

				elif "Course:" in lines[i]:
					tokens = lines[i].split(" ")
					dbdict["course_uuid"] = tokens[1].lower() + tokens[2][:4]
					dbdict["Subject Code"] = tokens[1]
					# Some Subject Codes are separated by spaces
					try:
						dbdict["Course Number"] = int(tokens[2][:4])
						dbdict["Section Number"] = int(tokens[2][-3:])
					except ValueError:
						dbdict["Subject Code"] += tokens[2]
						dbdict["Course Number"] = int(tokens[3][:4])
						dbdict["Section Number"] = int(tokens[3][-3:])
					

				elif "Instructors:" in lines[i] or "instructors" in lines[i]:
					tokens = lines[i].split(" ")
					dbdict["Instructor First Name"] = tokens[1].title()
					dbdict["Instructor Last Name"] = tokens[2].title()
					instructor2["Instructor First Name"] = tokens[4].title()
					instructor2["Instructor Last Name"] = tokens[5].title()

				elif "Instructor:" in lines[i] or "instructor" in lines[i]:
					tokens = lines[i].split(" ")
					dbdict["Instructor First Name"] = tokens[1].title()
					dbdict["Instructor Last Name"] = tokens[2].title()
					if len(tokens) > 3:
						dbdict["Instructor Last Name"] += tokens[3].title()
				
				elif "Section Title" in lines[i]:
					dbdict["Section Title"] = lines[i][15:]

				i += 1

			# find if we are testing or not, use appropriate collection
			if bool(sys.argv[2]) == True
				collection_name = "test_joe"
			else:
				collection_name = dbdict["College Code"].upper()

			collection = db[collection_name]

			for i in range(0, len(db_objects)):
				db_objects[i]["Term Code"] = int(f.rstrip(".pdf")[-6:])
				db_objects[i]["College Code"] = dbdict["College Code"]
				db_objects[i]["Subject Code"] = dbdict["Subject Code"]
				db_objects[i]["Course Number"] = dbdict["Course Number"]
				db_objects[i]["Section Number"] = dbdict["Section Number"]
				db_objects[i]["Section Title"] = dbdict["Section Title"]
				db_objects[i]["Instructor First Name"] = dbdict["Instructor First Name"]
				db_objects[i]["Instructor Last Name"] = dbdict["Instructor Last Name"]
				find_id = collection.find_one({'Instructor First Name': dbdict["Instructor First Name"],
												'Instructor Last Name': dbdict["Instructor Last Name"]})
				# If this professor already has an ID
				if find_id != None:
					db_objects[i]["Instructor ID"] = find_id["Instructor ID"]
				# Else just use python's hash function to make one for them, should be sufficiently unique
				else:
					db_objects[i]["Instructor ID"] = hash(dbdict["Instructor First Name"] + dbdict["Instructor Last Name"])
				collection.insert_one(db_objects[i])

			# If there is an Instructor 2, just change the name and ID
			if instructor2:
				for i in range(0, len(db_objects)):
					# Instructor ID
					db_objects[i]["Instructor First Name"] = instructor2["Instructor First Name"]
					db_objects[i]["Instructor Last Name"] = instructor2["Instructor Last Name"]
					# Needed so that we arent trying to add a duplicate object_id
					db_objects[i].pop('_id', None)
					find_id = collection.find_one({'Instructor First Name': dbdict["Instructor First Name"],
													'Instructor Last Name': dbdict["Instructor Last Name"]})
					# If this professor already has an ID
					if find_id != None:
						db_objects[i]["Instructor ID"] = find_id["Instructor ID"]
					# Else just use python's hash function to make one for them, should be sufficiently unique
					else:
						db_objects[i]["Instructor ID"] = hash(dbdict["Instructor First Name"] + dbdict["Instructor Last Name"])
					collection.insert_one(db_objects[i])

if __name__ == '__main__':

	if len(sys.argv) < 3 or len(sys.argv) > 3:
		print("USAGE: review_ocr %s %s" % "db_name", "test_bool")

	if bool(argv[1]) == True:
		pdf_splitter("test/bus201410.pdf", name[:-6], name[-6:])
		directory = os.fsencode('test/split/')
		parse_files(directory)
		exit(1)

	else:

		url = "http://www.ou.edu/provost/course-evaluation-data"

		names_urls = web_crawl(url)

		for name, url in names_urls:
			pdf_splitter("pdfs/" + name + ".pdf", name[:-6], name[-6:])

		directory = os.fsencode('pdfs/split/')
		parse_files(directory)
		exit(1)
