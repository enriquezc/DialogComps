import json
import psycopg2
import re

global conn
conn = psycopg2.connect(host = "cmc307-07.mathcs.carleton.edu", \
database = "dialogcomps", user = "dialogcomps", password = "dialog!=comps")

cur = conn.cursor()
prof_query = "SELECT cache FROM reason WHERE cache LIKE '%faculty%'"

cur.execute(prof_query)
results = cur.fetchall()

prof_dict = {}

for result in results:
    #print(result[0])
    try:
        json_data = json.loads(str(result[0]))
        if ('faculty' in json_data):
            faculty_dict = json_data['faculty']
            if len(faculty_dict) == 1:
                for key in faculty_dict.keys():
                    name_dict = faculty_dict[key]
                    key = name_dict['Id']
                    value = name_dict['Fac_Catalog_Name']
                    #print(faculty_dict[key])
                    if key not in prof_dict:
                        print("key: " + key + ", value: " + value)
                        prof_dict[key] = value
    except:
        print("EXCEPTION!")
        list_of_items = re.findall(r"[\w']+", str(result[0]))
        faculty_id = ""
        faculty_name = ""
        for i in range(len(list_of_items)):
            if list_of_items[i] == 'Id':
                faculty_id = list_of_items[i + 1]
            elif list_of_items[i] == 'First_Name':
                faculty_name = list_of_items[i + 1]
            elif list_of_items[i] == 'Carleton_Name':
                faculty_name = faculty_name + " " + list_of_items[i + 1]

        if faculty_id not in prof_dict:
            prof_dict[faculty_id] = faculty_name
            print("key: " + str(faculty_id) + ", value: " + str(faculty_name))

        if faculty_name == None or faculty_id == None:
            print(re.findall(r"[\w']+", result[0]))


for key, value in prof_dict.items():
    key = key
    value = value.replace("'", "''")
    query_string = "INSERT INTO professors VALUES ({},'{}');".format(key, value)
    print(cur.mogrify(query_string))
    cur.execute(query_string)
    conn.commit()
