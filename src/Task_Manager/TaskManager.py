# Task Manager.py
# Serves to decide what actions need to be taken next to facilitate
# conversation for the Dialogue Manager

import psycopg2
from src.Dialog_Manager import Course

# class Course:
#     def __init__(self):
#         #name of class
#         self.name = None
#         self.id = None
#         self.prof = None
#         self.term = None
#         self.department = None
#         self.courseNum = None
#         #A score from 1-10 of how much they liked the class
#         self.sentiment = 0
#         #how confident are we in this sentiment
#         self.confidence = 0
#         self.scrunch = False
#         self.requirements_fulfilled = []
#         #Some way of storing start time, end time, and days of the week. Format undecided as of yet.
#         self.time = None
#         self.prereqs = []
#         #description from enroll
#         self.description = ""
#         #context the user gave about the class, just in case we still need it
#         self.user_description = ""
#         #Boolean. Have they taken the class yet?
#         self.taken = None
#         self.credits = None


def connect_to_db():

    conn = psycopg2.connect(host = "thacker.mathcs.carleton.edu", \
    database = "enriquezc", user = "enriquezc", password = "towel784tree")

    return conn

def query_courses(course):
    '''
    Returns a list of course objects which share the attributes defined for the
    course object passed as argument. Used to query courses based on multiple
    criteria.
    '''

    conn = connect_to_db()
    #(sec_term LIKE '16%' OR sec_term LIKE '17%')
    query_string = "SELECT * FROM COURSE WHERE (sec_term LIKE '16%' OR sec_term LIKE '17%') AND "

    if course.department != None:
        query_string = query_string + "sec_subject = '" + course.department
        query_string = query_string + "' AND "

    if course.courseNum != None:
        query_string = query_string + "sec_course_no = '" \
        + str(course.courseNum)
        query_string = query_string + "' AND "

    query_string = query_string[:-5]

    cur = conn.cursor()
    cur.execute(query_string)
    query_results = cur.fetchall()

    results = []
    print(query_string)

    for result in query_results:
        print("Getting results from query")
        result_course = Course()
        result_course.name = result[16]
        result_course.description = result[6]
        result_course.term = result[19]
        classroom_str = result[24]
        if classroom_str != None:
            classroom_str = classroom_str.split()
            classroom = classroom_str[0] + " " + classroom_str[1]
            result_course.time = classroom

        results.append(result_course)



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

if __name__ == "__main__":
    course = Course()
    course.department = "JAPN"
    course.courseNum = 101
    results = query_courses(course)

    for result in results:
        print(str(result.name) + " " + str(result.term) + " " + str(result.description) + " " + str(result.time))
