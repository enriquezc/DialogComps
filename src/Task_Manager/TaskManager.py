"""
 TaskManager.py
 Serves to decide what actions need to be taken next to facilitate conversation for the Dialog Manager

"""

import psycopg2
import numpy as np
import string
import io
import string
from src.Dialog_Manager import Course
import src.utils.debug as debug
import json

conn = None
dept_dict = {}
distro_dict = {}
major_dict = {}
concentration_dict = {}
stop_words = None
debug_value = None

def init(init_debug = False):

    create_dept_dict()
    create_major_dict()
    create_concentration_dict()
    create_distro_dictionary()
    create_stop_words_set()

    global debug_value
    debug_value = init_debug

    config_file = open("./config.json")
    config = json.load(config_file)
    connect_to_db(config["database_host"], config["database_name"], config["database_password"])

def connect_to_db(db_host, db_name, db_password):
    global conn
    conn = psycopg2.connect(host = db_host, \
    database = db_name, user = db_name, password = db_password)


def query_courses(course, approximate = False):
    '''
    Returns a list of course objects which share the attributes defined for the
    course object passed as argument. Used to query courses based on multiple
    criteria.
    :param course: course object that has a select group of attributes already
    filled
    :param approximate: boolean flag that tell us whether or not to use
    approximations instead of precise course numbers
    :return: a list of course objects
    '''

    #call_debug_print("ENTERING QUERY COURSES FUNCTION")
    call_debug_print("QUERYING COURSES: ")

    course_query = "SELECT * FROM COURSE WHERE ((sec_term LIKE '17%') AND sec_term NOT LIKE '%SU') AND "
    if not approximate:
        if course.department != "":
            course_query = course_query + "sec_subject = '" + course.department.upper()
            course_query = course_query + "' AND "
            call_debug_print(course.department)

        if course.course_num != "":
            course_query = course_query + "sec_course_no = '" \
            + str(course.course_num)
            course_query = course_query + "' AND "
            call_debug_print(course.course_num)

        if course.name != "":
            course_name = smart_description_expansion(str(course.name))
            course_query = course_query + "lower(sec_short_title) = '" \
            + course_name
            course_query = course_query + "' AND "
            call_debug_print(course.name)

    else:
        if course.department != "":
            course_query = course_query + "sec_subject = '" + course.department.upper()
            course_query = course_query + "' AND "
            call_debug_print(course.department)

        if course.course_num != "":
            if type(course.course_num) is list:
                course_query += "("
                for course_num_level in course.course_num:
                     course_query += "sec_course_no LIKE '" + course_num_level[:-2]
                     course_query += "%%' OR "
                course_query = course_query[:-3]
                course_query += ") AND "
            elif type(course.course_num) is str:
                if course.course_num == "100":
                    course_query = course_query + "sec_course_no LIKE '1%%' AND "
                elif course.course_num == "200":
                    course_query = course_query + "sec_course_no LIKE '2%%' AND "
                elif course.course_num == "300":
                    course_query = course_query + "sec_course_no LIKE '3%%' AND "

    course_query = course_query + "sec_name NOT LIKE '%WL%' AND sec_avail_status = 'Open'"

    global conn

    cur = conn.cursor()
    cur.execute(course_query)
    course_results = cur.fetchall()

    #call_debug_print(course_query)

    results = fill_out_courses(course_results)
    return list(set(results))


def query_by_title(title_string, department = None):
    """
    Takes an approximate title, and uses the LIKE syntax to find the nearest
    course that matches that course
    :param title_string: string that is an approximation of the title
    :param department: department that could be used to limit the query
    :return: a list of course objects
    """
    if type(title_string) != type("this is a string"):
        return []

    call_debug_print("QUERYING BY COURSES: " + title_string)
    if department != None:
        call_debug_print(department)

    global conn
    word_array = title_string.split()
    new_word_array = title_string.split()

    # if there is only whitespace in our title_string, we return an empty list
    if len(new_word_array) < 1:
        return []

    # putting each word in the title string into smart description to check if
    # the word can be expanded
    for i in range(len(word_array)):
        new_word_array[i] = smart_description_expansion(word_array[i])

    new_string = "%"
    cur_string = "%"
    for i in range(len(new_word_array)):
        # if the first word is being read, no need for a space before the word
        # anything else, and we add a space before
        if i > 0:
            new_string = new_string + " " + new_word_array[i].lower() + "%"
            if word_array[i].upper() not in dept_dict:
                # do nothing if a stop word is currently being read
                if word_array[i].lower() in stop_words:
                    continue
                else:
                    cur_string = cur_string + " " + word_array[i].lower() + "%"
            else:
                dept_string = dept_dict[word_array[i].upper()].lower()
                for word in dept_string.split():
                    if word in stop_words:
                        dept_string = dept_string.replace(" " +word, "%")
                cur_string = cur_string + " " + dept_string + "%"
        else:
            new_string = new_string + new_word_array[i].lower() + "%"
            if word_array[i].upper() not in dept_dict:
                if word_array[i] in stop_words:
                    continue
                else:
                    cur_string = cur_string + word_array[i].lower() + "%"
            else:
                dept_string = dept_dict[word_array[i].upper()].lower()
                for word in dept_string.split():
                    if word in stop_words:
                        dept_string = dept_string.replace(word, "%")
                cur_string = cur_string + dept_string + "%"
    call_debug_print(new_string)
    call_debug_print(cur_string)
    # Placing both strings in a query for the database
    query_string = "SELECT * FROM COURSE WHERE ((sec_term LIKE '17%%') AND sec_term NOT LIKE '%%SU') AND \
                    (lower(sec_short_title) LIKE %s OR \
                    lower(sec_short_title) \
                    LIKE %s) AND sec_name NOT LIKE '%%WL%%'"

    # adding a deparment criteria to narrow search if passed
    if department != None:
        query_string = query_string + " AND sec_subject = '" + department + "'"

    cur = conn.cursor()
    call_debug_print(cur.mogrify(query_string, (new_string, cur_string)))
    cur.execute(query_string, (new_string, cur_string))

    results = cur.fetchall()
    courses = fill_out_courses(results)
    for course in courses:

        call_debug_print(course.name)


    return list(set(courses))



def fill_out_courses(results, new_keywords = None, student_major = None, student_interests = None):
    """
    Helper function that takes the SQL results list, and fills out a list of course objects according to the contents
    of the SQL list. Only works if the SQL query is run on course with a SELECT * function. Otherwise, will have an
    index out of bounds error
    :param results: List of PSQL query result arrays
    :param new_keywords: List of String keywords to determine relevancy with
    :param student_major: String major of Student object query being done for
    :param student_interests: List of String interests of Student object query being done for
    :return: List of Course objects built from query results
    """

    global conn

    cur = conn.cursor()
    courses = []

    for result in results:
        # Build Course object from current result
        result_course = Course.Course()
        result_course.department = result[17]
        result_course.course_num = result[2]
        result_course.id = result[13]
        result_course.name = result[16]
        result_course.term = result[19]
        result_course.credits = result[11]

        # Parse classroom/meeting times/description/prerequisites if defined
        if result[24] != None:
            res = parse_time_room(result[24])
            if res != None:
                result_course.classroom = res[0]
                result_course.time = res[1]
        if result[29] != None:
            result_course.description = result[29]
        if result[30] != None:
            result_course.prereqs = result[30]
        call_debug_print(result_course.prereqs)

        # Adding professor information based on id found in courses
        if result[21] != None:
            result_course.faculty_id = result[21]
            if '|' in result_course.faculty_id:
                prof_ids = result_course.faculty_id.split('|')
                query_str = "SELECT * FROM professors WHERE id = \'"
                for id_num in prof_ids:
                    query_str = query_str + str(int(id_num)) + "' OR id = '"
                query_str = query_str[:-10]
                cur.execute(query_str)
                names = cur.fetchall()
                result_course.faculty_id = ""
                for result in names:
                    result_course.faculty_id = result_course.faculty_id + result[0] + ", "
                    result_course.faculty_name = result_course.faculty_name + result[1] + ", "
                if result_course.faculty_id != "" and result_course.faculty_id != "":
                    result_course.faculty_name = result_course.faculty_name[:-2]
                    result_course.faculty_id = result_course.faculty_id[:-2]
            else:
                query_str = "SELECT name FROM professors WHERE id = \'" \
                             + str(int(result_course.faculty_id)) + "'"
                cur.execute(query_str)
                name = cur.fetchall()
                if len(name) > 0 and len(name[0]) > 0:
                    result_course.faculty_name = name[0][0]

        # Only runs in the case where this is called by query_by_keywords
        # Uses the new_keywords list in the query_by_keywords function
        if new_keywords is not None:
            relevance_list, weighted_relevance = calculate_course_relevance(result_course, new_keywords,
                                                                            student_major, student_interests)
            result_course.relevance = relevance_list
            result_course.weighted_score = weighted_relevance
        courses.append(result_course)

    return courses


def makeOccurenceMatrix():
    """
    Helper function to construct co-occurrence matrix, which is now stored on the database
    """
    from ast import literal_eval as make_tuple
    stop_words = set()
    stop_words_file = open('stop_words.txt', 'r')
    for word in stop_words_file:
        stop_words.add(word.strip())
    global conn

    cur = conn.cursor()

    depts_query = "select distinct org_id from reason"

    cur.execute(depts_query)

    dept_results = cur.fetchall()

    distinct_word = set()
    dept_dictionaries = []

    # Columns correspond to department
    for dept in dept_results:
        call_debug_print("dept: {}".format(dept[0]))
        if dept[0] != None:
            courses_query = "select title, long_description from reason where org_id = "
            courses_query = courses_query + "'" + str(dept[0]) + "'"
            cur.execute(courses_query)
            dept_tuples = cur.fetchall()

            punctuationset = set(string.punctuation)
            dept_dictionary = {}

            # Strip punctuation/stop words and populate distinct words
            for title, description in dept_tuples:
                titleArray = title.split()
                for word in titleArray:
                    w = ''.join(ch for ch in word if ch not in punctuationset)
                    w = w.upper()
                    if w not in stop_words:
                        distinct_word.add(w)
                    if w not in dept_dictionary:
                        dept_dictionary[w] = 1
                    else:
                        dept_dictionary[w] = dept_dictionary[w] + 1

                long_description_array = description.split()
                for word2 in long_description_array:
                    w = ''.join(ch for ch in word2 if ch not in punctuationset)
                    w = w.upper()
                    if w not in stop_words:
                        distinct_word.add(w)
                    if w not in dept_dictionary:
                        dept_dictionary[w] = 1
                    else:
                        dept_dictionary[w] = dept_dictionary[w] + 1


            dept_dictionaries.append((str(dept), dept_dictionary))

    call_debug_print("Done with that")
    distinct_word_list = list(distinct_word)
    matrix = []

    # Build matrix
    for (dept_name, d) in dept_dictionaries:
        call_debug_print("Dept_name {}".format(dept_name))
        l = [None] * (len(distinct_word_list) + 1)
        l[0] = make_tuple(dept_name)[0]
        for i, word in enumerate(distinct_word_list):
            r = i + 1
            if word in d:
                l[r] = d[word]
            else:
                l[r] = 0
        matrix.append(l)

    # Write to csv to upload to sql database
    result_file = io.open('results.csv', 'w', encoding='utf8')
    transpose = []

    for i in range(len(matrix[0])):
        dept_row = []
        for j in range(len(matrix)):
            dept_row.append(matrix[j][i])
        transpose.append(dept_row)
    numrows = 0

    for i, row in enumerate(transpose):
        if i == 0:
            result_file.write(','.join(row))
            result_file.write('\n')
            continue

        call_debug_print(row)

        if sum(row) < 5:
            continue
        numrows += 1
        row_str = [str(d) for d in row]

        if i > 0:
            row_str.insert(0, distinct_word_list[i - 1])

        result_file.write(','.join(row_str))
        result_file.write('\n')

    result_file.close()
    call_debug_print("Rows: {}".format(numrows))


def smart_description_expansion(description):
    """
    Checks if a description can be expanded from shorthand used
    :param description: String which contains some keywords for query
    :return: String description with shorthands expanded
    """

    call_debug_print("EXPANDING DESCRIPTION: " + description)

    global conn

    new_description = ""
    cur = conn.cursor()

    for word in description.split():
        query = "select * from shorthands where lower(short)=lower('{}')".format(word)
        cur.execute(query)
        res = cur.fetchone()
        if res != None:
            s, l = res
            if l != None:
                new_description += " {}".format(l)
            else:
                new_description += " {}".format(word)
        else:
            new_description += " {}".format(word)

    if len(new_description) > 0 and new_description[0] == ' ':
        new_description = new_description[1:]
        call_debug_print("RETURNING EXPANDED: " + new_description)
        return new_description
    else:
        return description

def create_stop_words_set():
    global stop_words
    stop_words = set()
    stop_words_file = open('./src/Task_Manager/stop_words.txt', 'r')
    for word in stop_words_file:
        stop_words.add(word.strip())
    stop_words.add("register")
    stop_words.add("course")
    stop_words.add("interest")
    stop_words.add("major")
    stop_words.add("student")
    stop_words.add("class")
    stop_words.add("i")
    stop_words.add("concentration")
    #stop_words.add("concentrate")
    stop_words.add("concentrator")
    stop_words.add("yes")

def create_distro_dictionary():
    global distro_dict
    distro_dict = {"AI":"a_and_i",
    "ARP":"arts_practice",
    "FSR":"statistical_reasoning",
    "LS":"lab","LA":"literary_analysis",
    "HI":"humanistic_inquiry",
    "SI":"social_inquiry",
    "WR2":"writing_rich_2","QRE":"quantitative_reasoning",
    "IDS":"intercultural_domestic_studies","IS":"international_studies"}


def query_by_keywords(keywords, exclude = None, threshold = 3, student_department = None, student_interests = None):
    """
    Queries a list of Courses based on a list of keyword Strings
    :param keywords: List of String keywords to query based on
    :param exclude: Set of Course objects to be excluded from query
    :param threshold: Optional Integer 'threshold' which limits number of courses to return
    :param student_department: String optional argument of department
    :param student_interests: List of length >= 0 containing Course objects which matched keywords
    :return: List of Course objects return by query, sorted based on relevancy
    """

    if type(keywords) != type([]):
        call_debug_print("QUERY BY KEYWORDS NOT PASSED LIST TYPE")
        return []

    global stop_words

    recommended_departments = set()
    new_keywords = []
    for keyword in keywords:
        kss = smart_description_expansion(keyword)
        ks = kss.split()
        for k in ks:
            if k.lower() not in stop_words:
                new_keywords.append(k.upper())

    # Trying to catch any errors if new_keywords is never changed
    if new_keywords == []:
        return []

    keywords_str = " in {}".format(tuple(new_keywords)) if len(new_keywords) > 1 else " = '{}'".format(new_keywords[0])
    query = "SELECT * FROM occurence where words {};".format(keywords_str)
    global conn
    cur = conn.cursor()
    cur.execute(query)
    results = cur.fetchall()
    for result in results:
        r = get_n_best_indices(result, 2)
        for i in r:
            recommended_departments.add(i)
    colnames = [desc[0] for desc in cur.description]
    department_names = []
    for i in recommended_departments - set((0,)):
        department_names.append(colnames[i].upper())

    # If we don't find any departments to query on, we just return nothing. DM's problem now
    if department_names == []:
        return []

    query = "SELECT DISTINCT * FROM COURSE c where UPPER(sec_subject) in {} \
             AND (( sec_term LIKE '17%') \
             AND sec_term NOT LIKE '%SU')".format(str(tuple(department_names)))
    query += " AND (UPPER(long_description) LIKE '%{}%'".format(new_keywords[0])

    if len(keywords) > 1:
        for keyword in new_keywords[1:]:
            query += "OR UPPER(long_description) LIKE '%{}%'".format(keyword)

    query += ")"
    query = query + " AND sec_name NOT LIKE '%WL%'"
    cur.execute(query)
    results = cur.fetchall()

    courses = fill_out_courses(results, new_keywords, student_major = student_department,
                               student_interests = student_interests)
    courses = list(set(courses))

    courses.sort(key = lambda course: course.weighted_score)
    courses.reverse()

    if len(courses) < 1:
        return []

    max = courses[0].weighted_score
    toReturn = []
    val = max * 0.3

    for course in courses:
        if course.weighted_score >= val:
            toReturn.append(course)

    if exclude is None:
        return toReturn

    coursesToReturn = []
    excludeCourses = set(exclude)

    for course in toReturn:
        if course not in excludeCourses:
            coursesToReturn.append(course)

    return coursesToReturn


def query_by_distribution(distribution, department = None, keywords = [], student_major_dept = None):
    """
    Queries a list of courses which fulfill a distribution requirement, considering dept/keywords and major
    :param distribution: String distribution requirement tag
    :param department: String department, initialized to None
    :param keywords: List of keywords included in distribution query, initially empty
    :param student_major_dept: String major of Student object distro is being queried for
    :return: List of Course objects returned by query
    """

    global dept_dict
    global conn

    call_debug_print("QUERYING BY DISTRO: " + distribution)

    # Resetting the department to be the four letter code
    if department != None:
        dept_items = dept_dict.items()
        for key, value in dept_items:
            if department == key or department == value:
                department = key
                call_debug_print(department)

    # Building the query string
    query_string = "SELECT DISTINCT course_name FROM distribution WHERE {} > 0".format(distribution)
    if department != None:
        query_string = query_string + "AND actual_dept = '{}".format(department.upper())
        query_string = query_string + "'"

    # Establishing database connection
    cur = conn.cursor()
    call_debug_print(cur.mogrify(query_string))
    cur.execute(query_string)

    # Fetching results...
    results = cur.fetchall()
    course_results = []
    new_results = []

    for result in results:
        # Try building Course which fulfills distribution
        try:
            course = Course.Course()
            course.department = result[0][:-3]
            course.course_num = result[0][-3:]
            course_results.extend(query_courses(course))
        except:
            continue

    # Check if results should be limited/sorted on defined keywords
    if keywords != []:
        new_keywords = []

        # Expand keywords
        for keyword in keywords:
            kss = smart_description_expansion(keyword)
            ks = kss.split()

            for k in ks:
                if k.lower() not in stop_words:
                    new_keywords.append(k.upper())

        # Calculate relevancy based on keywords/major
        for course in course_results:
            course.weighted_score = calculate_course_relevance(course, new_keywords, student_major_dept, None)[1]
            if course.prereqs == "":
                new_results.append(course)

    # Sort results based on matching if keywords defined
    if keywords != []:
        new_results.sort(key=lambda course: course.weighted_score)
        new_results.reverse()
        course_results = new_results

    # Return 10 best results
    if len(course_results) > 10:
        return course_results[:10]
    else:
        return course_results


def calculate_course_relevance(course_obj, new_keywords, student_major_dept, student_interests):
    """
    Determine weighted score/relevance of course to be returned by query based on keywords, major and interests
    :param course_obj: Course object built from query
    :param new_keywords: List of String keywords to be compared to Course object properties
    :param student_major_dept: String major department of Student object the course is being queried for
    :param student_interests: List of String interests of Student object the course is being queried for
    :return: Tuple containing List of 4 Integer relevance component scores and Integer weighted composite score
    """

    # Relevance components: Number of distinct keywords, keyword matches, major matches, and interest matches
    relevance = [0, 0, 0, 0]

    # Strip punctuation
    punctuationset = set(string.punctuation)
    description = course_obj.description
    description = ''.join(ch for ch in description if ch not in punctuationset)

    title = course_obj.name
    title = ''.join(ch for ch in title if ch not in punctuationset)

    words = description.split()
    words2 = title.split()

    distinct_keywords = set([])
    distinct_keywords2 = set([])

    # Match Course object to properties to keywords
    for word in words:
        if word.upper() in new_keywords:
            relevance[1] += 1
            distinct_keywords.add(word.upper())
    for word in words2:
        if word.upper() in new_keywords:
            relevance[1] += 1
            distinct_keywords2.add(word.upper())

    # Add number of number of distinct keywords to relevancy
    relevance[0] = len(distinct_keywords)
    relevance[0] += len(distinct_keywords2)

    # Match Course object to properties to department
    if student_major_dept is not None:
        for major in student_major_dept:
            if department_match(course_obj.department) == department_match(major):
                relevance[2] += 1

    # Match Course object to properties to interests
    if student_interests is not None:
        for interest in student_interests:
            if interest in course_obj.description:
                relevance[3] += 1

    # Determine weighted score
    weights = [10, 1, 6, 3]
    weighted_score = sum([relevance[i] * weights[i] for i in range(len(relevance))])

    return relevance, weighted_score


def create_dept_dict():
    global dept_dict
    file = open('./src/Task_Manager/course_subjects.txt', 'r')
    #file = open('course_subjects.txt', 'r')
    for line in file:
        line = line.strip()
        pair = line.split(';')

        dept_dict[pair[0]] = pair[1]


def create_major_dict():
    global major_dict
    file = open('./src/Task_Manager/majors.txt', 'r')
    # file = open('course_subjects.txt', 'r')
    for line in file:
        line = line.strip()
        pair = line.split(';')

        major_dict[pair[1]] = pair[0]


def create_concentration_dict():
    global concentration_dict
    file = open('./src/Task_Manager/concentrations.txt', 'r')
    # file = open('course_subjects.txt', 'r')
    for line in file:
        line = line.strip()
        pair = line.split(';')

        concentration_dict[pair[1]] = pair[0]


def edit_distance(s1, s2):
    """
    Deletion, insertion, and replacement edit distance algorithm taken from wiki/Algorithm_Implementation
    :param s1: String to be compared
    :param s2: String to be compared
    :return: Integer smallest number of edits between s1 and s2
    """

    # Order inputs
    if len(s1) < len(s2):
        return edit_distance(s2, s1)

    # Return on empty string input
    if len(s2) == 0:
        return len(s1)

    # For each character/index in s1
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]

        # For each character/index in s2
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)

            # Insert shortest edit operation
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    # Return last dynamic programming table entry
    return previous_row[-1]


# @params String object 'str_in' which is a department code or description
# @return String object that is the best guess for a valid, capitalized dept code
def department_match(str_in):
    """
    Match input string to department
    :param str_in: String description of dept
    :return: String dept
    """

    call_debug_print("MATCHING DEPT: " + str_in)

    # Handling bad input
    if str_in.isspace():
        return None
    elif str_in == "":
        return None
    elif str_in == None:
        return None
    global dept_dict
    global stop_words

    # If the string is in our stop words set, return None type
    if str_in in stop_words:
        return None

    cur_match = None
    cur_best = 100
    dept_items = dept_dict.items()

    # Check to see if the input already matches a department
    for key, value in dept_items:
        if str_in.upper() == key:
            return value
        if str_in.lower() == value.lower():
            return value

    # Otherwise, use edit distance to find the nearest department
    for key in dept_dict:
        dist = edit_distance(key,str_in.upper())
        if dist < cur_best:
            cur_match = dept_dict[key]
            cur_best = dist
        dist = edit_distance(dept_dict[key].lower(),str_in.lower())
        if dist < cur_best:
            cur_match = dept_dict[key]
            cur_best = dist

    return cur_match


def distro_match(str_in):
    """
    Match input string to distribution
    :param str_in: String description of distro
    :return: String distro
    """

    # Handling bad input
    if str_in.isspace():
        return None
    elif str_in == "":
        return None
    elif str_in == None:
        return None

    global distro_dict
    global stop_words

    # If the string is in our set of stop words, we return nothing
    if str_in in stop_words:
        return None

    cur_match = None
    cur_best = 20
    distro_items = distro_dict.items()

    # Check to see if the input already matches a distro
    for key, value in distro_items:
        if str_in.lower() == key.lower():
            return value
        if str_in.lower() == value.lower():
            return value

    # Otherwise, use edit distance to find the nearest distro
    for key in distro_dict:
        dist = edit_distance(key.lower(),str_in.lower())
        if dist < cur_best:
            cur_match = distro_dict[key]
            cur_best = dist
        dist = edit_distance(distro_dict[key].lower(),str_in.lower())
        if dist < cur_best:
            cur_match = distro_dict[key]
            cur_best = dist

    return cur_match


def major_match(str_in):
    """
    Match input string to major
    :param str_in: String description of major
    :return: String major
    """

    # Handling bad input
    if str_in.isspace():
        return None
    elif str_in == "":
        return None
    elif str_in == None:
        return None

    global major_dict
    global stop_words

    # If the string is in stop words set, return None type
    if str_in in stop_words:
        return None

    new_word_array = []
    for word in str_in.split():
        if word not in stop_words:
            new_word_array.append(word)

    str_in = " ".join(new_word_array)

    if str_in.isspace():
        return None

    cur_match = None
    cur_best = 100
    major_items = major_dict.items()

    # Check to see if the input already matches a major
    for key, value in major_items:
        if str_in.lower() == key.lower():
            return key
        if str_in.lower() == value.lower():
            return key

    # Otherwise, use edit distance to find the nearest major
    for key in major_dict:
        dist = edit_distance(key.lower(),str_in.lower())
        if dist < cur_best:
            cur_match = key
            cur_best = dist
        dist = edit_distance(major_dict[key].lower(),str_in.lower())
        if dist < cur_best:
            cur_match = key
            cur_best = dist

    return cur_match


def concentration_match(str_in):
    """
    Match input string to concentration
    :param str_in: String description of concentration
    :return: String concentration
    """

    call_debug_print(str_in)

    # Handling bad input
    if str_in.isspace():
        return None
    elif str_in == "":
        return None
    elif str_in == None:
        return None

    global concentration_dict
    global stop_words

    # If the string is in the stop word set, return None type
    if str_in in stop_words:
        return None
    new_word_array = []
    for word in str_in.split():
        if word not in stop_words:
            new_word_array.append(word)

    str_in = " ".join(new_word_array)

    call_debug_print(str_in)

    cur_match = None
    cur_best = 100
    concentration_items = concentration_dict.items()

    # Check to see if the input already matches a concentration
    for key, value in concentration_items:
        if str_in.lower() == key.lower():
            return key
        if str_in.lower() == value.lower():
            return key

    # Otherwise, use edit distance to find the nearest concentration
    for key in concentration_dict:
        dist = edit_distance(key.lower(),str_in.lower())
        if dist < cur_best:
            cur_match = key
            cur_best = dist
        dist = edit_distance(concentration_dict[key].lower(),str_in.lower())
        if dist < cur_best:
            cur_match = key
            cur_best = dist

    return cur_match


def parse_time_room(str_in):
    """
    Helper function for parsing classroom and meeting time from database string
    :param str_in: String of white space separated classroom/meeting times for course
    :return: Tuple containing classroom string and nested list of meeting time/dates
    """

    # Handling bad input
    if str_in.isspace():
        return None
    elif str_in == "":
        return None
    elif str_in == None:
        return None

    classroom = ""
    meeting_times = []

    # Meeting times separated by | character
    meeting_strings = str_in.split('|')

    for meeting_string in meeting_strings:
        meeting_list = meeting_string.split()

        # Check for valid formatting on DB side
        if len(meeting_list) < 2 or len(meeting_list) > 5:
            return None
        else:
            # Populate classroom string with appropriate substrings
            if classroom == "":
                classroom = meeting_list[0] + " " + meeting_list[1]

            # Check for course with classroom/time still to be determined
            if meeting_list[2] == "TBA" or meeting_list[3] == "TBA":
                break
            elif len(meeting_list) == 5:
                # Each meeting_times list element is a start/end time string tuple
                meeting = [meeting_list[2]]
                meeting.append((meeting_list[3].lstrip('0'), meeting_list[4].lstrip('0')))
                meeting_times.append(meeting)
            else:
                break

    return (classroom, meeting_times)


def query_courses_by_level(course):
    """
    Helper function that triggers general type class queries, setting approximate tag 'True'
    :param course: Course object to be queried on
    :return: List of Course objects returned by query_courses function
    """

    dept = course.department
    for key, value in dept_dict.items():
        if dept.lower() == key.lower() or dept.lower() == value.lower():
            course.department = key.upper()
            break

    return query_courses(course, True)


def get_n_best_indices(row, n):
    """
    Finds the n best departments in a given row
    :param row: List containing occurrence counts by Department
    :param n: Integer size of result List
    :return: List containing best n departments
    """

    res = []
    arr = np.array(row[1:len(row)])

    while len(res) < n:
        i = np.argmax(arr)

        if arr[i] == 0:
            return arr

        res.append(i + 1)
        arr[i] = 0

    return res


def call_debug_print(ob):
    """
    Shell function for debug printing in TaskManager
    :param ob: Object containing debug text/variable to be output to command line
    """

    global debug_value
    debug.debug_print(ob, debug_value)


## main function for isolated testing purposes ##
if __name__ == "__main__":
    init()
    # results = query_by_distribution("quantitative_reasoning", department = None, keywords = ["math", "science", "computer"])
    # for course in results:
    #     print(course.name)
    #     print(course.description)
    #print(major_match("English"))
    #print(concentration_match("NEURO"))
    #print(concentration_match("American Music")[0] + concentration_match("American Music")[1])
    #print(parse_time_room("OLIN 102      T       10:10AM 11:55AM|OLIN 104      T       10:10AM 11:55AM"))
    #print(parse_time_room("COWL DANC     MW      08:55PM 09:35PM"))
    #print(parse_time_room("MDRC LL30     TBA     TBA"))
    #print(parse_time_room("LDC  330      MW      08:30AM 09:40AM|LDC  330      TTH     08:15AM 09:20AM|LDC  330      F       08:30AM 09:30AM"))
    #print(parse_time_room("LDC  345      MTWTHF  08:00AM 05:00PM"))
    '''
    results = query_by_distribution("literary_analysis", "ENGL")
    for course in results:
        call_debug_print(course.name)
        print(course.description)
        '''
