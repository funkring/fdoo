'''
Created on 16.08.2012

@author: martin
'''
from collections import OrderedDict


class olsr_support(object):
   
    def olsr_config(self):
        res_defaults = OrderedDict()
        res_defaults["DebugLevel"]=0
        res_defaults["ClearScreen"]=True
        res_defaults["IpVersion"]=4
        res_defaults["AllowNoInt"]=True
        res_defaults["UseNiit"]=False
        res_defaults["SmartGateway"]=False
        res_defaults["TcRedundancy"]=2
        res_defaults["MprCoverage"]=7
        res_defaults["UseHysteresis"]=False
        res_defaults["Pollrate"]=0.025
        res_defaults["FIBMetric"]="flat"                 
        res_defaults["LinkQualityLevel"]=2
        #"LinkQualityAlgorithm" : "etx_ff",
        res_defaults["LinkQualityAlgorithm"]="etx_fpm"
        res_defaults["LinkQualityAging"]=0.05
        res_defaults["LinkQualityFishEye"]=1    
                
        iface_defaults = OrderedDict()
        iface_defaults["HelloInterval"] = 3.0
        iface_defaults["HelloValidityTime"] = 125.0
        iface_defaults["TcInterval"] = 2.0
        iface_defaults["TcValidityTime"] = 500.0
        iface_defaults["MidInterval"] = 25.0
        iface_defaults["MidValidityTime"] = 500.0
        iface_defaults["HnaInterval"] = 10.0
        iface_defaults["HnaValidityTime"] = 125.0
  
        plugin_dyn_gw_0_5 = OrderedDict()
        plugin_dyn_gw_0_5["section_type"]="LoadPlugin"
        plugin_dyn_gw_0_5["Interval"]=40
        plugin_dyn_gw_0_5["Ping"]=["195.191.252.198","192.36.148.17"]
               
        plugin_arprefresh_0_1 = OrderedDict()
        plugin_arprefresh_0_1["section_type"]="LoadPlugin"
                
        plugin_txtinfo_0_1 = OrderedDict()
        plugin_txtinfo_0_1["section_type"]="LoadPlugin"
        plugin_txtinfo_0_1["accept"]=["0.0.0.0"]
        
        res = { "Defaults" : res_defaults,                
                "InterfaceDefaults" : iface_defaults,
                "olsrd_dyn_gw.so.0.5" : plugin_dyn_gw_0_5,
                "olsrd_arprefresh.so.0.1" : plugin_arprefresh_0_1,
                "olsrd_txtinfo.so.0.1" : plugin_txtinfo_0_1
              }
        return res
    
    def olsr_config_txt(self,section="Defaults"):
        config = self.olsr_config().get(section)
        section_type = None
        if config:
            values = []
            for key,value in config.items():
                if key!="section_type":
                    if "LoadPlugin" == section_type:
                        if isinstance(value,list):
                            for svalue in value:
                                values.append('PlParam "%s" "%s"' % (key,svalue))
                        else:
                            values.append('PlParam "%s" "%s"' % (key,value))
                    else:            
                        str_value = None
                        if type(value) is bool:
                            str_value =value and "yes" or "no"            
                        elif not value is None:
                            if isinstance(value,str):
                                str_value='"%s"' % (str(value),)
                            else:
                                str_value=str(value)            
                        if str_value:
                            values.append("%s %s" % (key,str_value))
                else:
                    section_type=value
            
            if section!="Defaults":                
                if section_type:
                    return '%s "%s" {\n    %s\n}\n' % (section_type,section,"\n    ".join(values),)
                return "%s {\n    %s\n}\n" % (section,"\n    ".join(values),)
            else:
                return "\n".join(values)
        else:
            return ""
        
if __name__ == '__main__':
    print olsr_support().olsr_config_txt("Defaults")
    print
    print olsr_support().olsr_config_txt("InterfaceDefaults")
    print
    print olsr_support().olsr_config_txt("olsrd_dyn_gw.so.0.5") 
    print 
    print olsr_support().olsr_config_txt("olsrd_arprefresh.so.0.1")
    print 
    print olsr_support().olsr_config_txt("olsrd_txtinfo.so.0.1")
            
