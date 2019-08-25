init:
	pip3 install -r requirements.txt

test: clean init
	rm -r test/split
	mkdir test/split
	python3 review_ocr.py test_db True

cleantest:
ifeq (,$(wildcard ./test/split/))
	mkdir test/split
endif
	rm -r test/split
	mkdir test/split

run: clean init
	python3 review_ocr.py ocr_db_v1 False
	

clean:
ifeq (,$(wildcard ./pdfs/))
	mkdir pdfs/
	mkdir pdfs/split/
endif
	rm -r pdfs/
	mkdir pdfs/
	mkdir pdfs/split/
	mkdir pdfs/txts/
.PHONY: init test
