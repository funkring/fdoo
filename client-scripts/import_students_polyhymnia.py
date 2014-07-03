# -*- coding: utf-8 -*-
#############################################################################
#
#    Copyright (c) 2007 Martin Reisenhofer <martin.reisenhofer@funkring.net>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import openerplib
import xlrd
import keyring


if __name__ == '__main__':

    def get_header(worksheet):
        cols = {}

        for col in range(worksheet.ncols):
            value = worksheet.cell_value(0, col)
            if value:
                cols[value.lower()] = col # lower() for lowercase letters

        return cols

    passwd = keyring.get_password("odoo/polyhymnia", "admin")
    client = openerplib.get_connection(hostname="localhost", protocol="jsonrpc", database="odoo_polyhymnia", login="admin", password=passwd)


    student_obj = client.get_model("academy.student")
    product_obj = client.get_model("product.product")
    location_obj = client.get_model("academy.location")
    trainer_obj = client.get_model("academy.trainer")
    partner_obj = client.get_model("res.partner")
    country_obj = client.get_model("res.country")
    state_obj = client.get_model("res.country.state")
    course_prod_obj = client.get_model("academy.course.product")
    mapping_obj = client.get_model("res.mapping")
    registration_obj = client.get_model("academy.registration")
    uom_obj = client.get_model("product.uom")

    workbook = xlrd.open_workbook("data/registration_list.xls")

    registration_list = None
    res_model = "academy.registration"

    for worksheet_name in workbook.sheet_names():
        if worksheet_name == "Anmeldungen":
            registration_list = workbook.sheet_by_name(worksheet_name)

    if registration_list:
        #Initialize columns
        header = get_header(registration_list)
        c_ref = header["sn"]
        c_first_name = header["vn"]
        c_last_name = header["nn"]
        c_group_lesson = header["gruppenunterricht"]
        c_unit = header["ei"]
        c_trainer = header["lehrer"]
        c_product = header["i"]
        c_street = header["str"]
        c_zip = header["plz"]
        c_city = header["ort"]
        c_state = header["bundesland"]
        c_location = header["sch"]
        c_phone = header["tel.nr."]
        c_mail = header["e-mail"]
        c_birthday = header["geb"]
        c_parent_ln = header["erz - vname"]
        c_parent_fn = header["erz - nname"]
        c_parent_bd = header["erz - geb"]
        c_parent_country = header["erz - svn"]

        mapping_uom = {
             (0, 60) : "60min",
             (0, 50) : "50min",
             (0, 45) : "45min",
             (0, 30) : "30min",
             (0, 25) : "25min",
             (1, 25) : "group2_50min",
             (1, 17) : "group3_50min",
             (1, 13) : "group4_50min",
             (1, 30) : "group2_60min",
             (1, 20) : "group3_60min",
             (1, 15) : "group4_60min"
            }

        for row in range(1, registration_list.nrows):
            #Initialize variables
            student_id = None
            trainer_id = None
            course_prod_id = None
            location_id = None

            #Check Student
            student_ref = registration_list.cell_value(row, c_ref)
            if not student_ref:
                print "Error: This student does not have a number!"
                continue
            else:
                student_ref = int(student_ref)
            student_ids = student_obj.search([("ref", "=", student_ref)])
            if len(student_ids):
                student_id = student_ids[0]
            else:
                #Create student
                student_name = registration_list.cell_value(row, c_last_name) + " " + registration_list.cell_value(row, c_first_name)
                student_birthday = registration_list.cell_value(row, c_birthday)#.replace("/", ".").replace(" ", "")
                student_mail = registration_list.cell_value(row, c_mail)
                student_street = registration_list.cell_value(row, c_street)
                student_zip = registration_list.cell_value(row, c_zip)
                if type(student_zip) == float:
                    student_zip = int(student_zip)
                student_city = registration_list.cell_value(row, c_city)
                student_phone = registration_list.cell_value(row, c_phone)
                student_nationality = registration_list.cell_value(row, c_parent_country)
                student_state_id = None
                student_parent_id = None

                if not isinstance(student_nationality, basestring):
                    student_nationality = None

                state_ids = state_obj.search([("name", "=", registration_list.cell_value(row, c_state))])
                if len(state_ids) == 1:
                    student_state_id = state_ids[0]

                parent_name = registration_list.cell_value(row, c_parent_ln) + " " + registration_list.cell_value(row, c_parent_fn)
                parent_ids = state_obj.search([("name", "=", parent_name)])
                if len(parent_ids):
                    student_parent_id = parent_ids[0]
                else:
                    parent_birthday = registration_list.cell_value(row, c_parent_bd)#.replace(" ", "")
                    student_parent_id = partner_obj.create({"name" : parent_name,
                                                            "birthdate" : parent_birthday,})

                student_value = {
                    "ref" : student_ref,
                    "name" : student_name,
                    "birthdate" : student_birthday,
                    "email" : student_mail,
                    "street" : student_street,
                    "zip" : student_zip,
                    "city" : student_city,
                    "mobile" : student_phone,
                    "state_id" : student_state_id,
                    "parent_id" : student_parent_id,
                    "nationality" : student_nationality
                }
                student_id = student_obj.create(student_value)

            #Check trainer
            trainer_name = registration_list.cell_value(row, c_trainer)
            trainer_ids = trainer_obj.search([("name", "=", trainer_name)])
            if len(trainer_ids):
                trainer_id = trainer_ids[0]
            else:
                #Create trainer
                trainer_id = trainer_obj.create({"name" : trainer_name})

            #Check course product
            product_name = registration_list.cell_value(row, c_product)
            product_ids = course_prod_obj.search([("name_template", "=", product_name)])
            if len(product_ids):
                course_prod_id = product_ids[0]
            else:
                #Create product
                product_id = product_obj.create({"name" : product_name})
                course_prod_id = course_prod_obj.create({"product_id" : product_id})

            #Check location
            location_name = registration_list.cell_value(row, c_location)
            location_ids = location_obj.search([("name", "=", location_name)])
            if len(location_ids):
                location_id = location_ids[0]
            else:
                #Create location
                location_id = location_obj.create({"name" : location_name})

            #Check unit
            is_group_lesson = registration_list.cell_value(row, c_group_lesson)
            if type(is_group_lesson) == float:
                is_group_lesson = int(is_group_lesson)
            unit = registration_list.cell_value(row, c_unit)
            if type(unit) == float:
                unit = int(unit)
            uom_code = mapping_uom.get((is_group_lesson, unit))
            uom_ids = uom_obj.search([("code", "=", uom_code)])
            uom_id = uom_ids and uom_ids[0] or None

            value = {
                "student_id" : student_id,
                "trainer_id" : trainer_id,
                "course_prod_id" : course_prod_id,
                "location_id" : location_id,
                "uom_id" : uom_id,
                "state" : "registered"
            }

            uuid = "Anmeldungen,%s" % student_ref
            #registration_id = mapping_obj.get_id(res_model, uuid)
            registration_id = None
            mapping_ids = mapping_obj.search([("uuid", "=", uuid)])
            if len(mapping_ids):
                registration_id = mapping_obj.read(mapping_ids[0], ["res_id"])["res_id"]

            if registration_id:
                registration_obj.write(registration_id, value)
                print "Updated registration %s" % uuid
            else:
                res_id = registration_obj.create(value)
                mapping_obj.create({"name" : "Imported registration",
                                    "res_model" : "academy.registration",
                                    "res_id" : res_id,
                                    "uuid" : uuid})
                print "Created registration %s" % uuid










