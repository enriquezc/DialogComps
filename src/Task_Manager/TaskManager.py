# Task Manager.py
# Serves to decide what actions need to be taken next to facilitate
# conversation for the Dialogue Manager

import psycopg2


class Course:
    def __init__(self):
        self.dept = None
        self.course_num = - 1
        self.section_num = - 1
        self.title = ""
        self.credits = - 1
        self.meeting_time = []
        self.course_description = ""
        self.prereqs = []
        self.instructor = ""

def connect_to_db():
    conn = psycopg2.connect(host = "cmc307-07.mathcs.carleton.edu", \
    database = "dialogComps", user = "dialogComps", password = "dln!=dialog")

def query_courses(course):
    '''
    Returns a list of course objects which share the attributes defined for the
    course object passed as argument. Used to query courses based on multiple
    criteria.
    '''

    # binary checking for all these conditions (512 possibilities) at this
    # point seems super inefficient
    # have to find a way to share some conditions

    if course.dept != None:
        # we know we are working with a specific department?

        if course.course_num != None:
            # we can now make a reasonable query with the intent of finding
            # a course that exists

    list_courses = []

    return list_courses

def query_by_string(course_description):
    '''
    Returns a list of course objects based on a string containing keywords
    about the course which were not parsed into a set of specific criteria.
    General search algorithm for courses based on a string description.
    '''

    list_courses = []

    return list_courses
