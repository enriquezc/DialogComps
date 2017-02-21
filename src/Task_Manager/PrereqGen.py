import psycopg2

global conn
conn = psycopg2.connect(host = "cmc307-07.mathcs.carleton.edu", \
database = "dialogcomps", user = "dialogcomps", password = "dialog!=comps")

cur = conn.cursor()
req_query = "SELECT course_number, list_of_prerequisites FROM reason"

cur.execute(req_query)
results = cur.fetchall()

prereq_dict = {}

for result in results:
    course = str(result[0]).split('.')
    prereqs = str(result[1])
    if prereqs != None and prereqs != "" and prereqs != "None":
        if (course[0],course[1]) not in prereq_dict:
            prereq_dict[(course[0],course[1])] = prereqs
        #elif (prereq_dict[(course[0],course[1])] != prereqs):
            #print("CONFLICT")
            #print(prereq_dict[(course[0],course[1])])
            #print("REPLACEMENT: " + prereqs)

print(prereq_dict)
