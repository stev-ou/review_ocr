try:
	from PIL import Image
except ImportError:
	import Image
import pytesseract
from wand.image import Image as Img
import pprint

# This is going to be needed to get the enrollment totals for each course
enrollement_totals = {}


"""
THIS IS WHERE LOOP WILL START
"""

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
	dbdict["Term Code"] = 201410
	dbdict["College Code"] = "BS?"
	"""
	TODO: Get Term Code
	Where are we getting:
		Instructor ID
		Dept Rank
		(SD) Course Rating - is this similar college?
	What do we do with multiple instructors?
		
	"""
	if "INDIVIDUAL" in line :
		icount += 1
		tokens = line.split(" ")
		dbdict["Avg Instructor Rating In Section"] += float(tokens[1])
		dbdict["SD Instructor Rating In Section"] += float(tokens[3])

	if "Total Enrollment" in line:
		tokens = line.split(" ")
		dbdict["Instructor Enrollment"] = int(tokens[2])

	if "Course:" in line:
		tokens = line.split(" ")
		dbdict["course_uuid"] = tokens[1].lower() + tokens[2][:4]
		dbdict["Subject Code"] = tokens[1]
		dbdict["Course Number"] = int(tokens[2][:4])

	if "Instructor:" in line:
		tokens = line.split(" ")
		dbdict["Instructor First Name"] = tokens[1]
		dbdict["Instructor Last Name"] = tokens[2]

	if "Section Title" in line:
		dbdict["Course Title"] = line[15:]

	if "DEPARTMENT" in line:
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


"""
EXIT LOOP
"""

# TODO: Now we need to go back through each item to update total enrollment... is this necessary?

# TODO: Now we add to the database

pprint.pprint(dbdict)


	