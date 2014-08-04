##############################################################################
#
# Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                    General contacts <info@kndati.lv>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from openerp.report import report_sxw
from lxml import etree

class Parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        model = self.pool.get(context['model'])
        ids = context['ids']

        model_id = self.pool.get('ir.model').search(cr, uid, [('model','=',model._name)])
        if model_id:
            model_desc = self.pool.get('ir.model').browse(cr, uid, model_id[0], context).name
        else:
            model_desc = model._description

        groupby = context.get('group_by',[])
        groupby_no_leaf = context.get('group_by_no_leaf',False)
        
        rows = None             
        fields_view  = model.fields_view_get(cr, uid, view_type='tree', context=context)
        fields_order = self._parse_string(fields_view['arch'])           
        fields_type = dict(map(lambda name: (name, fields_view['fields'][name]['type']), fields_view['fields']))
        
        if groupby:
            rows = []
            for group in groupby:
                fields_order.remove(group)                
            fields_order = groupby + fields_order            
                        
            for field in fields_order:
                field_type = fields_type.get(field)
                if field_type and field_type == "many2one":
                    fields_type[field]="char"
                    
            
            def get_groupby_data(groupby = [], domain = []):
                records =  model.read_group(cr, uid, domain, fields_order, groupby , 0, None, context)
                for rec in records:
                    rec['__group'] = True
                    rec['__no_leaf'] = groupby_no_leaf
                    rec['__grouped_by'] = groupby[0] if (isinstance(groupby, list) and groupby) else groupby
                    for f in fields_order:
                        if f not in rec:
                            rec.update({f:False})
                        elif isinstance(rec[f], tuple):
                            rec[f] = rec[f][1]
                    rows.append(rec)
                    inner_groupby = (rec.get('__context', {})).get('group_by',[])
                    inner_domain = rec.get('__domain', [])
                    if inner_groupby:
                        get_groupby_data(inner_groupby, inner_domain)
                    else:
                        if groupby_no_leaf:
                            continue
                        child_ids = model.search(cr, uid, inner_domain)
                        res = model.read(cr, uid, child_ids, fields_view['fields'].keys(), context)
                        #res.sort(lambda x,y: cmp(ids_count.index(x['id']), ids.index(y['id'])))
                        rows.extend(res)
            dom = [('id','in',ids)]
            if groupby_no_leaf and len(ids) and not ids[0]:
                dom = datas.get('_domain',[])
            get_groupby_data(groupby, dom)
            
            field_with_value = set()
            for row in rows:
                for field in fields_order:
                    if row.get(field):
                        field_with_value.add(field)
            
            new_fields_order = []          
            for field in fields_order:
                if field in field_with_value:
                    new_fields_order.append(field)            
            fields_order = new_fields_order
                    
                
        else:        
            rows = model.browse(cr, uid, ids, context=context)

        print rows
        self.localcontext.update({
            'screen_fields': fields_order,
            'screen_fields_type': fields_type,
            'screen_rows': rows,
            'screen_model': context['model'],
            'screen_title': model_desc,
          
        })

    def _parse_node(self, root_node):
        result = []
        for node in root_node:
            if node.tag == 'field':
                result.append(node.get('name'))
            else:
                result.extend(self._parse_node(node))
        return result

    def _parse_string(self, view):
        try:
            dom = etree.XML(view.encode('utf-8'))
        except:
            dom = etree.XML(view)   
        return self._parse_node(dom)

