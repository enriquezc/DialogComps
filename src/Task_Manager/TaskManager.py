# Task Manager.py
# Serves to decide what actions need to be taken next to facilitate
# conversation for the Dialogue Manager

import psycopg2
import src.Dialog_Manager.Course


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

    query_string = "SELECT * FROM COURSE WHERE sec_term = '16/FA' AND "

    if course.department != None:
        query_string = query_string + "sec_subject = '" + course.dept
        query_string = query_string + "' AND "

    if course.course_num != None:
        query_string = query_string + "sec_course_no = '" \
        + str(course.course_num)
        query_string = query_string + "' AND "

    query_string = query_string[:-5]

    cur = conn.cursor()
    cur.execute(query_string)
    result = cur.fetchone()

    course.name = result[16]
    course.description = result[6]
    classroom_str = result[24]
    classroom_str = classroom_str.split()
    classroom = classroom_str[0] + " " + classroom_str[1]
    course.time = classroom

    #list_courses = []

    return course

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
    conn = connect_to_db()
    cur = conn.cursor()
