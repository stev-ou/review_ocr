# Stuent Review OCR
This web scraper performs the following steps/ routines:

1. Crawls the [OU evals website](http://www.ou.edu/provost/course-evaluation-data) using Beautiful Soup and downloads pdfs associated with each college and term code; PDFs saved into pdfs directory by College and Term Code
2. Splits the pdfs into individual pages, named according to page number, college, and term code (indicator for semester)
3. Parses each pdf into a defined schema using a multiprocessing function built around *Tika*, a python module for reading text from pdf, and regex
4. Uploads the scraped and parsed data into a MongoDB db, sorted such that each collection corresponds to a college

# USAGE:
`make run`
- This command will run both the scraper, parser, and uploader
-- OR - -

`python3 review_ocr db_name collection_name test_bool`
- This command will just scrape and parse, will not upload to MongoDB. For upload after, use `python3 mongo_writer.py db_name`

Note that entering "True" for test_bool will not web-crawl, it will only split the test file that I have provided (bus201410.pdf)
and add those documents to specified db under a collection called "joe_test" (will fail if collection does not exist)

Make sure to check the MongoDB cluster for your proposed db_name to make sure that you will not overwrite existing data; New scraped databases should be denoted with a new version (ocr_db_v1, ocr_db_v2, ...)


# TEST:
make test

test automatically cleans, "make clean" will not clean test folder

# CLEAN:
make clean

This will delete the pdfs folder, the results .txt files, and recreate them with the necessary subdirectories. **Be Careful!** as this command will delete any scraped results.

## Current Statistics (08/31/2019)
### Web Scraping
Currently, 72.8% of colleges, semesters, and years are successfully scraped (the corresponding pdfs are successfully downloaded). However, the real number should actually be higher, because some pdfs on the course evaluations page are poor links, and others are simply missing entries (eg. Summer 2013 doesnt exist for Gallogly College of Engineering). I expect our true accuracy/ability to get existing links from the page is ~85%.

### PDF Splitting
PDF Splitting into single pages is 100% efficient.

### Parsing
Parsing is currently successful for 93.0% of individual pdf pages. This number is also a lower-end estimate, as many pdfs contain blank pages and other content that is not parse-able.

### Overall
Overall efficiency is (~85% * 93%) = ~79% of data on the webpage is scraped into the pdf.

## Program RunTime
Program time depends upon machine and network, but recently on Macbook Pro 2013 crawling took ~30 minutes, splitting took ~1 minute, parsing took ~60 minutes, and uploading to MongoDB took ~ 8 hours, for a total time of 
