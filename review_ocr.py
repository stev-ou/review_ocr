import os
import sys
import urllib.request
import urllib.error
from multiprocessing import Pool
import multiprocessing
import re
try:
    from PIL import Image
except ImportError:
    import Image
import pprint
from PyPDF2 import PdfFileReader, PdfFileWriter
from bs4 import BeautifulSoup
import requests
from pymongo import MongoClient, errors
import pymongo
from tqdm import tqdm
import time
from copy import deepcopy
from dns.exception import DNSException
from tika import parser

debug = ""

CURRENT_YEARS = ["2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019"]
SEMESTERS = {"Spring": 20, "Summer": 30, "Fall": 10}

BUG_CITY = ["_", "-", '—', "=", '__', "--", "==", '_—', '——']
BUG_CITY2 = {"Bio": 57.35, "Bony": 55.17, "Sere)": 53.33, "Sle25)": 31.25, "mos": 7.35, "oo": 7.35, "Bro": 57.35, "FE": 5,
             "iD": 5, "iD)": 5, "S": 5, "a": 5}
FIND_Q = ["1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. ", "8. ", "9. ", "10. ",
          "11. ", "12. ", "13. ", "14. ", "15. ", "16. ", "17. ", "18. ", "19. ", "20. ",
          "21. ", "22. ", "23. ", "24. ", "25. ", "26. ", "27. ", "28. ", "29. ", "30. ",
          "31. ", "32. ", "33. ", "34. ", "35. ", "36. ", "37. ", "38. ", "39. ", "40. ",
          ]
baddata = []

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

## Parsing helper functions
def recursive_separate(textfile, separators, section_list = []):
    """
    Separates a textfile into a sequential list of sections as dictated by the separators
    """
    el = separators.pop(0)
    splits = textfile.split(el)
    front = splits[0]
    back = el.join(splits[1:]).strip()
    if back == '':
        raise Exception('Separating failed for ' + textfile + ' and ' + el)
    if front != '':
        section_list.append(front)
    if len(separators) == 0:
        section_list.append(back)
        return section_list
    return recursive_separate(back, separators, section_list)
###

def web_crawl(url):
    """
    This function will crawl the given url, and download specific pdfs that correspond to the 
    entries in the header_col_mapper.
    """
    urls = []
    names = []
    page = requests.get(url, timeout=5)
    soup = BeautifulSoup(page.text, "html.parser")
    print(len(soup.findAll('div')))
    # Each header with a 'articleheader' tag contains title for a college; 
    # Get this div, so we can check the next div for encompassed pdfs
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
                                # Gotta git rid of some unnecessary characters in the url and set it up to parse properly
                                if 'https://' in a.get('href'):
                                    print('Error on ' + f'{col}{year}{SEMESTERS[semester]}')
                                    continue
                                else:
                                    full_url = url + a.get('href')
                                # pdf_url = full_url
                                pdf_url = (full_url[:18] + full_url[49:])
                                name = f'{col}{year}{SEMESTERS[semester]}'
                                if pdf_url not in urls and name not in names: # Kind of sketchy, theoretically shouldnt be duplicates
                                    urls.append(pdf_url)
                                    names.append(str(col) + str(year) +
                                                str(SEMESTERS[semester]))
                                    print(f"Adding {col}{year}{SEMESTERS[semester]} to Write Queue...")
                                    print(pdf_url + "\n")

    # Finished scraping, all college semester names in names, urls
    # Now we "download" the pdfs by writing to pdf files
    for name, url in zip(names, urls):
        try:
            print("Attempting to open: " + url)
            resp = urllib.request.urlopen(url)

            try:
                pdf = open("pdfs/" + name + ".pdf", 'xb')
                print("Writing " + name + "\n")
                pdf.write(resp.read())
                pdf.close()
            except FileExistsError:
                print(name + " ALREADY EXISTS IN DIRECTORY!!\n")

        except urllib.error.HTTPError:
            print("404 Error on this page... This PDF may not exist yet.\n")
            names.remove(name)
    return names

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

def bug_city(l, key):
    # Welcome to Bug City
    # Remove Citizens of Bug City1
    for i in range(0, len(l)-1):
        if l[i] in BUG_CITY:
            l.pop(i)

    for i in range(0, len(l)):
        if l[i] in BUG_CITY2.keys():
            l[i] = BUG_CITY2[l[i]]

    new = []
    k = 0
    while k < len(l):
        if l[k] == key:
            new.append(l[k])
            k += 1
            break
        else:
            k += 1

    for i in range(k, len(l)):
        try:
            f = float(l[i])
            new.append(f)
        except ValueError:
            try:
                n = int(l[i])
                new.append(n)
            except ValueError:
                break

    return new

def parse_files(file):
    """
    This function extracts the text from a single page pdf file, then parses the text to fit into a defined schema.
    """
    try:
    # for pkl in ['nope']:
        current = multiprocessing.current_process()
        f = os.fsdecode(file)

        # # This file SUCKS!!!!
        # if f == "349ints201710.pdf":
        #     return

        if f.endswith(".pdf"):
            print("Running: " + f)
            raw = parser.from_file(directory + file)
            text_Tika = raw['content']
            lines = text_Tika.splitlines()
            # Save the txt file to compare
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
            # Should be able to get Term Code and College Code from previous parsing
            # Still need 'Subject Code', 'Course Number', 'Individual Responses', 'Section Title'
            # Use keywords to split the metadata into sections
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
            meta_dict['Subject Code'] = re.findall(r"[A-Z]+", meta_sections[1])[0]
            meta_dict['Course Number'] = int(re.findall(r"[0-9]+", meta_sections[1])[0])
            meta_dict['Individual Responses'] = int(re.findall(r"[0-9]+", meta_sections[2])[0])
            meta_dict['Section Title'] = meta_sections[3].strip(' ') 
            # Get the term and College Code from the filename
            col_header_mapper = dict(map(reversed, header_col_mapper.items()))
            str_file = file.decode('utf-8')
            col = re.findall(r"[A-z]+", str_file)[0]
            if col in col_header_mapper.keys():
                meta_dict['College Code'] = col
                meta_dict['Term Code'] = str_file[5:10]
            else:
                raise Exception(f'The filename {str_file} cannot be parsed to obtain college code and term code')
                        
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
                # Associate latter arrays with last name
                entry_list[-1]['Instructor Last Name'] = ' '.join(instr_string.split()[1:]).strip()

            ## Now that we know the number of instructors, we can parse the Question text (Q_text)
            # Separate the question averages from the Response Key
            Q_text, _ = Q_text.split(' Response Key ')

            # Find the Question Numbers and use to get the questions
            question_numbers = re.findall(r'( [1-9]{1,2}\. )', Q_text)

            # Find duplicate elements in the question_numbers list; Duplicate questions indicate multiple instructors
            Q_dupes = [x for n, x in enumerate(question_numbers) if x in question_numbers[:n]]
            Q_uniq = [x for n, x in enumerate(question_numbers) if x not in question_numbers[:n] and x not in Q_dupes]
            # Make sure we have enough questions for all of the instructors
            assert len(question_numbers)-len(Q_uniq) - len(Q_dupes)*len(entry_list) == 0

            # Use the recursive separate to split Q_text into sections
            Q_sections = recursive_separate(Q_text, deepcopy(question_numbers), section_list = [])
            assert len(Q_sections) == len(question_numbers) 

            # Split the question sections up by instructors
            partitioned_Q_sections = [-1]*len(entry_list) # Need as many sections as entries
            shared_sections, sections_by_instructor  = Q_sections[:len(Q_uniq)], Q_sections[len(Q_uniq):]
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
                for qn, qs in zip(Q_uniq + Q_dupes, partitioned_Q_sections[el_i]):
                    Q_dict = {}
                    # Assigns the question content as a value and the question number as key in a dict, which is added to 'questions' list
                    Q_dict['Question Number'] =  qn.strip(' ').strip('.')
                    Q_dict['Question'] =  re.findall(r"[A-z, , ', \,, ]*", qs)[0].replace(' INDIVIDUAL ', '').strip(' ')
                    # Find the question instructor rating based on known column after INSTRUCTOR (tabular format)
                    Q_dict['Mean'] = float(qs.split(' ')[qs.split(' ').index('INDIVIDUAL')+1])
                    Q_dict['Standard Deviation'] = float(qs.split(' ')[qs.split(' ').index('INDIVIDUAL')+3])
                    # Ensure we're getting reasonable values for the mean, std
                    for metric in [Q_dict['Mean'], Q_dict['Standard Deviation']]:
                        assert (0 <= metric and metric <= 5)
                    # Add in the question ratings to the list
                    questions.append(Q_dict)

                # Add the metadata to the individual questions to log them as rows in the table
                for i in questions:
                    for k,v in entry.items():
                        i[k] = v
                    db_objects.append(i)

        for i in db_objects:
            print("Adding " + i["Instructor First Name"] + " " +
                    i["Instructor Last Name"] + " to " + i["College Code"]+i['Term Code'])
            #collection.insert_one(db_objects[i])
            with open(str(current.name) + ".txt", "a+") as ff:
                ff.write(str(i) + "\n")  
            with open("run_files.txt", "a+") as runf:
                runf.write(f + "\n")

    except ValueError:
        print(ValueError)
        print('At filename '+ file.decode('utf-8'))
    # except pymongo.errors.AutoReconnect:
    #     print("sleeping...")
    #     baddata.append(f)
    #     with open("baddata.txt", "a+") as ff:
    #         ff.write(f + "\n")
    #     time.sleep(300)
    #     return

    # except DNSException:
    #     print("DNS Timeout... sleeping for a bit...")
    #     baddata.append(f)
    #     with open("baddata.txt", "a+") as ff:
    #         ff.write(f + "\n")
    #     time.sleep(300)
    #     return
    # except Exception:
    #     baddata.append(f)
    #     with open("baddata.txt", "a+") as ff:
    #         ff.write(f + "\n")
    #     time.sleep(300)
    #     return
    # return
            

if __name__ == '__main__':
    # Testing for web crawl
    # names = web_crawl('https://www.ou.edu/provost/course-evaluation-data')
    db_name = sys.argv[1]


    if len(sys.argv) < 3 or len(sys.argv) > 3:
        print("USAGE: review_ocr %s %s" % "db_name", "test_bool")

    if sys.argv[2] == "True":
        pdf_splitter("test/CoA201030.pdf", "CoA", "201030")
        directory = os.fsencode('test/split/')
        files = os.listdir(directory)
        for file in files[:]:
            # pprint.pprint(parse_files(file))
            _ = parse_files(file)
        exit(0)

    else:
        """
        print("Crawling...")
 
        url = "http://www.ou.edu/provost/course-evaluation-data"
 
        names = web_crawl(url)
 
        # print(names)
        for name in names:
            print("Splitting: " + name)
            pdf_splitter("pdfs/" + name + ".pdf", name[:-6], name[-6:])
        """

        directory = os.fsencode('pdfs/split/')
        files = os.listdir(directory)
        # parse_files(directory)

        CPUS = os.cpu_count()
        print("Number of CPU's detected: {}".format(CPUS))
        print("Running with {} processes".format(CPUS//2))
        #list(map(parse_files, files))
        #with Pool(processes=CPUS//2) as pool:
        exit(0)
        with Pool(processes=4) as pool:
            r = list(pool.imap(parse_files, files))
        exit(0)