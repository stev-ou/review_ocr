init:
	pip3 install -r requirements.txt

test: clean init
ifeq (,$(wildcard ./test/split/))
	mkdir test/split
endif
	rm -r test/split
	mkdir test/split
	python3 review_ocr.py test_db True

run: clean init
	python3 review_ocr.py ocr_db_v1 False
	python3 evaluate.py
	python3 mongo_writer.py ocr_db_v1	

clean:
ifeq (,$(wildcard ./pdfs/))
	mkdir pdfs/
	mkdir pdfs/split/
endif

ifeq (,$(wildcard successful_tests.txt))
	touch successful_tests.txt
endif

ifeq (,$(wildcard failed_tests.txt))
	touch failed_tests.txt
endif

	rm successful_tests.txt
	rm failed_tests.txt
	rm -r pdfs/
	mkdir pdfs/
	mkdir pdfs/split/
	mkdir pdfs/txts/

.PHONY: init test