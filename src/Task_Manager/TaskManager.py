# Task Manager.py
# Serves to decide what actions need to be taken next to facilitate
# conversation for the Dialogue Manager
import psycopg2
import numpy as np
import string
import io
import string
from src.Dialog_Manager import Course

conn = None
dept_dict = {}
distro_list = []
stop_words = None

def init():
    connect_to_db()
    create_dept_dict()
    create_distro_list()
    create_stop_words_set()


def connect_to_db():
    global conn
    conn = psycopg2.connect(host = "cmc307-07.mathcs.carleton.edu", \
    database = "dialogcomps", user = "dialogcomps", password = "dialog!=comps")

# @params Course object 'course' containing some initialized member variables,
# and searches for courses which share those values
# @return List of length >= 0 containing Course objects which match the input
def query_courses(course):
    '''
    Returns a list of course objects which share the attributes defined for the
    course object passed as argument. Used to query courses based on multiple
    criteria.
    '''

    #print("ENTERING QUERY COURSES FUNCTION")
    print("QUERYING COURSES: ")

    course_query = "SELECT * FROM COURSE WHERE ((sec_term LIKE '17%') AND sec_term NOT LIKE '%SU') AND "

    if course.department != "":
        course_query = course_query + "sec_subject = '" + course.department.upper()
        course_query = course_query + "' AND "
        print(course.department)

    if course.course_num != "":
        course_query = course_query + "sec_course_no = '" \
        + str(course.course_num)
        course_query = course_query + "' AND "
        print(course.course_num)

    if course.name != "":
        course_name = smart_description_expansion(str(course.name))
        course_query = course_query + "lower(sec_short_title) = '" \
        + course_name
        course_query = course_query + "' AND "
        print(course.name)

    course_query = course_query + "sec_name NOT LIKE '%WL%' AND sec_avail_status = 'Open'"

    global conn

    cur = conn.cursor()
    cur.execute(course_query)
    course_results = cur.fetchall()

    #print(course_query)

    results = fill_out_courses(course_results)
    return list(set(results))


# Takes a title string and a potential department, returns a list of classes
# @params String object 'title_string'
# @params Optional String object 'department'
# @return List of length >= 0 containing Course objects which match title_string
def query_by_title(title_string, department = None):
    # just confirming that we are being given a string
    if type(title_string) != type("this is a string"):
        return []

    print("QUERYING BY COURSES: " + title_string)
    if department != None:
        print(department)

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
            new_string = new_string  + " " + new_word_array[i].lower() + "%"
            if word_array[i].upper() not in dept_dict:
                # do nothing if a stop word is currently being read
                if word_array[i].lower() in stop_words:
                    continue
                else:
                    cur_string = cur_string + " " + word_array[i].lower() + "%"
            else:
                cur_string = cur_string + " " \
                + dept_dict[word_array[i].upper()].lower() + "%"
        else:
            new_string = new_string  + new_word_array[i].lower() + "%"
            if word_array[i] not in dept_dict:
                if word_array[i] in stop_words:
                    continue
                else:
                    cur_string = cur_string + word_array[i].lower() + "%"
            else:
                cur_string = cur_string + dept_dict[word_array[i]].lower() + "%"

    # Placing both strings in a query for the database
    query_string = "SELECT * FROM COURSE WHERE ((sec_term LIKE '17%') AND sec_term NOT LIKE '%SU') AND \
                    (lower(sec_short_title) LIKE '{}' OR \
                    lower(sec_short_title) \
                    LIKE '{}') AND sec_name NOT LIKE '%WL%'".format(new_string, cur_string)

    # adding a deparment criteria to narrow search if passed
    if department != None:
        query_string = query_string + " AND sec_subject = '" + department + "'"

    cur = conn.cursor()
    cur.execute(query_string)

    results = cur.fetchall()
    courses = fill_out_courses(results)

    return list(set(courses))


# Helper function that takes the SQL results list, and fills out a list of
# course objects according to the contents of the SQL list. Only works if the
# SQL query is run on course with a SELECT * function. Otherwise, will have an
# index out of bounds error.
# returns a list of course objects
def fill_out_courses(results, new_keywords=None, student_major=None, student_interests=None):
    global conn
    cur = conn.cursor()
    courses = []
    for result in results:
        result_course = Course.Course()
        #result_course = Course()
        result_course.department = result[17]
        result_course.course_num = result[2]
        result_course.id = result[13]
        result_course.name = result[16]
        result_course.term = result[19]
        result_course.credits = result[11]
        classroom_str = result[24]
        if classroom_str != None:
            classroom_str = classroom_str.split()
            classroom = classroom_str[0] + " " + classroom_str[1]
            result_course.classroom = classroom
        result_course.description = result[29]
        # adding professor information based on id found in courses
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

        # only runs in the case where this is called by query_by_keywords
        # uses the new_keywords list in the query_by_keywords function
        if new_keywords is not None:
            relevance_list, weighted_relevance = calculate_course_relevance(result_course, new_keywords,
                                                                            student_major, student_interests)
            result_course.relevance = relevance_list
            result_course.weighted_score = weighted_relevance
        courses.append(result_course)

    return courses

# Helper function
def makeCooccurenceMatrix():
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

    for dept in dept_results:
        print("dept: {}".format(dept[0]))
        if dept[0] != None:
            courses_query = "select title, long_description from reason where org_id = "
            courses_query = courses_query + "'" + str(dept[0]) + "'"
            cur.execute(courses_query)
            dept_tuples = cur.fetchall()

            punctuationset = set(string.punctuation)
            dept_dictionary = {}
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
    print("Done with that")
    distinct_word_list = list(distinct_word)
    matrix = []
    for (dept_name, d) in dept_dictionaries:
        print("Dept_name {}".format(dept_name))
        l = [None] * (len(distinct_word_list) + 1)
        l[0] = make_tuple(dept_name)[0]
        for i, word in enumerate(distinct_word_list):
            r = i + 1
            if word in d:
                l[r] = d[word]
            else:
                l[r] = 0
        matrix.append(l)

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
        print(row)
        if sum(row) < 5:
            continue
        numrows += 1
        row_str = [str(d) for d in row]
        if i > 0:
            row_str.insert(0, distinct_word_list[i - 1])
        result_file.write(','.join(row_str))
        result_file.write('\n')
    result_file.close()
    print("Rows: {}".format(numrows))

# checks if a description can be expanded from shorthand used
# @params String object 'description' which contains some keywords for query
# @return String object which has all shorthand keywords expanded
def smart_description_expansion(description):
    print("EXPANDING DESCRIPTION: " + description)
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
        print("RETURNING EXPANDED: " + new_description)
        return new_description
    else:
        return description

def create_stop_words_set():
    global stop_words
    stop_words = set()
    stop_words_file = open('./src/Task_Manager/stop_words.txt', 'r')
    #stop_words_file = open('stop_words.txt', 'r')
    for word in stop_words_file:
        stop_words.add(word.strip())
    stop_words.add("register")
    stop_words.add("course")
    stop_words.add("interest")
    stop_words.add("major")

def create_distro_list():
    global distro_list
    distro_list = "a_and_i;arts_practice;statistical_reasoning;lab;literary_analysis;humanistic_inquiry;social_inquiry;\
        writing_rich_1;writing_rich_2;quantitative_reasoning;\
        intercultural_domestic_studies;international_studies".split(';')

# takes a list of keywords, returns a list of classes
# @params List object 'keywords' which contains words to query on
# @params Optional int 'threshold' which limits number of courses to return
# @return List of length >= 0 containing Course objects which matched keywords
def query_by_keywords(keywords, exclude=None, threshold = 3, student_department=None, student_interests=None):
    if type(keywords) != type([]):
        print("QUERY BY KEYWORDS NOT PASSED LIST TYPE")
        return []

    global stop_words
    recommended_departments = set()
    new_keywords = []
    for keyword in keywords:
        kss = smart_description_expansion(keyword)
        #new_keywords.append(keyword)
        #new_keywords.append(kss)
        ks = kss.split()
        for k in ks:
            if k.lower() not in stop_words:
                new_keywords.append(k.upper())

    # trying to catch any errors if new_keywords is never changed
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
    #print(department_names)
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
    courses = fill_out_courses(results, new_keywords, student_major=student_department,
                               student_interests=student_interests)
    courses = list(set(courses))
    courses.sort(key = lambda course: course.weighted_score)
    courses.reverse()
    if len(courses) < 1:
        return []
    max = courses[0].weighted_score
    for course in courses:
        val = max - threshold
        if course.weighted_score < val:
            courses.remove(course)
    if exclude is None:
        return courses
    coursesToReturn = []
    excludeCourses = set(exclude)
    for course in courses:
        if course not in excludeCourses:
            coursesToReturn.append(course)
    return coursesToReturn

# queries a list of classes that fill out a distribution
def query_by_distribution(distribution, department = None):
    global dept_dict
    global conn

    print("QUERYING BY DISTRO: " + distribution)
    # resetting the department to be the four letter code
    if department != None:
        dept_items = dept_dict.items()
        for key, value in dept_items:
            if department == key or department == value:
                department = key
                print(department)
    # Building the query string
    query_string = "SELECT DISTINCT course_name FROM distribution WHERE {} > 0".format(distribution)
    if department != None:
        query_string = query_string + "AND actual_dept = '{}".format(department)
        query_string = query_string + "'"

    cur = conn.cursor()

    cur.execute(query_string)

    results = cur.fetchall()
    course_results = []
    for result in results:
        try:
            course = Course.Course()
            course.department = result[0][:-3]
            course.course_num = result[0][-3:]

            course_results.extend(query_courses(course))
        except:
            continue

    return course_results


def calculate_course_relevance(course_obj, new_keywords, student_major_dept, student_interests):
    relevance = [0, 0, 0, 0]
    punctuationset = set(string.punctuation)
    description = course_obj.description
    description = ''.join(ch for ch in description if ch not in punctuationset)
    title = course_obj.name
    title = ''.join(ch for ch in title if ch not in punctuationset)
    words = description.split()
    words2 = title.split()
    distinct_keywords = set([])
    distinct_keywords2 = set([])
    for word in words:
        if word.upper() in new_keywords:
            relevance[1] += 1
            distinct_keywords.add(word.upper())
    for word in words2:
        if word.upper() in new_keywords:
            relevance[1] += 1
            distinct_keywords2.add(word.upper())
    relevance[0] = len(distinct_keywords)
    relevance[0] += len(distinct_keywords2)
    if student_major_dept is not None:
        for major in student_major_dept:
            if department_match(course_obj.department) == department_match(major):
                relevance[2] += 1
    if student_interests is not None:
        for interest in student_interests:
            if interest in course_obj.description:
                relevance[3] += 1
    weights = [10, 1, 6, 3]
    weighted_score = sum([relevance[i] * weights[i] for i in range(len(relevance))])
    return relevance, weighted_score

# called in the init function, reads the file to create a dictionary
def create_dept_dict():
    global dept_dict
    file = open('./src/Task_Manager/course_subjects.txt', 'r')
    #file = open('course_subjects.txt', 'r')
    for line in file:
        line = line.strip()
        pair = line.split(';')

        dept_dict[pair[0]] = pair[1]

## Taken from wiki/Algorithm_Implementation ##
def edit_distance(s1, s2):
    if len(s1) < len(s2):
        return edit_distance(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

# @params String object 'str_in' which is a department code or description
# @return String object that is the best guess for a valid, capitalized dept code
def department_match(str_in):
    print("MATCHING DEPT: " + str_in)
    if str_in.isspace():
        return None
    global dept_dict
    global stop_words

    # if the string is in our set of stop words, we return nothing
    if str_in in stop_words:
        return None

    if str_in.lower() == "major":
        return None

    cur_match = None
    cur_best = 100
    dept_items = dept_dict.items()
    # check to see if the input already matches a department
    for key, value in dept_items:
        if str_in.upper() == key:
            return value
        if str_in.lower() == value.lower():
            return value
    # otherwise, use edit distance to find the nearest major
    for key in dept_dict:
        dist = edit_distance(key,str_in.upper())
        if dist < cur_best:
            cur_match = dept_dict[key]
            cur_best = dist
        dist = edit_distance(dept_dict[key],str_in)
        if dist < cur_best:
            cur_match = dept_dict[key]
            cur_best = dist
    print("MATCHED: " + cur_match)
    return cur_match

def distro_match(str_in):
    if str_in.isspace():
        return None
    elif str_in == "":
        return None
    elif str_in == None:
        return None

    global dept_dict
    global distro_list
    global stop_words

    # if the string is in our set of stop words, we return nothing
    if str_in in stop_words:
        return None

    if '&' in str_in:
        return "a_and_i"
    elif "science" in str_in.split():
        return "lab"
    elif "art" in str_in.split() or "arts" in str_in.split():
        return "arts_practice"
    elif "domestic" in str_in.split() or "intercultural" in str_in.split():
        return "intercultural_domestic_studies"
    else:
        cur_best = 100
        cur_match = None
        str_expand = smart_description_expansion(str_in)
        for distro in distro_list:
            distro_str = distro.replace('_',' ')
            edit_dist = edit_distance(distro_str, str_expand)
            if edit_dist < cur_best:
                cur_best = edit_dist
                cur_match = distro
        return cur_match



def get_n_best_indices(row, n):
    res = []
    arr = np.array(row[1:len(row)])
    while len(res) < n:
        i = np.argmax(arr)
        if arr[i] == 0:
            return arr
        res.append(i + 1)
        arr[i] = 0
    return res


if __name__ == "__main__":
    init()
    '''
    results = query_by_distribution("literary_analysis", "ENGL")
    for course in results:
        print(course.name)
        print(course.description)
        '''
