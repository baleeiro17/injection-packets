import os
from utils.info_placa import mostra_slots_depara_depois, mostra_portas_slots_depara_depois
from models.controle import Controle
import re
from utils.regex import checa_vlan_voip


def get_slot_porta_destino(porta, slot, deparas):
    for depara in deparas:
        if depara.split("_")[0].split("/")[1] == porta and depara.split("_")[0].split("/")[0] == slot:
            return "0/" + depara.split("_")[1].split("/")[0] + "/" + depara.split("_")[1].split("/")[1]

def posicao_config_bbs(values):
    index = 0
    for value in values:
        if '<bbs-config>' in value:
            break
        else:
            index += 1
    return index + 1

def posicao_final_config_bbs(values):
    index = 0
    for value in values:
        if '[btv-config]' in value:
            return index
        elif '[abs-config]' in value:
            return index
        else:
            index += 1
    return index

def posicao_config_btv(values):
    index = 0
    for value in values:
        if '<btv-config>' in value:
            break
        else:
            index += 1
    return index + 2

def posicao_final_config_btv(values):
    index = 0
    for value in values:
        if 'return' in value:
            return index
        else:
            index += 1
    return index

def find_parte_config(values):
    config = ''
    for value in values:
        if len(value) > 0:
            if value[0] == ' ':
                config += '\n'
                break
            elif value != '#':
                config += value
    return config

def mapeamento_outros(values):
    config = []
    i = 0
    for value in values:
        if find_pattern_service_port(value) == False:
            if value != '#' and value.strip() != 'btv' and ',' not in value:
                config.append(value)
        i += 1
    return config


def find_pattern_service_port(value):

    pattern = re.compile('service-port')

    group = pattern.findall(value)
    if group == []:
        return False
    else:
        return True
    

def find_service_port(value):

    pattern = re.compile('service-port (\d+)')

    group = pattern.findall(value)
    if group == []:
        return {'valid': False, 'value': ''}
    else:
        return {'valid': True, 'value': group[0]}

def find_porta(value):

    pattern = re.compile('gpon (\d+)/(\d+)/(\d+)')

    group = pattern.findall(value)
    if group == []:
        return {'valid': False, 'value': ''}
    else:
        return {
            'valid': True, 
            'value_slot': group[0][1], 
            'value_port': group[0][2], 
            'value': group[0][0] + "/" + group[0][1] + "/" + group[0][2]
        }

def get_param_alteracao_add(output):

    patternService = re.compile('add( \d+ )')
    services = patternService.findall(output)
    if services == []:
        return {'valid': False, 'value': ''}
    else:
        return {'valid': True, 'value': services[0]}


def find_multicast(value, service_port):

    pattern = re.compile(
        'multicast-unknown policy service-port-list .*?(,| )(' + service_port + ')')

    group = pattern.findall(value)
    if group == []:
        return False
    else:
        return True

def find_service_port2(value, service_port):
    
    pattern = re.compile('service-port ' + service_port + ' ')

    group = pattern.findall(value)
    if group  == []:
        return False
    else:
        return True

def mapeamento_porta_service_port(values):
    services = []
    i = 0
    for value in values:
        if find_pattern_service_port(value):
            services.append(value + find_parte_config(values[i+1:]))
            # services += find_parte_config(values[i+1:])
        i += 1
    return services

def get_porta_slot_origem(porta, slot, deparas):
    for depara in deparas:
        if depara.split("_")[1].split("/")[1] == porta and depara.split("_")[1].split("/")[0] == slot:
            return depara.split("_")[0].split("/")[0], depara.split("_")[0].split("/")[1]

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
    
def cria_procedimento_btv(values, outros, patternservice, serviceport):

    configs = ''

    for value in values:

        if len(value) > 0:

            if value == '#' or value == 'return' or '#' in value:
                continue
            elif find_service_port2(value, patternservice):
                patternadd = get_param_alteracao_add(value)['value']
                configs += value.split("add" + patternadd)[0] + "add " + value.split("add" + patternadd)[1].split(
                    patternservice)[0] + serviceport + value.split("add" + patternadd)[1].split(patternservice)[1] + "\n"
                for outro in outros:
                    if 'multicast-vlan' in outro:
                        configs += outro + "\n"
                        break
                configs += '  igmp multicast-vlan member service-port-list ' + serviceport
            elif find_multicast(value, patternservice):
                configs += 'multicast-unknown policy service-port ' + serviceport + ' transparent'
    
    return configs
        
def gera_proc_service_port_huawei_new(hostname_origem, hostname_destino, depara, serviceport):

    path = os.path.join(os.getcwd(), "anexos")
    excel_path = os.path.join(path, f"{hostname_origem}-service-port.txt")

    slots = mostra_slots_depara_depois(depara)
    portas = mostra_portas_slots_depara_depois(depara)

    with open(excel_path, "w") as file:

        for slot in slots:

            for porta in portas:

                if porta.split("/")[0] == slot:

                    slotorigem, portaorigem = get_porta_slot_origem(porta.split("/")[1], slot, depara)

                    # função que chama a output do huawei
                    output = Controle.gera_slot_info(
                        hostname_origem, hostname_destino,
                        slotorigem, portaorigem
                    )

                    if output == "":
                        continue

                    nova_output = output.splitlines()

                    inicio = posicao_config_bbs(nova_output)
                    fim = posicao_final_config_bbs(nova_output)

                    services_porta = mapeamento_porta_service_port(nova_output[inicio:fim])

                    for serviceporta in services_porta:

                        serviceid = find_service_port(serviceporta)
                        portas_service = find_porta(serviceporta)

                        if serviceid['valid'] and portas_service['valid']:

                            porta_destino = get_slot_porta_destino(
                                portas_service['value_port'],
                                portas_service['value_slot'],
                                depara
                            )

                            config = "service-port " + serviceporta.split("service-port " + serviceid['value'] + " ")[0] + str(serviceport) \
                                + " " + serviceporta.split("service-port " + serviceid['value'] + " ")[1].split(" " + portas_service['value'] + " ")[0] + " " + porta_destino \
                                + " " + serviceporta.split("service-port "+ serviceid['value'] + " ")[1].split(" " + portas_service['value'] + " ")[1]
                            
                            file.write(config + "\n")

                            serviceport += 1

                    file.write("\n")

    return

def gera_proc_service_port_huawei_new_aplicacao(hostname_origem, hostname_destino, depara, serviceport):


    slots = mostra_slots_depara_depois(depara)
    portas = mostra_portas_slots_depara_depois(depara)

    aplicacao = []

    for slot in slots:

        for porta in portas:

                if porta.split("/")[0] == slot:

                    slotorigem, portaorigem = get_porta_slot_origem(porta.split("/")[1], slot, depara)

                    # função que chama a output do huawei
                    output = Controle.gera_slot_info(
                        hostname_origem, hostname_destino,
                        slotorigem, portaorigem
                    )

                    if output == "":
                        continue

                    nova_output = output.splitlines()

                    inicio = posicao_config_bbs(nova_output)
                    fim = posicao_final_config_bbs(nova_output)

                    services_porta = mapeamento_porta_service_port(nova_output[inicio:fim])

                    for serviceporta in services_porta:

                        serviceid = find_service_port(serviceporta)
                        portas_service = find_porta(serviceporta)

                        if serviceid['valid'] and portas_service['valid']:

                            porta_destino = get_slot_porta_destino(
                                portas_service['value_port'],
                                portas_service['value_slot'],
                                depara
                            )

                            config = "service-port " + serviceporta.split("service-port " + serviceid['value'] + " ")[0] + str(serviceport) \
                                + " " + serviceporta.split("service-port " + serviceid['value'] + " ")[1].split(" " + portas_service['value'] + " ")[0] + " " + porta_destino \
                                + " " + serviceporta.split("service-port "+ serviceid['value'] + " ")[1].split(" " + portas_service['value'] + " ")[1]
                            
                            aplicacao.append(config + "\n")

                            serviceport += 1

                    aplicacao.append("\n")

    return

def gera_proc_btv_huawei_new(hostname_origem, hostname_destino, depara, vlan_multicast, serviceport):

    path = os.path.join(os.getcwd(), "anexos")
    excel_path = os.path.join(path, f"{hostname_origem}-btv.txt")

    slots = mostra_slots_depara_depois(depara)
    portas = mostra_portas_slots_depara_depois(depara)

    mapeamentos = []

    services_btv = []

    with open(excel_path, "w") as file:

        for slot in slots:

            for porta in portas:

                if porta.split("/")[0] == slot:

                    slotorigem, portaorigem = get_porta_slot_origem(porta.split("/")[1], slot, depara)

                    # função que chama a output do huawei
                    output = Controle.gera_slot_info(
                        hostname_origem, hostname_destino,
                        slotorigem, portaorigem
                    )

                    if output == "":
                        continue

                    nova_output = output.splitlines()

                    inicio = posicao_config_bbs(nova_output)
                    fim = posicao_final_config_bbs(nova_output)

                    services_porta = mapeamento_porta_service_port(nova_output[inicio:fim])

                    for serviceporta in services_porta:

                        serviceid = find_service_port(serviceporta)
                        portas_service = find_porta(serviceporta)

                        if serviceid['valid'] and portas_service['valid']:

                            mapeamentos.append({
                                'service_port': serviceid['value'],
                                'service_port_para': str(serviceport)
                            })

                            serviceport += 1
                    
                    inicio = posicao_config_btv(nova_output)

                    fim = posicao_final_config_btv(nova_output)

                    outros = mapeamento_outros(nova_output[inicio:fim])

                    for mapeamento in mapeamentos:

                        config_final = cria_procedimento_btv(
                            nova_output[inicio:fim],
                            outros,
                            mapeamento['service_port'],
                            mapeamento['service_port_para']
                        )

                        if len(config_final) > 0:

                            for line in config_final.splitlines():
                                if checa_igmp(line):
                                    file.write(line + "\n")
                            
                            services_btv.append(mapeamento['service_port_para'])

                            for line in config_final.splitlines():

                                if checa_igmp_member(line) == False and \
                                    checa_igmp(line) == False and checa_multicast_vlan(line) == False:
                                    file.write(" " + line + "\n") 
        
        # configurações de vlan multicast
        file.write("multicast-vlan " + vlan_multicast + "\n")

        for service_btv in services_btv:
            file.write("igmp multicast-vlan member service-port " + service_btv + "\n")

    return 

def gera_proc_btv_huawei_new_aplicacao(hostname_origem, hostname_destino, depara, vlan_multicast, serviceport):

    slots = mostra_slots_depara_depois(depara)
    portas = mostra_portas_slots_depara_depois(depara)

    mapeamentos = []

    services_btv = []

    aplicacao = []

    for slot in slots:

        for porta in portas:

                if porta.split("/")[0] == slot:

                    slotorigem, portaorigem = get_porta_slot_origem(porta.split("/")[1], slot, depara)

                    # função que chama a output do huawei
                    output = Controle.gera_slot_info(
                        hostname_origem, hostname_destino,
                        slotorigem, portaorigem
                    )

                    if output == "":
                        continue

                    nova_output = output.splitlines()

                    inicio = posicao_config_bbs(nova_output)
                    fim = posicao_final_config_bbs(nova_output)

                    services_porta = mapeamento_porta_service_port(nova_output[inicio:fim])

                    for serviceporta in services_porta:

                        serviceid = find_service_port(serviceporta)
                        portas_service = find_porta(serviceporta)

                        if serviceid['valid'] and portas_service['valid']:

                            mapeamentos.append({
                                'service_port': serviceid['value'],
                                'service_port_para': str(serviceport)
                            })

                            serviceport += 1
                    
                    inicio = posicao_config_btv(nova_output)

                    fim = posicao_final_config_btv(nova_output)

                    outros = mapeamento_outros(nova_output[inicio:fim])

                    for mapeamento in mapeamentos:

                        config_final = cria_procedimento_btv(
                            nova_output[inicio:fim],
                            outros,
                            mapeamento['service_port'],
                            mapeamento['service_port_para']
                        )

                        if len(config_final) > 0:

                            for line in config_final.splitlines():
                                if checa_igmp(line):
                                    aplicacao.append(line + "\n")
                            
                            services_btv.append(mapeamento['service_port_para'])

                            for line in config_final.splitlines():

                                if checa_igmp_member(line) == False and \
                                    checa_igmp(line) == False and checa_multicast_vlan(line) == False:
                                    aplicacao.append(" " + line + "\n") 
        
        # configurações de vlan multicast
        aplicacao.append("multicast-vlan " + vlan_multicast + "\n")

        for service_btv in services_btv:
            aplicacao.append("igmp multicast-vlan member service-port " + service_btv + "\n")

    return 

def gera_proc_service_port_huawei_new_aplicacao_segunda(
    hostname_origem, hostname_destino, depara, serviceport, vlanvoipantiga, vlanvoipnova):


    slots = mostra_slots_depara_depois(depara)
    portas = mostra_portas_slots_depara_depois(depara)

    aplicacao = []

    for slot in slots:

        for porta in portas:

                if porta.split("/")[0] == slot:

                    slotorigem, portaorigem = get_porta_slot_origem(porta.split("/")[1], slot, depara)

                    # função que chama a output do huawei
                    output = Controle.gera_slot_info(
                        hostname_origem, hostname_destino,
                        slotorigem, portaorigem
                    )

                    if output == "":
                        continue

                    nova_output = output.splitlines()

                    inicio = posicao_config_bbs(nova_output)
                    fim = posicao_final_config_bbs(nova_output)

                    services_porta = mapeamento_porta_service_port(nova_output[inicio:fim])

                    for serviceporta in services_porta:

                        serviceid = find_service_port(serviceporta)
                        portas_service = find_porta(serviceporta)

                        if serviceid['valid'] and portas_service['valid']:

                            porta_destino = get_slot_porta_destino(
                                portas_service['value_port'],
                                portas_service['value_slot'],
                                depara
                            )

                            config = "service-port " + serviceporta.split("service-port " + serviceid['value'] + " ")[0] + str(serviceport) \
                                + " " + serviceporta.split("service-port " + serviceid['value'] + " ")[1].split(" " + portas_service['value'] + " ")[0] + " " + porta_destino \
                                + " " + serviceporta.split("service-port "+ serviceid['value'] + " ")[1].split(" " + portas_service['value'] + " ")[1]

                            if checa_vlan_voip(config, vlanvoipantiga):
                            
                                config = config.split(" " + vlanvoipantiga + " ")[0] \
                                            + " " + vlanvoipnova + " " + config.split(" " + vlanvoipantiga + " ")[1]
                                
                            aplicacao.append(config + "\n")

                            serviceport += 1

                    aplicacao.append("\n")

    return

def gera_proc_service_port_huawei_new_segunda(
    hostname_origem, hostname_destino, depara, serviceport, vlanvoipantiga, vlanvoipnova):

    path = os.path.join(os.getcwd(), "anexos")
    excel_path = os.path.join(path, f"{hostname_origem}-service-port.txt")

    slots = mostra_slots_depara_depois(depara)
    portas = mostra_portas_slots_depara_depois(depara)

    with open(excel_path, "w") as file:

        for slot in slots:

            for porta in portas:

                if porta.split("/")[0] == slot:

                    slotorigem, portaorigem = get_porta_slot_origem(porta.split("/")[1], slot, depara)

                    # função que chama a output do huawei
                    output = Controle.gera_slot_info(
                        hostname_origem, hostname_destino,
                        slotorigem, portaorigem
                    )

                    if output == "":
                        continue

                    nova_output = output.splitlines()

                    inicio = posicao_config_bbs(nova_output)
                    fim = posicao_final_config_bbs(nova_output)

                    services_porta = mapeamento_porta_service_port(nova_output[inicio:fim])

                    for serviceporta in services_porta:

                        serviceid = find_service_port(serviceporta)
                        portas_service = find_porta(serviceporta)

                        if serviceid['valid'] and portas_service['valid']:

                            porta_destino = get_slot_porta_destino(
                                portas_service['value_port'],
                                portas_service['value_slot'],
                                depara
                            )

                            config = "service-port " + serviceporta.split("service-port " + serviceid['value'] + " ")[0] + str(serviceport) \
                                + " " + serviceporta.split("service-port " + serviceid['value'] + " ")[1].split(" " + portas_service['value'] + " ")[0] + " " + porta_destino \
                                + " " + serviceporta.split("service-port "+ serviceid['value'] + " ")[1].split(" " + portas_service['value'] + " ")[1]

                            if checa_vlan_voip(config, vlanvoipantiga):
                            
                                config = config.split(" " + vlanvoipantiga + " ")[0] \
                                            + " " + vlanvoipnova + " " + config.split(" " + vlanvoipantiga + " ")[1]
                            
                            file.write(config + "\n")

                            serviceport += 1

                    file.write("\n")

    return