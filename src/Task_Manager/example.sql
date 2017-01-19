SELECT c.sec_subject, r.title, r.long_description, c.sec_course_no
FROM ((SELECT * FROM COURSE  where sec_subject in ('phys', 'posc') AND (sec_term LIKE '16%' OR sec_term LIKE '17%')) AS c
     JOIN
     (SELECT * FROM REASON WHERE org_id in ('phys', 'posc')) AS r
     ON c.sec_course_no = r.course_number)
