# review_ocr
Using Google's Tesseract OCR to extract data from public PDFs

MAKE SURE THAT TESSERACT IS IN YOUR SYSTEM'S PATH
	if on ubuntu - sudo apt-get install tesseract-ocr

ALSO MUST HAVE IMAGEMAGICK
	if on ubuntu - sudo apt-get install libmagickwand-dev

There may be a policy issue with ImageMagick that requires a workaround:
in /etc/ImageMagick-6/policy.xml make the following changes:
policy domain="coder" rights="read" pattern="PDF"

# USAGE:
make run

-- OR - -

python3 review_ocr db_name collection_name test_bool

entering "True" for test_bool will not web-crawl, it will only split the test file that I have provided (bus201410.pdf)
and add those documents to specified db under a collection called "joe_test" (will fail if collection does not exist)

# TEST:
make test

test automatically cleans, "make clean" will not clean test folder

# CLEAN:
make clean

this will simply delete the pdfs folder and recreate it with the necessary subdirectories