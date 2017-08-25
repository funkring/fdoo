# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-

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

from openerp.osv import fields,osv

class crm_case_categ(osv.osv):   
    _inherit = "crm.case.categ"   
    _columns = {
        "code": fields.char("Code", size=8, select=True)
    }


class crm_lead(osv.osv):
    _inherit = "crm.lead"
    
    def action_schedule_meeting(self, cr, uid, ids, context=None):
        """
        Open meeting's calendar view to schedule meeting on current opportunity.
        :return dict: dictionary value for created Meeting view
        """
        lead = self.browse(cr, uid, ids[0], context)
        res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid, 'calendar', 'action_calendar_event', context)
        user = lead.user_id or self.pool['res.users'].browse(cr, uid, uid, context=context)
        partner_ids = [user.partner_id.id]
        if lead.partner_id:
            partner_ids.append(lead.partner_id.id)
            
        meeting_context =  {
            'search_default_opportunity_id': lead.type == 'opportunity' and lead.id or False,
            'default_opportunity_id': lead.type == 'opportunity' and lead.id or False,
            'default_partner_id': lead.partner_id and lead.partner_id.id or False,
            'default_partner_ids': partner_ids,
            'default_section_id': lead.section_id and lead.section_id.id or False,
            'default_user_id': user.id,
            'default_name': lead.name
        }
        res['context'] = meeting_context
        
        location = []
        
        address = []
        if lead.zip:
            address.append(lead.zip.strip())
        if lead.city:
            address.append(lead.city.strip())
        if lead.street:            
            address.append(lead.street.strip())
            
        if address:
            location.append(" ".join(address))
            
        if lead.phone:            
            location.append(lead.phone.replace(" ",""))
        
        if location:
            meeting_context["default_location"] = ", ".join(location)
            
        return res
    
    _columns = {
        "editor_id": fields.many2one("res.users", "Editor", select=True)
    }
    _defaults = {
        "editor_id": lambda s, cr, uid, c: uid,
    }