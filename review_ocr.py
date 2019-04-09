try:
	from PIL import Image
except ImportError:
	import Image
import pytesseract
from wand.image import Image as Img

with Img(filename='pdfs/page1.pdf', resolution=300) as img:
	img.compression_quality = 99
	# rotate image so it can be properly read, may or may not be necessary in batch run
	img.rotate(90)
	img.save(filename='pdfs/page1.jpg')

img = Image.open('pdfs/page1.jpg')

text = pytesseract.image_to_string(img)

dbdict =   {"Avg Instructor Rating In Section": 0}
deptcount = 0
icount = 0

for line in text.splitlines():
	print(line)
	dbdict["Term Code"] = 201410
	dbdict["College Code"] = "BS?"
	"""
	TODO: Get Term Code
	TODO:  Get College Code
	"""
	if "INDIVIDUAL" in line :
		icount += 1
		tokens = line.split(" ")
		dbdict["Avg Instructor Rating In Section"] += float(tokens[1])

	if "Total Enrollment" in line:
		tokens = line.split(" ")
		dbdict["Instructor Enrollment"] = int(tokens[2])

	if "Course:" in line:
		tokens = line.split(" ")
		dbdict["course_uuid"] = tokens[1].lower() + tokens[2][:4]

	if "Instructor:" in line:
		tokens = line.split(" ")
		dbdict["Instructor First Name"] = tokens[1]
		dbdict["Instructor Last Name"] = tokens[2]

	if "Section Title" in line:
		dbdict["Course Title"] = line[15:]







	