Salt配置复杂nodegroup
#####################

:date: 2014-01-16
:tags: SaltStack, 进阶
:slug: salt-nodegroup-complex
:author: pengyao
:summary: `SaltStack`_ 支持Nodegroup嵌套Nodegroup, 进而实现复杂Nodegroup

* 原文出处: `http://pengyao.org/salt-nodegroup-complex.html <http://pengyao.org/salt-nodegroup-complex.html>`_
* 作者: `pengyao <http://pengyao.org/>`_

昨天拉风在群里问, 定义了A, B两个nodegroup,  是否可以定义一个nodegroup C, 包含A, B两个group, 实现nodegroup嵌套nodegroup进而实现复杂nodegroup(哈哈,各种绕口)

由于手册中并没有相关介绍, 就查询了下官方的issue, 找到了之前有人反馈过的 `issue #2020 <https://github.com/saltstack/salt/issues/2020>`_ , tom说0.10.4已经实现了这个功能, 就在测试环境进行了测试:

*/etc/salt/master.d/nodegroups.conf*

.. code-block:: yaml

  nodegroups:
    test1: 'L@salt-minion-01'
    test2: 'L@salt-minion-02'
    test: 'N@test1 or N@test2’

测试:

.. code-block:: bash

  salt -N test test.ping

输出结果:

.. code-block:: yaml

  salt-minion-01:
      True
  salt-minion-02:
      True


从输出来看, nodegroup嵌套是支持的


.. _SaltStack: http://saltstack.com/
