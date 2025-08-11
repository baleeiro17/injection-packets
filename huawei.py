from flask import Blueprint, jsonify, request, send_file
from models.controle import Controle
from models.huawei import Huawei
from datetime import datetime
import threading
from utils.dto import dto_st2, dto_de_para, dto_clientes
from utils.gera_logs import gera_logs_btv, gera_logs_interface, gera_logs_service_port
from utils.gera_proc_swap_huawei import gera_proc_interface_huawei, gera_proc_corrigido_huawei, gera_proc_service_port_huawei_segunda, \
    gera_proc_service_port_huawei, gera_proc_btv_huawei, gera_proc_service_port_huawei_aplicacao_segunda, gera_proc_abs_huawei, \
    gera_proc_interface_huawei_aplicacao, gera_proc_service_port_huawei_aplicacao, gera_proc_btv_aplicacao_huawei
from utils.gera_proc_swap_nokia import gera_proc_interface_nokia, \
    gera_proc_service_port_nokia, gera_proc_btv_nokia, gera_proc_interface_aplicacao_nokia, \
        gera_proc_service_port_aplicacao_nokia, gera_proc_btv_aplicacao_nokia
from utils.relatorios_huawei import relatorios_huawei
from utils.processa_de_para import processa_de_para, prenche_de_para
from utils.valida_duplicacao_serviceport import valida_duplicacao_serviceport, valida_existencia_serviceport
from utils.valida_config_interface import valida_config_interface
from utils.valida_config_serviceport import valida_config_serviceport
from utils.valida_config_tv import valida_config_tv
from utils.valida_onts import valida_onts_slot_porta
from utils.get_hl4_vendor import get_hl4_vendor
from utils.gera_proc_swap_new_huawei import gera_proc_btv_huawei_new, gera_proc_service_port_huawei_new_aplicacao_segunda, \
    gera_proc_service_port_huawei_new, gera_proc_service_port_huawei_new_aplicacao, gera_proc_btv_huawei_new_aplicacao, \
    gera_proc_service_port_huawei_new_segunda
from utils.relatorios_huawei import relatorios_erros_encontrados, gera_relatorio_falta_config_clientes
import os
import pandas as pd

sem = threading.Semaphore()

huawei_bp = Blueprint('huawei_bp', __name__)


@huawei_bp.route('/cria/swap/',  methods=['POST'])
def cria_swap():
    swap = request.json
    try:
        controle_db = Controle(
            data=datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
            user_id=swap['user_id'],
            hostname_olt_destino=swap['hostname_olt_destino'],
            controle_service_port1='50000',
            controle_service_port2='80000',
            controle_service_port3='110000',
        )
        controle_db.save()

        return {}, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/adiciona/olt/',  methods=['POST'])
def adiciona_olt():
    try:
        file = request.files['depara']
        hostname_destino_olt = request.form['hostname_destino_olt']
        vendor = request.form['vendor']
        hostname_olt_para = request.form['hostname_para_olt']
        hostname_hl4 = request.form['hostname_hl4']

        print(hostname_hl4)

        olt_controle = Controle.get_controle_by_destino(
            hostname_destino_olt
        )

        if len(olt_controle['hostname_olt_para']) == 0:
            controle_olt = True
        else:
            controle_olt = False

        # atualiza controle com OLT DE PARA
        if Controle.atualiza_controle_hostname_olt_para(
            str(olt_controle['id']),
            hostname_olt_para,
            controle_olt,
            vendor,
            hostname_hl4,
            get_hl4_vendor(hostname_hl4)
        ):
            prenche_de_para(file, hostname_destino_olt, hostname_olt_para)
            return {}, 200
        else:
            return {}, 404
        
    except Exception as e:
        print(e)
        return {}, 404

@huawei_bp.route('/remocao/olt/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['DELETE'])
def remocao_olt(hostname_origem, hostname_destino):
    try:
        if Controle.delete_olt_by_destino(hostname_origem, hostname_destino) and Huawei.remove_huawei_clientes(hostname_origem):
            return {}, 200
        else:
            return {}, 404
    except Exception as e:
        print(e)
        return {}, 404

@huawei_bp.route('/aciona/config/olt/para/<string:hostname_para>/destino/<string:hostname_destino>',  methods=['POST'])
def aciona_configuracao_olt(hostname_para, hostname_destino):
    try:
        payload = request.json

        userolt = payload['user_olt']
        pwdolt = payload['pwd_olt']
        ipolt = payload['ip_olt']

        if Controle.atualiza_config_olt(
            hostname_para,
            hostname_destino,
            ipolt, 
            userolt, 
            pwdolt
        ):
            if Controle.atualiza_estado_mensagem(
                hostname_para, hostname_destino, "Pendente Configuração", "Pendente Configuração"):
                return {}, 200
            else:
                return {}, 404
        else:
            {}, 404

    except Exception as e:
        print(e)
        return {}, 404

@huawei_bp.route('/atualiza/config/olt/interface/logs/origem/<string:hostname_para>/destino/<string:hostname_destino>/',  methods=['POST'])
def atualiza_logs_interface_olt(hostname_para, hostname_destino):
    try:
        payload = request.json

        logs = payload['logs']

        if Controle.atualiza_logs_olt(
            hostname_para, 
            hostname_destino, 
            logs, "interface"):
            return {}, 200
        else:
            return {}, 404

    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/atualiza/config/olt/service/logs/origem/<string:hostname_para>/destino/<string:hostname_destino>/',  methods=['POST'])
def atualiza_logs_service_olt(hostname_para, hostname_destino):
    try:
        payload = request.json

        logs = payload['logs']

        if Controle.atualiza_logs_olt(
            hostname_para, 
            hostname_destino, 
            logs, "service"):
            return {}, 200
        else:
            return {}, 404

    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/atualiza/config/olt/btv/logs/origem/<string:hostname_para>/destino/<string:hostname_destino>/',  methods=['POST'])
def atualiza_logs_btv_olt(hostname_para, hostname_destino):
    try:
        payload = request.json

        logs = payload['logs']

        if Controle.atualiza_logs_olt(
            hostname_para, 
            hostname_destino, 
            logs, "btv"):
            return {}, 200
        else:
            return {}, 404

    except Exception as e:
        print(e)
        return {}, 404

@huawei_bp.route('/gera/logs/olt/origem/<string:hostname_para>/destino/<string:hostname_destino>',  methods=['GET'])
def gera_logs_olt_origem(hostname_para, hostname_destino):
    try:

        logs = Controle.get_controle_by_hostname_logs(
            hostname_para, 
            hostname_destino
        )

        return {
            'aplicacao': logs,
            'ip_olt': '',
            'user_olt': '',
            'pwd_olt': ''
        }, 200
    
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/lista/olt/',  methods=['GET'])
def lista_olt():

    controles = Controle.get_controles()

    olts = []

    for controle in controles:

        estado = 'Concluído'

        if len(controle['hostname_olt_para']) > 0:

            for olt_para in controle['hostname_olt_para']:

                if 'Pendente' in olt_para['estado'] or 'processamento' in olt_para['estado'] or 'Aguardando' in olt_para['estado']:
                    estado = 'Pendente'
                elif 'Erro' in olt_para['estado']:
                    estado = 'Pendente'
                elif olt_para['estado'] == 'Concluído Procedimento':
                    estado = 'Procedimento Pronto'
                elif olt_para['estado'] == 'Concluído Configuração':
                    estado = 'Dispositivo Configurado'
                else:
                    estado = 'Concluído'

                olts.append({
                    'id': str(controle['id']),
                    'data': controle['data'],
                    'user_id': controle['user_id'],
                    'estado': estado,
                    'mensagem': estado,
                    'hostname_olt_destino': controle['hostname_olt_destino'],
                    'hostname_olt_para': olt_para['hostname']
                })

        else:

            olts.append({
                'id': "",
                'data': controle['data'],
                'user_id': controle['user_id'],
                'estado': "Concluído",
                'mensagem': "Concluído",
                'hostname_olt_destino': controle['hostname_olt_destino'],
                'hostname_olt_para': ""
            })

    return olts, 200


@huawei_bp.route('/pendentes/olt/',  methods=['GET'])
def pendentes_olt():

    if len(Controle.get_controle_em_processamento()) > 3:
        return {}, 404

    olts_primeira = Controle.get_controle_pendentes_primeira_olt()
    if olts_primeira != []:
        return olts_primeira, 200

    olts_segunda = Controle.get_controle_pendentes_segunda_olt()
    if olts_segunda != []:
        return olts_segunda, 200

    return {}, 404


@huawei_bp.route('/gera/planilha/de/para/<string:hostname_olt>/destino/<string:hostname_olt_destino>',  methods=['GET'])
def gera_de_para_planilha(hostname_olt, hostname_olt_destino):
    try:
        planilhadepara = Controle.get_controle_de_para_by_hostname(
            hostname_olt_destino, hostname_olt)
        clientes = Huawei.get_huawei_by_hostname(hostname_olt)
        return dto_de_para(clientes, planilhadepara), 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/valida/criacao/clientes/<string:hostname_olt>',  methods=['GET'])
def valida_criacao_clientes_olt(hostname_olt):
    try:
        clientes = Huawei.get_huawei_by_hostname(hostname_olt)
        if len(clientes) == 0:
            return {'status': 'nao criado'}, 204
        else:
            return {'status': 'criado'}, 200
    except Exception as e:
        return {}, 404


@huawei_bp.route('/gera/output/onts/<string:hostname_olt_origem>/destino/<string:hostname_olt_destino>',  methods=['GET'])
def gera_output_onts(hostname_olt_origem, hostname_olt_destino):
    output = Controle.get_controle_output_ont_by_hostname(
        hostname_olt_destino, hostname_olt_origem)
    return {'output': output}, 200


@huawei_bp.route('/gera/output/bridges/<string:hostname_olt_origem>/destino/<string:hostname_olt_destino>',  methods=['GET'])
def gera_output_bridges(hostname_olt_origem, hostname_olt_destino):
    output = Controle.get_controle_output_bridge_by_hostname(
        hostname_olt_destino, hostname_olt_origem)
    return {'output': output}, 200


@huawei_bp.route('/gera/clientes/de/para/<string:hostname_olt>/slotporta/',  methods=['PUT'])
def gera_de_para_clientes(hostname_olt):
    info = request.json
    try:
        clientes = Huawei.get_huawei_by_hostname(hostname_olt)
        return dto_clientes(clientes, info['slotporta']), 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/gera/output/config/interface/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['PUT'])
def gera_output_config(hostname_origem, hostname_destino):
    info = request.json
    try:
        output = Controle.gera_slot_info(
            hostname_origem,
            hostname_destino,
            info['slotporta'].split("/")[1].strip(),
            info['slotporta'].split("/")[2].strip()
        )
        return {'output': output}, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/gera/fluxo/swap/<string:swap_id>',  methods=['PUT'])
def gera_de_para_fluxo(swap_id):
    info = request.json
    try:
        Huawei.atualiza_estado_mensagem(
            swap_id, "Pendente Interface", "Pendente Interface")
        return {}, 200
    except Exception as e:
        return {}, 404


@huawei_bp.route('/atualiza/estado/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['PUT'])
def atualiza_estado(hostname_origem, hostname_destino):
    info = request.json
    try:
        Controle.atualiza_estado_mensagem(
            hostname_origem, hostname_destino, 
            info['estado'], info['mensagem']
        )
        return {}, 200
    except Exception as e:
        return {}, 404


@huawei_bp.route('/adiciona/cliente/<string:hostname_olt>',  methods=['PUT'])
def adiciona_cliente(hostname_olt):
    info = request.json
    try:
        Huawei.atualiza_cliente_portade_ontid(hostname_olt, info['clientes'])
        return {}, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/adiciona/cliente/nokia7342/<string:hostname_olt>', methods=['PUT'])
def adiciona_cliente_nokia_7342(hostname_olt):
    info = request.json
    try:
        Huawei.atualiza_cliente_portade_nokia7342(
            hostname_olt, info['clientes'])
        return {}, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/atualiza/services/nokia7342/<string:swap_olt>', methods=['PUT'])
def atualiza_services_nokia_7342(swap_olt):
    info = request.json
    try:
        sem.acquire(10)
        Huawei.atualiza_services_portade_nokia7342(swap_olt, info['services'])
        sem.release()
        return {}, 200
    except Exception as e:
        sem.release()
        print(e)
        return {}, 404


@huawei_bp.route('/adiciona/vlan/voip/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['PUT'])
def adiciona_vlan_voip(hostname_origem, hostname_destino):
    info = request.json
    try:
        Controle.atualiza_vlan_voip(hostname_origem, hostname_destino, info['vlanvoip'])
        return {}, 200
    except Exception as e:
        return {}, 404


@huawei_bp.route('/adiciona/vlan/b2b/vpn/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['PUT'])
def adiciona_vlan_b2b_vpn(hostname_origem, hostname_destino):
    info = request.json
    try:
        Controle.atualiza_vlan_b2b_vpn(hostname_origem, 
            hostname_destino, info['vlanb2b'])
        return {}, 200
    except Exception as e:
        return {}, 404


@huawei_bp.route('/adiciona/vlan/b2b/internet/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['PUT'])
def adiciona_vlan_b2b_internet(hostname_origem, hostname_destino):
    info = request.json
    try:
        Controle.atualiza_vlan_b2b_internet(hostname_origem, hostname_destino, info['vlanb2b'])
        return {}, 200
    except Exception as e:
        return {}, 404

@huawei_bp.route('/adiciona/vlan/b2b/sip/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['PUT'])
def adiciona_vlan_b2b_sip(hostname_origem, hostname_destino):
    info = request.json
    try:
        Controle.atualiza_vlan_b2b_sip(hostname_origem, hostname_destino, info['vlanb2b'])
        return {}, 200
    except Exception as e:
        return {}, 404


@huawei_bp.route('/adiciona/vlan/rede/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['PUT'])
def adiciona_vlan_rede(hostname_origem, hostname_destino):
    info = request.json
    try:
        Controle.atualiza_vlan_rede(hostname_origem, hostname_destino, info['vlanrede'])
        return {}, 200
    except Exception as e:
        return {}, 404


@huawei_bp.route('/adiciona/vlan/multicast/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['PUT'])
def adiciona_vlan_multicast(hostname_origem, hostname_destino):
    info = request.json
    try:
        Controle.atualiza_vlan_multicast(hostname_origem, hostname_destino, info['vlanmulticast'])
        return {}, 200
    except Exception as e:
        return {}, 404

@huawei_bp.route('/adiciona/vlan/unicast/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['PUT'])
def adiciona_vlan_unicast(hostname_origem, hostname_destino):
    info = request.json
    try:
        Controle.atualiza_vlan_unicast(hostname_origem, hostname_destino, info['vlanunicast'])
        return {}, 200
    except Exception as e:
        return {}, 404


@huawei_bp.route('/adiciona/config/interface/<string:hostname_olt>',  methods=['PUT'])
def adiciona_config_interface(hostname_olt):
    info = request.json
    try:
        Huawei.atualiza_config_interface(hostname_olt, info['config_interface'],
                                         info['ontid'], info['portade'])
        return {}, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/adiciona/porta/para/<string:swap_id>',  methods=['PUT'])
def adiciona_porta_para(swap_id):
    info = request.json
    try:
        Huawei.atualiza_porta_para(swap_id, info['portapara'],
                                   info['ontid'], info['portade'])
        return {}, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/reinicia/service/port/<string:swap_id>',  methods=['GET'])
def reinicia_service_port_rota(swap_id):
    try:
        Huawei.reinicia_service_port(swap_id)
        return {}, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/valida/duplicacao/service/port/origem/<string:hostname_olt_origem>/destino/<string:hostname_olt_destino>',  methods=['GET'])
def valida_duplicacao_service_port(hostname_olt_origem, hostname_olt_destino):
    try:
        dto = valida_duplicacao_serviceport(
            hostname_olt_origem, hostname_olt_destino)
        return dto, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/valida/existencia/service/port/<string:hostname_olt>',  methods=['PUT'])
def valida_existencia_service_port(hostname_olt):
    info = request.json
    try:
        dto = valida_existencia_serviceport(
            hostname_olt, info['service_ports_router'])
        return dto, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/valida/config/interface/<string:swap_id>',  methods=['GET'])
def valida_config_interface_rota(swap_id):
    try:
        olt = Huawei.get_huawei_by_id(swap_id)
        dto = valida_config_interface(olt)
        return dto, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/valida/config/serviceport/<string:swap_id>',  methods=['GET'])
def valida_config_serviceport_rota(swap_id):
    try:
        olt = Huawei.get_huawei_by_id(swap_id)
        dto = valida_config_serviceport(olt)
        return dto, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/valida/config/tv/<string:hostname_olt>',  methods=['PUT'])
def valida_config_tv_rota(hostname_olt):
    info = request.json
    try:
        dto = valida_config_tv(hostname_olt, info['clientestv'])

        Controle.atualiza_validacao_btv(
            hostname_olt, dto['analise'], dto['semconfig'])

        return dto, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/valida/numero/onts/<string:hostname_olt>',  methods=['PUT'])
def valida_numero_onts(hostname_olt):
    info = request.json
    try:

        clientes = Huawei.get_huawei_by_hostname(hostname_olt)

        dto = valida_onts_slot_porta(
            clientes,
            info['slotporta'],
            info['totalslotporta']
        )

        Controle.atualiza_validacao_slot_info(
            hostname_olt,
            info['slotporta'], dto['analise'], dto['total'],
            dto['totalcaixa']
        )

        return dto, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/adiciona/service/port/<string:swap_id>',  methods=['PUT'])
def adiciona_service_port(swap_id):
    info = request.json

    sem.acquire(10)

    try:
        Huawei.atualiza_cliente_service_port(swap_id,
            info['hostname_olt'], info['ontid'],
            info['portade'], info['serviceports'])
        sem.release()
        return {}, 200
    except Exception as e:
        sem.release()
        print(e)
        return {}, 404


@huawei_bp.route('/adiciona/config/service/port/<string:hostname_olt>',  methods=['PUT'])
def adiciona_config_service_port(hostname_olt):
    info = request.json

    try:
        Huawei.atualiza_cliente_config_service_port(hostname_olt,
                                                    info['ontid'], info['portade'],
                                                    info['serviceport'], info['configservice'])
        return {}, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/adiciona/config/service/btv/<string:hostname_olt>',  methods=['PUT'])
def adiciona_config_service_btv(hostname_olt):
    info = request.json

    try:
        Huawei.atualiza_cliente_config_btv(hostname_olt,
                                           info['ontid'], info['portade'],
                                           info['serviceport'], info['configbtv'])
        return {}, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/adiciona/config/service/abs/<string:hostname_olt>',  methods=['PUT'])
def adiciona_config_service_abs(hostname_olt):
    info = request.json

    try:
        Huawei.atualiza_cliente_config_abs(hostname_olt,
                                           info['ontid'], info['portade'],
                                           info['serviceport'], info['configabs'])
        return {}, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/atualiza/output/interface/<string:swap_id>',  methods=['PUT'])
def atualiza_output_interface(swap_id):
    info = request.json
    try:
        Huawei.atualiza_output_interface(swap_id,
                                         info['ontid'], info['portade'],
                                         info['output'])
        return {}, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/atualiza/slot/info/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['PUT'])
def atualiza_slot_info(hostname_origem, hostname_destino):
    info = request.json
    try:
        Controle.atualiza_slot_port_info(
            hostname_origem, hostname_destino, 
            info['name'], info['output']
        )
        return {}, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/atualiza/output/onts/<string:hostname_olt>',  methods=['PUT'])
def atualiza_output_onts(hostname_olt):
    info = request.json
    try:
        Controle.atualiza_controle_output_onts_by_hostname(
            hostname_olt, info['output'])
        return {}, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/atualiza/output/bridges/<string:hostname_olt>',  methods=['PUT'])
def atualiza_output_bridges(hostname_olt):
    info = request.json
    try:
        Controle.atualiza_controle_output_bridge_by_hostname(
            hostname_olt, info['output'])
        return {}, 200
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/gera/proc/interfaces/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['GET'])
def gera_proc_interfaces_huawei(hostname_origem, hostname_destino):
    try:

        clientes = Huawei.get_huawei_by_hostname(hostname_origem)

        vendor = Controle.get_controle_by_vendor_hostname_origem(hostname_origem, hostname_destino)

        depara = Controle.get_controle_de_para_by_hostname(hostname_destino, hostname_origem)

        if vendor == "huawei":

            gera_proc_interface_huawei(clientes, hostname_origem, depara)

        elif vendor == "nokia-7342" or vendor == 'nokia-7302':

            vlans_internet = Controle.get_controle_by_vlan_internet_hostname_origem(
                hostname_origem)

            vlans_vpn = Controle.get_controle_by_vlan_vpn_hostname_origem(
                hostname_origem)

            gera_proc_interface_nokia(
                clientes, hostname_origem, vlans_vpn, vlans_internet)

        path = os.path.join(os.getcwd(), "anexos")
        excel_path = os.path.join(path, f"{hostname_origem}-interface.txt")

        return send_file(excel_path, as_attachment=True)
    except Exception as e:
        print(e)
        return {}, 404

@huawei_bp.route('/gera/logs/serviceport/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['GET'])
def gera_logs_serviceport_huawei(hostname_origem, hostname_destino):
    try:
        logs = Controle.get_controle_by_logs_service_hostname_origem(hostname_origem, hostname_destino)

        path = os.path.join(os.getcwd(), "anexos")
        excel_path = os.path.join(path, f"{hostname_origem}-logs-service-port.txt")

        gera_logs_service_port(logs, hostname_origem)

        return send_file(excel_path, as_attachment=True)
    
    except Exception as e:
        print(e)
        return {}, 404

@huawei_bp.route('/gera/logs/interface/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['GET'])
def gera_logs_interface_huawei(hostname_origem, hostname_destino):
    try:
        logs = Controle.get_controle_by_logs_interface_hostname_origem(hostname_origem, hostname_destino)

        gera_logs_interface(logs, hostname_origem)

        path = os.path.join(os.getcwd(), "anexos")
        excel_path = os.path.join(path, f"{hostname_origem}-logs-interface.txt")

        return send_file(excel_path, as_attachment=True)
    
    except Exception as e:
        print(e)
        return {}, 404

@huawei_bp.route('/gera/logs/btv/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['GET'])
def gera_logs_btv_huawei(hostname_origem, hostname_destino):
    try:
        logs = Controle.get_controle_by_logs_btv_hostname_origem(hostname_origem, hostname_destino)

        gera_logs_btv(logs, hostname_origem)

        path = os.path.join(os.getcwd(), "anexos")
        excel_path = os.path.join(path, f"{hostname_origem}-logs-btv.txt")

        return send_file(excel_path, as_attachment=True)
    
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/gera/proc/serviceport/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['GET'])
def gera_proc_serviceport_huawei(hostname_origem, hostname_destino):
    try:

        clientes = Huawei.get_huawei_by_hostname(hostname_origem)

        vendor = Controle.get_controle_by_vendor_hostname_origem(hostname_origem, hostname_destino)

        depara = Controle.get_controle_de_para_by_hostname(hostname_destino, hostname_origem)

        tipo_olt = Controle.get_controle_by_hostname_tipo_olt(hostname_origem, hostname_destino)

        if vendor == "huawei":

            if tipo_olt:
                
                gera_proc_service_port_huawei_new(
                    hostname_origem, hostname_destino, depara, 50000)

            else:
                
                vlan_voip_antiga = Controle.get_controle_by_hostname_vlan_voip(hostname_destino, hostname_origem)

                vlan_voip_nova = Controle.get_controle_by_hostname_vlan_voip_primeira(hostname_destino, hostname_origem)

                gera_proc_service_port_huawei_new_segunda(hostname_origem, hostname_destino, depara, 80000, vlan_voip_antiga, vlan_voip_nova)


        elif vendor == "nokia-7342" or vendor == 'nokia-7302':

            vlans_b2b_sip = Controle.get_controle_by_vlan_sip_hostname_origem_destino(
                hostname_origem, hostname_destino)

            vlans_b2b_internet = Controle.get_controle_by_vlan_internet_hostname_origem_destino(
                hostname_origem, hostname_destino)
            
            vlans_b2b_vpn = Controle.get_controle_by_vlan_vpn_hostname_origem_destino(
                hostname_origem, hostname_destino)

            gera_proc_service_port_nokia(clientes, hostname_origem, vlans_b2b_sip, vlans_b2b_internet, vlans_b2b_vpn)

        path = os.path.join(os.getcwd(), "anexos")
        excel_path = os.path.join(path, f"{hostname_origem}-service-port.txt")

        return send_file(excel_path, as_attachment=True)

    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/gera/proc/btv/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['GET'])
def gera_proc_btv_huawei_rota(hostname_origem, hostname_destino):

    try:

        vendor = Controle.get_controle_by_vendor_hostname_origem(hostname_origem, hostname_destino)

        clientes = Huawei.get_huawei_by_hostname(hostname_origem)
        
        depara = Controle.get_controle_de_para_by_hostname(hostname_destino, hostname_origem)

        tipo_olt = Controle.get_controle_by_hostname_tipo_olt(hostname_origem, hostname_destino)

        if vendor == "huawei":

            if tipo_olt:

                vlanmulticast = Controle.get_controle_by_hostname_vlan_multicast(
            hostname_origem, hostname_destino)
                
                gera_proc_btv_huawei_new(hostname_origem, hostname_destino, depara, vlanmulticast, 50000)

            else:

                vlanmulticast = Controle.get_controle_by_hostname_vlan_multicast_primeira(
                    hostname_origem, hostname_destino)
                
                gera_proc_btv_huawei(clientes, hostname_origem, vlanmulticast, depara)

        elif vendor == "nokia-7342" or vendor == 'nokia-7302':

            vlanmulticast = Controle.get_controle_by_hostname_vlan_multicast(
                hostname_origem, hostname_destino)

            gera_proc_btv_nokia(clientes, hostname_origem, vlanmulticast)

        path = os.path.join(os.getcwd(), "anexos")
        excel_path = os.path.join(path, f"{hostname_origem}-btv.txt")

        return send_file(excel_path, as_attachment=True)

    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/gera/proc/abs/<string:hostname>',  methods=['GET'])
def gera_proc_abs_huawei_rota(hostname):
    try:

        clientes = Huawei.get_huawei_by_hostname(hostname)

        gera_proc_abs_huawei(clientes, hostname)

        path = os.path.join(os.getcwd(), "anexos")
        excel_path = os.path.join(path, f"{hostname}-abs.txt")

        return send_file(excel_path, as_attachment=True)
    except Exception as e:
        print(e)
        return {}, 404

@huawei_bp.route('/gera/proc/correcao/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['GET'])
def gera_proc_correcao_huawei_rota(hostname_origem, hostname_destino):
    try:

        clientes = Huawei.get_huawei_by_hostname(hostname_origem)

        vlan_rede = Controle.get_controle_by_hostname_vlan_rede(hostname_destino, hostname_origem)

        vlan_voip = Controle.get_controle_by_hostname_vlan_voip(hostname_destino, hostname_origem)

        depara = Controle.get_controle_de_para_by_hostname(hostname_destino, hostname_origem)

        gera_proc_corrigido_huawei(clientes, hostname_origem, vlan_rede, vlan_voip, depara)

        path = os.path.join(os.getcwd(), "anexos")
        excel_path = os.path.join(path, f"{hostname_origem}-correcao.txt")

        return send_file(excel_path, as_attachment=True)
    except Exception as e:
        print(e)
        return {}, 404

@huawei_bp.route('/gera/proc/interfaces/aplicacao/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['GET'])
def gera_proc_aplicacao_interfaces_huawei(hostname_origem, hostname_destino):

    try:
        clientes = Huawei.get_huawei_by_hostname(hostname_origem)

        vendor = Controle.get_controle_by_vendor_hostname_origem(hostname_origem, hostname_destino)

        depara = Controle.get_controle_de_para_by_hostname(hostname_destino, hostname_origem)

        ip_olt = Controle.get_controle_by_ip_olt(hostname_origem, hostname_destino)

        user_olt = Controle.get_controle_by_user_olt(hostname_origem, hostname_destino)

        pwd_olt = Controle.get_controle_by_pwd_olt(hostname_origem, hostname_destino)

        if vendor == "huawei":

            aplicacao = gera_proc_interface_huawei_aplicacao(clientes, hostname_origem, depara)

        elif vendor == "nokia-7342" or vendor == 'nokia-7302':

            vlans_internet = Controle.get_controle_by_vlan_internet_hostname_origem(
                hostname_origem)

            vlans_vpn = Controle.get_controle_by_vlan_vpn_hostname_origem(
                hostname_origem)

            aplicacao = gera_proc_interface_aplicacao_nokia(clientes, hostname_origem, vlans_vpn, vlans_internet)
        
        return {
            'aplicacao': aplicacao,
            'ip': ip_olt,
            'user': user_olt, 
            'pwd': pwd_olt, 
        }, 200

    except Exception as e:

        return {},404

@huawei_bp.route('/gera/proc/services/aplicacao/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['GET'])
def gera_proc_aplicacao_services_huawei(hostname_origem, hostname_destino):

    try:
        clientes = Huawei.get_huawei_by_hostname(hostname_origem)

        vendor = Controle.get_controle_by_vendor_hostname_origem(hostname_origem, hostname_destino)

        depara = Controle.get_controle_de_para_by_hostname(hostname_destino, hostname_origem)

        ip_olt = Controle.get_controle_by_ip_olt(hostname_origem, hostname_destino)

        user_olt = Controle.get_controle_by_user_olt(hostname_origem, hostname_destino)

        pwd_olt = Controle.get_controle_by_pwd_olt(hostname_origem, hostname_destino)

        tipo_olt = Controle.get_controle_by_hostname_tipo_olt(hostname_origem, hostname_destino)

        if vendor == "huawei":

            if tipo_olt:
                
                aplicacao = gera_proc_service_port_huawei_new_aplicacao(
                    hostname_origem, hostname_destino, depara, 50000)

            else:

                vlan_voip_antiga = Controle.get_controle_by_hostname_vlan_voip(hostname_destino, hostname_origem)

                vlan_voip_nova = Controle.get_controle_by_hostname_vlan_voip_primeira(hostname_destino, hostname_origem)

                aplicacao = gera_proc_service_port_huawei_new_aplicacao_segunda(hostname_origem, hostname_destino, depara, 80000, vlan_voip_antiga, vlan_voip_nova)
        
        elif vendor == "nokia-7342" or vendor == 'nokia-7302':

            vlans_b2b_sip = Controle.get_controle_by_vlan_sip_hostname_origem_destino(
                hostname_origem, hostname_destino)

            vlans_b2b_internet = Controle.get_controle_by_vlan_internet_hostname_origem_destino(
                hostname_origem, hostname_destino)
            
            vlans_b2b_vpn = Controle.get_controle_by_vlan_vpn_hostname_origem_destino(
                hostname_origem, hostname_destino)

            aplicacao = gera_proc_service_port_aplicacao_nokia(clientes, 
                hostname_origem, vlans_b2b_sip, vlans_b2b_vpn, vlans_b2b_internet)

        return {
            'aplicacao': aplicacao,
            'ip': ip_olt,
            'user': user_olt, 
            'pwd': pwd_olt, 
        }, 200

    except Exception as e:
        print(e)
        return {}, 404

@huawei_bp.route('/gera/proc/btv/aplicacao/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['GET'])
def gera_proc_aplicacao_btv_huawei_rota(hostname_origem, hostname_destino):

    try:

        vendor = Controle.get_controle_by_vendor_hostname_origem(hostname_origem, hostname_destino)

        clientes = Huawei.get_huawei_by_hostname(hostname_origem)

        vlanmulticast = Controle.get_controle_by_hostname_vlan_multicast(
            hostname_origem, hostname_destino)
        
        depara = Controle.get_controle_de_para_by_hostname(hostname_destino, hostname_origem)

        ip_olt = Controle.get_controle_by_ip_olt(hostname_origem, hostname_destino)

        user_olt = Controle.get_controle_by_user_olt(hostname_origem, hostname_destino)

        pwd_olt = Controle.get_controle_by_pwd_olt(hostname_origem, hostname_destino)

        tipo_olt = Controle.get_controle_by_hostname_tipo_olt(hostname_origem, hostname_destino)

        if vendor == "huawei":

            if tipo_olt:

                aplicacao = gera_proc_btv_huawei_new_aplicacao(
                    hostname_origem, hostname_destino, depara, vlanmulticast, 50000)
            
            else:

                vlanmulticast = Controle.get_controle_by_hostname_vlan_multicast_primeira(
            hostname_origem, hostname_destino)

                aplicacao = gera_proc_btv_aplicacao_huawei(clientes, hostname_origem, vlanmulticast, depara)

        elif vendor == "nokia-7342" or vendor == 'nokia-7302':

            vlanmulticast = Controle.get_controle_by_hostname_vlan_multicast(
            hostname_origem, hostname_destino)

            aplicacao = gera_proc_btv_aplicacao_nokia(clientes, hostname_origem, vlanmulticast)

        return {
            'aplicacao': aplicacao,
            'ip': ip_olt,
            'user': user_olt, 
            'pwd': pwd_olt, 
        }, 200

        
    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/gera/relatorio/slid/<string:swap_id>',  methods=['GET'])
def gera_relatorio_slid_huawei_rota(swap_id):
    try:
        olt = Huawei.get_huawei_by_id(swap_id)

        olts = relatorios_huawei(olt)

        olts_df = pd.DataFrame(columns=['SLID', 'ONTID', 'SLOT', 'PORT'])
        olts_df = pd.DataFrame(olts)

        path = os.path.join(os.getcwd() + "/anexos/")
        excel_path = os.path.join(
            path, f"relatorio-slids-" + datetime.now().strftime('%Y-%m-%d') + ".xlsx")

        olts_df.to_excel(excel_path, sheet_name='Relatório', index=False)

        return send_file(excel_path, as_attachment=True)

    except Exception as e:
        print(e)
        return {}, 404


@huawei_bp.route('/adiciona/de/para/origem/<string:hostname_olt_origem>/destino/<string:hostname_olt_destino>',  methods=['POST'])
def adiciona_de_para(hostname_olt_origem, hostname_olt_destino):

    file = request.files['depara']

    if file:

        try:

            prenche_de_para(file, hostname_olt_destino, hostname_olt_origem)

            Controle.atualiza_estado_mensagem(
                hostname_olt_origem,
                hostname_olt_destino,
                "Aguardando depara",
                "Aguardando depara"
            )

            return {}, 200

        except Exception as e:
            print(e)
            return {}, 404

@huawei_bp.route('/adiciona/de/para/logico/origem/<string:hostname_olt_para>/destino/<string:hostname_olt_destino>',  methods=['PUT'])
def adiciona_de_para_logico(hostname_olt_destino, hostname_olt_para):

    infos = request.json

    try:
       
        for info in infos['vlans']:

            if info['tipo'] == 'VOIP' and (info['vlandestino'] != info['vlanorigem']):

                Controle.atualiza_vlan_voip(hostname_olt_para, hostname_olt_destino, info['vlanorigem'])
            
            elif info['tipo'] == 'MULTICAST' and (info['vlandestino'] != info['vlanorigem']):

                Controle.atualiza_vlan_multicast(hostname_olt_para, hostname_olt_destino, info['vlanorigem'])
            
            elif info['tipo'] == 'VPN B2B' and (info['vlandestino'] != info['vlanorigem']):

                if info['vlandestino'] == 'Definir':

                    Controle.atualiza_vlan_b2b_vpn_partes(hostname_olt_para, hostname_olt_destino, info['vlanorigem'])
                
                else:

                    Controle.atualiza_vlan_b2b_vpn_valores(hostname_olt_para, hostname_olt_destino, info['vlandestino'], info['vlanorigem'])

            
            elif info['tipo'] == 'INTERNET B2B' and (info['vlandestino'] != info['vlanorigem']):

                if info['vlandestino'] == 'Definir':

                    Controle.atualiza_vlan_b2b_internet_partes(hostname_olt_para, hostname_olt_destino, info['vlanorigem'])

                else:

                    Controle.atualiza_vlan_b2b_internet_valores(hostname_olt_para, hostname_olt_destino, info['vlandestino'], info['vlanorigem'])

            
            elif info['tipo'] == 'SIP B2B' and (info['vlandestino'] != info['vlanorigem']):
                
                if info['vlandestino'] == 'Definir':

                    Controle.atualiza_vlan_b2b_sip_partes(hostname_olt_para, hostname_olt_destino, info['vlanorigem'])
                
                else:

                    Controle.atualiza_vlan_b2b_sip_valores(hostname_olt_para, hostname_olt_destino, info['vlandestino'], info['vlanorigem'])

        # Controle.atualiza_vlan_voip(hostname_olt_para, hostname_olt_destino, info['vlanvoip'])
        # Controle.atualiza_vlan_multicast(hostname_olt_para, hostname_olt_destino, info['vlanmulticast'])
        # Controle.atualiza_vlan_b2b_internet(hostname_olt_para, hostname_olt_destino, info['vlanb2binternet'])
        # Controle.atualiza_vlan_b2b_vpn(hostname_olt_para, hostname_olt_destino, info['vlanb2bvpn'])
        # Controle.atualiza_vlan_rede(hostname_olt_para, hostname_olt_destino, info['vlanrede'])

        return {}, 200

    except Exception as e:

        print(e)

        return {}, 404


@huawei_bp.route('/gera/de/para/logico/<string:hostname_olt>/destino/<string:hostname_olt_destino>',  methods=['GET'])
def gera_de_para_logico(hostname_olt, hostname_olt_destino):
    controle = Controle.get_controle_by_origem_destino(hostname_olt_destino, hostname_olt)

    for olt_para in controle['hostname_olt_para']:

        if olt_para['hostname'] == hostname_olt:

            dto = []

            # B2B VPN
            if len(olt_para['vlanb2bvpn']) > 0:

                for vlan_vpn in olt_para['vlanb2bvpn']:

                    dto.append({
                        'vlanorigem': vlan_vpn,
                        'vlandestino': vlan_vpn,
                        'tipo': 'VPN B2B'
                    })

                if len(olt_para['vlanb2bvpn']) == 1:

                    dto.append({
                        'vlanorigem': 'Definir',
                        'vlandestino': 'Definir',
                        'tipo': 'VPN B2B'
                    })

                    dto.append({
                        'vlanorigem': 'Definir',
                        'vlandestino': 'Definir',
                        'tipo': 'VPN B2B'
                    })

                elif len(olt_para['vlanb2bvpn']) == 2:

                    dto.append({
                        'vlanorigem': 'Definir',
                        'vlandestino': 'Definir',
                        'tipo': 'VPN B2B'
                    })

            else:

                dto.append({
                    'vlanorigem': 'Definir',
                    'vlandestino': 'Definir',
                    'tipo': 'VPN B2B'
                })

                dto.append({
                    'vlanorigem': 'Definir',
                    'vlandestino': 'Definir',
                    'tipo': 'VPN B2B'
                })

                dto.append({
                    'vlanorigem': 'Definir',
                    'vlandestino': 'Definir',
                    'tipo': 'VPN B2B'
                })

            # B2B INTERNET 
            if len(olt_para['vlanb2binternet']) > 0:

                for vlan_internet in olt_para['vlanb2binternet']:
                    dto.append({
                        'vlanorigem': vlan_internet,
                        'vlandestino': vlan_internet,
                        'tipo': 'INTERNET B2B'
                    })

                if len(olt_para['vlanb2binternet']) == 1:

                    dto.append({
                        'vlanorigem': 'Definir',
                        'vlandestino': 'Definir',
                        'tipo': 'INTERNET B2B'
                    })

                    dto.append({
                        'vlanorigem': 'Definir',
                        'vlandestino': 'Definir',
                        'tipo': 'INTERNET B2B'
                    })

                elif len(olt_para['vlanb2binternet']) == 2:

                    dto.append({
                        'vlanorigem': 'Definir',
                        'vlandestino': 'Definir',
                        'tipo': 'INTERNET B2B'
                    })

            else:

                dto.append({
                    'vlanorigem': "Definir",
                    'vlandestino': "Definir",
                    'tipo': 'INTERNET B2B'
                })

                dto.append({
                    'vlanorigem': "Definir",
                    'vlandestino': "Definir",
                    'tipo': 'INTERNET B2B'
                })

                dto.append({
                    'vlanorigem': "Definir",
                    'vlandestino': "Definir",
                    'tipo': 'INTERNET B2B'
                })
            
            # B2B SIP Trunking 
            if len(olt_para['vlanb2bsip']) > 0:

                for vlan_sip in olt_para['vlanb2bsip']:
                    dto.append({
                        'vlanorigem': vlan_sip,
                        'vlandestino': vlan_sip,
                        'tipo': 'SIP B2B'
                    })

                if len(olt_para['vlanb2bsip']) == 1:

                    dto.append({
                        'vlanorigem': 'Definir',
                        'vlandestino': 'Definir',
                        'tipo': 'SIP B2B'
                    })

                    dto.append({
                        'vlanorigem': 'Definir',
                        'vlandestino': 'Definir',
                        'tipo': 'SIP B2B'
                    })

                elif len(olt_para['vlanb2bsip']) == 2:

                    dto.append({
                        'vlanorigem': 'Definir',
                        'vlandestino': 'Definir',
                        'tipo': 'SIP B2B'
                    })
            else:
                dto.append({
                    'vlanorigem': "Definir",
                    'vlandestino': "Definir",
                    'tipo': 'SIP B2B'
                })

                dto.append({
                    'vlanorigem': "Definir",
                    'vlandestino': "Definir",
                    'tipo': 'SIP B2B'
                })

                dto.append({
                    'vlanorigem': "Definir",
                    'vlandestino': "Definir",
                    'tipo': 'SIP B2B'
                })

            # HSI/REDE
            if len(olt_para['vlanrede']) > 0:
                for vlan_rede in olt_para['vlanrede']:
                    dto.append({
                        'vlanorigem': vlan_rede,
                        'vlandestino': vlan_rede,
                        'tipo': 'REDE'
                    })
            else:
                dto.append({
                    'vlanorigem': "Definir",
                    'vlandestino': "Definir",
                    'tipo': 'REDE'
                })

                dto.append({
                    'vlanorigem': "Definir",
                    'vlandestino': "Definir",
                    'tipo': 'REDE'
                })

                dto.append({
                    'vlanorigem': "Definir",
                    'vlandestino': "Definir",
                    'tipo': 'REDE'
                })
                   

            # VOIP
            if olt_para['vlanvoip'] != "":
                dto.append({
                    'vlanorigem': olt_para['vlanvoip'],
                    'vlandestino': olt_para['vlanvoip'],
                    'tipo': 'VOIP'
                })
            else:
                dto.append({
                    'vlanorigem': "Definir",
                    'vlandestino': "Definir",
                    'tipo': 'VOIP'
                })

            # MULTICAST
            if olt_para['vlanmulticast'] != "":
                dto.append({
                    'vlanorigem': olt_para['vlanmulticast'],
                    'vlandestino': olt_para['vlanmulticast'],
                    'tipo': 'MULTICAST'
                })
            else:
                dto.append({
                    'vlanorigem': "Definir",
                    'vlandestino': "Definir",
                    'tipo': 'MULTICAST'
                })
            
            # UNICAST
            if olt_para['vlanunicast'] != "":
                dto.append({
                    'vlanorigem': olt_para['vlanunicast'],
                    'vlandestino': olt_para['vlanunicast'],
                    'tipo': 'UNICAST'
                })
            else:
                dto.append({
                    'vlanorigem': "Definir",
                    'vlandestino': "Definir",
                    'tipo': 'UNICAST'
                })

    return dto, 200

@huawei_bp.route('/gera/de/para/fisico/<string:hostname_olt>/destino/<string:hostname_olt_destino>',  methods=['GET'])
def gera_de_para_fisco(hostname_olt, hostname_olt_destino):
    try:
        depara = Controle.get_controle_de_para_by_hostname(hostname_olt_destino, hostname_olt)
        dto = []
        for porta in depara:
            dto.append({
                'origem': porta.split("_")[0],
                'destino': porta.split("_")[1]
            })
        return dto, 200
    except:
        return {}, 404

# rotas de validação
@huawei_bp.route('/valida/config/interface/falta/<string:hostname_olt>',  methods=['GET'])
def valida_config_interface(hostname_olt):
    clientes = Huawei.get_huawei_by_hostname(hostname_olt)
    
    problemas = relatorios_erros_encontrados(clientes)

    gera_relatorio_falta_config_clientes(hostname_olt, problemas)

    path = os.path.join(os.getcwd(), "anexos")

    excel_path = os.path.join(path, f"{hostname_olt}-falta-config.txt")

    return send_file(excel_path, as_attachment=True), 200

@huawei_bp.route('/total/onts/porta/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['GET'])
def valida_total_onts(hostname_origem, hostname_destino):

    try:

        deparas = Controle.get_controle_de_para_by_hostname(hostname_destino, hostname_origem)

        vlansb2bvpn = Controle.get_controle_by_hostname_vlan_b2b_vpn(hostname_destino, hostname_origem)

        vlansb2binternet = Controle.get_controle_by_hostname_vlan_b2b_internet(hostname_destino, hostname_origem)

        vlansb2bsip = Controle.get_controle_by_hostname_vlan_b2b_sip(hostname_destino, hostname_origem)

        data_destino = []

        for depara in deparas:

            total_clientes = Huawei.get_huawei_by_portade(hostname_origem, "0/(\s|)" + depara.split("_")[0] + "$")

            total_serviceport_de = Huawei.get_huawei_by_portade_serviceportde(hostname_origem, "0/(\s|)" + depara.split("_")[0] + "$")

            total_serviceport_para = Huawei.get_huawei_by_portade_serviceportpara(hostname_origem, "0/(\s|)" + depara.split("_")[0] + "$")

            total_btv = Huawei.get_huawei_by_portade_btv(hostname_origem, "0/(\s|)" + depara.split("_")[0] + "$")

            total_b2b_vpn = Huawei.get_huawei_by_portade_b2b_vpn(hostname_origem, "0/(\s|)" + depara.split("_")[0] + "$", vlansb2bvpn)

            total_b2b_internet = Huawei.get_huawei_by_portade_b2b_vpn(hostname_origem, "0/(\s|)" + depara.split("_")[0] + "$", vlansb2binternet)

            total_b2b_sip = Huawei.get_huawei_by_portade_b2b_vpn(hostname_origem, "0/(\s|)" + depara.split("_")[0] + "$", vlansb2bsip)
            
            data_destino.append({
                'total_clientes_onts': total_clientes,
                'porta_origem': "0/" + depara.split("_")[1],
                'total_serviceport_origem': total_serviceport_de,
                'total_serviceport_para': total_serviceport_para,
                'total_btv': total_btv,
                'total_b2b_vpn': total_b2b_vpn,
                'total_b2b_internet': total_b2b_internet,
                'total_b2b_sip': total_b2b_sip
            })
        
        return data_destino, 200
    
    except:
        
        return {}, 404

# testes nova versão proc
@huawei_bp.route('/gera/proc/services/nova/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['GET'])
def gera_proc_services_nova_huawei(hostname_origem, hostname_destino):
    try:
        vendor = Controle.get_controle_by_vendor_hostname_origem(hostname_origem, hostname_destino)

        depara = Controle.get_controle_de_para_by_hostname(hostname_destino, hostname_origem)

        if vendor == 'huawei':

            gera_proc_service_port_huawei_new(
                hostname_origem, hostname_destino, depara, 50000)

        path = os.path.join(os.getcwd(), "anexos")
        excel_path = os.path.join(path, f"{hostname_origem}-service-port.txt")

        return send_file(excel_path, as_attachment=True)
    except Exception as e:
        print(e)
        return {}, 404

# testes nova versão proc
@huawei_bp.route('/gera/proc/btv/nova/origem/<string:hostname_origem>/destino/<string:hostname_destino>',  methods=['GET'])
def gera_proc_btv_nova_huawei(hostname_origem, hostname_destino):
    try:
        vendor = Controle.get_controle_by_vendor_hostname_origem(hostname_origem, hostname_destino)

        depara = Controle.get_controle_de_para_by_hostname(hostname_destino, hostname_origem)

        vlanmulticast = Controle.get_controle_by_hostname_vlan_multicast(
            hostname_origem, hostname_destino)

        if vendor == 'huawei':

            gera_proc_btv_huawei_new(
                hostname_origem, hostname_destino, depara, vlanmulticast, 50000)

        path = os.path.join(os.getcwd(), "anexos")
        excel_path = os.path.join(path, f"{hostname_origem}-btv.txt")

        return send_file(excel_path, as_attachment=True)
    except Exception as e:
        print(e)
        return {}, 404