Salt中ZeroMQ那点事
#####################

:date: 2014-09-06
:tags: SaltStack, 进阶
:category: SaltStack
:slug: salt-zeromq-01
:author: pengyao
:summary: `Salt`_ 底层网络架构采用 `ZeroMQ`_ 进行实现(2014.1及之前版本, 从2014.7起, Salt新增 `RAET`_ ), 那么Salt都使用了ZeroMQ哪些模式? 各个组件间又是如何协作的?

* 原文出处: `http://pengyao.org/salt-zeromq-01.html <http://pengyao.org/salt-zeromq-01.html>`_
* 作者: `pengyao <http://pengyao.org/>`_

基本简介
****************
`Salt`_ 底层网络架构采用 `ZeroMQ`_ 进行实现(2014.1及之前版本, 从2014.7起, Salt新增 `RAET`_ ), `官方手册 <http://docs.saltstack.com/en/latest/topics/index.html#building-on-proven-technology>`_ 有简短描述. 那么今天就一窥在Salt内部使用了哪些 `ZeroMQ`_ pattern? 各个组件间又是如何协作的哪?

前置阅读
****************
* `0MQ - The Guide: Sockets and Patterns  <http://zguide.zeromq.org/page:all#Chapter-Sockets-and-Patterns>`_

环境说明
****************
* CentOS6.4
* Salt `2014.1.10 <https://github.com/saltstack/salt/tree/v2014.1.10/salt>`_ ,默认配置

Salt中的ZeroMQ patterns
***************************

Salt Master
==================

Salt Master为Salt中心管控节点. 为Salt环境提供命令下发, 文件, 结果收集等服务.

在Master启动时, 首先启动名为 `ReqServer <https://github.com/saltstack/salt/blob/v2014.1.10/salt/master.py#L452>`_ , `ReqServer在初始化 <https://github.com/saltstack/salt/blob/v2014.1.10/salt/master.py#L584>`_ 时, 立即创建如下ZeroMQ patterns:

 * *clients*:
 
   * ZeroMQ pattern: zmq.ROUTER
   * listen地址: tcp://0.0.0.0:4506
   * listen方式: bind
   * 作用: Salt Master Ret接口, 支持认证(auth), 文件服务, 结果收集等功能
 
 * *workers*:

   * ZeroMQ pattern: zmq.DEALER
   * listen地址: ipc:///var/run/salt/master/workers.ipc
   * listen方式: bind
   * 作用: Salt Master任务处理进程接口

同时clients与workers, 建立了一个 `zeromq.device <https://github.com/saltstack/salt/blob/v2014.1.10/salt/master.py#L635>`_ :

.. code-block:: python

     zmq.device(zmq.QUEUE, self.clients, self.workers)
    
通过zmq.device, 实现了clients接收到请求后, 转发到workers进程接口上进行处理

接下来, Master会启动 `Publisher <https://github.com/saltstack/salt/blob/v2014.1.10/salt/master.py#L635>`_ , 立即创建了如下ZeroMQ patterns:

 * *pub*:
 
   * ZeroMQ pattern: zmq.PUB
   * listen地址: tcp://0.0.0.0:4505
   * listen方式: bind
   * 作用: Salt Master pub接口, 提供远程执行命令发送功能
 
 * *pull*:
 
   * ZeroMQ pattern: zmq.PULL
   * listen地址: ipc:///var/run/salt/master/publish_pull.ipc
   * listen方式: bind
   * 作用: Salt Master远程执行命令pull接口

pull接口在接收到数据后, 会将数据从pub接口上进行发送:

.. code-block:: python

     package = pull_sock.recv()
     pub_sock.send(package)


接下来, Master启动 `EventPublisher <https://github.com/saltstack/salt/blob/v2014.1.10/salt/utils/event.py#L430>`_, 以实现Event BUS, 创建了如下ZeroMQ patterns:

 * *epub*:
 
   * ZeroMQ pattern: zmq.PUB
   * listen地址: ipc:///var/run/salt/master/master_event_pub.ipc
   * listen方式: bind
   * 作用: Salt Master event pub接口, 以方便其他或第三方应用订阅event bus上的event
   
 * *epull*:
   
   * ZeroMQ pattern: zmq.PULL
   * listen地址: ipc:///var/run/salt/master/master_event_pull.ipc
   * listen方式: bind
   * 作用: Salt Master event pull接口
 
同时epull接口在收到包时, 会将数据在pub接口上进行发送:

.. code-block:: python

    package = self.epull_sock.recv()
    self.epub_sock.send(package)

在启动EventPublisher之后, Salt Master会继续启动Halite, Reactor系统, 该部分暂不描述. 随后, Salt会启动多个Work进程(默认是5, 在规模较大的环境中, 建议增加配置文件中的 *worker_threads* 数目来增加该类进程)来进行任务处理, 每个Worker进程会创建如下ZeroMQ patterns:

 * *socket*

   * ZeroMQ pattern: zmq.REP
   * listen地址: ipc:///var/run/salt/master/workers.ipc
   * listen方式: connect
   * 作用: Salt Master任务处理进程, 处理验证Minion, 获取Master配置, Mine, pillar, fileserver文件获取, minion event fire到master的event接口, 收集minions的返回结果等任务


Salt Minion
================

Salt Minion为Salt环境操作节点, 远程命令从Master发送过来后, 会在该主机上进行执行并将结果返回给Master.

Salt `Minion <https://github.com/saltstack/salt/blob/v2014.1.10/salt/minion.py#L524>`_ 在启动时从配置文件中获取Master的地址, 如果为域名, 则进行解析. 解析完毕后, 会连接Master的Ret接口进行key认证. 认证通过, 会获取到master的 *publish_port* , 这就是为什么在Minion的配置文件中只需要指定Minion的 *ret_port* (对应minion配置文件中的master_port) 即可.

在获取到master的publish_port(默认为4505)之后, 会建立minion本地的Event接口:

 * *epub*:
 
   * ZeroMQ pattern: zmq.PUB
   * listen地址: ipc:///var/run/salt/minion/minion_event_{id_hash}_pub.ipc
   * listen方式: bind
   * 作用: Salt Minion event pub接口, 以便其他或第三方应用通过该event bus获取event信息

 * *epull*:
 
   * ZeroMQ pattern: zmq.PULL
   * listen地址: ipc:///var/run/salt/minion/minion_event_{id_hash}_pull.ipc
   * listen方式: bind
   * 作用: Salt Minion event pull接口

epull接口在接收到数据后, 会检查是否需要处理, 如果需要处理, 则进行执行. 随后将该数据包传送到epub接口:

.. code-block:: python

    # Check the event system
    if socks.get(self.epull_sock) == zmq.POLLIN:
        package = self.epull_sock.recv(zmq.NOBLOCK)
        log.debug("Handling event %r", package)
        try:
            if package.startswith('module_refresh'):
                self.module_refresh()
            elif package.startswith('pillar_refresh'):
                self.pillar_refresh()
            elif package.startswith('grains_refresh'):
                if self.grains_cache != self.opts['grains']:
                    self.pillar_refresh()
                    self.grains_cache = self.opts['grains']
                 elif package.startswith('fire_master'):
                     tag, data = salt.utils.event.MinionEvent.unpack(package)
                     log.debug("Forwarding master event tag={tag}".format(tag=data['tag']))
                     self._fire_master(data['data'], data['tag'], data['events'], data['pretag'])

            self.epub_sock.send(package)
        except Exception:
            log.debug("Exception while handling events", exc_info=True)

在event接口建立完毕后, 会建立如下ZeroMQ pattern:

 * *socket*:
 
   * ZeroMQ pattern: zmq.SUB
   * listen地址: tcp://{master_ip}:4505
   * listen方式: connect
   * 作用: 订阅来自Master pub接口的任务

由于远程执行命令的发送, 是通过ZeroMQ PUB/SUB pattern进行建立的, 即当master下发操作指令时, 所有的minion均可以接收到, 然后minion会检查本机是否target match, 如果match, 则进行执行.执行完毕后, 会通过 `SREQ <https://github.com/saltstack/salt/blob/v2014.1.10/salt/payload.py#L159>`_ 发送到Master的Ret接口, 期间会创建如下ZeroMQ pattern:

 * *socket*:
 
   * ZeroMQ pattern: zmq.REQ
   * listen地址: tcp://{master_ip}:4506
   * listen方式: connect
   * 作用: 将执行结果发送给Master

更多关于Minion如何来执行任务, 请访问: http://devopstarter.info/yuan-ma-jie-du-saltstackyun-xing-ji-zhi-zhi-job-runtime/

Salt
=============

Salt Master与Salt Minion建立了对应的ZeroMQ pattern, 那么当一个远程执行指令下发下去, 其数据流向是怎么个流程哪? 以执行test.ping为例:

1. 在master端bash下, 执行:

.. code-block:: bash

    salt '*' test.ping

其对应的 `python执行 <https://github.com/saltstack/salt/blob/v2014.1.10/salt/scripts.py#L126>`_ 是:

.. code-block:: python

    client = salt.cli.SaltCMD()
    client.run()

在内部, 又是调用:

.. code-block:: python

    local = salt.client.LocalClient()
    cmd_fun = local.cmd_cli()
    for full_ret in cmd_func(kwargs):
        ret, out = self._format_ret(full_ret)
        self._output_ret(ret, out)

2. 在 `LocalClient <https://github.com/saltstack/salt/blob/v2014.1.10/salt/client/__init__.py#L77>`_ 对象初始化时, 会创建用于对发送的数据进行序列化的 `Serial <https://github.com/saltstack/salt/blob/v2014.1.10/salt/client/__init__.py#L77>`_ 对象, 及 `MasterEvent <https://github.com/saltstack/salt/blob/v2014.1.10/salt/utils/event.py#L406>`_ 对象. MasterEvent对象会创建如下ZeroMQ pattern:

 * *sub*:
 
   * ZeroMQ pattern: zmq.SUB
   * listen地址: ipc:///var/run/salt/master/master_event_pub.ipc
   * listen方式: connect
   * 作用: 用于订阅来自于Master event pub接口的数据

3. `cmd_cli <https://github.com/saltstack/salt/blob/v2014.1.10/salt/client/__init__.py#L524>`_ 在执行时, 会首先通过 `run_job <https://github.com/saltstack/salt/blob/v2014.1.10/salt/client/__init__.py#L234>`_ 将操作指令封装成如下内容:

    {'tgt_type': 'glob', 'jid': '', 'key': 'LCkViTMgqKBqb5ooG8kznznztLYPsWR1xdTYnAz9udkU9/Lla32yDvUmVKLPaUNSMtbWdBoQPIs=', 'tgt': '*', 'arg': [], 'fun': 'test.ping', 'kwargs': {'show_timeout': False}, 'cmd': 'publish', 'ret': '', 'user': 'root'}

将发送到本地master的Ret接口, 期间会创建如下ZeroMQ pattern:

 * *socket*:
 
   * ZeroMQ pattern: zmq.REQ
   * listen地址: tcp://127.0.0.1:4506
   * listen方式: connect
   * 作用: 将封装后的指令发送到Master Ret接口

4. Master Ret接口接收到3中发送的数据后, 会通过chminions.check_minions获取本次需要哪些minions执行, 并产生jid, 然后在master event接口上进行fire_event操作, 之后对数据使用master私钥(master.pem)进行签名, 然后创建如下ZeroMQ pattern:

 * *pub_socket*:
 
   * ZeroMQ pattern: zmq.PUSH
   * listen地址: ipc:///var/run/salt/master/publish_pull.ipc
   * listen方式: connect
   * 作用: 将指令传送到Master Pull接口

Master Pull接口接收到数据后, 会迅速的在Master Pub接口上发送将之前收到的数据

同时将jid及minions封装后的结果返回给3, 3中cmd_cli获取到数据后, 调用 `get_cli_event_returns <https://github.com/saltstack/salt/blob/v2014.1.10/salt/client/__init__.py#L1142>`_ ,监听Master端的Event bus, 过滤出本次任务jid所对应的event, 用来获取执行结果

5. 此时Minion通过PUB/SUB, 即可收到来自于Master Pub接口的消息. Minion接收到消息后, 会首先通过本地的master pub_key(minion_master.pub)进行解密, 已确保消息来自于Master. 解密完成后, 本地进行target匹配, 如果匹配上, 表示需要执行, 派生出一个新的进程进行执行. 反之则直接忽略.

6. Minion执行完毕后, 会通过 `_return_pub <https://github.com/saltstack/salt/blob/v2014.1.10/salt/minion.py#L938>`_ 将封装后的结果通过AES加密发送到Master的Ret接口

7. Master Ret接收到6中发送的数据后, 会进行AES解密, 然后通过 `_return <https://github.com/saltstack/salt/blob/v2014.1.10/salt/master.py#L1354>`_, 首先将解密后的数据在本地event接口上进行fire_event, 并将结果存储在master本地.

8. 由于7中进行fire_event, 此时4中的get_cli_event_returns即可捕捉到, 由于采用迭代器, 每个收到的结果均能马上显示出来, 一旦捕获到的minions的结果大于等于之前获得的minions数目, 即表示所有minions均已返回结果, 退出.

总结
**********
Salt利用ZeroMQ灵活高效的patterns, 使Salt网络拓扑变得非常灵活高效. 利用PUB/SUB, 实现了高效的远程执行指令下发机制; 利用ROUTER/REQ, 实现认证及异步的远程执行结果返回; 利用DEALER/REP, 实现多进程任务处理机制; 利用PULL/PUB, 实现Event BUS, 使其他或第三方应用可以快速的使用PUB/SUB接收到Event BUS上的消息.

I love Salt, I love ZeroMQ!

.. _Salt: https://github.com/saltstack/salt
.. _SaltStack: http://saltstack.com/
.. _ZeroMQ: http://zeromq.org/
.. _RAET: https://github.com/saltstack/raet
