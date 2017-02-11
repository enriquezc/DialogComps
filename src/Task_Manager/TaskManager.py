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
stop_words = None

def init():
    connect_to_db()
    create_dept_dict()
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

    course_query = "SELECT * FROM COURSE WHERE ((sec_term LIKE '16%' OR \
                    sec_term LIKE '17%') AND sec_term NOT LIKE '%SU') AND "

    if course.department != None:
        course_query = course_query + "sec_subject = '" + course.department.upper()
        course_query = course_query + "' AND "

    if course.course_num != None:
        course_query = course_query + "sec_course_no = '" \
        + str(course.course_num)
        course_query = course_query + "' AND "

    if course.name != None:
        course_name = smart_description_expansion(str(course.name))
        course_query = course_query + "lower(sec_short_title) = '" \
        + course_name
        course_query = course_query + "' AND "

    course_query = course_query[:-5]

    global conn

    cur = conn.cursor()
    cur.execute(course_query)
    course_results = cur.fetchall()

    #print(course_query)

    results = []

    for result in course_results:
        result_course = Course.Course()
        result_course.department = result[17]
        result_course.course_num = result[2]
        result_course.id = result[13]
        result_course.name = result[16]
        result_course.term = result[19]
        classroom_str = result[24]
        if classroom_str != None:
            classroom_str = classroom_str.split()
            if len(classroom_str) > 1:
                classroom = classroom_str[0] + " " + classroom_str[1]
                result_course.classroom = classroom
            else:
                result_course.classroom = None
        result_course.description = result[29]

        if result[21] != None:
            result_course.faculty_id = result[21]
            if '|' in result_course.faculty_id:
                prof_ids = result_course.faculty_id.split('|')
                query_str = "SELECT DISTINCT * FROM professors WHERE id = "
                for id_num in prof_ids:
                    query_str = query_str + str(int(id_num)) + " OR id = "
                query_str = query_str[:-9]
                cur.execute(query_str)
                names = cur.fetchall()
                result_course.faculty_id = ""
                for result in names:
                    if len(result) > 1:
                        result_course.faculty_id = result_course.faculty_id + result[0] + ","
                        result_course.faculty_name = result_course.faculty_name + result[1] + ","
                    else:
                        result_course.faculty_id = None
                        result_course.faculty_name = None
                if result_course.faculty_name != None and result_course.faculty_id != None:
                    result_course.faculty_name = result_course.faculty_name[:-1]
                    result_course.faculty_id = result_course.faculty_id[:-1]
            else:
                query_str = "SELECT name FROM professors WHERE id = \'" \
                             + str(int(result_course.faculty_id)) + "'"
                cur.execute(query_str)
                name = cur.fetchall()
                if len(name) > 0 and len(name[0]) > 0:
                    result_course.faculty_name = name[0][0]
        results.append(result_course)
    return results


# Takes a title string and a potential department, returns a list of classes
# @params String object 'title_string'
# @params Optional String object 'department'
# @return List of length >= 0 containing Course objects which match title_string
def query_by_title(title_string, department = None):
    # just confirming that we are being given a string
    if type(title_string) != type("this is a string"):
        return []

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
                if word_array[i] in stop_words:
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
    query_string = "SELECT * FROM COURSE WHERE ((sec_term LIKE '16%' \
                    OR sec_term LIKE '17%') AND sec_term NOT LIKE '%SU') AND \
                    (lower(sec_short_title) LIKE '{}' OR \
                    lower(sec_short_title) \
                    LIKE '{}')".format(new_string, cur_string)

    # adding a deparment criteria to narrow search if passed
    if department != None:
        query_string = query_string + " AND sec_subject = '" + department + "'"

    cur = conn.cursor()
    print(cur.mogrify(query_string))
    cur.execute(query_string)

    results = cur.fetchall()
    courses = []
    for result in results:
        result_course = Course.Course()
        #result_course = Course()
        result_course.department = result[17]
        result_course.course_num = result[2]
        result_course.id = result[13]
        result_course.name = result[16]
        result_course.term = result[19]
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
                query_str = "SELECT * FROM professors WHERE id = "
                for id_num in prof_ids:
                    query_str = query_str + str(int(id_num)) + " OR id = "
                query_str = query_str[:-9]
                cur.execute(query_str)
                names = cur.fetchall()
                result_course.faculty_id = ""
                for result in names:
                    if len(result) > 1:
                        result_course.faculty_id = result_course.faculty_id + result[0] + ","
                        result_course.faculty_name = result_course.faculty_name + result[1] + ","
                    else:
                        result_course.faculty_id = None
                        result_course.faculty_name = None
                result_course.faculty_name = result_course.faculty_name[:-1]
                result_course.faculty_id = result_course.faculty_id[:-1]
            else:
                query_str = "SELECT name FROM professors WHERE id = \'" \
                             + str(int(result_course.faculty_id)) + "'"
                cur.execute(query_str)
                name = cur.fetchall()
                if len(name) > 0 and len(name[0]) > 0:
                    result_course.faculty_name = name[0][0]

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

# takes a list of keywords, returns a list of classes
# @params List object 'keywords' which contains words to query on
# @params Optional int 'threshold' which limits number of courses to return
# @return List of length >= 0 containing Course objects which matched keywords
def query_by_keywords(keywords, threshold = None):
    if type(keywords) != type([]):
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
            if k not in stop_words:
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
             AND ((sec_term LIKE '16%' OR sec_term LIKE '17%') \
             AND sec_term NOT LIKE '%SU')".format(str(tuple(department_names)))
    query += " AND (UPPER(long_description) LIKE '%{}%'".format(new_keywords[0])
    if len(keywords) > 1:
        for keyword in new_keywords[1:]:
            query += "OR UPPER(long_description) LIKE '%{}%'".format(keyword)

    query += ")"
    cur.execute(query)
    results = cur.fetchall()
    courses = []
    for result in results:
        new_course = Course.Course()
        new_course.department = result[17]
        new_course.course_num = result[2]
        new_course.id = result[13]
        new_course.name = result[16]
        new_course.description = result[29]
        new_course.relevance = [0,0]
        punctuationset = set(string.punctuation)
        description = new_course.description
        description = ''.join(ch for ch in description if ch not in punctuationset)
        title = new_course.name
        title = ''.join(ch for ch in title if ch not in punctuationset)
        words = description.split()
        words2 = title.split()
        distinct_keywords = set([])
        distinct_keywords2 = set([])
        for word in words:
            if word.upper() in new_keywords:
                new_course.relevance[1] = new_course.relevance[1] + 1
                distinct_keywords.add(word.upper())
        for word in words2:
            if word.upper() in new_keywords:
                new_course.relevance[1] = new_course.relevance[1] + 1
                distinct_keywords2.add(word.upper())
        new_course.relevance[0] = len(distinct_keywords)
        new_course.relevance[0] = new_course.relevance[0] + len(distinct_keywords2)
        new_course.weighted_score = 10 * new_course.relevance[0] + new_course.relevance[1]
        courses.append(new_course)

    courses.sort(key = lambda course: (course.relevance[0], course.relevance[1]))
    courses.reverse()
    if threshold != None:
        for course in courses:
            if course.weighted_score < threshold:
                courses.remove(course)
    return courses

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
    global dept_dict
    cur_match = None
    cur_best = 100
    if str_in.upper() in dept_dict.keys():
        return str_in.upper()
    for key in dept_dict:
        dist = edit_distance(key,str_in.upper())
        if dist < cur_best:
            cur_match = key
            cur_best = dist
        dist = edit_distance(dept_dict[key],str_in)
        if dist < cur_best:
            cur_match = dept_dict[key]
            cur_best = dist
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

    results = smart_department_search(["sports"])
    for course in results:
        print(course.name)
        print(course.description)
