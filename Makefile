init:
	pip install -r requirements.txt

test:
	python3 review_ocr.py test_db True
	rm -r test/split
	rm -r test/jpgs
	mkdir test/split
	mkdir test/jpgs

run:
	init
	python3 review_ocr.py reviews-db False
	clean

clean:
	rm -r pdfs/
	mkdir pdfs/
	mkdir pdfs/split/
	mkdir pdfs/jpgs/

.PHONY: init test