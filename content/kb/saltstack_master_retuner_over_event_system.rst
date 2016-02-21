基于Salt Event系统构建Master端returner
############################################

:date: 2014-04-18
:tags: SaltStack, 进阶
:slug: saltstack_master_retuner_over_event_system
:author: pengyao
:summary: SaltStack的returner是由minion端主动连接returner完成执行结果的存储, 在部分场景下并不能满足需求. 由于Salt底层已经构建了一套Event系统, 所有的操作均会产生event. 因此基于Salt Event System构建Master端returner成为一种可能.

* 原文出处: `http://pengyao.org/saltstack_master_retuner_over_event_system.html <http://pengyao.org/saltstack_master_retuner_over_event_system.html>`_
* 作者: `pengyao <http://pengyao.org/>`_

`SaltStack`_ 的 `returner`_ 是由minion端主动连接returner完成执行结果的存储, 在部分场景下并不能满足需求. 由于Salt底层已经构建了一套 `Event系统`_ , 所有的操作均会产生event. 因此基于Salt Event系统构建Master端returner成为一种可能.

之前已经完成了 `SaltStack Event系统监听events测试 <http://pengyao.org/saltstack_event_system_listen_events.html>`_, 本文将基于Salt Event系统构建Master端returner.

前置阅读
**************
* SaltStack Event系统: http://docs.saltstack.com/en/latest/topics/event/index.html
* SaltStack Event系统监听events测试: http://pengyao.org/saltstack_event_system_listen_events.html

环境说明
**************
* 测试结构: Master/Minions结构, 共一台minion, 对应id为: *salt-minion-01.example.com*
* Salt Version: *2014.1.1*
* 本次测试结果将存放在MySQL中, 为了方便测试, 已经在Master本地部署了MySQL Server

开工
**************
.. note::

    以下操作如非特别注明, 均在Master端进行

前置配置
==================

安装MySQLdb依赖

.. code-block:: bash

    yum -y install MySQL-python

配置本次测试需要使用的数据库及用户

.. code-block:: bash

    # 创建salt数据库
    mysql -e 'create database salt'
    # 创建用于连接salt数据库的用户
    mysql -e '"grant all on salt.* to salt@localhost identified by "salt_pass';
    # 将数据库配置添加至master配置文件中
    echo -e "\n\n# MySQL\nmysql.host: 'localhost'\nmysql.user: 'salt'\nmysql.pass: 'salt_pass'\nmysql.db: 'salt'\nmysql.port: 3306" >> /etc/salt/master

为了与salt自带的 `mysql returner`_ 兼容, 本次直接使用mysql retuner对应的数据库表结构::

    USE `salt`;

    --
    -- Table structure for table `jids`
    --

    DROP TABLE IF EXISTS `jids`;
    CREATE TABLE `jids` (
      `jid` varchar(255) NOT NULL,
      `load` mediumtext NOT NULL,
      UNIQUE KEY `jid` (`jid`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8;

    --
    -- Table structure for table `salt_returns`
    --

    DROP TABLE IF EXISTS `salt_returns`;
    CREATE TABLE `salt_returns` (
      `fun` varchar(50) NOT NULL,
      `jid` varchar(255) NOT NULL,
      `return` mediumtext NOT NULL,
      `id` varchar(255) NOT NULL,
      `success` varchar(10) NOT NULL,
      `full_ret` mediumtext NOT NULL,
      `alter_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      KEY `id` (`id`),
      KEY `jid` (`jid`),
      KEY `fun` (`fun`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8;

编写returner
=================

*salt_event_to_mysql.py*

.. code-block:: python

    #!/bin/env python
    #coding=utf8

    # Import python libs
    import json

    # Import salt modules
    import salt.config
    import salt.utils.event

    # Import third party libs
    import MySQLdb

    __opts__ = salt.config.client_config('/etc/salt/master')

    # Create MySQL connect
    conn = MySQLdb.connect(host=__opts__['mysql.host'], user=__opts__['mysql.user'], passwd=__opts__['mysql.pass'], db=__opts__['mysql.db'], port=__opts__['mysql.port'])
    cursor = conn.cursor()

    # Listen Salt Master Event System
    event = salt.utils.event.MasterEvent(__opts__['sock_dir'])
    for eachevent in event.iter_events(full=True):
        ret = eachevent['data']
        if "salt/job/" in eachevent['tag']:
            # Return Event
            if ret.has_key('id') and ret.has_key('return'):
                # Igonre saltutil.find_job event
                if ret['fun'] == "saltutil.find_job":
                    continue

                sql = '''INSERT INTO `salt_returns`
                    (`fun`, `jid`, `return`, `id`, `success`, `full_ret` )
                    VALUES (%s, %s, %s, %s, %s, %s)'''
                cursor.execute(sql, (ret['fun'], ret['jid'],
                                     json.dumps(ret['return']), ret['id'],
                                     ret['success'], json.dumps(ret)))
                cursor.execute("COMMIT")
        # Other Event
        else:
            pass

运行本returner:

.. code-block:: bash

    python salt_event_to_mysql.py

测试
============

新开启一个终端, 运行Salt指令:

.. code-block:: bash

    salt '*' test.ping

输出为:

.. code-block:: yaml

    salt-minion-01.example.com:
        True
 
检查mysql数据库, 查询salt_returns表数据:

.. code-block:: bash

    mysql salt -e "select * from salt_returns\G"

输出为::

    *************************** 1. row ***************************
        fun: test.ping
        jid: 20140417161103569310
        return: true
        id: salt-minion-01.example.com
        success: 1
        full_ret: {"fun_args": [], "jid": "20140417161103569310", "return": true, "retcode": 0, "success": true, "cmd": "_return", "_stamp": "2014-04-17T16:11:03.584859", "fun": "test.ping", "id": "salt-minion-01.example.com"}
        alter_time: 2014-04-17 16:11:03

入库成功


.. _SaltStack: http://saltstack.com/
.. _returner: http://docs.saltstack.com/en/latest/ref/returners/
.. _Event系统: http://docs.saltstack.com/en/latest/topics/event/index.html
.. _mysql returner: http://docs.saltstack.com/en/latest/ref/returners/all/salt.returners.mysql.html


