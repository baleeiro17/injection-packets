import os
from utils.info_placa import mostra_slots_depara_antes, mostra_portas_slots_depara_antes
from utils.info_placa import mostra_slots_depara_depois, mostra_portas_slots_depara_depois
from utils.relatorios_huawei import relatorios_falta_config
from utils.regex import checa_igmp, checa_igmp_member, checa_multicast_vlan, checa_vlan_voip, get_svlan_serviceport, pattern_tcont


def calcula_gem_port_hsi(ont_id):
    return str(int(ont_id) + 128)


def calcula_gem_port_tv(ont_id):
    return str(int(ont_id) + 256)


def calcula_gem_port_voip(ont_id):
    return str(int(ont_id) + 384)


def get_slot_destino(slot, deparas):
    for depara in deparas:
        if depara.split("_")[0].split("/")[0] == slot:
            return depara.split("_")[1].split("/")[0]


def get_porta_destino(porta, slot, deparas):
    for depara in deparas:
        if depara.split("_")[0].split("/")[1] == porta and depara.split("_")[0].split("/")[0] == slot:
            return depara.split("_")[1].split("/")[1]


def gera_proc_interface_huawei(clientes, hostname, depara):

    path = os.path.join(os.getcwd(), "anexos")
    excel_path = os.path.join(path, f"{hostname}-interface.txt")

    slots = mostra_slots_depara_depois(depara)
    portas = mostra_portas_slots_depara_depois(depara)

    with open(excel_path, "w") as file:
        # configurações por slot
        for slot in slots:
            file.write("interface gpon 0/" +
                       slot + "\n")
            file.write("\n")
            for porta in portas:
                if porta.split("/")[0] == slot:
                    # configura os clientes por porta
                    for index in range(128, 576, 64):
                        file.write("gemport add " + porta.split("/")[1] + " gemportid " + str(
                            index) + "-" + str(index + 63) + " eth encrypt on\n")
                    file.write("\n")
                    for cliente in clientes:
                        try:
                            if cliente['portapara'].split("/")[1].strip() == porta.split("/")[0] \
                                    and cliente['portapara'].split("/")[2].strip() == porta.split("/")[1]:
                                file.write("interface gpon 0/" +
                                           slot + "\n")
                                file.write("\n")
                                configs = cliente['configinterface'].splitlines(
                                )
                                for config in configs[1:]:
                                    file.write(config + "\n")
                                file.write("\n")
                        except:
                            continue

    return


def gera_proc_interface_huawei_aplicacao(clientes, hostname, depara):

    path = os.path.join(os.getcwd(), "anexos")
    excel_path = os.path.join(path, f"{hostname}-interface.txt")

    slots = mostra_slots_depara_depois(depara)
    portas = mostra_portas_slots_depara_depois(depara)

    aplicacao = []

    # configurações por slot
    for slot in slots:
        aplicacao.append("interface gpon 0/" +
                         slot + "\n")
        # file.write("\n")
        for porta in portas:
            if porta.split("/")[0] == slot:
                # configura os clientes por porta
                for index in range(128, 576, 64):
                    aplicacao.append("gemport add " + porta.split("/")[1] + " gemportid " + str(
                        index) + "-" + str(index + 63) + " eth encrypt on\n")
                # file.write("\n")
                for cliente in clientes:
                    try:
                        if cliente['portapara'].split("/")[1].strip() == porta.split("/")[0] \
                                and cliente['portapara'].split("/")[2].strip() == porta.split("/")[1]:
                            aplicacao.append(
                                "interface gpon 0/" + slot + "\n")
                            # file.write("\n")
                            configs = cliente['configinterface'].splitlines()
                            for config in configs[1:]:
                                aplicacao.append(config + "\n")
                            # file.write("\n")
                    except:
                        continue

    return aplicacao


def gera_proc_service_port_huawei_aplicacao(clientes, hostname, depara):

    slots = mostra_slots_depara_depois(depara)
    portas = mostra_portas_slots_depara_depois(depara)

    aplicacao = []

    # configurações por slot
    for slot in slots:
        for porta in portas:
            if porta.split("/")[0] == slot:
                # configura os clientes por porta
                for cliente in clientes:
                    try:
                        if cliente['portapara'].split("/")[1].strip() == slot \
                                and cliente['portapara'].split("/")[2].strip() == porta.split("/")[1]:
                            for serviceport in cliente['serviceportpara']:
                                config = serviceport['configserviceport']
                                aplicacao.append(config + "\n")
                            # file.write("\n")
                    except:
                        continue

    return aplicacao


def gera_proc_service_port_huawei_aplicacao_segunda(clientes, vlanvoipantiga, vlanvoipnova, depara):

    slots = mostra_slots_depara_depois(depara)
    portas = mostra_portas_slots_depara_depois(depara)

    aplicacao = []

    # configurações por slot
    for slot in slots:
        for porta in portas:
            if porta.split("/")[0] == slot:
                # configura os clientes por porta
                for cliente in clientes:
                    try:
                        if cliente['portapara'].split("/")[1].strip() == slot \
                                and cliente['portapara'].split("/")[2].strip() == porta.split("/")[1]:
                            for serviceport in cliente['serviceportpara']:
                                if checa_vlan_voip(serviceport['configserviceport'], vlanvoipantiga):
                                    config = serviceport['configserviceport'].split(" " + vlanvoipantiga + " ")[0] \
                                        + " " + vlanvoipnova + " " + \
                                        serviceport['configserviceport'].split(
                                            " " + vlanvoipantiga + " ")[1]
                                else:
                                    config = serviceport['configserviceport']
                                aplicacao.append(config + "\n")
                            # file.write("\n")
                    except:
                        continue

    return aplicacao


def gera_proc_service_port_huawei(clientes, hostname, depara):

    path = os.path.join(os.getcwd(), "anexos")
    excel_path = os.path.join(path, f"{hostname}-service-port.txt")

    slots = mostra_slots_depara_depois(depara)
    portas = mostra_portas_slots_depara_depois(depara)

    with open(excel_path, "w") as file:
        # configurações por slot
        for slot in slots:
            for porta in portas:
                if porta.split("/")[0] == slot:
                    # configura os clientes por porta
                    for cliente in clientes:
                        try:
                            if cliente['portapara'].split("/")[1].strip() == slot \
                                    and cliente['portapara'].split("/")[2].strip() == porta.split("/")[1]:
                                for serviceport in cliente['serviceportpara']:
                                    config = serviceport['configserviceport']
                                    file.write(config + "\n")
                                file.write("\n")
                        except:
                            continue

    return


def gera_proc_service_port_huawei_segunda(clientes, hostname, depara, vlanvoipantiga, vlanvoipnova):

    path = os.path.join(os.getcwd(), "anexos")
    excel_path = os.path.join(path, f"{hostname}-service-port.txt")

    slots = mostra_slots_depara_depois(depara)
    portas = mostra_portas_slots_depara_depois(depara)

    with open(excel_path, "w") as file:
        # configurações por slot
        for slot in slots:
            for porta in portas:
                if porta.split("/")[0] == slot:
                    # configura os clientes por porta
                    for cliente in clientes:
                        try:
                            if cliente['portapara'].split("/")[1].strip() == slot \
                                    and cliente['portapara'].split("/")[2].strip() == porta.split("/")[1]:
                                for serviceport in cliente['serviceportpara']:
                                    if checa_vlan_voip(serviceport['configserviceport'], vlanvoipantiga):
                                        config = serviceport['configserviceport'].split(" " + vlanvoipantiga + " ")[0] \
                                            + " " + vlanvoipnova + " " + \
                                            serviceport['configserviceport'].split(
                                                " " + vlanvoipantiga + " ")[1]
                                    else:
                                        config = serviceport['configserviceport']
                                    file.write(config + "\n")
                                file.write("\n")
                        except:
                            continue

    return


def gera_proc_btv_huawei(clientes, hostname, vlan_multicast, depara):

    path = os.path.join(os.getcwd(), "anexos")
    excel_path = os.path.join(path, f"{hostname}-btv.txt")

    slots = mostra_slots_depara_depois(depara)
    portas = mostra_portas_slots_depara_depois(depara)

    with open(excel_path, "w") as file:
        file.write("btv\n")

        # configurações por slot
        for slot in slots:
            for porta in portas:
                if porta.split("/")[0] == slot:
                    # procura configs de igmp
                    for cliente in clientes:
                        try:
                            if cliente['portapara'].split("/")[1].strip() == slot \
                                    and cliente['portapara'].split("/")[2].strip() == porta.split("/")[1]:
                                # procura configs de igmp
                                for serviceport in cliente['serviceportpara']:
                                    if len(serviceport['configbtv']) > 0:
                                        for line in serviceport['configbtv'].splitlines():
                                            if checa_igmp(line):
                                                file.write(line + "\n")
                        except:
                            continue

        # configurações faltantes
        for slot in slots:
            for porta in portas:
                if porta.split("/")[0] == slot:
                    # procura configs de igmp
                    for cliente in clientes:
                        try:
                            if cliente['portapara'].split("/")[1].strip() == slot \
                                    and cliente['portapara'].split("/")[2].strip() == porta.split("/")[1]:
                                # procura configs de igmp
                                for serviceport in cliente['serviceportpara']:
                                    if len(serviceport['configbtv']) > 0:
                                        for line in serviceport['configbtv'].splitlines():
                                            if checa_igmp_member(line) == False and \
                                                    checa_igmp(line) == False and checa_multicast_vlan(line) == False:
                                                file.write(" " + line + "\n")
                        except:
                            continue

        # configurações de vlan multicast
        file.write("multicast-vlan " + vlan_multicast + "\n")

        # configurações de service port list
        for slot in slots:
            for porta in portas:
                if porta.split("/")[0] == slot:
                    # procura configs de service port list
                    for cliente in clientes:
                        try:
                            if cliente['portapara'].split("/")[1].strip() == slot \
                                    and cliente['portapara'].split("/")[2].strip() == porta.split("/")[1]:
                                # procura configs de igmp
                                for serviceport in cliente['serviceportpara']:
                                    if len(serviceport['configbtv']) > 0:
                                        for line in serviceport['configbtv'].splitlines():
                                            if checa_igmp_member(line):
                                                file.write(line + "\n")
                        except:
                            continue

    return


def gera_proc_btv_aplicacao_huawei(clientes, hostname, vlan_multicast, depara):

    slots = mostra_slots_depara_depois(depara)
    portas = mostra_portas_slots_depara_depois(depara)

    aplicacao = []

    aplicacao.append("btv\n")

    # configurações por slot
    for slot in slots:
        for porta in portas:
            if porta.split("/")[0] == slot:
                # procura configs de igmp
                for cliente in clientes:
                    try:
                        if cliente['portapara'].split("/")[1].strip() == slot \
                                and cliente['portapara'].split("/")[2].strip() == porta.split("/")[1]:
                            # procura configs de igmp
                            for serviceport in cliente['serviceportpara']:
                                if len(serviceport['configbtv']) > 0:
                                    for line in serviceport['configbtv'].splitlines():
                                        if checa_igmp(line):
                                            aplicacao.append(line + "\n")
                    except:
                        continue

    # configurações faltantes
    for slot in slots:
        for porta in portas:
            if porta.split("/")[0] == slot:
                # procura configs de igmp
                for cliente in clientes:
                    try:
                        if cliente['portapara'].split("/")[1].strip() == slot \
                                and cliente['portapara'].split("/")[2].strip() == porta.split("/")[1]:
                            # procura configs de igmp
                            for serviceport in cliente['serviceportpara']:
                                if len(serviceport['configbtv']) > 0:
                                    for line in serviceport['configbtv'].splitlines():
                                        if checa_igmp_member(line) == False and \
                                                checa_igmp(line) == False and checa_multicast_vlan(line) == False:
                                            aplicacao.append(" " + line + "\n")
                    except:
                        continue

    # configurações de vlan multicast
    aplicacao.append("multicast-vlan " + vlan_multicast + "\n")

    # configurações de service port list
    for slot in slots:
        for porta in portas:
            if porta.split("/")[0] == slot:
                # procura configs de service port list
                for cliente in clientes:
                    try:
                        if cliente['portapara'].split("/")[1].strip() == slot \
                                and cliente['portapara'].split("/")[2].strip() == porta.split("/")[1]:
                            # procura configs de igmp
                            for serviceport in cliente['serviceportpara']:
                                if len(serviceport['configbtv']) > 0:
                                    for line in serviceport['configbtv'].splitlines():
                                        if checa_igmp_member(line):
                                            aplicacao.append(line + "\n")
                    except:
                        continue

    return aplicacao


def gera_proc_abs_huawei(clientes, hostname):

    path = os.path.join(os.getcwd(), "anexos")
    excel_path = os.path.join(path, f"{hostname}-abs.txt")

    slots = mostra_slots_depara_antes(clientes)
    portas = mostra_portas_slots_depara_antes(clientes)

    with open(excel_path, "w") as file:
        # configurações por slot
        for slot in slots:
            for porta in portas:
                if porta.split("/")[0] == slot:
                    # configura os clientes por porta
                    for cliente in clientes:
                        if cliente['portapara'].split("/")[1].strip() == slot \
                                and cliente['portapara'].split("/")[2].strip() == porta.split("/")[1]:
                            for serviceport in cliente['serviceportpara']:
                                if len(serviceport['configabs']) > 0:
                                    config = serviceport['configabs']
                                    file.write(config + "\n")

    return


def gera_proc_corrigido_huawei(clientes, hostname, vlanrede, vlanvoip, depara):

    path = os.path.join(os.getcwd(), "anexos")
    excel_path = os.path.join(path, f"{hostname}-correcao.txt")

    slots = mostra_slots_depara_depois(depara)
    portas = mostra_portas_slots_depara_depois(depara)

    with open(excel_path, "w") as file:
        for slot in slots:
            for porta in portas:
                if porta.split("/")[0] == slot:
                    file.write("\n")
                    for cliente in clientes:
                        try:
                            if cliente['portapara'].split("/")[1].strip() == slot \
                                    and cliente['portapara'].split("/")[2].strip() == porta.split("/")[1]:
                                if relatorios_falta_config(cliente):
                                    tcont = pattern_tcont(cliente['configinterface'])
                                    if tcont['valid']:
                                        file.write(
                                            "interface gpon 0/" + slot + "\n")
                                        # file.write("\n")
                                        configs = cliente['configinterface'].splitlines(
                                        )
                                        for config in configs[1:]:
                                            file.write(config + "\n")
                                        for service in tcont['value']:
                                            if service == '500':
                                                file.write("ont port vlan " + cliente['portapara'].split("/")[2].strip(
                                                ) + " " + str(int(cliente['ontid'])) + " eth 10 1 translation s-vlan 10\n")
                                                file.write("ont gemport bind " + cliente['portapara'].split("/")[2].strip() + " " + str(
                                                    int(cliente['ontid'])) + " " + calcula_gem_port_hsi(cliente['ontid']) + " 4 gemport-car 6\n")
                                                file.write("ont gemport mapping " + cliente['portapara'].split("/")[2].strip() + " " + str(
                                                    int(cliente['ontid'])) + " " + calcula_gem_port_hsi(cliente['ontid']) + " vlan 10\n")
                                            elif service == '20':
                                                file.write("ont port vlan " + cliente['portapara'].split("/")[2].strip(
                                                ) + " " + str(int(cliente['ontid'])) + " eth 30 1 translation s-vlan 30\n")
                                                file.write("ont gemport bind " + cliente['portapara'].split("/")[2].strip() + " " + str(
                                                    int(cliente['ontid'])) + " " + calcula_gem_port_voip(cliente['ontid']) + " 3 gemport-car 30\n")
                                                file.write("ont gemport mapping " + cliente['portapara'].split("/")[2].strip() + " " + str(
                                                    int(cliente['ontid'])) + " " + calcula_gem_port_voip(cliente['ontid']) + " vlan 30\n")
                                            elif service == "30":
                                                file.write("ont port vlan " + cliente['portapara'].split("/")[2].strip(
                                                ) + " " + str(int(cliente['ontid'])) + " eth 20 1 translation s-vlan 20\n")
                                                file.write("ont gemport bind " + cliente['portapara'].split("/")[2].strip() + " " + str(
                                                    int(cliente['ontid'])) + " " + calcula_gem_port_tv(cliente['ontid']) + " 2 gemport-car 42\n")
                                                file.write("ont gemport mapping " + cliente['portapara'].split("/")[2].strip() + " " + str(
                                                    int(cliente['ontid'])) + " " + calcula_gem_port_tv(cliente['ontid']) + " vlan 20\n")
                                                file.write("ont multicast-forward " + cliente['portapara'].split("/")[
                                                    2].strip() + " " + str(int(cliente['ontid'])) + " tag translation 20\n")
                                else:
                                    continue
                        except:
                            continue
    return
