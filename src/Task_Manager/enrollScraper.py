import re, csv, requests

all = re.findall(r'''value="[^"]*"''', '''<option value="AFAM">African/African American Studies (AFAM)</option>
<option value="AMMU">American Music Concentration (AMMU)</option>
<option value="AMST">American Studies (AMST)</option>
<option value="ARBC">Arabic (ARBC)</option>
<option value="ARCN">Archaeology (ARCN)</option>
<option value="ARTH">Art History (ARTH)</option>
<option value="ASST">Asian Studies (ASST)</option>
<option value="ASTR">Astronomy (ASTR)</option>
<option value="BIOL">Biology (BIOL)</option>
<option value="CHEM">Chemistry (CHEM)</option>
<option value="CHIN">Chinese (CHIN)</option>
<option value="CAMS">Cinema and Media Studies (CAMS)</option>
<option value="CLAS">Classics (CLAS)</option>
<option value="CGSC">Cognitive Science (CGSC)</option>
<option value="CS">Computer Science (CS)</option>
<option value="CCST">Cross Cultural Studies (CCST)</option>
<option value="DANC">Dance (DANC)</option>
<option value="ECON">Economics (ECON)</option>
<option value="EDUC">Educational Studies (EDUC)</option>
<option value="ENGL">English (ENGL)</option>
<option value="ENTS">Environmental Studies (ENTS)</option>
<option value="EUST">European Studies (EUST)</option>
<option value="FREN">French and Francophone Studies (FREN)</option>
<option value="GEOL">Geology (GEOL)</option>
<option value="GERM">German (GERM)</option>
<option value="GRK">Greek (GRK)</option>
<option value="HEBR">Hebrew (HEBR)</option>
<option value="HIST">History (HIST)</option>
<option value="IDSC">Interdisciplinary (IDSC)</option>
<option value="JAPN">Japanese (JAPN)</option>
<option value="LATN">Latin (LATN)</option>
<option value="LTAM">Latin American Studies (LTAM)</option>
<option value="LING">Linguistics (LING)</option>
<option value="LCST">Lit & Cultural Studies (LCST)</option>
<option value="MATH">Mathematics (MATH)</option>
<option value="MARS">Medieval and Renaissance St (MARS)</option>
<option value="MELA">Middle Eastern Languages (MELA)</option>
<option value="MUSC">Music (MUSC)</option>
<option value="NEUR">Neuroscience (NEUR)</option>
<option value="PHIL">Philosophy (PHIL)</option>
<option value="PHTOP">Photography & Optics (PHTOP)</option>
<option value="PE">Phys-Ed, Ath/Rec (PE)</option>
<option value="PHYS">Physics (PHYS)</option>
<option value="POSC">Political Science (POSC)</option>
<option value="PSYC">Psychology (PSYC)</option>
<option value="RELG">Religion (RELG)</option>
<option value="RUSS">Russian (RUSS)</option>
<option value="SOAN">Sociology/Anthroplgy (SOAN)</option>
<option value="SPAN">Spanish (SPAN)</option>
<option value="COGSC">Special:  Cognitive Science (COGSC)</option>
<option value="DANCE">Special:  Dance (DANCE)</option>
<option value="ARTS">Studio Art (ARTS)</option>
<option value="THEA">Theater Arts (THEA)</option>
<option value="WGST">Women's and Gender Studies (WGST)</option>
''')

for i in range(len(all)):
    all[i] = all[i][7:-1]
    #print all[i]
    
e = open("CourseData.csv", "w")
w = csv.writer(e)
w.writerow(["Course_Name", "Related_Dept", "Actual_Dept", "A&I", "Arts_Practice", "Statistical_Reasoning", "Lab",
 "Literary_Analysis", "Humanistic_Inquiry", "Social_Inquiry", "Writing_Rich_1", "Writing_Rich_2", "Quantitive_Reasoning",
  "Intercultural_Domestic_Studies", "International_Studies"])

'''course format is: [name of course, related_dept, actual_dept, A&I, Arts Practice, Statistical Reasoning, Lab,
 Literary analysis, Humanistic Inquiry, Social Inquiry, WR1, WR2, Quantitive Reasoning,
  Intercultural Domestic Studies, International Studies]'''
courses = []
requirements = ["Argument & Inquiry Seminar", "Arts Practice", "Formal or Statistical Reasoning", "Science with Lab Component", "Literary/Artistic Analysis", "Humanistic Inquiry", "Social Inquiry", "Writing Rich 1", "Writing Rich 2", "Quantitative Reasoning", "Intercultural Domestic Studies", "International Studies"]
for dept in all:

    coursesFallURL = 'https://apps.carleton.edu/campus/registrar/schedule/enroll/?term=16FA&subject=''' + dept
    coursesWinterURL = 'https://apps.carleton.edu/campus/registrar/schedule/enroll/?term=17WI&subject=''' + dept
    coursesSpringURL = 'https://apps.carleton.edu/campus/registrar/schedule/enroll/?term=17SP&subject=''' + dept
    coursesFall = requests.get(coursesFallURL).text.split("Search for Courses")[0].split('''h3 class="title"><span class="coursenum" title=''')[1:]
    coursesWinter = requests.get(coursesWinterURL).text.split("Search for Courses")[0].split('''h3 class="title"><span class="coursenum" title=''')[1:]
    coursesSpring = requests.get(coursesSpringURL).text.split("Search for Courses")[0].split('''h3 class="title"><span class="coursenum" title=''')[1:]
    allCourses = coursesFall
    allCourses.extend(coursesWinter)
    allCourses.extend(coursesSpring)
    for course in allCourses:
        courseName = course[7:].split(".")[0].split(">")
        courseName = courseName[len(courseName) - 1]
        related_dept = dept
        actual_dept = courseName.split(" ")[0]
        courseName = courseName.replace(" ", "")
        #print courseName, related_dept, actual_dept
        reqs = []
        for req in requirements:
            if req in course:
                reqs.append(1)
            else:
                reqs.append(0)
        
        info = [courseName, related_dept, actual_dept]
        info.extend(reqs)
        w.writerow(info)
        print courseName
    
    
    #print coursesFall[1]
    #break
    
    