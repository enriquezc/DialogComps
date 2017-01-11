from src.Dialog_Manager import Course

class Student:
    def __init__(self):
        self.name = None
        self.current_classes = []
        self.major = []
        self.concentration = None
        self.previous_classes = []
        self.distributions_needed = []
        self.major_classes_needed = []
        self.terms_left = 12
        self.total_credits = None
        #some way of listing interests. Three proposals so far are:
        #1. Departments and professors they enjoy taking classes in
        #2. Enums of different categories of interests we've thought of, which we can expand as we go
        #3. Strings with phrases we believe they said they were interested in
        self.interests = []
        self.abroad = None
        self.all_classes = []
        self.potential_courses = []
