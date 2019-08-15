def recursive_separate(textfile, separator, section_list = []):
    """
    Separates a textfile into a sequential list of sections as dictated by the separators
    """
    
    if len(section_list) == len(separators)+1:
        return section_list
    front,back = textfile.split(separators.pop(0))
    section_list.append(front)
    return recursive_separate(back, separators, section_list)
