init:
	pip3 install -r requirements.txt

test: init
	rm -r test/split
	rm -r test/jpgs
	mkdir test/split
	mkdir test/jpgs
	python3 review_ocr.py test_db True

cleantest:
	rm -r test/split
	rm -r test/jpgs
	mkdir test/split
	mkdir test/jpgs

run: init
	clean
	python3 review_ocr.py reviews-db False
	clean

clean:
ifeq (,$(wildcard ./pdfs/))
	mkdir pdfs/
	mkdir pdfs/split/
	mkdir pdfs/jpgs/
endif
	rm -r pdfs/
	mkdir pdfs/
	mkdir pdfs/split/
	mkdir pdfs/jpgs/

.PHONY: init test