import re

def checa_interface(output):   
    pattern = re.compile('interface gpon ')
    valida = pattern.findall(output)
    if valida == []:
        return False
    else:
        return True

def checa_igmp(output):   
    pattern = re.compile('igmp user add')
    valida = pattern.findall(output)
    if valida == []:
        return False
    else:
        return True

def checa_igmp_member(output):   
    pattern = re.compile('igmp multicast-vlan member')
    valida = pattern.findall(output)
    if valida == []:
        return False
    else:
        return True

def checa_multicast_vlan(output):   
    pattern = re.compile('multicast-vlan 30')
    valida = pattern.findall(output)
    if valida == []:
        return False
    else:
        return True

def checa_vlan_voip(output, vlan_voip):   
    pattern = re.compile("vlan " + vlan_voip + " gpon")
    valida = pattern.findall(output)
    if valida == []:
        return False
    else:
        return True

def pattern_tcont(output):
    pattern = re.compile('tcont bind-profile \d+ \d+ \d+ profile-id (\d+)')
    groups = pattern.findall(output)
    if groups == []:
        return {'valid': False}
    else:
        return {'valid': True, 'value': groups}


def pattern_gemport_bind(output):
    pattern = re.compile('ont gemport bind (\d+) (\d+) (\d+) (\d+)')
    groups = pattern.findall(output)
    if groups == []:
        return {'valid': False}
    else:
        return {'valid': True, 'value': groups}

def pattern_gemport_mapping(output):
    pattern = re.compile('ont gemport mapping (\d+) (\d+) (\d+) vlan (\d+)')
    groups = pattern.findall(output)
    if groups == []:
        return {'valid': False}
    else:
        return {'valid': True, 'value': groups}


def pattern_on_port_vlan(output):
    pattern = re.compile('ont port vlan (\d+) (\d+) eth (\d+) (\d+) translation s-vlan (\d+)')
    groups = pattern.findall(output)
    if groups == []:
        return {'valid': False}
    else:
        return {'valid': True, 'value': groups}

def pattern_ont_multicast(output):

    pattern = re.compile('ont multicast-forward (\d+) (\d+) tag translation (\d+)')
    groups = pattern.findall(output)
    if groups == []:
        return {'valid': False}
    else:
        return {'valid': True, 'value': groups}
    
def get_svlan_serviceport(output):

    pattern = re.compile('service-port \d+ vlan (\d+)')
    groups = pattern.findall(output)
    if groups == []:
        return {'valid': False}
    else:
        return {'valid': True, 'value': groups[0]}

    