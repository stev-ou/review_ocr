try:
	from PIL import Image
except ImportError:
	import Image
import pytesseract
from wand.image import Image as Img
import pprint
import os
from PyPDF2 import PdfFileReader, PdfFileWriter
from bs4 import BeautifulSoup
import requests
import urllib
from pymongo import MongoClient

client = MongoClient("mongodb+srv://zach:G8GqPsUgP6b9VUvc"
        "@cluster0-svcn3.gcp.mongodb.net/test?retryWrites=true")
db = client['test_db']
collection = db['joe_test']

CURRENT_YEARS = ["2013", "2014", "2015", "2016", "2017", "2018"]
SEMESTERS = {"Spring": 20, "Summer": 30, "Fall": 10}
 
def pdf_splitter(path):
	fname = os.path.splitext(os.path.basename(path))[0]
	pnum = 0
	pdf = PdfFileReader(path)
	for page in range(pdf.getNumPages()):
		pdf_writer = PdfFileWriter()
		pdf_writer.addPage(pdf.getPage(page))
 
		output_filename = '{}_page_{}.pdf'.format(
			fname, page+1)
 
		with open(output_filename, 'wb') as out:
			pdf_writer.write(out)

		pnum += 1
		print('Created: {}'.format(output_filename))
	return pnum

"""
urls = []
names = []
url = "http://www.ou.edu/provost/course-evaluation-data"
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



						urls.append(full_url)
						names.append(col + year + SEMESTERS[semester])
						continue
"""

directory = os.fsencode('pdfs/')

for file in os.listdir(directory):
	f = os.fsdecode(file)
	if f.endswith(".pdf"):
		dbdict =   {}
		instructor2 = {} # In case there is a second instructor

		# Can't read from pdfs, so we need to convert each one to a jpg
		with Img(filename='pdfs/' + f, resolution=300) as img:
			img.compression_quality = 99
			# rotate image so it can be properly read, may or may not be necessary in batch run
			img.rotate(90)
			img.save(filename='pdfs/jpgs/' + f.rstrip(".pdf") + '.jpg')

		# Now that we have a jpg, we can read it into text -  just a massive wall of text
		img = Image.open('pdfs/jpgs/' + f.rstrip(".pdf") + '.jpg')
		text = pytesseract.image_to_string(img)

		# list of the dbdictionaries that will be added
		db_objects = []

		lines = text.splitlines()
		i = 0
		while i < len(lines):
			#print(lines[i])
			dbdict["Term Code"] = 201410
			"""
			TODO: Get Term Code
			Where are we getting:
				Instructor ID - lets just hash
				Dept Rank
				(SD) Course Rating - is this similar college?
			What do we do with multiple instructors?
			"""
			
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
					tokens = lines[i].split(" ")
					if "INDIVIDUAL" in lines[i]:
						db_objects[x]["Mean"] = float(tokens[1])
						db_objects[x]["Median"] = int(tokens[2])
						db_objects[x]["Standard Deviation"] = float(tokens[3])
						db_objects[x]["Percent Rank - Department"] = float(tokens[-1])
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
					i += 1

			elif "Total Enrollment" in lines[i]:
				tokens = lines[i].split(" ")
				dbdict["Instructor Enrollment"] = int(tokens[2])

			elif "Course:" in lines[i]:
				tokens = lines[i].split(" ")
				dbdict["course_uuid"] = tokens[1].lower() + tokens[2][:4]
				dbdict["Subject Code"] = tokens[1]
				dbdict["Course Number"] = int(tokens[2][:4])
				dbdict["Section Number"] = int(tokens[2][-3:])

			elif "Instructors:" in lines[i]:
				tokens = lines[i].split(" ")
				dbdict["Instructor First Name"] = tokens[1]
				dbdict["Instructor Last Name"] = tokens[2]
				instructor2["Instructor First Name"] = tokens[4]
				instructor2["Instructor Last Name"] = tokens[5]

			elif "Instructor:" in lines[i]:
				tokens = lines[i].split(" ")
				dbdict["Instructor First Name"] = tokens[1]
				dbdict["Instructor Last Name"] = tokens[2]

			elif "Section Title" in lines[i]:
				dbdict["Section Title"] = lines[i][15:]

			i += 1

		for i in range(0, len(db_objects)):
			db_objects[i]["Term Code"] = int(f.rstrip(".pdf")[-6:])
			db_objects[i]["College Code"] = dbdict["College Code"]
			db_objects[i]["Subject Code"] = dbdict["Subject Code"]
			db_objects[i]["Course Number"] = dbdict["Course Number"]
			db_objects[i]["Section Number"] = dbdict["Section Number"]
			db_objects[i]["Section Title"] = dbdict["Section Title"]
			db_objects[i]["Instructor First Name"] = dbdict["Instructor First Name"]
			db_objects[i]["Instructor Last Name"] = dbdict["Instructor Last Name"]
			collection.insert_one(db_objects[i])
			# Instructor ID

		# If there is an Instructor 2, just change the name and ID
		if instructor2:
			for i in range(0, len(db_objects)):
				# Instructor ID
				db_objects[i]["Instructor First Name"] = instructor2["Instructor First Name"]
				db_objects[i]["Instructor Last Name"] = instructor2["Instructor Last Name"]
				# Needed so that we arent trying to add a duplicate object_id
				db_objects[i].pop('_id', None)
				collection.insert_one(db_objects[i])



# EXIT LOOP

#pprint.pprint(dbdict)


	