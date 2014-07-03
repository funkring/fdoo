# -*- coding: utf-8 -*-
__name__ = "Correct Year to Semester"

def migrate(cr,v):
    cr.execute(" SELECT ar.id, sem.id FROM academy_registration AS ar " 
               " INNER JOIN academy_year AS ay ON ay.id = ar.year_id " 
               " INNER JOIN academy_semester AS sem ON sem.year_id = ay.id AND sem.date_start = (SELECT MIN(sem2.date_start) FROM academy_semester sem2 WHERE sem2.year_id = ay.id)) ")
    
    for ar_id, semester_id in cr.fetchall():
        cr.execute("UPDATE academy_registration SET semester_id = %s WHERE id = %s",(semester_id, ar_id))
