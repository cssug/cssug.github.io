基于Salt Master/Minions快速构建Salt SSH环境
###########################################################

:date: 2013-11-08
:tags: SaltStack, 进阶
:slug: howto_setup_salt_ssh_from_minion
:author: pengyao
:summary: Salt 0.17版本重要的特性是引入了Salt SSH系统，本文基于已有的SaltStack Master/Minions环境,快速构建Salt SSH维护环境, 提供Salt多重维护方式.

* 原文出处: `http://pengyao.org/howto_setup_salt_ssh_from_minion.html <http://pengyao.org/howto_setup_salt_ssh_from_minion.html>`_
* 作者: `pengyao <http://pengyao.org/>`_

Salt 0.17版本已发布，该版本中重要的特性是引入了Salt SSH系统，提供了无需Minion、基于SSH的维护方式。原有的Salt维护环境已经初具规模，再手动重新构建Salt SSH环境成本较高。偷懒是人的天性，利用原有SaltStack Master/Minions环境，如何快速构建新的Salt SSH维护环境将是本文的主题.

前置阅读
***********************

预则立，不预则废。阅读本文前先阅读如下文章:

* Salt 0.17 Release Note: http://docs.saltstack.com/topics/releases/0.17.0.html
* Salt SSH: http://docs.saltstack.com/topics/ssh/
* Salt Rosters: http://docs.saltstack.com/topics/ssh/roster.html

环境说明
***********************
* Minion版本: 本文会采用 `Salt Mine <http://docs.saltstack.com/topics/mine/>`_ 获取已有的Minion ID及IP地址，由于Salt Mine为0.15.0引入的新功能，所以需要保证Minion的版本等于或高于0.15.0

* Master的安装采用EPEL仓库yum方式

* 所有minion端sshd服务已启动，并允许Master访问

* Master所在服务器上同时安装有Minion并运行Master进行管理, 对应的Minion ID为 *salt*

* Salt file_roots目录为 */srv/salt/* , pillar_roots目录为 */srv/pillar/* 

开工
***********************

.. note::

  以下所有操作在Master端进行

创建用于Salt SSH环境的用户及key认证管理环境
============================================

生成Master SSH key

.. code-block:: bash

  ## 创建master ssh key目录
  mkdir /etc/salt/pki/master/ssh/
  ## 生成Master SSH key
  cd /etc/salt/pki/master/ssh/
  ssh-keygen -t rsa -P "" -f salt-ssh.rsa
  ## 复制master public key至 salt fileserver 
  cp /etc/salt/pki/master/ssh/salt-ssh.rsa.pub /srv/salt/salt/files/salt-ssh.rsa.pub

编写用于Salt SSH管理的用户及key认证状态管理文件, */srv/salt/salt/ssh/init.sls*  

.. code-block:: yaml

  salt-user:
    {# salt user #}
    user.present:
      - name: salt
    {# salt user sudoer #}
    file.managed:
      - name: /etc/sudoers.d/salt
      - source: salt://salt/files/etc/sudoers.d/salt
      - require:
        - user: salt-user
          
  salt-master-key:
    ssh_auth.present:
      - user: salt
      - source: salt://salt/files/salt-ssh.rsa.pub
      - require:
        - user: salt-user        


*salt* 用户对应的sudoer文件 */srv/salt/salt/files/etc/sudoers.d/salt*::

  Defaults:salt !requiretty
  salt ALL=(ALL) NOPASSWD: ALL 

应用状态

.. code-block:: bash

  salt '*' state.sls salt.ssh

配置Mine,以获取Minion id及IP地址
==================================

配置Salt Mine, */srv/pillar/salt/mine.sls*

.. code-block:: yaml

  mine_functions:
    network.ip_addrs:
      - eth0    

配置pillar top.sls, */srv/pillar/top.sls*      

.. code-block:: yaml

  base:
    '*':
      - salt.mine

刷新Pillar，并验证Salt Mine配置

.. code-block:: bash

  salt '*' saltutil.refresh_pillar
  salt '*' pillar.get mine_functions

更新Salt Mine，并测试获取所有Minions的ID及IP

.. code-block:: bash

  salt '*' mine.update
  salt 'salt' mine.get '*' network.ip_addrs 


生成Salt Rosters
==============================

配置Salt Rosters state

*/srv/salt/salt/ssh/roster.sls*

.. code-block:: yaml

  salt-rosters:
    {# salt rosters file for salt-ssh #}
    file.managed:
      - name: /etc/salt/roster
      - source: salt://salt/files/etc/salt/roster
      - template: jinja

*/srv/salt/salt/files/etc/salt/roster*::

  {% for eachminion, each_mine in salt['mine.get']('*', 'network.ip_addrs').iteritems() -%}
  {{eachminion}}:
    host: {{each_mine[0]}}
    user: salt 
    sudo: True
  {% endfor -%}  

生成Salt Rosters

.. code-block:: bash

  salt 'salt' state.sls salt.ssh.roster


应用Salt SSH
==================

将Master升级至0.17及以上版本(EPEL Stable当前版本为已经为0.17.1-1), 至此, Salt SSH环境已经构建完毕

.. code-block:: bash

  yum update salt-master
  service salt-master restart

测试Salt SSH

.. code-block:: bash
   
  ## 运行Salt Module
  salt-ssh '*' test.ping
  ## 运行原始SHELL命令
  salt-ssh '*' -r 'uptime'


后话
*****************

Salt这是要抢 `Fabric <https://github.com/fabric/fabric>`_ 饭碗的节奏啊，个人更喜欢Salt Master/Minions这样的管理方式，Salt SSH作为补充，用于升级Minion、重启Minion等等自维护工作还是很靠谱的。有了Salt SSH，再也不用担心是先有鸡还是先有蛋的问题了.

