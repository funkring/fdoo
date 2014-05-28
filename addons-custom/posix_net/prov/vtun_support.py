'''
Created on 16.08.2012

@author: martin
'''
from collections import OrderedDict


class vtun_support(object):
   
    def vtun_brctl(self):
        return "/usr/sbin/brctl"
    
    def vtun_ip(self):
        return "/usr/sbin/ip"
   
    def vtun_config(self):
        res_options = OrderedDict()
        res_options["port"]=300
        res_options["timeout"]=30
        
        res_default = OrderedDict()
        res_default["type"]="tun"
        res_default["proto"]="udp"
        res_default["keepalive"]="yes"    
        res_default["multi"]="killold"
        res_default["persist"]="yes"
        res_default["encrypt"]="no"
        res_default["compress"]="no"
                
    
        res = { "options" : res_options,                
                "default" : res_default
              }
        return res
            
    def vtun_tunnel_txt(self,name,password,multi=False,bridge=None,device=None,proto=None):
        values = []
        up_values = []
        down_values = []
        if password:
            values.append("password %s;" % (password,))
        if proto:
            values.append("proto %s;" % (proto,))
        if device:
            values.append("device %s;" % (device,))
        if multi:
            values.append("multi yes;")
        if bridge: 
            values.append("type ether;")
            up_values.append('ifconfig "%% up";')
            up_values.append('program "%s addif %s %%%%";' % (self.vtun_brctl(),bridge))
            down_values.append('ifconfig "%% down";')            
            
        if up_values:
            values.append("up {")
            values.extend(["    %s" % (x,) for x in up_values])            
            values.append("};")
        
        if down_values:
            values.append("down {")
            values.extend(["    %s" % (x,) for x in down_values])            
            values.append("};")
                    
        return "%s {\n    %s\n}" % (name,"\n    ".join(values))
            
            
    def vtun_config_txt(self,section="options"):
        config = self.vtun_config().get(section)        
        if config:
            values = []
            for key,value in config.items():
                str_value = None
                if type(value) is bool:
                    str_value =value and "yes" or "no"            
                elif not value is None:
                    if isinstance(value,str):
                        str_value='%s' % (str(value),)
                    else:
                        str_value=str(value)            
                if str_value:
                    values.append("%s %s;" % (key,str_value))                            
            return "%s {\n    %s\n}" % (section,"\n    ".join(values),)            
        else:
            return ""
        
if __name__ == '__main__':
    print vtun_support().vtun_config_txt()
    print
    print vtun_support().vtun_config_txt("default")
    print
    print vtun_support().vtun_tunnel_txt("guest","abcd",multi=True,bridge="br-guest")
    print
    print vtun_support().vtun_tunnel_txt("guest","abcd",bridge="br-guest")
    pass
            
