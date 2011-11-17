# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import re

from invenio.authorextract_re import get_single_and_extra_author_pattern, \
                                     get_author_affiliation_numeration_str
from invenio.authorextract_xml import build_formatted_xml_author_affiliation_line
from invenio.refextract_find import get_reference_section_beginning

re_tagged_author_aff_line = re.compile(r"""
          \<cds\.                ## open tag: <cds.
          ((AUTHstnd)            ## an Author tag
          |(AFF))                ## or an Affiliation tag
          (\s\/)?                ## optional /
          \>                     ## closing of tag (>)
          """, re.UNICODE|re.VERBOSE)

re_aff_email = re.compile(r"^.*?@.*?$")

## Targets single author names
re_single_author_pattern_with_numeration = re.compile(get_single_and_extra_author_pattern(), re.VERBOSE)

re_author_tag = \
    re.compile(r"^\s*((prepared|(?P<editor>edited)|written)\sby|authors?)\s*[,:;]?", \
               re.UNICODE | re.IGNORECASE)


def get_post_author_section_keyword_patterns():
    """ Return a list of compiled regex's based on keywords used as an indication of the
        end of a possible author section on the title page of a document.
        @return: (List of compiled keywords which denote a possible end of author
        section)
    """
    keywords = ['abstract', 'acknowledgements', 'introduction', 'intro', 'overview',
                'contents', 'content', 'context', 'table of contents', 'table',
                'objectives', 'page', 'preface', 'summary', 'copyright', 'keywords',
                'figure', 'fig']

    ptns = map(_create_regex_pattern_add_optional_spaces_to_word_characters, keywords)
    ## Add an optional chapter numeration (1., 1.1, i, A..) to the start of each pattern
    ptns = ['\s*([ai1]\s*\.?\s*[1]?\s*\.?\s*)?'+x for x in ptns]
    ## Page number 1 ... must force a 'page' match, sometimes numeration is broken
    ptns.append('\s*page\s*[i\d]\s*\.?\s*$')
    ## Number one at the start of a possible chapter
    #ptns.append('\s*\d\.?\s*$')
    compiled_patterns = []
    for p in ptns:
        compiled_patterns.append(re.compile(p, re.I | re.UNICODE))
    return compiled_patterns

re_aff_num = re.compile(r"(^[\d]+[A-Z])")
re_aff_name = re.compile(r"(univ|institut|laborator)", re.I)
re_aff_univ = re.compile(r"univ[a-z]+\s+(of)?\s+([a-z\s\-]+)|([a-z\s\-]+)\s+(?!univ[a-z]+\sof)univ[a-z]+", re.I)
re_splitting_comma = re.compile(",[^\d]", re.UNICODE)

def arrange_possible_authors(line, delimiter=None):
    """Break a line according to a delimiter. Replace 'and' phrases
       with the delimiter before splitting.
       @param line: (string) The line containing possible authors.
       @param delimiter: (char) A delimiter found when rearranging
       numeration around characters. This rearranging took place
       prior to this, and was used to partially repair pdftotext issues.
       @return: (list) Broken up line.
    """
    if not delimiter:
        delimiter = ","
    ## Replace and's with delimiter (comma as standard)
    delimited_line = re.sub(r"(^\s*|\s)([Aa][Nn][Dd]|&)\s", delimiter, line)
    ## Split by delimiter
    possible_authors = delimited_line.split(delimiter)
    ## Remove empty stuff
    possible_authors = filter(lambda x: x.strip(), possible_authors)
    return possible_authors

def gather_affiliated_authors_by_numeration(lines, aff_positions, number_to_find):
    """ Use the found affiliation to try and help with author extraction.
        Using affiliation positions, and the number to find, look for authors above
        the affiliations, by comparing the numeration found adjacent to authors.
        An extraction procedure tends to spend the majority of its time inside this
        function, if the number of numerated, affiliated authors is high.
        @param lines: (list) The search space.
        @param aff_positions: (list) Positions of already found affiliations.
        @param number_to_find: (int) The number to find against authors.
        @return: (tuple) of two lists, one holding numerated author matches,
        and the other holding authors which resided on a line holding a numerated
        author, and were split using some common, found delimiter.
    """
    def has_number(possible_auth, number_to_find):
        """Does this possible author have the numeration I want?"""
        (auth_nums, auth_num_match) = obtain_author_affiliation_numeration_list(possible_auth)
        return number_to_find in auth_nums

    def remove_excess_numeration(author_match):
        """See function signature."""
        return re.sub("^\d+|\d+$", "", author_match)

    ## Holds numerated authors.
    numerated_authors = []
    all_split_authors = []
    ## Make a copy of the list of above lines [must be a copy due to pop()]
    lines_to_check = lines[:]
    while lines_to_check:
        line = lines_to_check.pop().strip()
        popped_position = len(lines_to_check)
        if aff_positions and (popped_position in aff_positions):
            continue
        ## Shift numeration around delimiters if needed
        ##FIXME shouldnt have to do this again here.. was done earlier for finding std authors
        (shifted_line, num_delimiter) = realign_shifted_line_numeration_around_commas(line)
        ## Split according to delimiter (default is comma)
        possible_authors = arrange_possible_authors(shifted_line, num_delimiter)
        ## Make a list of ok authors found in the split line, for this affiliation
        numerated_authors.extend(filter(lambda a: has_number(a, number_to_find), possible_authors))
        ## So, on this line, a numerated author was found. So,
        ## make sure to save the rest of the split authors in this line.
        if numerated_authors:
            all_split_authors.extend(possible_authors)

    return (map(remove_excess_numeration, numerated_authors), \
            map(remove_excess_numeration, all_split_authors))

def initiate_affiliated_author_search(affiliations, top_lines, aff_positions):
    """Using obtained affiliation details, try to find authors, using primarily the
    numeration-associated method (pairing numerated authors with numerated affiliations,
    and as a fall-back, the 'lines-above' affiliation.
    @param affiliations: (dictionary) Already collected affiliations, with their possible
    numeration too.
    @param top_lines: (list) The top lines (search space) of the document
    @param aff_positions: (list) A numeric list of positions where known affiliations
    exist (ignores these lines; prevents returning an affiliation as a possible author)
    @return: (tuple) affiliation data, and loose authors (all authors found)
    """
    ## Used to validate a set of words found above an affiliation
    ## This is used when no authors have been found for a paper, but an affiliation has
    ## Will try to match a single ambiguous author, such as "William J. Smith"
    tried_numeration = []
    ## Holds all split items in a line where numerated authors were found!
    loose_authors = []

    for cur_aff in affiliations:
        if cli_opts['verbosity'] >= 2:
            sys.stdout.write("---Finding affiliated authors for %s...\n" % cur_aff['line'].encode("UTF-8").strip())
        ## Using numerated affiliations
        if cur_aff['aff_nums']:
            numerated_authors = []
            for num in cur_aff['aff_nums']:
                if not num in tried_numeration:
                    ## For this single, new, affiliation numeration val
                    ## use it to find authors, using:
                    ## 1. Lines above the affiliation
                    ## 2. The already identified affiliation positions
                    ## 3. The affiliation number, for authors, to look for
                    (numerated_authors_single_num, all_split_authors) = \
                        gather_affiliated_authors_by_numeration(top_lines, \
                                                                    aff_positions, \
                                                                    number_to_find=num)
                    numerated_authors.extend(numerated_authors_single_num)
                    ## Save all split authors, if at least one numerated author was found!
                    ## Otherwise, this is just an empty addition
                    loose_authors.extend(all_split_authors)
                    tried_numeration.append(num)

            ## Substantially reliable
            cur_aff['author_data'] = {'authors'  : numerated_authors,
                                      'strength' : 1}
            if cli_opts['verbosity'] >= 7:
                sys.stdout.write("----Found %d strong affiliated authors.\n" % len(numerated_authors))
        else:
            ## Using (line-above) NON-numerated affiliations to look for authors
            ## This method is far less accurate than using numeration, but nonetheless
            ## correct in a wide variety of situations.
            ## Get the next non-empty line above the affiliation
            position_above = cur_aff['position']-1
            while (position_above >= assumed_top_section_start) and \
                    (position_above >= 0) and \
                    (not top_lines[position_above].strip()):
                position_above -= 1

            ## The position above is a line which is another affiliation
            ##i.e. no 'non-blank' possible author line inbetween
            if position_above in aff_positions:
                position_above = -1

            ## If a valid line (not empty & not another affiliation) was found above the affiliation
            if position_above >= 0:
                lines_above = [top_lines[position_above]]
                ## For each line, look for an 'and' start and collect them up
                while re_comma_or_and_at_start.search(top_lines[position_above]) and \
                        (not position_above in aff_positions):
                    try:
                        lines_above.append(top_lines[position_above-1])
                    except IndexError:
                        break
                    position_above -= 1

                collected_line_above_authors = []
                ## For each 'possible author' line above the affiliation
                ## Build a list of weakly-matched authors
                for line_above in lines_above:
                    ## Insert commas over 'and's and split using commas
                    split_line_above = arrange_possible_authors(line_above)
                    ## If the list of comma separated line elements in the above line
                    ## is longer than 1 (i.e. it has commas separating components)
                    if len(split_line_above) > 1:
                        ## This makes for a more reliable match (comma separated line above aff)
                        strength_for_this_line_above = 1
                    else:
                        ## This match isnt so reliable
                        strength_for_this_line_above = 0
                    collected_line_above_authors = filter(lambda a: re_ambig_auth.search(a), split_line_above)

                ## Far less reliable than the numerated version
                cur_aff['author_data'] = {'authors'   : collected_line_above_authors,
                                          'strength'  : strength_for_this_line_above,}

                if cli_opts['verbosity'] >= 7:
                    sys.stdout.write("----Found %d weak affiliated authors.\n" % len(collected_line_above_authors))

    return (affiliations, loose_authors)

def build_start_end_numeration_str(predefined_punct=None):
    """Pieces together the leading and trailing numeration strings,
    for affiliations and authors.
    @param predefined_number: (int) punctuation which surrounds numeration.
    (e.g. brackets)
    @return: (regex) The regex which will match both starting and ending
    numeration on a line, with any additional punctuation included."""
    ## It is important that the regex matches the number AND something else relevant on the line
    numeration_str = "^"+get_author_affiliation_numeration_str(predefined_punct)+r"[^\d](?:(?:.*?)[^\d\s\.,\:;\-\[\]\(\)\*\\](?:.*?))" \
                    +"|"+r"(?:(?:.*?)[^\s\.,\:;\-\[\]\(\)\*\\](?:.*?))[^\d]"+get_author_affiliation_numeration_str(predefined_punct) \
                    +"$"
    return numeration_str

def obtain_author_affiliation_numeration_list(line, punct=None):
    """Extract the leading or trailing numeration from the line.
    @param line: (string) a line of text (possibly holding an affiliation)
    @param punct: (string) the punctuation known to surround numeration
    elements. (makes the search more strict)
    @return: (list) stripped and raw integer numeration"""
    ## List of integer numeration associated with this author/affiliation
    i_stripped_nums = []
    ## Given a line with an affiliation, see if numeration is on the line
    re_numeration = \
        re.compile(build_start_end_numeration_str(punct), re.UNICODE|re.VERBOSE)
    num_match = re.search(re_numeration, line.strip())
    ## Numeration exists for this affiliation
    if num_match:
        ## Get the start/end number match (or string of separated numbers)!
        str_num = num_match.group(2) or num_match.group(5)
        ## Split if multiple numbers
        if ";" in str_num:
            stripped_nums = str_num.split(";")
        elif "," in str_num:
            stripped_nums = str_num.split(",")
        else:
            stripped_nums = [str_num]
        ## Attempt to convert each numeration value to an integer
        try:
            i_stripped_nums = map(lambda n: int(n.strip()), stripped_nums)
        except ValueError:
            pass
    ## num_match is used to obtain punctuation around the numeration
    return (i_stripped_nums, num_match)

def replace_affiliation_names(line):
    """  Standardise some affiliations. Convert some
    domain specific HEP names to a standard form.
    This will very likely be moved out into a kb soon.
    @param line: (string) Line from the document holding a
    possibly unstandardised affiliation.
    @return: the line holding now standardised affiliations
    """
    ## Removes numeration, 'the'/'and', and replace titles
    line = line.strip()
    for term, repl in CFG_REFEXTRACT_INSTITUTION_REPLACEMENTS.items():
        line = re.sub(term, repl, line)
    line = re.sub(r"\s[tT][hH][eE]\s", " ", line)
    line = re.sub(r"\s[aA][nN][dD]\s", " ", line)
    return line

def reduce_affiliation_names(line):
    """ Standardise some affiliations. This will remove numeration,
    and will convert university names into a standard format.
    @param line: (string) Line from the document holding a
    possibly unstandardised affiliation.
    @return: the line holding now standardised formats of affiliations
    """
    ## Kill numeration
    line = re.sub(r"[0-9]","",line)
    ## Format the found affiliation
    univ_name = re_aff_univ.search(line)
    if univ_name:
        ## Get the University name
        line = (univ_name.group(2) or univ_name.group(3)) + " U."
    ## Check and set an institution
    for inst in CFG_REFEXTRACT_INSTITUTION_REDUCTIONS:
        if line.find(inst) != -1:
            line = inst
            break
    return line

def extract_numerated_affiliations(num_data, num_find, missing):
    """ Collect numerated affiliations, using a section of the document, and
    the number which to search for. The punctuation surrounding any numeration (the
    first number found) (if any) is used to improve the strictness of the search.
    @param num_position: (int) position in section from where to look
    for numerated affiliations
    @param num_section: (list) section holding numerated affiliations
    @param num_find: (int) number to find, paired with affiliations
    @param num_punct: (string) punctuation around affiliation numeration (if any)
    @return: (list) of dictionary elements corresponding to the position,
    content and numeration data of an affiliation.
    """
    affs = []

    if num_data['position'] < len(num_data['top']):
        ## First line, holding first affiliation with the number 1
        line = num_data['top'][num_data['position']].strip()
        ## A number has been found before this iteration
        ## Use previous number, and previous punctuation!
        (aff_nums, specific_num_match) = obtain_author_affiliation_numeration_list(line, num_data['punc'])
        if num_find in aff_nums:
            ## Attempt to get numeration for this affiliation
            try:
                num_find = num_find + 1
            except ValueError:
                sys.stderr.write("Error: Unable to obtain integer affiliation numeration.")
                sys.exit(1)
            ## Save the punctuation surrounding the numeration
            affs.append({'position'             : num_data['position'],
                         'line'                 : reduce_affiliation_names(line),
                         'aff_nums'             : aff_nums,
                         'author_data'          : None})

        elif num_find in missing:
            ## Get the next non missing number and use that
            while num_find in missing:
                num_find += 1

        ## Increment position and remove top line
        num_data['position'] += 1
        ## Do until end of docbody section (num_section)
        affs.extend(extract_numerated_affiliations(num_data, \
                                                       num_find, \
                                                       missing))
    return affs

## Numeration at the start of the line
re_start_numeration = re.compile("^%s$" % get_author_affiliation_numeration_str(), \
                                 re.VERBOSE|re.UNICODE)

def realign_numeration(toplines):
    """ Create a duplicate document body, but with starting numeration
    replicated on the next line. This is to do with the reparation
    of numeration across multiple lines, from the pdftottext conversion.
    Both of these docbody's are later checked, and the one which makes
    sense in terms of numeration positioning is used from then onwards.
    Essentially means that the conversion of pdf to text is less likely
    to hinder numeration searching.
    @param docbody: (list) List of lines of the entire input document.
    @return: (list) The list of lines of the entire input document,
    with any start-line numeration shifted accordingly.
    """

    toplines_alternate = toplines[:]
    ## Get the positions of all single '1's
    ## These positions will denote the start of each realignment process
    starting_numeration = []
    for position, line in enumerate(toplines):
        num_match = re_start_numeration.search(line)
        if num_match:
            try:
                i_num = int(num_match.group(2))
                if i_num == 1:
                    ## If this number found is
                    starting_numeration.append(position)
            except ValueError:
                continue

    numeration_swaps = 0

    ## Now, using the positions of the '1's, go forward and locate
    ## subsequent numeration, and replicate on the following line if need be
    missing_nums = []
    for start in starting_numeration:
        alignment_error = 0
        num = 1
        for position, line in enumerate(toplines[start:]):
            num_match = re_start_numeration.search(line)

            if num_match:
                ## Sanity check, make sure the match is an integer
                try:
                    i_num = int(num_match.group(2))
                except ValueError:
                    continue

                ## Hit a number which is not expected, and is not just 2 ahead
                if (i_num != num) and ((i_num < num) or ((i_num - num) > \
                                                             CFG_REFEXTRACT_AFFILIATION_NUMERATION_ALLOWABLE_GAP)):
                    ## Skipping can occur, but only whilst the number is within the allowable gap
                    continue
                else:
                    ## When there exists an acceptable missed number, for whatever reason
                    if (i_num > num) and ((i_num - num) <= CFG_REFEXTRACT_AFFILIATION_NUMERATION_ALLOWABLE_GAP):
                        ## Append all the missing numbers between the gap
                        missing_num = num
                        while missing_num != i_num:
                            missing_nums.append(missing_num)
                            missing_num += 1
                        num += (i_num - num)

                    try:
                        ## Otherwise, if this number found is equal to the incremented number
                        toplines_alternate[start+position] = "\n"
                    except IndexError:
                        alignment_error = 3
                    else:
                        lookahead = start+position

                        ## Now place the number on the next NON-EMPTY line
                        while not alignment_error:
                            lookahead += 1
                            try:
                                line_ahead = toplines_alternate[lookahead].strip()
                                int_val_line = int(line_ahead)
                            except ValueError:
                                ## ValueError is good
                                if line_ahead:
                                    toplines_alternate[lookahead] = \
                                        num_match.group(0).strip() + line_ahead

                                    ## Increment the next number to look for
                                    num += 1
                                    numeration_swaps += 1
                                    break
                            except IndexError:
                                alignment_error = 4
                            else:
                                ## A line following a found lone number is also a number
                                ## To dangerous to continue.
                                alignment_error = 5

            if alignment_error:
                if cli_opts['verbosity'] >= 1:
                    sys.stdout.write("---Warning: Realign numeration problem #%d.\n" % alignment_error)
                ## Scrap the alternate version
                toplines_alternate = toplines
                break

    if cli_opts['verbosity'] >= 8:
        sys.stdout.write("---realign numeration made %d changes.\n" % numeration_swaps)

    return (toplines_alternate, missing_nums)

def find_affiliations(lines, start, end=None, use_to_find_authors=False):
    """ Given a possible author section, attempt to retrieve any affliations.
        @param lines: (list) The entire document body as a list of lines.
        @param start: (int) The start position, from where to start finding
        affiliations.
        @param end: (int) The boundary position: Stop searching here.
        @param use_to_find_authors: (boolean) whether or not the affiliations found
        within this function should be used to support the identification of authors.
        (This will be True in the case when '--authors' is selected, and no authors
        have been found using the specific author regular expression during the first
        method.)
        @return (tuple): Affilations and the possibly improved author section.
    """
    def get_smaller(x, y):
        if x < y:
            return x
        return y

    affiliations = []
    numerated_aff_data = {'position' : None,
                          'punc'     : None,
                          'top'      : None,}
    if not start:
        start = 0

    ## If a keyword was found, then use it to limit the search space
    if end:
        top_lines_orig = lines[start:end]
    else:
        top_lines_orig = lines[start:]

    ## Get an alternative version of the top section, of the same length
    ## but with some alone numeration replicated on the next line!
    (top_lines_alt, missing_nums) = realign_numeration(top_lines_orig)

    for position in range(len(top_lines_orig)):
        ## Standardise some affiliations
        line = replace_affiliation_names(top_lines_orig[position].strip())
        line_alt = replace_affiliation_names(top_lines_alt[position].strip())

        ## If a previous numeration value was found in the previous iteration
        ## check for the increment of this value on this line
        if re_aff_num.search(line) or re_aff_name.search(line):

            ## Check numeration in line from original & realigned docbodies
            (aff_nums, num_match) = obtain_author_affiliation_numeration_list(line)
            (aff_nums_alt, num_match_alt) = obtain_author_affiliation_numeration_list(line_alt)

            ## Set the information to the correct top_section, depending on
            ## if the numeration was found split across lines or not.
            if aff_nums or not aff_nums_alt:
                top_version_for_line = top_lines_orig
            else:
                top_version_for_line = top_lines_alt
                aff_nums = aff_nums_alt
                num_match = num_match_alt

            if cli_opts['verbosity'] >= 4:
                sys.stdout.write("---Affiliation match on line: %s\n" % \
                                     top_version_for_line[position].encode("UTF-8").strip())

            ## Aff number '1' numeration found, save position and punctuation
            if aff_nums and num_match and (1 in aff_nums):
                ## Set the top version to use, depending on how this initial aff was found
                numerated_aff_data = {'position'         : position,
                                      'top'              : top_version_for_line,
                                      'punc'             : num_match.group(1),}
            ## So, an AFFILIATION KEYWORD was found on this line, but this is not a '1'!
            ## Move up lines to get the starting affiliation position, using NUMERATION
            elif aff_nums and num_match:
                ## Get the smallest affiliation number, and minus 1 from it
                find_num = reduce(lambda x, y: get_smaller(x, y), aff_nums) - 1
                reversed_position = position - 1
                ## Attempt to go back and find the start of this numeration section
                ## Get numeration for this line
                while (reversed_position >= 0) and (numerated_aff_data['position'] is None):
                    ## Check numeration in the numeration-realigned docbody
                    (rev_aff_nums, rev_num_match) = \
                        obtain_author_affiliation_numeration_list(top_version_for_line[reversed_position])
                    ## Check for numeration n, n = 1
                    if find_num == 1 and (find_num in rev_aff_nums):
                        ## Set the top version to use, depending on how this initial aff was found
                        numerated_aff_data = {'position'         : reversed_position,
                                              'top'              : top_version_for_line,
                                              'punc'             : rev_num_match.group(1),}
                    ## Check for numeration n, 1 < n < last found
                    elif find_num in rev_aff_nums:
                        find_num = find_num - 1
                    ## Move position up one line
                    reversed_position = reversed_position - 1

                if not numerated_aff_data['position']:
                    ## Could not find start. Abort everything.
                    break
            else:
                ## No numeration -- append affiliation normally
                affiliations.append({'position'     : position,
                                     'line'         : reduce_affiliation_names(line),
                                     'aff_nums'     : None,
                                     'author_data'  : None,})

        ## Stop searching if a starting numerated affiliation has been found
        if numerated_aff_data['position'] is not None:
            break

    starting_aff_position = None
    ## Collect all numerated affiliations, using the starting affiliation
    ## Missing numeration was detected during the realignment process
    if numerated_aff_data['position'] is not None:
        ## Need to save this, since finding numerated affs will change it
        starting_aff_position = numerated_aff_data['position']

        affiliations = extract_numerated_affiliations(numerated_aff_data, \
                                                          1, \
                                                          missing_nums)
        if cli_opts['verbosity'] >= 4:
            sys.stdout.write("---The collection of numerated affiliations returned %d affiliations.\n" % len(affiliations))

    loose_authors = []
    ## Get affiliated authors, if specified
    if use_to_find_authors:
        top_to_use_to_find_authors = numerated_aff_data['top'] or top_lines_orig

        ## If numerated affiliations are being used, only look at the lines above
        ## the first numerated affiliation
        if numerated_aff_data['position']:
            top_to_use_to_find_authors = top_to_use_to_find_authors[:starting_aff_position]
        aff_positions = [aff['position'] for aff in affiliations]
        ## Look for authors associated with obtained affiliations
        (affiliations, loose_authors) = initiate_affiliated_author_search(affiliations, \
                                                                              top_to_use_to_find_authors, \
                                                                              aff_positions)
        if cli_opts['verbosity'] >= 4:
            sys.stdout.write("---The collection of affiliated authors returned authors for %d affiliations.\n" % \
                                 len([x['author_data']['authors'] for x in affiliations if (x['author_data'] and x['author_data']['authors'])]))

    ## Remove undesirable characters
    for tmp_aff in affiliations:
        tmp_aff['line'] = replace_undesirable_characters( \
            reduce_affiliation_names(tmp_aff['line']).strip(".,:;- []()*\\"))

    return (affiliations, loose_authors)

def collect_tagged_authors(top_section, position, first_line=None, \
                               orig_blank_lines=None, cur_blank_lines=None):
    """Recursively try to obtain authors after an 'author tag' has been
    found.
    @param top_section: (list) Lines corresponding to the document's top section
    @param position: (integer) Current position in the top_section
    @param first_line: (string) An optional, over-riding line to be processed on the
    first iteration
    @param orig_blank_lines: (integer) The static gap width, calculated when finding the
    first non-empty line, before collecting subsequent lines. The blank line count is
    reset to this value for each tagged author collected.
    @param cur_blank_lines: (integer) An optional, blank line count, which is calculated
    after traversing lines after a tag, before iterating. This is then used to find possible
    subsequent authors.
    @return: list holding the list of collected tagged authors,
    and the position of the last author line
    """
    def leading_comma(line):
        return line.rstrip().endswith(",")

    line_parts = []
    if position < len(top_section):
        if first_line:
            line = first_line.strip()
        else:
            line = top_section[position].strip()

        if orig_blank_lines and not cur_blank_lines:
            dec_blank_lines = orig_blank_lines - 1
        elif cur_blank_lines:
            dec_blank_lines = cur_blank_lines - 1
        else:
            dec_blank_lines = orig_blank_lines

        comma_subd_line = re.sub(r"\s([Aa][Nn][Dd]|&)\s", ", ", line)
        line_has_leading_comma = leading_comma(comma_subd_line)
        line_parts = comma_subd_line.split(",")

        #FIXME possibly generate a pattern from the tagged author match, to be used to verify other authors! (pattern from FIRST match)

        ## Check to see if this line starts with an 'and'
        ## or a comma, or has an author form. In either case it's likely
        ## that more author names preceed it.
        author_match = re_single_author_pattern_with_numeration.search(line)
        if line_has_leading_comma or author_match:
            if line_has_leading_comma:
                ## Reset and reuse the blank line count (comma found at the end of the line)
                dec_blank_lines = orig_blank_lines
            else:
                ## Do not consider any more blank lines when searching
                dec_blank_lines = 0
            (position, more_line_parts) = collect_tagged_authors(top_section, \
                                                                     position+1, \
                                                                     first_line=None, \
                                                                     orig_blank_lines=orig_blank_lines, \
                                                                     cur_blank_lines=dec_blank_lines)
            ## Extend the parts found on this line, with the parts found
            ## in previous iterations. (going backwards)
            line_parts.extend(more_line_parts)
        ## Or if it is known that there exists blank lines between tagged authors,
        ## and this line has a leading comma (evidence for more authors somewhere),
        ## or is blank then continue to look for authors, until the gap width
        ## (blank line count) is reached
        elif cur_blank_lines > 0 and ((not line) or line_has_leading_comma):
            (position, more_line_parts) = collect_tagged_authors(top_section, \
                                                                     position+1, \
                                                                     first_line=None, \
                                                                     orig_blank_lines=orig_blank_lines, \
                                                                     cur_blank_lines=dec_blank_lines)
            ## Nothing gets added from this line, just pass the line to the next iteration
            line_parts = more_line_parts

    return (position, line_parts)

re_misaligned_numeration_around_comma = re.compile("(.*?)(?P<delim>[,;])\s*(\d{1,3})")
def realign_shifted_line_numeration_around_commas(line):
    ## First see how many swap substitutions will take place, before-hand.
    swaps = [x for x in re_misaligned_numeration_around_comma.finditer(line)]
    delimiter = None
    if len(swaps) >= 1:
        ## Get the first matches' delimiter, which can be reused to split a line later.
        delimiter = swaps[0].group("delim")
        ## Do the swapping.
        line = re_misaligned_numeration_around_comma.sub(r"\g<1>\g<3>,", line).strip(",")
    return (line, delimiter)

## Used in the event that no keyword is found (max length of top section)
assumed_top_section_length = 300

## Used to force the validity of found keywords
## (Valid if they appear after this position)
assumed_top_section_start = 1

## Was extract_authors_from_fulltext
def extract_top_document_information_from_fulltext(docbody, first_author=None):
    """ Given a list of lines from a document body, obtain author/affiliation
        information of the document. This is done via the examination of the top
        section of the document, via similar regex's used to identify authors in
        references, and also author tags and the use of affiliation information.
        Tagged authors always have the highest level of precedence when deciding
        which group of authors to output for this document. In general,
        affiliated authors have a higher precedence level than standard authors,
        however, this can change depending on the method used to identify
        the affiliated authors, and whether or not the affiliated authors is a
        smaller subset of the standard author list.

        The number of lines which will constitute the search-space, is
        identified through two configuration values, and more importantly, by
        using usual 'start-of-document-body' keyword (abstract, introduction etc..)

        Author identification is completed by running through three, partially-
        separated steps:

        1. Obtain authors which are explicitly tagged as such

        2. Collect up standard-authors, using the re_auth comprehensive regex.

        3. Attempt to collect authors using affiliation matches.
            3.1 Lean on numerated affiliations to allow for the accurate extraction
            of paired numerated authors.
            3.2 Look at the lines above affiliations, and check for possible authors.
        @param docbody: (list) List of lines corresponding to the entire text version
        of the input document.
        @param first_author: (string) An optional first author from where to start
        @return: (tuple) The top document information, holding affiliations
        and the chosen set of author names. Also holds two status values.
    """

    def check_for_end_of_author_section_match_keywords(docbody):
        """ Given a lowercase, stripped line from the start of a document, try to find a match the
            line exactly for a keyword. A match should indicate the end of the author section.
            @param line: The line to be checked for ending section keywords.
            @return (match object): The match object returned when a keyword match is found.
        """

        found_ending_keyword = None
        found_author_tag = None
        ending_keyword_ptns = get_post_author_section_keyword_patterns()
        for position, line in enumerate(docbody):
            ## Find top section ending keywords
            ## Must exceed the first 3 lines
            keyword_hit = perform_regex_match_upon_line_with_pattern_list(line, ending_keyword_ptns)
            if keyword_hit and not found_ending_keyword and (position > 3):
                if cli_opts['verbosity'] >= 7:
                    sys.stdout.write("---Ending keyword match: %s, position: %d\n" % \
                                         (keyword_hit.group(0).strip(), position))
                found_ending_keyword = position

            ## Look for author tags
            author_tag_hit = re_author_tag.search(line)
            if author_tag_hit and not found_author_tag:
                if cli_opts['verbosity'] >= 7:
                    sys.stdout.write("---Author tag match: %s, position: %d\n" % \
                                         (author_tag_hit.group(0).strip(), position))
                found_author_tag = position

            ## Only in the top X lines
            if (found_ending_keyword and found_author_tag) \
                    or position >= assumed_top_section_length:
                break

        return (found_ending_keyword, found_author_tag)

    # Example docbody
    # docbody = ['Some title', 'Some date',
    #            'Chris Hayward, Tim Smith, Joe Harris',
    #            'University of Bath', '', 'Abstract']
    # docbody = ['Some title', 'Some date',
    #            'Authors:', 'Chris Hayward,', '', 'Tim Smith,', '',
    #            'Joe Harris', 'University of Bath', '', 'Abstract']

    affiliations = []

    # Always find the position of the start of the reference section.
    # Strip from document body.
    refs_start = get_reference_section_beginning(docbody)

    # Strip references. This will prevent analysing this section for authors.
    if refs_start:
        docbody = docbody[:refs_start['start_line']]

    # Default return values
    status = how_found_start = 0

    # end-of-top-section-keyword position, if any
    (pre_ending_keyword, pre_author_tag) = check_for_end_of_author_section_match_keywords(docbody)

    if pre_ending_keyword:
        if cli_opts['verbosity'] >= 4:
            sys.stdout.write("---Using top section keyword as a delimiter.\n")
        top_section = docbody[:pre_ending_keyword]
    elif len(docbody) < assumed_top_section_length:
        # Half total length
        if cli_opts['verbosity'] >= 4:
            sys.stdout.write("---Using entire document body as top section.\n")
        top_section = docbody
    else:
        # First N lines
        if cli_opts['verbosity'] >= 4:
            sys.stdout.write("---Using first %d lines as top section.\n" % \
                                 (assumed_top_section_length))
        top_section = docbody[:assumed_top_section_length]

    tagged_author_information = []
    just_tagged_authors = []
    first_author_tag_position = None

    # METHOD 1 -------------- Look for tagged authors.
    for position in range(len(top_section)):
        line = top_section[position]
        # 'Prepared/edited/written by:', or 'authors:'
        if re_author_tag.search(line):
            # We know there's a tag, save this position
            first_author_tag_position = last_tagged_author_position = position
            # Remove the tag, and check content
            detagged_line = re_author_tag.sub('', line, 1).strip()
            if detagged_line:
                # From this point, go on and collect tagged authors
                (last_tagged_author_position, tagged_authors) = \
                    collect_tagged_authors(top_section, \
                                               position, \
                                               first_line=detagged_line)
            else:
                # So, in this situation, there is nothing following the
                # author tag on the same line, but a tag is present, meaning
                # that authors are below the tag somewhere!
                # Get the next non-empty line, and look at that.
                position_find = position + 1
                tagged_authors = None
                # From this point
                while (position_find < len(top_section)) and (not tagged_authors):
                    # Hit a non-blank line after a tag, start searching recursively from here
                    if top_section[position_find].strip() != '':
                        gap_width = position_find - position
                        (last_tagged_author_position, tagged_authors) = \
                            collect_tagged_authors(top_section, \
                                                       position_find, \
                                                       orig_blank_lines=gap_width)
                        # Save the position of the last author line
                    position_find += 1

            if tagged_authors:
                tagged_author_information = [{'authors'      : tagged_authors,
                                              'affiliation'  : None,}]
                just_tagged_authors = tagged_authors
            # Break with whatever was collected from the author tag.
            break

    # METHOD 2 -------------- look for standard authors (basic pattern)
    # Look for standard (initials surname, or surname initials) authors.
    # This is done before affiliation-assisted author-search is initiated
    # since the positions can be used to improve affiliation detection.

    first_standard_author_position = None
    standard_authors = []
    standard_author_matches = []

    # Either original, or shifted, using numeration
    top_section_version = None

    for position in range(len(top_section)):
        # An author tag was found, delay the search until the tag position is reached
        if first_author_tag_position and (position < first_author_tag_position):
            continue

        line = top_section[position]
        (shifted_line, numeration_delimiter) = \
            realign_shifted_line_numeration_around_commas(line)

        # Look for authors (with or without numeration) on the original line
        # and on the augmented line (with numeration shifted)
        author_matches = \
            [x for x in re_single_author_pattern_with_numeration.finditer(line)]
        author_matches_alt = \
            [y for y in re_single_author_pattern_with_numeration.finditer(shifted_line)]

        if author_matches or author_matches_alt:
            if not first_standard_author_position:
                first_standard_author_position = position
            last_standard_author_position = position

            if author_matches and author_matches_alt:
                # Save the list of matching authors in a list
                if len(author_matches) <= len(author_matches_alt):
                    use_line = "alt"
            elif author_matches_alt:
                use_line = "alt"

            if use_line == "alt":
                which_line = re.sub("\s([Aa][Nn][Dd]|&)\s", ",", shifted_line.strip())
                standard_author_matches = author_matches_alt
            else:
                which_line = re.sub("\s([Aa][Nn][Dd]|&)\s", ",", line.strip())
                standard_author_matches = author_matches

            new_standard_authors = [x.group(0) for x in standard_author_matches]

            # Split the line based on a common delimiter,
            # If at least two authors were matched on this line
            if len(standard_author_matches) >= 2:
                first_matched_auth = standard_author_matches[0].group(0)
                second_matched_auth = standard_author_matches[1].group(0)
                try:
                    delimiter = None
                    # Take either the delimiter from two author matches
                    # or from the result of swapping numeration eariler.
                    # Use this information to split a line, thus maximising the author count.
                    if first_matched_auth.strip()[-1] == second_matched_auth.strip()[-1]:
                        delimiter = first_matched_auth.strip()[-1]
                    elif numeration_delimiter:
                        delimiter = numeration_delimiter
                    if delimiter:
                        split_authors = [n for n in which_line.split(delimiter) if n.strip(", ")]
                        # Take the authors obtained from splitting the line
                        if len(split_authors) >= len(new_standard_authors):
                            new_standard_authors = split_authors
                except IndexError:
                    pass

            # Standard author strings
            standard_authors.append(new_standard_authors)

    # By this point, we've managed to try and get tagged authors, as well
    # as anything in the top section that looks like an author using the standard
    # author pattern.

    # METHOD 3 -------------- Look for authors using affiliations
    # and handle the assembly of standard authors too

    affiliation_associated_affiliated_authors = []
    affiliation_associated_standard_authors = []

    just_standard_authors = []
    just_affiliated_authors = []

    # Now, attempt to obtain authors using affiliation positions.
    # A tagged author position is considered the best starting point.
    # Otherwise start from the top of the section.
    # Always attempt to find authors too.
    (affiliations, loose_authors) = find_affiliations(top_section, \
                                                          start=first_author_tag_position, \
                                                          use_to_find_authors=True)

    if affiliations is not None:
        # Attempt to pair together standard authors with identified affiliations.
        # If the number of affiliation is equal to the number of author lines
        if len(affiliations) == len(standard_authors):
            # Increase strength for this (when len(aff)=len(auth))?
            for x in range(len(standard_authors)):
                # Associate authors with affiliations
                affiliation_associated_standard_authors.append({'authors'     : standard_authors[x],
                                                                'affiliation' : affiliations[x]['line']})
                just_standard_authors.extend(standard_authors[x])
        # Now assemble affiliated authors, with their affiliations
        for aff in affiliations:
            # Append any affiliation supported authors, but only if authors exist.
            if aff['author_data']:
                author_list_for_affiliation = aff['author_data']['authors']
                affiliated_author_strength = aff['author_data']['strength']
                affiliation_associated_affiliated_authors.append( \
                    {'authors'       : [auth for auth in author_list_for_affiliation if auth not in just_affiliated_authors],
                     'affiliation'   : aff['line'],
                     'strength'      : affiliated_author_strength,})
                just_affiliated_authors.extend([auth for auth in author_list_for_affiliation])

    # In the event that standard authors were not paired with affiliations
    # then just make a list of dictionaries of authors without affiliations
    if standard_authors and not affiliation_associated_standard_authors:
        for s in standard_authors:
            affiliation_associated_standard_authors.append({'authors'     : s,
                                                            'affiliation' : None,})
            just_standard_authors.extend(s)

    # Print the extracted author counts
    if cli_opts['verbosity'] >= 4:
        sys.stdout.write("---Author counts for each extraction type:\n")
        sys.stdout.write("----1. Tagged, count %d.\n" % \
                             (len([l for l in just_tagged_authors if l.strip()])))
        sys.stdout.write("----2. Standard, count %d.\n" % \
                             (len([k for k in just_standard_authors if k.strip()])))
        sys.stdout.write("----3. Affiliated, count %d.\n" % \
                             (len([j for j in just_affiliated_authors if j.strip()])))

    # Print the physical author matches
    if cli_opts['verbosity'] == 9:
        sys.stdout.write("---Author extraction type contents:\n")
        sys.stdout.write("----1. Tagged authors:\n%s\n" % \
                             tagged_author_information)
        sys.stdout.write("----2. Standard authors:\n%s\n" % \
                             affiliation_associated_standard_authors)
        sys.stdout.write("----3. Affiliated authors:\n%s\n" % \
                             [x['authors'] for x in affiliation_associated_affiliated_authors])

    # Given three lists of authors, which have been extracted using
    # three different methods decide which list to return as the most
    # reliable representation of this paper's authors (if any)
    (final_authors, chosen_type) = choose_author_method(tagged_author_information, \
                                                            affiliation_associated_standard_authors, \
                                                            affiliation_associated_affiliated_authors, \
                                                            just_tagged_authors, \
                                                            just_standard_authors, \
                                                            just_affiliated_authors)

    # Display the results of choosing the set of authors
    if cli_opts['verbosity'] >= 8:
        sys.stdout.write("---Chosen author-type: %d\n" % chosen_type)
        sys.stdout.write("\n********************\nExtracted top data:\n" % final_authors)
        sys.stdout.write("   Authors:\n\t%s\n" % final_authors)
        sys.stdout.write("   Affiliations:\n\t%s\n********************\n\n" % affiliations)

    document_information = {'authors'           : final_authors,
                            'affiliations'      : affiliations}

    return (document_information, status, chosen_type)

def mark_up_affiliation(affiliation):
    """ Tags a string, with the affiliation tags.
    """
    def process_aff(a):
        """Remove unacceptable end characters."""
        a = replace_undesirable_characters(a).strip(".,:;- []()*\\")
        return a

    processed_aff = process_aff(affiliation)

    tagged_aff = ""
    if processed_aff:
        tagged_aff = "%s%s%s" % ("<cds.AFF>", \
                                     processed_aff, \
                                     CFG_REFEXTRACT_MARKER_CLOSING_AFFILIATION)
    return tagged_aff

def mark_up_affiliations(affiliations):
    """ Tag a set of lines as affiliations. Note the first
        affiliation too.
        @param affiliations: (list) Strings which should be marked up
        as affiliations.
        @return: (list) of tuples. Holding a boolean, as to whether or not
        this affiliation or author is the first one in the list.
    """

    tagged_affiliations = []

    is_first_aff = True
    for a in affiliations:
        marked_up_aff = mark_up_affiliation(a)
        if marked_up_aff:
            tagged_affiliations.append((is_first_aff, marked_up_aff))
            if is_first_aff:
                is_first_aff = False

    return tagged_affiliations

def mark_up_authors_with_affiliations(final_authors):
    """ Prepare authors and any possible associated affiliations
    into marked-up (tagged) lines according to identified authors.
    @param final_authors: (list) Holding dictionary items
    holding lists of authors with their optional affiliation.
    @return: (list) A list of lines, holding marked-up authors
    and their affiliations.
    """
    # Pair authors and affiliations together, in the event that
    # affiliated supported authors were found!
    tagged_authors = []

    def process_authors(a):
        # Also remove numeration
        a = re.sub('\d+', '', a)
        a = replace_undesirable_characters(a).strip(".,:;- []()*\\")
        return a

    is_first_author = True

    for aff_auth_dict in final_authors:
        for authors in aff_auth_dict['authors']:
            # Otherwise the closing element tag dissappears (!?)
            if authors:
                if not aff_auth_dict['affiliation']:
                    aff_for_authors = ""
                else:
                    # Use the affiliation tags to tag this affiliation
                    aff_for_authors = mark_up_affiliation(aff_auth_dict['affiliation'])
                # Tag authors, and any of their associated affiliations
                tagged_authors.append((is_first_author, "%s%s%s%s" % ("<cds.AUTHstnd>", \
                                                            process_authors(authors), \
                                                            CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_STND, \
                                                            aff_for_authors)))
                if is_first_author:
                    is_first_author = False

    return tagged_authors

def choose_author_method(tagged_info, std_info, aff_info,
                             tagged_authors, std_authors, aff_authors):
    """Decide which list of authors to treat as the most accurate and
    reliable list of authors for a document. This is accomplished
    primarily through set operations of the author values, and the methods
    by which they were extracted.
    @param tagged_info: (dict) Affiliation and author information for authors
    obtained using explicit in-document author notation (tags).
    @param std_info: (dict) Affiliation and author information for authors
    obtained using the comphrehensive author pattern.
    @param aff_info: (dict) Affiliation and author information for authors
    obtained using two types of affiliation-context (numeration, and positioning).
    @param tagged_authors: (list) List of purely tagged authors.
    @param std_authors: (list) List of purely standard-matched authors.
    @param aff_authors: (list) List of purely affiliated authors.
    @return: (tuple) Affiliation and author information which is deemed to be
    the most accurate for the document, and the type used --
    (standard [2] or affiliated [3]).
    """

    # Immediately discard non-sets of authors (hold duplicate entries)
    if len(tagged_authors) != len(set(tagged_authors)):
        sys.stdout.write("Warning: tagged authors list has duplicates.\n")
        tagged_info = []
    if len(std_authors) != len(set(std_authors)):
        sys.stdout.write("Warning: standard authors list has duplicates.\n")
        std_info = []
    if len(aff_authors) != len(set(aff_authors)):
        sys.stdout.write("Warning: affiliated authors list has duplicates.\n")
        aff_info = []

    tagged_authors = map(lambda x: x.strip(" ,"), tagged_authors)
    std_authors = map(lambda y: y.strip(" ,"), std_authors)
    aff_authors = map(lambda z: z.strip(" ,"), aff_authors)

    # False if there is a 'weak' affiliation-supported author match
    # AND none of them are found in the list of standard authors
    weak_affiliated_authors = False

    # True if 'weak' affiliated authors are present, and at least one of
    # those authors has, as a subset, an author from the standard author list
    author_match_with_standard_authors = False

    # If standard authors and affiliated authors exist
    # Otherwise there's no point in deciding which to take
    if std_authors and aff_authors:
        # Is there a 'line-above' author line?
        weak_affiliated_authors = filter(lambda tmp_aff: \
                                             ((tmp_aff['strength'] is 0) and tmp_aff['authors']), aff_info)

        for f in aff_info:
            if (f['strength'] is 0) and f['authors']:
                # Given that there exists at least one 'line above' set of authors
                # See if any of these so-called weak authors also exist in the
                # set of standard authors (even as substrings)
                for auth in f['authors']:
                    # If there exists a standard author which is a substring
                    # of at least one affiliated author
                    author_match_with_standard_authors = filter(lambda tmp_std: \
                                                                    auth.find(tmp_std), std_authors)
                    # Do not place precedence on the standard authors
                    if author_match_with_standard_authors:
                        break
                # Do not give precedence to standard authors when there exists
                # a line-above author in the list of standard authors
                if author_match_with_standard_authors:
                    weak_affiliated_authors = False
                    break

    aff_authors_is_a_subset_of_std_authors = False
    if set(aff_authors).difference(std_authors) and set(aff_authors).issubset(std_authors):
        # Is the set of affiliated authors a subset of standard authors
        # And do they differ?!
        aff_authors_is_a_subset_of_std_authors = True

    # The situations where std_info has precendence over aff_info
    # 1. There exists at least one 'line above affiliation' (weakly) found author
    # 2. Affiliated authors are a subset of standard authors
    # 3. Standard authors double the number of affiliated authors
    standard_over_affiliated = weak_affiliated_authors or \
        aff_authors_is_a_subset_of_std_authors or \
        ((len(aff_authors) * 2) < len(std_authors))

    if not (tagged_authors or std_authors or aff_authors):
        if cli_opts['verbosity'] >= 4:
            sys.stdout.write("---Unable to find any authors.\n")
        return ([], 0)
    elif tagged_authors:
        if cli_opts['verbosity'] >= 4:
            sys.stdout.write("---Choosing tagged authors.\n")
        return (tagged_info, 1)
    # Make the choice, with the appropriate precedence
    elif standard_over_affiliated:
        if cli_opts['verbosity'] >= 4:
            sys.stdout.write("---Choosing standard over affiliated authors.\n")
        if std_info:
            return (std_info, 2)
        else:
            return (aff_info, 3)
    else:
        if cli_opts['verbosity'] >= 4:
            sys.stdout.write("---Choosing affiliated over standard authors.\n")
        if aff_info:
            return (aff_info, 3)
        else:
            return (std_info, 2)


def get_affiliation_canonical_value(proposed_affil):
    """Given a proposed affiliation, look for a canonical form in the
    affils knowledge base
 
    @param proposed_affil the possible affiliation name to be looked for
    @return canonical form returns none if no key matches
 
    """
 
    try:
        from invenio.bibformat_dblayer import get_kb_mapping_value
    except ImportError:
        def get_kb_mapping_value(kb_name, key):
            """ if we have no kb, just accept affiliations as they are"""
            return None # default


def convert_processed_auth_aff_line_to_marc_xml(line, first_author):
    """ Given a line holding either tagged authors, affiliations or both, convert it to its
        MARC-XML representation.

        @param line: (string) The tagged author-affiliation line. The line may hold a
        single author, an author and an affiliation, or an affiliation.
        @return xml_line: (string) the MARC-XML representation of the tagged author/aff line
        @return count_*: (integer) the number of * (pieces of info) found in the author/aff line.
    """

    count_auth = count_aff = 0
    xml_line = ""
    processed_line = line
    cur_misc_txt = u""

    tag_match = re_tagged_author_aff_line.search(processed_line)

    # contains a list of dictionary entries of previously cited items
    author_elements = []
    # the last tag element found when working from left-to-right across the line
    identified_author_element = None

    while tag_match is not None:

        ## While there are tags inside this reference line...
        tag_match_start = tag_match.start()
        tag_match_end   = tag_match.end()
        tag_type        = tag_match.group(1)
        cur_misc_txt += processed_line[0:tag_match_start]

        if tag_type.find("AUTH") != -1:
            ## This tag is an identified Author:
            ## extract the author from the line:
            idx_closing_tag_nearest = processed_line.find(\
                CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_STND, tag_match_end)

            if idx_closing_tag_nearest == -1:
                ## no closing </cds.AUTH****> tag found - strip the opening tag
                ## and move past it
                processed_line = processed_line[tag_match_end:]
                identified_citation_element = None
            else:
                auth_txt = processed_line[tag_match_end:idx_closing_tag_nearest]
                ## Now move past the ending tag in the line:
                processed_line = processed_line[idx_closing_tag_nearest + \
                                                    len("</cds.AUTHxxxx>"):]
                #SAVE the current misc text
                identified_author_element = { 'type'       : "AUTH",
                                              'content'    : "%s" % auth_txt,
                                            }
                ## Increment the stats counters:
                count_auth += 1
                cur_misc_txt = u""

        elif tag_type.find("AFF") != -1:
            ## This tag is an identified affiliation:
            ## extract the affiliation from the line:
            idx_closing_tag_nearest = processed_line.find(\
                CFG_REFEXTRACT_MARKER_CLOSING_AFFILIATION, tag_match_end)

            if idx_closing_tag_nearest == -1:
                ## no closing </cds.AFF> tag found - strip the opening tag
                ## and move past it
                processed_line = processed_line[tag_match_end:]
                identified_citation_element = None
            else:
                aff_txt = processed_line[tag_match_end:idx_closing_tag_nearest]
                ## Now move past the ending tag in the line:
                processed_line = processed_line[idx_closing_tag_nearest + \
                                                    len(CFG_REFEXTRACT_MARKER_CLOSING_AFFILIATION):]
                #SAVE the current misc text
                identified_author_element =   {   'type'       : "AFF",
                                                  'content'    : "%s" % aff_txt,
                                                }
                ## Increment the stats counters:
                count_aff += 1
                cur_misc_txt = u""

        if identified_author_element != None:
            ## Append the found tagged data and current misc text
            author_elements.append(identified_author_element)
            identified_author_element = None

        ## Look for the next tag in the processed line:
        tag_match = re_tagged_author_aff_line.search(processed_line)

    ## Now, run the method which will take as input:
    ## 1. A list of dictionaries, where each dictionary is a author or an
    ## affiliation.
    xml_line = build_formatted_xml_author_affiliation_line(author_elements, first_author)

    ## return the reference-line as MARC XML:
    return (xml_line, count_auth, count_aff)


def get_affiliation_canonical_value(proposed_affil):
    """Given a proposed affiliation, look for a canonical form in the
    affils knowledge base

    @param proposed_affil the possible affiliation name to be looked for
    @return canonical form returns none if no key matches

    """

    try:
        from invenio.bibformat_dblayer import get_kb_mapping_value
    except ImportError:
        def get_kb_mapping_value(kb_name, key):
            """ if we have no kb, just accept affiliations as they are"""
            return None   #default


def begin_extraction(daemon_cli_options=None):
    """Starts the core extraction procedure. [Entry point from main]
       Only refextract_daemon calls this directly, from _task_run_core()
       @param daemon_cli_options: contains the pre-assembled list of cli flags
       and values processed by the Refextract Daemon. This is full only when
       called as a scheduled bibtask inside bibsched.
    """

    global cli_opts, running_independently
    ## Global 'running mode' dependent functions
    global write_message, task_update_progress, task_sleep_now_if_required

    ## If running inside as a bibtask, set the functions relating to the
    ## interface between bibsched and refextract
    if daemon_cli_options:
        running_independently = False
        ## Try to assign the write_message function from bibtask
        ## which will format log messages properly
        try:
            write_message = bibtask_write_message
            task_update_progress = bibtask_task_update_progress
            task_sleep_now_if_required = bibtask_task_sleep_now_if_required
        except NameError:
            raise StandardError("Error: Unable to import essential bibtask functions.")
        ## Set the cli options to be those assembled by refextract_daemon
        cli_opts = daemon_cli_options
    else:
        running_independently = True
        (cli_opts, cli_args) = get_cli_options()
    ## A dictionary to contain the counts of all 'bad titles' found during
    ## this reference extraction job:
    all_found_titles_count = {}

    ## Gather fulltext document locations from input arguments
    if len(cli_opts['fulltext']) == 0:
        ## no arguments: error message
        usage(wmsg="Error: No input file specified.")
    else:
        extract_jobs = get_recids_and_filepaths(cli_opts['fulltext'])

    if len(extract_jobs) == 0:
        ## no files provided for reference extraction - error message
        usage(wmsg="Error: No valid input file specified (-f id:file [-f id:file ...])")

    ## What top section data do I want?
    extract_top_section_metadata = cli_opts['authors'] or cli_opts['affiliations']

    done_coltags = 0 ## flag to signal that the starting XML collection
                     ## tags have been output to either an xml file or stdout

    for num, curitem in enumerate(extract_jobs):
        ## Safe to sleep/stop the extraction here
        task_sleep_now_if_required(can_stop_too=True)
        ## Update the document extraction number
        task_update_progress("Extracting from %d of %d" % (num+1, len(extract_jobs)))

        how_found_start = -1  ## flag to indicate how the reference start section was found (or not)
        extract_error = 0  ## extraction was OK unless determined otherwise
        ## reset the stats counters:
        count_misc = count_title = count_reportnum = count_url = count_doi = count_auth_group = 0
        recid = curitem[0]
        write_message("--- processing RecID: %s pdffile: %s; %s\n" \
                         % (str(curitem[0]), curitem[1], ctime()), verbose=2)

        ## 1. Get this document body as plaintext:
        (docbody, extract_error) = \
            get_plaintext_document_body(curitem[1], \
                                            extract_top_section_metadata)
        if extract_error == 1:
            ## Non-existent or unreadable pdf/text directory.
            write_message("***%s\n\n" % curitem[1], sys.stderr, verbose=0)
            halt(msg="Error: Unable to open '%s' for extraction.\n" \
                 % curitem[1], exit_code=1)
        if extract_error == 0 and len(docbody) == 0:
            extract_error = 3
        write_message("-----get_plaintext_document_body gave: " \
                             "%s lines, overall error: %s\n" \
                             % (str(len(docbody)), str(extract_error)), verbose=2)

        if not done_coltags:
            ## Output opening XML collection tags:
            ## Initialise output xml file if the relevant cli flag/arg exists
            if cli_opts['xmlfile']:
                try:
                    ofilehdl = open(cli_opts['xmlfile'], 'w')
                    ofilehdl.write("%s\n" \
                                       % CFG_REFEXTRACT_XML_VERSION.encode("utf-8"))
                    ofilehdl.write("%s\n" \
                                       % CFG_REFEXTRACT_XML_COLLECTION_OPEN.encode("utf-8"))
                    ofilehdl.flush()
                except Exception, err:
                    write_message("***%s\n%s\n" % (cli_opts['xmlfile'], err), \
                                      sys.stderr, verbose=0)
                    halt(err=IOError, msg="Error: Unable to write to '%s'" \
                             % cli_opts['xmlfile'], exit_code=1)

            ## else, write the xml lines to the stdout
            else:
                sys.stdout.write("%s\n" \
                                     % CFG_REFEXTRACT_XML_VERSION.encode("utf-8"))
                sys.stdout.write("%s\n" \
                                     % CFG_REFEXTRACT_XML_COLLECTION_OPEN.encode("utf-8"))
            done_coltags = 1

        if len(docbody) > 0:
            ## the document body is not empty:
            ## 2. If necessary, locate the reference section:
            if cli_opts['treat_as_raw_section']:
                ## don't search for sections in the document body:
                ## treat entire input as relevant section:
                extract_lines = docbody
            else:
                ## launch search for the relevant section in the document body
                (document_info, extract_error, author_type) = \
                    extract_top_document_information_from_fulltext(docbody, first_author=cli_opts['first_author'])

            ## I want authors/affiliations!
            ## Handle the xml processing separately, in the case that authors/
            ## affiliations are being extracted
            if cli_opts['authors']:
                extract_lines = document_info['authors']
                ## Associate authors with their affiliations if possible
                out_lines = mark_up_authors_with_affiliations(extract_lines)
            else:
                extract_lines = document_info['affiliations']
                ## Just the list of affiliations
                out_lines = mark_up_affiliations(set([aff['line'] for aff in extract_lines]))

            if not document_info and extract_error == 0:
                extract_error = 6
            elif extract_error == 2:
                extract_lines = []

            if cli_opts['verbosity'] >= 1:
                sys.stdout.write("-----author/affiliation extraction " \
                                     "gave len(extract_lines): %s overall error: " \
                                     "%s\n" \
                                     % (str(len(extract_lines)), str(extract_error)))

            processed_lines = []
            for first_auth_aff, l in out_lines:
                (xml_line, \
                 count_auth, \
                 count_aff) = \
                 convert_processed_auth_aff_line_to_marc_xml(l.replace('\n',''), \
                                                                 first_auth_aff)
                processed_lines.append(xml_line)

        else:
            ## document body is empty, therefore the reference section is empty:
            extract_lines = []
            processed_lines = []

        ## 4. Display the extracted references, status codes, etc:
        if cli_opts['output_raw']:
            ## now write the raw references to the stream:
            raw_file = str(recid) + '.rawrefs'
            try:
                rawfilehdl = open(raw_file, 'w')
                write_raw_references_to_stream(recid, extract_lines, rawfilehdl)
                rawfilehdl.close()
            except:
                write_message("***%s\n\n" % raw_file, \
                                  sys.stderr, verbose=0)
                halt(err=IOError, msg="Error: Unable to write to '%s'" \
                              % raw_file, exit_code=1)
        ## If found ref section by a weaker method and only found misc/urls then junk it
        ## studies show that such cases are ~ 100% rubbish. Also allowing only
        ## urls found greatly increases the level of rubbish accepted..
        if count_reportnum + count_title == 0 and how_found_start > 2:
            count_misc = count_url = count_doi = count_auth_group = 0
            processed_lines = []
            if cli_opts['verbosity'] >= 1:
                sys.stdout.write("-----Found ONLY miscellaneous/Urls so removed it how_found_start=  %d\n" % (how_found_start))
        elif  count_reportnum + count_title  > 0 and how_found_start > 2:
            if cli_opts['verbosity'] >= 1:
                sys.stdout.write("-----Found journals/reports with how_found_start=  %d\n" % (how_found_start))

        if extract_top_section_metadata:
            out = display_auth_aff_xml_record(recid, \
                                                  processed_lines)
        else:
            ## Display the processed reference lines:
            out = display_references_xml_record(extract_error, \
                                                    count_reportnum, \
                                                    count_title, \
                                                    count_url, \
                                                    count_doi, \
                                                    count_misc, \
                                                    count_auth_group, \
                                                    recid, \
                                                    processed_lines)

            ## Compress mulitple 'm' subfields in a datafield
            out = compress_subfields(out, CFG_REFEXTRACT_SUBFIELD_MISC)
            ## Compress multiple 'h' subfields in a datafield
            out = compress_subfields(out, CFG_REFEXTRACT_SUBFIELD_AUTH)

            ## Filter the processed reference lines to remove junk
            out = filter_processed_lines(out)  ## Be sure to call this BEFORE compress_subfields
                                               ## since filter_processed_lines expects the
                                               ## original xml format.

        lines = out.split('\n')
        write_message("-----display_xml_record gave: %s significant " \
                         "lines of xml, overall error: %s\n" \
                         % (str(len(lines) - 7), extract_error), verbose=2)
        if cli_opts['xmlfile']:
            ofilehdl.write("%s" % (out.encode("utf-8"),))
            ofilehdl.flush()
        else:
            ## Write the record to the standard output stream:
            sys.stdout.write("%s" % out.encode("utf-8"))

    ## If an XML collection was opened, display closing tag
    if done_coltags:
        if (cli_opts['xmlfile']):
            ofilehdl.write("%s\n" \
                               % CFG_REFEXTRACT_XML_COLLECTION_CLOSE.encode("utf-8"))
            ofilehdl.close()
            ## limit m tag data to something less than infinity
            limit_m_tags(cli_opts['xmlfile'], 2024)
        else:
            sys.stdout.write("%s\n" \
                                 % CFG_REFEXTRACT_XML_COLLECTION_CLOSE.encode("utf-8"))

