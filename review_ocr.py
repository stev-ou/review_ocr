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

CURRENT_YEARS = ["2013", "2014", "2015", "2016", "2017", "2018"]
SEMESTERS = ["Spring", "Summer", "Fall"]
 
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
				for semester in SEMESTERS:
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
						names.append(col + semester.lower() + year)
print(names)



"""
# This is going to be needed to get the enrollment totals for each course
enrollement_totals = {}



# THIS IS WHERE LOOP WILL START


# Need to make these 0 so we can average later, rest of the items will be added in loop
dbdict =   {
				"Avg Instructor Rating In Section": 0,
				"SD Instructor Rating In Section": 0,
				"Avg Department Rating": 0,
				"SD Department Rating": 0,
				"Course Enrollment": 0
				}
# used for averaging
dcount = 0
icount = 0

# Can't read from pdfs, so we need to convert each one to a jpg
with Img(filename='pdfs/page1.pdf', resolution=300) as img:
	img.compression_quality = 99
	# rotate image so it can be properly read, may or may not be necessary in batch run
	img.rotate(90)
	img.save(filename='pdfs/page1.jpg')

# Now that we have a jpg, we can read it into text -  just a massive wall of text
img = Image.open('pdfs/page1.jpg')
text = pytesseract.image_to_string(img)


for line in text.splitlines():
	print(line)
	dbdict["Term Code"] = 201410
	"""
"""
	TODO: Get Term Code
	Where are we getting:
		Instructor ID
		Dept Rank
		(SD) Course Rating - is this similar college?
	What do we do with multiple instructors?
	"""
"""
	if "College of" in line:
		tokens = line.split(" ")

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

	elif "INDIVIDUAL" in line :
		icount += 1
		tokens = line.split(" ")
		dbdict["Avg Instructor Rating In Section"] += float(tokens[1])
		dbdict["SD Instructor Rating In Section"] += float(tokens[3])

	elif "Total Enrollment" in line:
		tokens = line.split(" ")
		dbdict["Instructor Enrollment"] = int(tokens[2])

	elif "Course:" in line:
		tokens = line.split(" ")
		dbdict["course_uuid"] = tokens[1].lower() + tokens[2][:4]
		dbdict["Subject Code"] = tokens[1]
		dbdict["Course Number"] = int(tokens[2][:4])

	elif "Instructor:" in line:
		tokens = line.split(" ")
		dbdict["Instructor First Name"] = tokens[1]
		dbdict["Instructor Last Name"] = tokens[2]

	elif "Section Title" in line:
		dbdict["Course Title"] = line[15:]

	elif "DEPARTMENT" in line:
		dcount += 1
		tokens = line.split(" ")
		dbdict["Avg Department Rating"] += float(tokens[1])
		dbdict["SD Department Rating"] += float(tokens[3])

# Add this section's enrollment to enrollment totals
if dbdict["course_uuid"] in enrollement_totals.keys():
	enrollement_totals[dbdict["course_uuid"]] += dbdict["Instructor Enrollment"]
else:
	enrollement_totals[dbdict["course_uuid"]] = dbdict["Instructor Enrollment"]

dbdict["Queryable Course String"] = dbdict["Subject Code"].lower() + " " + str(dbdict["Course Number"]) + " " + dbdict["Course Title"].lower()

# Get averages
dbdict["Avg Instructor Rating In Section"] /= icount
dbdict["SD Instructor Rating In Section"] /= icount
dbdict["Avg Department Rating"] /= dcount
dbdict["SD Department Rating"] /= dcount



# EXIT LOOP


# TODO: Now we need to go back through each item to update total enrollment... is this necessary?

# TODO: Now we add to the database

pprint.pprint(dbdict)

"""
	