#!/usr/bin/env python

# Використання:
# git clone (посилання на репозиторії з бекапом)
# або
# git pull (в папці з вже завантаженим репозиторієм)
#
# ./olt_config.py /шлях_до_файлу/ім`я_файлу_резервної_копії

from collections import defaultdict
import sys, os, re

port_vlan = defaultdict(dict)
port_mac = defaultdict(dict)
port_desc = defaultdict(dict)
port_vlan[0]=port_mac[0]=port_desc[0]={}


# ================================ читаєм файл =================================

data=os.popen('git --no-pager --git-dir {folder}.git log -p -- {file}'.format(file=re.sub(r'.*/', '', sys.argv[1]),folder=re.sub(r'[^/]*$', '', sys.argv[1]))).read()


# ================= робимо асоціацію PON->LLID=VLAN|MAC|DESCRIPTION ============

for row in data.split('\n'):
    if row.find('interface EPON') != -1:
        if row.find(':') != -1:
            epon=int(row.split('/')[1].split(':')[0])
            llid=int(row.split(':')[1])
        else:
            epon=int(row.split('/')[1])
    if row.find('!') != -1:
        epon=llid=0
    splited = re.sub(r'^\+|^\-', '', row).split()
    if row.find('vlan mode tag') != -1:
        if splited[0] == 'epon':
            port_vlan[epon][llid] = splited[8]
    if row.find('description') != -1:
        if splited[0] == 'description':
            port_desc[epon][llid] = splited[1]
    if row.find('bind-onu') != -1:
        port_mac[epon][splited[4]] = splited[3]


# ====================== видаляємо неправильні асоціації =======================

del port_vlan[0], port_mac[0], port_desc[0]


# ===================== генеруємо кофігурацію привязки ONU =====================

for key, val in sorted(port_mac.items()):
    print('interface EPON0/{pon}'.format(pon=key))
    for i in range(65):
        if val.get(str(i), None):
            print('  epon bind-onu mac {mac} {llid}'.format(llid=i,mac=val[str(i)]))
    print('!')


# ========================== генеруємо налаштування на ONU =====================

for key, val in sorted(port_vlan.items()):
    for i in range(65):
        if val.get(i, None):
            print('interface EPON0/{pon}:{llid}\n  description {desc}\n  epon onu port 1 ctc vlan mode tag {vlan} priority 0'.format(llid=i,pon=key,vlan=val[i],desc=port_desc[key].get(i, None)))
            print('!')
