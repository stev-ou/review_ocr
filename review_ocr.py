try:
	from PIL import Image
except ImportError:
	import Image
import pytesseract
from wand.image import Image as Img

with Img(filename='pdfs/page1.pdf', resolution=300) as img:
	img.compression_quality = 99
	# rotate image so it can be properly read
	img.rotate(90)
	img.save(filename='pdfs/page1.jpg')

img = Image.open('pdfs/page1.jpg')

text = pytesseract.image_to_string(img)