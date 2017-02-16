class Course:
    def __init__(self):
        #name of class
        self.name = ""
        self.id = ""
        self.term = ""
        self.department = ""
        self.course_num = ""
        self.classroom = ""
        self.faculty_id = ""
        self.faculty_name = ""
        #A score from 1-10 of how much they liked the class
        self.sentiment = 0
        #how confident are we in this sentiment
        self.confidence = 0
        self.scrunch = ""
        self.requirements_fulfilled = []
        #Some way of storing start time, end time, and days of the week. Format undecided as of yet.
        self.time = ""
        self.prereqs = []
        #description from enroll
        self.description = ""
        #context the user gave about the class, just in case we still need it
        self.user_description = ""
        #Boolean. Have they taken the class yet?
        self.taken = False
        self.credits = 0
        self.relevance = None
        self.weighted_score = 0.0

    def __str__(self):
        return "{} : {}\n{}".format(self.id, self.name, self.description)

    def __eq__(self, other):
        return other is not None and self.department == other.department and self.course_num == other.course_num