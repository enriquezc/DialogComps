from src.Dialog_Manager import Course

'''Student object
Basically stores all our information about the student
There's some info we don't use, but could be used in the future
Variable names are self explanitory. '''
class Student:
    def __init__(self):
        self.name = None
        self.current_classes = []
        self.major = set()
        self.concentration = set()
        self.previous_classes = []
        self.distributions_needed = []
        self.major_classes_needed = []
        self.terms_left = 12
        self.total_credits = 0
        self.current_credits = 0
        self.interests = set()
        self.abroad = None
        self.all_classes = set()
        self.potential_courses = []
        self.relevant_class = Course.Course()
        self.distro_courses= {}

    '''Prints out relevant information about student
    Never used outside of testing
    '''
    def __str__(self):
        major_str = ""
        if len(self.major) == 0:
            major_str = "Undecided"
        elif len(self.major) == 1:
            major_str = "a {} major".format(self.major[0])
        else:
            major_str = "a {}-{} double-major".format(self.major[0], self.major[1])
        concentration_str = ""
        if len(self.concentration) == 1:
            concentration_str = " and a {} concentration".format(self.concentration[0])
        courses_str = ""
        if len(self.current_classes) > 0:
            courses_str += " and are registered for:\n"
            for course in self.current_classes:
                courses_str += "\t{}\n".format(course.name)
        return "{}, {}{}{}".format(self.name, major_str, concentration_str, courses_str)