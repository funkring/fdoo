# -*- coding: utf-8 -*-
__name__ = "Correct Year to Semester"

def migrate(cr,v):
    cr.execute(" SELECT ar.id, sem.date_start, sem.id FROM academy_registration AS ar "
               " INNER JOIN academy_year AS ay ON ay.id = ar.year_id "
               " INNER JOIN academy_semester AS sem ON sem.year_id = ay.id ")
    reg_dict = {}

    #Loop assigns available semester_ids for every registration
    for id, date_start, semester_id in cr.fetchall():
        reg_dict[id] = {semester_id : date_start}

    for reg_id, sem_dict in reg_dict.iteritems():
        earliest_date = min(sem_dict.values())
        sem_id = None
        for key, value in sem_dict.iteritems():
            if value == earliest_date:
                sem_id = key

        cr.execute("UPDATE academy_registration SET semester_id = %s WHERE id = %s",(sem_id, reg_id))