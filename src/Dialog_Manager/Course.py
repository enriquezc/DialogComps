class Course:
    def __init__(self, name = ""):
        #name of class
        self.name = name
        self.id = ""
        self.term = ""
        self.department = ""
        self.course_num = ""
        self.classroom = ""
        self.faculty_id = ""
        self.faculty_name = ""
        self.gen_distributions = []
        #A score from 1-10 of how much they liked the class
        self.sentiment = 0
        #how confident are we in this sentiment
        self.confidence = 0
        self.scrunch = ""
        self.requirements_fulfilled = []
        #Some way of storing start time, end time, and days of the week. Format undecided as of yet.
        self.time = []
        self.prereqs = ""
        #description from enroll
        self.description = ""
        #context the user gave about the class, just in case we still need it
        self.user_description = ""
        #Boolean. Have they taken the class yet?
        self.taken = False
        self.credits = 0
        self.relevance = None
        self.weighted_score = 0.0

    def __str__(self, index):
        description = ""
        desc_tokens = self.description.split()
        line_length = 80
        cur_line_length = 0
        for token in desc_tokens:
            if line_length < cur_line_length + len(token):
                description += "\n"
                cur_line_length = 0
            cur_line_length += len(token)
            description += " " + token
        top_line = "{} : {}, {} credits".format(self.id, self.name, self.credits)
        centering_spaces = " " * int((line_length - len(top_line) - 2) / 2)
        top_line = "{}){}{}{}".format(index, centering_spaces, top_line, centering_spaces)
        professor_centering_spaces = " " * int((line_length - len(self.faculty_name))/2)
        prof_line = "{}{}\n".format(professor_centering_spaces, self.faculty_name) if self.faculty_name != "" else ""
        return "\n{}\n{}\n{}\n".format(top_line, prof_line, description)

    def __eq__(self, other):
        return other is not None and self.department == other.department and self.course_num == other.course_num

    def __hash__(self):
        return hash((self.department, self.course_num))
