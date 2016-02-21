基于Salt管理iptables防火墙规则
########################################

:date: 2014-12-17
:tags: SaltStack, 进阶
:slug: managing-firewall-with-salt
:author: pengyao
:summary: Salt 2014.7支持pillar merge功能, 尝试基于此完成统一的iptables防火墙规则的管理

* 原文出处: `http://pengyao.org/managing-firewall-with-salt.html <http://pengyao.org/managing-firewall-with-salt.html>`_
* 作者: `pengyao <http://pengyao.org/>`_


Salt 2014.7支持pillar merge功能, 尝试基于该功能, 进行统一的iptables防火墙的管理. 本文采用在iptables INPUT链中增加防火墙规则
(各个服务对应自己的自定义链),同时如果规则中有allow, 则表示该防火墙规则为白名单机制(只允许allow对应的主机访问, 其余均拒绝),
如果没有allow, 则判断是否存在deny, 如果存在, 则执行黑名单机制(只拒绝deny对应的主机, 其余均允许)

环境说明
*****************

* OS: CentOS 6.5
* Salt架构: Master/Minions架构, 版本为2014.7.0

由于2014.7.0中iptables模块存在匹配Bug, 导致会不断进行重复配置, 当前develop分支已经修复这一问题(为修复这个问题的思路点赞), 需要进行对Minion进行如下操作:

.. code-block:: bash

    # 更新已修复匹配Bug的最新iptables模块
    curl -so /usr/lib/python2.6/site-packages/salt/modules/iptables.py \
    https://raw.githubusercontent.com/saltstack/salt/develop/salt/modules/iptables.py
    # 重启salt-minion
    service salt-minion restart

开工
********************

Pillar
================

/srv/pillar/sshd/init.sls:

.. code-block:: yaml

    firewall:
      sshd_firewall:
        port: 22
        deny:
          - 192.168.0.0/24
          - 8.8.8.8

/srv/pillar/httpd/init.sls:

.. code-block:: yaml

    firewall:
      httpd_firewall:
        port: 80
        allow:
          - 127.0.0.1
          - 192.168.0.0/24

/srv/pillar/top.sls

.. code-block:: yaml

    base:
      '*':
        - sshd
        - httpd

获取pillar信息:

.. code-block:: bash

    salt '*' pillar.item firewall --output=yaml

结果如下:

.. code-block:: yaml

    minion-01.example.com:
      firewall:
        httpd_firewall:
          allow:
            - 127.0.0.1
            - 192.168.0.0/24
          port: 80
        sshd_firewall:
          deny:
            - 192.168.0.0/24
            - 8.8.8.8
          port: 22

State
=============

/srv/salt/iptables/init.sls::

    {% for eachfw, fw_rule in pillar['firewall'].iteritems() %}
    # Add custom chain
    {{ eachfw }}-chain:
      iptables.chain_present:
        - save: True

    # Custom chain rules
    {% if 'allow' in fw_rule %}
    # White Lists
    {% for each_allow in fw_rule['allow'] %}
    {{ eachfw }}_allow_{{ each_allow }}:
      iptables.insert:
        - table: filter
        - chain: {{ eachfw }}-chain
        - position: 1
        - source: {{ each_allow }}
        - jump: ACCEPT
        - require:
          - iptables: {{ eachfw }}-chain
        - require_in:
          - iptables: {{ eachfw }}_deny
        - save: True
    {% endfor %}
    # Deny all
    {{ eachfw }}_deny:
      iptables.append:
        - table: filter
        - chain: {{ eachfw }}-chain
        - jump: DROP
        - save: True

    {% elif 'deny' in fw_rule %}
    # Black Lists
    {% for each_deny in fw_rule['deny'] %}
    {{ eachfw }}_deny_{{ each_deny }}:
      iptables.insert:
        - table: filter
        - chain: {{ eachfw }}-chain
        - position: 1
        - source: {{ each_deny }}
        - jump: DROP
        - require:
          - iptables: {{ eachfw }}-chain
        - require_in:
          - iptables: {{ eachfw }}_allow
        - save: True
    {% endfor %}
    # Accept all
    {{ eachfw }}_allow:
      iptables.append:
        - table: filter
        - chain: {{ eachfw }}-chain
        - jump: ACCEPT
        - save: True
    {% endif %}

    # Export traffic to custom chain
    {{ eachfw }}-main:
      iptables.insert:
        - table: filter
        - chain: INPUT
        - position: 1
        - proto: tcp
        - dport: {{ fw_rule['port'] }}
        - jump: {{ eachfw }}-chain
    {% endfor %}


应用iptables配置管理:

.. code-block:: bash

    salt '*' state.sls iptables

结果输出如下::

    minion-01.example.com:
    ----------
              ID: sshd_firewall-chain
        Function: iptables.chain_present
          Result: True
         Comment: iptables sshd_firewall-chain chain is already exist in filter table for ipv4
         Started: 07:58:23.325688
        Duration: 6.976 ms
         Changes:
    ----------
              ID: sshd_firewall_deny_192.168.0.0/24
        Function: iptables.insert
          Result: True
         Comment: iptables rule for sshd_firewall_deny_192.168.0.0/24 already set for ipv4 (--source 192.168.0.0/24 --jump DROP)
                  Saved iptables rule for sshd_firewall_deny_192.168.0.0/24 to: --source 192.168.0.0/24 --jump DROP for ipv4
         Started: 07:58:23.333635
        Duration: 46.198 ms
         Changes:
    ----------
              ID: sshd_firewall_deny_8.8.8.8
        Function: iptables.insert
          Result: True
         Comment: iptables rule for sshd_firewall_deny_8.8.8.8 already set for ipv4 (--source 8.8.8.8 --jump DROP)
                  Saved iptables rule for sshd_firewall_deny_8.8.8.8 to: --source 8.8.8.8 --jump DROP for ipv4
         Started: 07:58:23.380231
        Duration: 47.926 ms
         Changes:
    ----------
              ID: sshd_firewall_allow
        Function: iptables.append
          Result: True
         Comment: iptables rule for sshd_firewall_allow already set (/sbin/iptables -t filter -A sshd_firewall-chain  --jump ACCEPT) for ipv4
                  Saved iptables rule for sshd_firewall_allow to: /sbin/iptables -t filter -A sshd_firewall-chain  --jump ACCEPT for ipv4
         Started: 07:58:23.430386
        Duration: 50.731 ms
         Changes:
    ----------
              ID: sshd_firewall-main
        Function: iptables.insert
          Result: True
         Comment: iptables rule for sshd_firewall-main already set for ipv4 (-p tcp --dport 22 --jump sshd_firewall-chain)
         Started: 07:58:23.481324
        Duration: 38.941 ms
         Changes:
    ----------
              ID: httpd_firewall-chain
        Function: iptables.chain_present
          Result: True
         Comment: iptables httpd_firewall-chain chain is already exist in filter table for ipv4
         Started: 07:58:23.520640
        Duration: 9.483 ms
         Changes:
    ----------
              ID: httpd_firewall_allow_127.0.0.1
        Function: iptables.insert
          Result: True
         Comment: iptables rule for httpd_firewall_allow_127.0.0.1 already set for ipv4 (--source 127.0.0.1 --jump ACCEPT)
                  Saved iptables rule for httpd_firewall_allow_127.0.0.1 to: --source 127.0.0.1 --jump ACCEPT for ipv4
         Started: 07:58:23.530949
        Duration: 48.088 ms
         Changes:
    ----------
              ID: httpd_firewall_allow_192.168.0.0/24
        Function: iptables.insert
          Result: True
         Comment: iptables rule for httpd_firewall_allow_192.168.0.0/24 already set for ipv4 (--source 192.168.0.0/24 --jump ACCEPT)
                  Saved iptables rule for httpd_firewall_allow_192.168.0.0/24 to: --source 192.168.0.0/24 --jump ACCEPT for ipv4
         Started: 07:58:23.579515
        Duration: 50.945 ms
         Changes:
    ----------
              ID: httpd_firewall_deny
        Function: iptables.append
          Result: True
         Comment: iptables rule for httpd_firewall_deny already set (/sbin/iptables -t filter -A httpd_firewall-chain  --jump DROP) for ipv4
                  Saved iptables rule for httpd_firewall_deny to: /sbin/iptables -t filter -A httpd_firewall-chain  --jump DROP for ipv4
         Started: 07:58:23.631684
        Duration: 50.886 ms
         Changes:
    ----------
              ID: httpd_firewall-main
        Function: iptables.insert
          Result: True
         Comment: iptables rule for httpd_firewall-main already set for ipv4 (-p tcp --dport 80 --jump httpd_firewall-chain)
         Started: 07:58:23.682788
        Duration: 44.153 ms
         Changes:

    Summary
    -------------
    Succeeded: 10
    Failed:     0
    -------------
    Total states run:     10


检查minion端iptables规则

.. code-block:: bash

    salt '*' cmd.run 'iptables-save'

结果::

    minion-01.example.com:
        # Generated by iptables-save v1.4.7 on Wed Dec 17 08:01:51 2014
        *filter
        :INPUT ACCEPT [65:13902]
        :FORWARD ACCEPT [0:0]
        :OUTPUT ACCEPT [79:24034]
        :httpd_firewall-chain - [0:0]
        :sshd_firewall-chain - [0:0]
        -A INPUT -p tcp -m tcp --dport 80 -j httpd_firewall-chain
        -A INPUT -p tcp -m tcp --dport 22 -j sshd_firewall-chain
        -A httpd_firewall-chain -s 192.168.0.0/24 -j ACCEPT
        -A httpd_firewall-chain -s 127.0.0.1/32 -j ACCEPT
        -A httpd_firewall-chain -j DROP
        -A sshd_firewall-chain -s 8.8.8.8/32 -j DROP
        -A sshd_firewall-chain -s 192.168.0.0/24 -j DROP
        -A sshd_firewall-chain -j ACCEPT
        COMMIT
        # Completed on Wed Dec 17 08:01:51 2014

达到预期

