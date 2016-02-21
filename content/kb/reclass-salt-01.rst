Salt整合reclass测试
#############################

:date: 2014-02-17
:tags: SaltStack, 进阶
:slug: reclass-salt-01
:author: pengyao
:summary: reclass是一个外部节点分类器(External Node Classifier, ENC), 可以与自动化管理工具如PUPPET, Salt及Ansible进行整合. 就对reclass进行下学习, 看能为Salt带来什么.

* 原文出处: `http://pengyao.org/reclass-salt-01.html <http://pengyao.org/reclass-salt-01.html>`_
* 作者: `pengyao <http://pengyao.org/>`_


reclass基本介绍
***********************

* 项目地址: https://github.com/madduck/reclass/tree
* 手册地址: http://reclass.pantsfullofunix.net/index.html

reclass, 全称Recursive External Node Classification, 可以与自动化管理工具结合, 为其提供ENC服务. reclass作者认为, ENC软件应该提供如下两个功能:

* 提供组(group)中节点(node)及组关系(group memberships)的信息
* 提供节点指定的信息, 如变量

对此, reclass定义了如下四种元素:

=============   ==================================================================
元素            描述
-------------   ------------------------------------------------------------------
node            一个节点, 通常是一个计算机
class           一个分类(categroy),tag,特性(feature)或角色(role), 支持嵌套和继承
application     一组行为(behaviour)
parameter       节点指定的变量,可以通过class进行继承
=============   ==================================================================

reclass在继承中, 如果parent中变量不存在, 则新增,如果存在同一变量, 类型为字符串, 则会进行覆盖. 如果变量为list类型, 则进行追加

reclass安装
**************************

.. code-block:: bash

  git clone https://github.com/madduck/reclass.git
  cd reclass
  python setup.py install

reclass配置及测试
**************************
测试目标: 通过reclass实现ntp变量的灵活扩展

通用信息, */srv/reclass/classes/ntp-common.yml*

.. code-block:: yaml

  parameters:
    ntp:
      ntpserver:
        - 0.asia.pool.ntp.org
        - 1.asia.pool.ntp.org

redhat系统继承ntp-common并进行一些特殊定制, */srv/reclass/classes/ntp-redhat.yml*

.. code-block:: yaml

  classes:
    - ntp-common

  parameters:
    ntp:
      pkg: ntp
      service: ntpd
      ntpserver:
        - 2.asia.pool.ntp.org
        - 3.asia.pool.ntp.org

配置node, */srv/reclass/nodes/salt-minion-01.yml*

.. code-block:: yaml

  classes:
    - ntp-redhat

测试节点分类信息

.. code-block:: bash

  reclass -b /srv/reclass --nodeinfo salt-minion-01

输出结果

.. code-block:: yaml

  __reclass__:
    environment: base
    name: salt-minion-01
    node: salt-minion-01
    timestamp: Mon Feb 17 09:29:53 2014
    uri: yaml_fs:///srv/reclass/nodes/salt-minion-01.yml
  applications: []
  classes:
  - ntp-common
  - ntp-redhat
  environment: base
  parameters:
    ntp:
      ntpserver:
      - 0.asia.pool.ntp.org
      - 1.asia.pool.ntp.org
      - 2.asia.pool.ntp.org
      - 3.asia.pool.ntp.org
      pkg: ntp
      service: ntpd


从输出结果看, 与reclass手册描述一致


reclass与salt整合测试
*****************************

Salt在0.17版本中,增加了 `reclass的支持 <http://docs.saltstack.com/ref/tops/all/salt.tops.reclass_adapter.html>`_ .

Salt与reclass元素对应关系

===============  ====================
reclass元素      Salt术语
---------------  --------------------
nodes            hosts
classes          (none)
applications     states
parameters       pillar
===============  ====================

测试目标: 通过reclass为salt minion提供对应的ntp pillar信息 

测试环境: Salt Master/Minion结构, 版本0.17.5

配置salt master, */etc/salt/master*

.. code-block:: yaml

  ...
  reclass: &reclass
  storage_type: yaml_fs
  inventory_base_uri: /srv/reclass

  master_tops:
    reclass: *reclass

  ext_pillar:
    - reclass: *reclass


重启salt master

.. code-block:: bash

  service salt-master restart

测试salt-minion-01对应的ntp pillar

.. code-block:: bash

  salt 'salt-minion-01' pillar.item ntp

输出结果

.. code-block:: yaml

  salt-minion-01:
      ----------
      ntp:
          ----------
          ntpserver:
              - 0.asia.pool.ntp.org
              - 1.asia.pool.ntp.org
              - 2.asia.pool.ntp.org
              - 3.asia.pool.ntp.org
          pkg:
              ntp
          service:
              ntpd

达成测试目标


总结
********************
salt pillar当前较弱, 只支持include, 并不支持extend等更高级的功能. 通过与reclass的整合, 借助reclass灵活的继承功能(支持多级继承), 为Salt提供专业的ENC服务, 弥补了pillar的不足. 

当前reclass的功能相对较弱, 不过可以看到的是如Class subdirectories这类实用的功能已经在to-do list中, 期待reclass功能更为强大.
   
