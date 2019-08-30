import os
import sys
import urllib.request
import urllib.error
from multiprocessing import Pool
import multiprocessing
import re
from pprint import pprint
from PyPDF2 import PdfFileReader, PdfFileWriter
from bs4 import BeautifulSoup
import requests
import pymongo
from tqdm import tqdm
import time
from copy import deepcopy
from dns.exception import DNSException
from tika import parser

CURRENT_YEARS = ["2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019"]
SEMESTERS = {"Spring": 20, "Summer": 30, "Fall": 10}

# These map the headers in the college to the short names in the db
header_col_mapper = {'College of Architecture': 'CoA', 
'College of Arts and Sciences': 'CoAaS', 
'College of Atmospheric & Geographic Sciences': 'CoA&GS', 
'College of Continuing Education - Department of Aviation': 'CoCE-DoA', 
'Michael F. Price College of Business': 'MFPCoB', 
'Melbourne College of Earth and Energy': 'MCoEaE', 
'Jeannine Rainbolt College of Education': 'JRCoE', 
'Gallogly College of Engineering': 'GCoE', 
'Weitzenhoffer Family College of Fine Arts': 'WFCoFA', 
'Honors College': 'HC', 'College of International Studies': 'CoIS', 
'Gaylord College of Journalism and Mass Communication': 'GCoJaMC', 
'College of Professional and Continuing Studies': 'CoPaCS', 
'University College': 'UC', 'Center for Independent and Distance Learning': 'CfIaDL', 
'Expository Writing Program': 'EWP', 'ROTC - Air Force': 'R-AF'}

# Create parsing errors to use
class ParsingError(Exception):
    def __init__(self,  message):
        super().__init__(message)
        self.__name__ = 'ParsingError'

## Parsing helper function
def recursive_separate(textfile, separators, section_list = []):
    """
    Separates a textfile into a sequential list of sections as dictated by the separators.
    Inputs: 
    textfile: A long string to separate into different sections
    separators: The keywords to separate the textfile by.
    section_list: A list to append the sections to. Please pass in empty string.

    Returns:
    section_list: The list of each section of the string, separated by the separators keywords. 
    Note that the resultant list wont contain the separator keywords
    """
    el = separators.pop(0)
    splits = textfile.split(el)
    front = splits[0]
    back = el.join(splits[1:]).strip()
    if back == '':
        raise ParsingError('Separating failed for ' + textfile + ' \n\n with separating element- ' + el )
    if front != '':
        section_list.append(front)
    if len(separators) == 0:
        section_list.append(back)
        return section_list
    return recursive_separate(back, separators, section_list)

def web_crawl(url):
    """
    This function will crawl the given url, and download specific pdfs that correspond to the 
    entries in the header_col_mapper.
    """
    urls = []; names = []
    page = requests.get(url, timeout=5)
    soup = BeautifulSoup(page.text, "html.parser")
    pprint(len(soup.findAll('div')))
    # Each header with a 'articleheader' tag contains title for a college; 
    # Get this div, so we can check the next div for encompassed pdfs
    # This section gets all of the urls and puts them into urls[]. Names of each are put into names[], matched by index.
    # Make a structure to keep track of which have been successfully crawled and which havent
    crawl_tracker = {coll:{year:{sem:False for sem in SEMESTERS.keys()} for year in CURRENT_YEARS} for coll in header_col_mapper.values()}
    for i, div in enumerate(soup.findAll('div')):
        if 'class' in div.attrs:
            if 'articleheader' in div.attrs['class'] and len(div.text)>0:
                # col_header is key to determine college
                col_header = div.text.strip('\n\n')
                col = header_col_mapper[col_header]
                # The semesters for the colleges are in div index i+4; get anchors from this index
                anchors = soup.findAll('div')[i+4].findChildren('a', recursive=True)
                for a in anchors:
                    for year in CURRENT_YEARS:
                        for semester in SEMESTERS.keys():
                            if semester in a.text and year in a.text:
                                # We are only saving the urls/names of current years and desired colleges
                                full_url = url + a.get('href')
                                pdf_url = (full_url[:18] + full_url[49:])
                                name = f'{col}{year}{SEMESTERS[semester]}'
                                if pdf_url not in urls and name not in names: # Kind of sketchy, theoretically shouldnt be duplicates but they showed up
                                    urls.append(pdf_url)
                                    names.append(name)
                                    # Now to download the pdf
                                    try:
                                        print("Processing Name: " + name)
                                        resp = urllib.request.urlopen(pdf_url)
                                        try:
                                            print("Attempting to open: " + pdf_url)
                                            with open("pdfs/" + name + ".pdf", 'xb') as pdf:
                                                print("Writing " + name + "\n")
                                                pdf.write(resp.read())
                                        except FileExistsError:
                                            print(name + " ALREADY EXISTS IN DIRECTORY!!\n")
                                        crawl_tracker[col][year][semester] = True
                                    except urllib.error.HTTPError:
                                        print(f'404 Error for name: {name} and url {pdf_url}\n')
                                        crawl_tracker[col][year][semester] = False
                                        names.remove(name)
    return names

    # Finished scraping, all college semester names in names, urls, crawl_tracker status in crawl_tracker
    with open('crawling_evaluation.txt', 'w') as crawl_file:
        crawl_results = [True if crawl_tracker[coll][year][sem] else False for coll in header_col_mapper.values() for year in CURRENT_YEARS for sem in SEMESTERS.keys()]
        true_counts, false_counts =crawl_results.count(True), crawl_results.count(False)
        crawl_file.write(f'The crawling was {100*true_counts/len(crawl_results)}% effective at finding Semesters and colleges in the year range\n')
        crawl_file.write(f' {CURRENT_YEARS}')
        pprint.pprint(f'The crawling was {100*true_counts/len(crawl_results)}% effective at finding Semesters and colleges in the year range\n')
        print(f' {CURRENT_YEARS}\n')
        crawl_file.write(f'The specific crawling results are shown below: \n\n')
        pprint(crawl_tracker, stream=crawl_file)

def pdf_splitter(path, col, term):
    """
    This function takes a pdf and splits it into individual pages, saving them to directory pdfs/split
    """
    fname = os.path.splitext(os.path.basename(path))[0]
    pnum = 0
    try:
        pdf = PdfFileReader(path)
    except FileNotFoundError:
        print("==========================================================================================")
        print("Cannot Find File: " + path)
        print("==========================================================================================")
        exit(0) # This shouldnt ever happen
        return
    for page in range(pdf.getNumPages()):
        pdf_writer = PdfFileWriter()
        pdf_writer.addPage(pdf.getPage(page))

        output_filename = str(page+1) + col + term + ".pdf"

        try:
            with open(path.split("/", 1)[0] + "/split/" + output_filename, 'xb') as out:
                pdf_writer.write(out)
                print('Created: {}'.format(output_filename))
        except FileExistsError:
            print(output_filename + " ALREADY EXISTS!")

        pnum += 1

    return pnum

def parse_files(file):
    """
    This function extracts the text from a single page pdf file, then parses the text to fit into a defined schema.
    Inputs: 
    - file: The name of the single page pdf file to extract text from
    Returns:
    - Nothing, writes successfully parsed tests to successful_tests.txt, and tests that failed to parse to failed_tests.txt.
    Also writes the db_objects, ie. the file text fit into the schema, into a ForkPoolWorker-1.txt. This is where the scraped data
    gets read from for the upload to MongoDB in mongo_writer.py.
    """
    for notavar in [1]:
        current = multiprocessing.current_process()
        f = os.fsdecode(file)

        if f.endswith(".pdf"):
            print("Running: " + f)
            raw = parser.from_file(directory + file)
            text_Tika = raw['content']
            lines = text_Tika.splitlines()
            # Save the txt file for reference; this could be eliminated in future iterations, its not used anywhere.
            with open('pdfs/txts/' + f.rstrip(".pdf")+ '.txt', 'w') as txtf:
                txtf.write(raw['content'])

            # Drop out the empty lines
            lines= [i for i in lines if i != '']

            # Combine the lines into a single string (they werent sorted by line correctly anyway)
            full_text = ' '.join(lines)
            
            # Separate out the metadata from from the question information
            meta, Q_text = full_text.split(' College Rank')

            ## Parse the meta data to find the number of instructors
            # Parse the metadata for fields of interest
            # Can get Term Code and College Code from pdf name
            # Still need 'Subject Code', 'Course Number', 'Individual Responses', 'Section Title'
            # Use keywords to split the metadata into sections
            # Instuctors is IMPORTANT. Has large impact on functionality downstream.
            if ' Instructors: ' in meta:
                Instructors = True
                # If Instructors: use this keyword
                meta_sections = recursive_separate(meta, [' Course: ', ' Enrollment: ', ' Section Title: ', ' Course Level: ', ' Instructors: ', ' Section Size: '], section_list = [])
            else:
                Instructors = False
                # If Instructor: , use this keyword
                meta_sections = recursive_separate(meta, [' Course: ', ' Enrollment: ', ' Section Title: ', ' Course Level: ', ' Instructor: ', ' Section Size: '], section_list = [])
                # Define meta object to store each of the metadata fields
            # fields = ['Subject Code', 'Course Number', 'Individual Responses', 'Section Title', 'Instructor First Name', 'Instructor Last Name']
            entry_list = []; meta_dict = {} # entry lists will have one meta_dict per instructor found
            # Fill out the meta dict with info for all instructors
            meta_dict['Subject Code'] = re.findall(r"[A-Z ]+", meta_sections[1])[0].replace(' ', '')
            meta_dict['Course Number'] = int(re.findall(r"[0-9]+", meta_sections[1])[0])
            meta_dict['Section Title'] = meta_sections[3].strip(' ') 
            # Get the term and College Code from the filename
            col_header_mapper = dict(map(reversed, header_col_mapper.items()))
            str_file = file.decode('utf-8')
            col = re.findall(r"[A-z]+", str_file)[0]
            if col in col_header_mapper.keys():
                meta_dict['College Code'] = col
                meta_dict['Term Code'] = int(re.findall(r"[2][0][1-3][0-9][123][0]", str_file)[-1])
            else:
                raise ParsingError(f'The filename {str_file} cannot be parsed to obtain college code and term code')
                        
            assert(len(re.findall(r"[0-9]+", meta_sections[5]))==0) # Make sure the name is all non-numeric
            # Define instructor list for adding instructors to
            if Instructors:
                # Get each of the instructor strings into instr_strings
                instr_strings = []
                [instr_strings.append(ms.strip()) for ms in meta_sections[5].split('/')]
            else:
                instr_strings = [meta_sections[5].strip()]
            for instr_string in instr_strings:
                entry_list.append(deepcopy(meta_dict)) # Each entry will have the same metadata; Different instrs
                instr_string = ''.join([i for i in instr_string if i.isalnum() or i==' ']).strip()
                entry_list[-1]['Instructor First Name'] = instr_string.split()[0].strip()
                # Associate latter elements with thelast name. 
                # Basically, this breaks 'Zach Van Dam' into FirstName: Zach, LastName: Van Dam
                entry_list[-1]['Instructor Last Name'] = ' '.join(instr_string.split()[1:]).strip()

            ## Now that we know the number of instructors, we can parse the Question text (Q_text)
            # Separate the question averages from the Response Key
            Q_text, _ = Q_text.split(' Response Key ')

            # Find the Question Numbers and use to get the questions
            question_numbers = re.findall(r'( [0-9]{1,2}\. )', Q_text)

            # Find duplicate elements in the question_numbers list; Duplicate questions indicate multiple instructors
            Q_dupes = [x for n, x in enumerate(question_numbers) if x in question_numbers[:n]]
            Q_uniq = [x for n, x in enumerate(question_numbers) if x not in question_numbers[:n] and x not in Q_dupes]
            # Make sure we have enough questions for all of the instructors
            assert len(question_numbers)-len(Q_uniq) - len(Q_dupes)*len(entry_list) == 0
            pprint(Q_text)
            # Use the recursive separate to split Q_text into sections
            Q_sections = recursive_separate(Q_text, deepcopy(question_numbers), section_list = [])
            # pprint(Q_sections)
            # The first split section will sometimes contain the instructor name. If so, get drop it
            Sections_to_drop = set()
            print(f'There are {len(entry_list)} in entry_list')
            for entry in entry_list:
                # Checking for Instr first or last name in the first element of Q_sections. If so, delete this element
                if entry['Instructor First Name'].title() in Q_sections[0].title() or entry['Instructor Last Name'].title() in Q_sections[0].title():
                    del Q_sections[0]
            
            assert len(Q_sections) == len(question_numbers) 

            # Split the question sections up by instructors
            partitioned_Q_sections = [-1]*len(entry_list) # Need as many sections as entries
            shared_sections, sections_by_instructor = Q_sections[:len(Q_uniq)], Q_sections[len(Q_uniq):]
            for c in range(len(partitioned_Q_sections)):
                partitioned_Q_sections[c] = shared_sections + sections_by_instructor[c*len(Q_dupes):(c+1)*len(Q_dupes)]
            assert len(set([len(pQs) for pQs in partitioned_Q_sections])) == 1 # Ensure all Q sections are same length
            
            # We'll parse the questions for each entry in entry_list
            # Add the final result to db_objects, for writing to file
            db_objects = []
            for el_i, entry in enumerate(entry_list):
                # Fill out the questions
                questions = []
                # Zip together the question numbers and the partitioned sections
                # Get question responses on a per question basis
                for qn, qs in zip(Q_uniq + Q_dupes, partitioned_Q_sections[el_i]):
                    Q_dict = {}
                    # Assigns the question content as a value and the question number as key in a dict, which is added to 'questions' list
                    Q_dict['Question Number'] =  int(qn.strip(' ').strip('.'))
                    Q_dict['Question'] =  re.findall(r"[A-z, , ', \,, ]*", qs)[0].replace(' INDIVIDUAL ', '').strip(' ')
                    # Find the question instructor rating based on known column after INSTRUCTOR (tabular format)
                    Q_dict['Mean'] = float(qs.split(' ')[qs.split(' ').index('INDIVIDUAL')+1])
                    try:
                        # Try to get the standard deviation, if it doesnt work, that indicates the professor had zero responses
                        Q_dict['Standard Deviation'] = float(qs.split(' ')[qs.split(' ').index('INDIVIDUAL')+3])
                    except:
                        # If professor had zero responses, delete them
                        break

                    # Ensure we're getting reasonable values for the mean, std
                    for metric in [Q_dict['Mean'], Q_dict['Standard Deviation']]:
                        assert (0 <= metric and metric <= 5)
                    # Add in the question ratings to the list
                    questions.append(Q_dict)
                else:
                    # This 'else' clause gets hit when the inner loop wasnt broken
                    # Add the metadata to the individual questions to log them as rows in the table
                    for i in questions:
                        for k,v in entry.items():
                            i[k] = v
                        db_objects.append(i)
                    continue
                break

        for i in db_objects:
            print("Adding " + i["Instructor First Name"] + " " +
                    i["Instructor Last Name"] + " to " + i["College Code"]+str(i['Term Code']))
            with open(str(current.name) + ".txt", "a+") as ff:
                ff.write(str(i) + "\n")  
        with open("successful_tests.txt", "a+") as runf:
            runf.write(f + "\n")
    
    # # Handle all of our potential errors. This is very general but future work could refine.
    # except (ValueError, ParsingError, AssertionError, IndexError, AttributeError) as Error:
    #     if hasattr(Error, '__name__'):
    #         name = Error.__name__
    #     else:
    #         name = 'AssertionError'
    #     with open("failed_tests.txt", "a+") as fail:
    #         fail.write(file.decode('utf-8') + f": Failed due to {name}\n")
    #     print(f'{name} at filename '+ file.decode('utf-8'))           

if __name__ == '__main__':

    # Catch Incorrect program calls
    if len(sys.argv) < 3 or len(sys.argv) > 3:
        print("USAGE: review_ocr %s %s" % "db_name", "test_bool")
    # Run the test case
    if sys.argv[2] == "True":
        pdf_splitter("test/CoA201030.pdf", "CoA", "201030")
        directory = os.fsencode('test/split/')
        files = os.listdir(directory)
        for file in files[:]:
            _ = parse_files(file)
        exit(0)
    # Run the main program
    else:
        # print("Crawling the OU website...")
 
        # url = "http://www.ou.edu/provost/course-evaluation-data"
 
        # names = web_crawl(url)
        # print('\n\n')
        # print(names)
        # print('\n\n')

        # print("Splitting PDFs... \n")
        # for name in names:
        #     print("Splitting: " + name)
        #     pdf_splitter("pdfs/" + name + ".pdf", name[:-6], name[-6:])

        directory = os.fsencode('pdfs/split/')
        files = os.listdir(directory)
        print("Parsing the split pdfs... \n")
        CPUS = os.cpu_count()
        print(f"Number of CPU's detected: {CPUS}")
        print(f"Running with {CPUS//2} processes")
        with Pool(processes=4) as pool: # Must be 4 processes for future mongo_writer step. Doesnt take too long anyway
            r = list(pool.imap(parse_files, files))
        
        # Build evaluation metric for parsing effectiveness
        with open('successful_tests.txt', 'r') as f:
            successful=sum(1 for _ in f)
        with open('failed_tests.txt', "r") as f:
            failed =sum(1 for _ in f)
        print(f'\n\n The parsing program successfully parsed {round(100*successful/(successful+failed),4)} % of files.')
        exit(0)