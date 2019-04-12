from setuptools import setup, find_packages

with open('README.md') as f:
	readme = f.read()
	f.close()

with open('LICENSE') as f:
	license = f.read()
	f.close()

setup(
	name='review_ocr',
	version='0.0.1',
	description="Using Google's Tesseract OCR to extract data from public PDFs",
	long_description=readme,
	author='Joe Lovoi',
	author_email='joelovoi@gmail.com',
	url='https://github.com/stev-ou/review_ocr',
	license=license,
	packages=find_packages(exclude=('tests', 'docs'))
)