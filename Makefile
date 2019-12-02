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
	python3 mongo_writer.py ocr_db_v1	

clean:
ifeq (,$(wildcard ./pdfs/))
	mkdir pdfs/
	mkdir pdfs/split/
endif
	touch crawling_evaluation.txt
	touch failed_tests.txt
	touch successful_tests.txt
	touch ForkPoolWorker-1.txt ForkPoolWorker-2.txt ForkPoolWorker-3.txt ForkPoolWorker-4.txt
	rm crawling_evaluation.txt
	rm ForkPoolWorker-1.txt ForkPoolWorker-2.txt ForkPoolWorker-3.txt ForkPoolWorker-4.txt
	rm successful_tests.txt
	rm failed_tests.txt
	rm -r pdfs/
	mkdir pdfs/
	mkdir pdfs/split/
	mkdir pdfs/txts/

.PHONY: init test
