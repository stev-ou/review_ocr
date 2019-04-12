init:
	pip3 install -r requirements.txt

test: clean init
	rm -r test/split
	rm -r test/jpgs
	mkdir test/split
	mkdir test/jpgs
	python3 review_ocr.py test_db True

cleantest:
ifeq (,$(wildcard ./test/split/))
	mkdir test/split
endif
else
	rm -r test/split
	mkdir test/split
ifeq (,$(wildcard ./test/jpgs/))
	mkdir test/jpgs
endif
else
	rm -r test/jpgs
	mkdir test/jpgs

run: clean init
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