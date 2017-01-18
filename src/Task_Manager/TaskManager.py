# Task Manager.py
# Serves to decide what actions need to be taken next to facilitate
# conversation for the Dialogue Manager

import psycopg2
import numpy as np
#from src.Dialog_Manager import Course

class Course:
    def __init__(self):
        #name of class
        self.name = None
        self.id = None
        self.prof = None
        self.term = None
        self.department = None
        self.courseNum = None
        self.term = None
        #A score from 1-10 of how much they liked the class
        self.sentiment = 0
        #how confident are we in this sentiment
        self.confidence = 0
        self.scrunch = False
        self.requirements_fulfilled = []
        #Some way of storing start time, end time, and days of the week. Format undecided as of yet.
        self.time = None
        self.prereqs = []
        #description from enroll
        self.description = ""
        #context the user gave about the class, just in case we still need it
        self.user_description = ""
        #Boolean. Have they taken the class yet?
        self.taken = None
        self.credits = None


def connect_to_db():

    conn = psycopg2.connect(host = "cmc307-07.mathcs.carleton.edu", \
    database = "dialogcomps", user = "dialogcomps", password = "dialog!=comps")

    return conn

def query_courses(course):
    '''
    Returns a list of course objects which share the attributes defined for the
    course object passed as argument. Used to query courses based on multiple
    criteria.
    '''

    conn = connect_to_db()
    #(sec_term LIKE '16%' OR sec_term LIKE '17%')
    course_query = "SELECT * FROM COURSE WHERE (sec_term LIKE '16%' OR sec_term LIKE '17%') AND "

    if course.department != None:
        course_query = course_query + "sec_subject = '" + course.department
        course_query = course_query + "' AND "

    if course.courseNum != None:
        course_query = course_query + "sec_course_no = '" \
        + str(course.courseNum)
        course_query = course_query + "' AND "

    course_query = course_query[:-5]

    cur = conn.cursor()
    cur.execute(course_query)
    course_results = cur.fetchall()

    print(course_query)

    results = []

    for result in course_results:
        print("Getting results from query")
        print(result)
        result_course = Course()
        result_course.department = result[17]
        result_course.courseNum = result[2]
        result_course.id = result[13]
        result_course.name = result[16]
        #result_course.comments = result[6]
        result_course.term = result[19]
        classroom_str = result[24]
        if classroom_str != None:
            classroom_str = classroom_str.split()
            classroom = classroom_str[0] + " " + classroom_str[1]
            result_course.time = classroom

        results.append(result_course)
        #academic_session

    for result in results:

        reason_query = "SELECT * FROM REASON WHERE "

        if result.id != None:
            reason_query = reason_query + "course_number = '" \
                 + result.id
            reason_query = reason_query + "' AND "

            if result.term != None:
                reason_query = reason_query + "academic_session = '" \
                     + result.term
                reason_query = reason_query + "' AND "

        elif course.department != None:
            reason_query = reason_query + "org_id = '" + course.department
            reason_query = reason_query + "' AND "

        elif course.courseNum != None:
            reason_query = reason_query + "course_number = '" \
            + str(course.courseNum)
            reason_query = reason_query + "' AND "

        reason_query = reason_query[:-5]

        #print(reason_query)

        cur = conn.cursor()
        cur.execute(reason_query)
        course_results = cur.fetchone()

        #print(course_results)

        result.description = course_results[16]

    #list_courses = []

    return results

def query_by_string(course_description, connection):
    '''
    Returns a list of course objects based on a string containing keywords
    about the course which were not parsed into a set of specific criteria.
    General search algorithm for courses based on a string description.
    '''
    conn = connection

    list_courses = []

    return list_courses

def smart_department_search(keywords):
    conn = connect_to_db()
    recommended_departments = set()
    keywords_str = " in {}".format(str(tuple(keywords))) if len(keywords) > 1 else " = '{}'".format(keywords[0])
    query = "SELECT * FROM occurence where words {};".format(keywords_str)
    cur = conn.cursor()
    cur.execute(query)
    for result in cur:
        r = get_n_best_indices(result, 2)
        for i in r:
            recommended_departments.add(i)
    colnames = [desc[0] for desc in cur.description]    
    department_names = []
    for i in recommended_departments - set((0,)):
        department_names.append(colnames[i])
    return department_names

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
    print(smart_keyword_search(["physics"]))

