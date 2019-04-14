init:
	pip3 install -r requirements.txt

test: init
	rm -r test/split
	rm -r test/jpgs
	mkdir test/split
	mkdir test/jpgs
	python3 review_ocr.py test_db True

cleantest:
ifeq (,$(wildcard ./test/split/))
	mkdir test/split
endif

ifeq (,$(wildcard ./test/jpgs/))
	mkdir test/jpgs
endif
	rm -r test/split
	mkdir test/split
	rm -r test/jpgs
	mkdir test/jpgs

run: clean init
	python3 review_ocr.py ocr_db False
	

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