基于SaltStack完成LVS的配置管理
########################################

:date: 2013-11-24
:tags: SaltStack, 进阶
:slug: howto_configure_linux_virtual_server_using_saltstack
:author: pengyao
:summary: SaltStack最新代码中已经包含了对LVS(Linux Virutal Server)的支持, 本文将简要描述如何基于SaltStack完成LVS Loadblance(DR)及RealServer的配置管理

* 原文出处: `http://pengyao.org/howto_configure_linux_virtual_server_using_saltstack.html <http://pengyao.org/howto_configure_linux_virtual_server_using_saltstack.html>`_
* 作者: `pengyao <http://pengyao.org/>`_

之前由于工作需求，编写了SaltStack的 `LVS远程执行模块`_  , `LVS service状态管理模块`_ 及 `LVS server状态管理模块`_ ,并 `提交给了SaltStack官方 <https://github.com/saltstack/salt/pull/8741>`_,现已合并至官方代码中，本文将描述如何基于SaltStack完成LVS Loadblance(DR)及RealServer的配置管理.

前置阅读
****************
* `LVS-DR模式配置详解 <http://blog.csdn.net/justlinux2010/article/details/8539205>`_ ,需要注意的是，LVS-DR方式工作在数据链路层，文中描述需要开启ip_forward,其实没有必要, 详情见 `LVS DR模式原理剖析 <http://zh.linuxvirtualserver.org/node/2585>`_

环境说明
***************
* 三台服务器用于LVS集群，其中主机名为lvs的担当的角色为loadblance，对应的IP地址为192.168.36.10；主机名为web-01和web-02的主机担当的角色为RealServer, 对应的IP地址分别为192.168.36.11及192.168.36.12
* LVS VIP: 192.168.36.33, Port: 80, VIP绑定在lvs的eth1口
* 最最重要的是loadblance主机为Linux，并已安装ipvsadm, Windows/Unix等主机的同学请绕过吧，这不是我的错......

开工
************

.. note::

   以下所有操作均在Master上进行

配置SaltStack LVS模块
===========================
* 如果使用的Salt版本已经包含了lvs模块，请忽略本节内容，测试方法:

.. code-block:: bash

    salt 'lvs' cmd.run "python -c 'import salt.modules.lvs'"

如果输出有 *ImportError* 字样，则表示模块没有安装，需要进行如下操作:

.. code-block:: bash

    test -d /srv/salt/_modules || mkdir /srv/salt/_modules
    test -d /srv/salt/_states || mkdir /srv/salt/_states
    wget https://raw.github.com/saltstack/salt/develop/salt/modules/lvs.py -O /srv/salt/_modules/lvs.py
    wget https://raw.github.com/saltstack/salt/develop/salt/states/lvs_service.py -O /srv/salt/_states/lvs_service.py
    wget https://raw.github.com/saltstack/salt/develop/salt/states/lvs_server.py -O /srv/salt/_states/lvs_server.py


配置pillar
==============
*/srv/pillar/lvs/loadblance.sls*

.. code-block:: yaml

    lvs-loadblance:
      - name: lvstest
        vip: 192.168.36.33
        vip-nic: eth1
        port: 80
        protocol: tcp
        scheduler: wlc
        realservers:
          - name: web-01
            ip: 192.168.36.11
            port: 80
            packet_forward_method: dr
            weight: 10 
          - name: web-02
            ip: 192.168.36.12
            port: 80
            packet_forward_method: dr
            weight: 30 

*/srv/pillar/lvs/realserver.sls*

.. code-block:: yaml

    lvs-realserver:
      - name: lvstest
        vip: 192.168.36.33

*/srv/pillar/top.sls*

.. code-block:: yaml

    base:
      'lvs':
        - lvs.loadblance
      'web-0*':
        - lvs.realserver

编写States
===================
*/srv/salt/lvs/loadblance.sls*

.. code-block:: jinja

    # config lvs
    {% if 'lvs-loadblance' in pillar %}
    {% for each_lvs in pillar['lvs-loadblance'] %}
    # config lvs vip
    {{each_lvs['name']}}-vip:
      network.managed:
        - name: {{each_lvs['vip-nic'] + ":" + each_lvs['name']}}
        - enable: True
        - type: eth
        - proto: none
        - ipaddr: {{each_lvs['vip']}}
        - netmask: 255.255.255.255

    {% set service_address = each_lvs['vip'] + ":" + each_lvs['port']|string() %}
    {{each_lvs['name']}}-service:
      lvs_service.present:
        - protocol: {{each_lvs['protocol']}}
        - service_address: {{service_address}}
        - scheduler: {{each_lvs['scheduler']}}

    {% for each_rs in each_lvs['realservers'] %}
    {% set server_address = each_rs['ip'] + ":" + each_rs['port']|string() %}
    {{each_rs['name']}}-server:
      lvs_server.present:
        - protocol: {{each_lvs['protocol']}}
        - service_address: {{service_address}}
        - server_address: {{server_address}}
        - packet_forward_method: {{each_rs['packet_forward_method']}}
        - weight: {{each_rs['weight']}}
    {% endfor %}
    {% endfor %}
    {% endif %}

*/srv/salt/lvs/realserver.sls*

.. code-block:: jinja

    # ignore arp
    net.ipv4.conf.all.arp_ignore:
      sysctl.present:
        - value: 1

    net.ipv4.conf.lo.arp_ignore:
      sysctl.present:
        - value: 1

    net.ipv4.conf.all.arp_announce:
      sysctl.present:
        - value: 2

    net.ipv4.conf.lo.arp_announce:
      sysctl.present:
        - value: 2


    # config lvs vip
    {% if 'lvs-realserver' in pillar %}
    {% for each_lvs in pillar['lvs-realserver'] %}
    lvs-vip:
      network.managed:
        - name: {{"lo" + ":" + each_lvs['name']}}
        - enable: True
        - type: eth
        - proto: none
        - ipaddr: {{each_lvs['vip']}}
        - netmask: 255.255.255.255
    {% endfor %}
    {% endif %}

* /srv/salt/top.sls*

.. code-block:: yaml

    base:
      'lvs':
        - lvs.loadblance
      'web-0*':
        - lvs.realserver

应用配置
==============
如果之前进行 *配置LVS模块* 的操作，需要进行同步模块的操作:

.. code-block:: bash

    salt 'lvs*' saltutil.sync_all

应用LVS配置:

.. code-block:: bash

    salt '*' state.highstate

查看LVS当前状态:

.. code-block:: bash

    salt 'lvs' lvs.list

    
总结
============
通过SaltStack LVS模块，可以快速的查询LVS状态，执行LVS常用指令及完成LVS的配置管理。如有需要调整RealServer规则或添加新的RealServer, 只需要修改 */srv/pillar/lvs/loadblance.sls* ，然后应用配置即可.

本文中所用到的代码已经上传至github，传送门: https://github.com/pengyao/salt-lvs

.. _LVS远程执行模块: https://github.com/pengyao/salt/blob/develop/salt/modules/lvs.py
.. _LVS service状态管理模块: https://github.com/pengyao/salt/blob/develop/salt/states/lvs_service.py
.. _LVS server状态管理模块: https://github.com/pengyao/salt/blob/develop/salt/states/lvs_server.py

