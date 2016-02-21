Title: SaltStack Event系统监听events测试
Date: 2014-04-24 09:03
Tags: SaltStack, 进阶
Slug: saltstack-event-system-listen-events
Summary: pengyao分享的基于SaltStack Event系统进行监听events的测试用例

* 原文出处: <http://pengyao.org/saltstack_event_system_listen_events.html>
* 作者: [pengyao](http://pengyao.org/)

{{toc}}

SaltStack 0.10版本中, 新增了Event系统, 官方在 [Release
Notes](http://docs.saltstack.com/en/latest/topics/releases/0.10.0.html#event-system)
对其描述如下:

>The Salt Master now comes equipped with a new event system. This event
system has replaced some of the back end of the Salt client and offers
the beginning of a system which will make plugging external applications
into Salt. The event system relies on a local ZeroMQ publish socket and
other processes can connect to this socket and listen for events. The
new events can be easily managed via Salt’s event library.

同时官方也在 [Salt
Event系统](http://docs.saltstack.com/en/latest/topics/event/index.html#listening-for-events)
页面中提供了监听event的例子程序, 基于其进行下Event系统学习.

## 环境说明

-   测试结构: Master/Minions结构, 共一台minion, 对应id为:
    *salt-minion-01.example.com*
-   Salt Version: *2014.1.1*

## 开工

新开一个终端, 运行python, 基于其尝试监听所有的Event:

    import salt.utils.event

    event = salt.utils.event.MasterEvent('/var/run/salt/master')

    for eachevent in event.iter_events(full=True):
        print eachevent
        print "------"

在另外一个终端执行:

    salt '*' test.ping

查看之前监听所有Event的终端, 有如下输出:

    {'tag': '20140417135823133764', 'data': {'_stamp': '2014-04-17T13:58:23.133956', 'minions': ['salt-minion-01.example.com']}}
    ------
    {'tag': 'new_job', 'data': {'tgt_type': 'glob', 'jid': '20140417135823133764', 'tgt': '*', '_stamp': '2014-04-17T13:58:23.134005', 'user': 'sudo_vagrant', 'arg': [], 'fun': 'test.ping', 'minions': ['salt-minion-01.example.com']}}
    ------
    {'tag': 'salt/job/20140417135823133764/new', 'data': {'tgt_type': 'glob', 'jid': '20140417135823133764', 'tgt': '*', '_stamp': '2014-04-17T13:58:23.134064', 'user': 'sudo_vagrant', 'arg': [], 'fun': 'test.ping', 'minions': ['salt-minion-01.example.com']}}
    ------
    {'tag': '20140417135823133764', 'data': {'fun_args': [], 'jid': '20140417135823133764', 'return': True, 'retcode': 0, 'success': True, 'cmd': '_return', '_stamp': '2014-04-17T13:58:23.150356', 'fun': 'test.ping', 'id': 'salt-minion-01.example.com'}}
    ------
    {'tag': 'salt/job/20140417135823133764/ret/salt-minion-01.example.com', 'data': {'fun_args': [], 'jid': '20140417135823133764', 'return': True, 'retcode': 0, 'success': True, 'cmd': '_return', '_stamp': '2014-04-17T13:58:23.150397', 'fun': 'test.ping', 'id': 'salt-minion-01.example.com'}}
    ------

从输出结果看, 对于tag只是jid的, 官方在源码中标记的注释是&quot;old dup
event&quot;, 推测是为了兼容旧的event系统(0.17.0版本event系统进行了更新),
本次对其不做处理. 下发任务对应的tag为 *new_job*,
并且下发任务时就master端就在event中注定了那些minions需要运行(对应的data字典中的minions).
如果tag中包含 *salt/job/* 字样并且data字典中 *return* 为True,
则表示该Event是minion返回的结果.

同时测试下超过timeout设置(默认为5秒)的任务:

    salt '*' cmd.run 'sleep 6; echo hello world'

输出结果为:

    {'tag': '20140417141834578593', 'data': {'_stamp': '2014-04-17T14:18:34.578822', 'minions': ['salt-minion-01.example.com']}}
    ------
    {'tag': 'new_job', 'data': {'tgt_type': 'glob', 'jid': '20140417141834578593', 'tgt': '*', '_stamp': '2014-04-17T14:18:34.578881', 'user': 'sudo_vagrant', 'arg': ['sleep 6; echo hello world'], 'fun': 'cmd.run', 'minions': ['salt-minion-01.example.com']}}
    ------
    {'tag': 'salt/job/20140417141834578593/new', 'data': {'tgt_type': 'glob', 'jid': '20140417141834578593', 'tgt': '*', '_stamp': '2014-04-17T14:18:34.578917', 'user': 'sudo_vagrant', 'arg': ['sleep 6; echo hello world'], 'fun': 'cmd.run', 'minions': ['salt-minion-01.example.com']}}
    ------
    {'tag': '20140417141839587706', 'data': {'_stamp': '2014-04-17T14:18:39.587908', 'minions': ['salt-minion-01.example.com']}}
    ------
    {'tag': 'new_job', 'data': {'tgt_type': 'glob', 'jid': '20140417141839587706', 'tgt': '*', '_stamp': '2014-04-17T14:18:39.587961', 'user': 'sudo_vagrant', 'arg': ['20140417141834578593'], 'fun': 'saltutil.find_job', 'minions': ['salt-minion-01.example.com']}}
    ------
    {'tag': 'salt/job/20140417141839587706/new', 'data': {'tgt_type': 'glob', 'jid': '20140417141839587706', 'tgt': '*', '_stamp': '2014-04-17T14:18:39.587985', 'user': 'sudo_vagrant', 'arg': ['20140417141834578593'], 'fun': 'saltutil.find_job', 'minions': ['salt-minion-01.example.com']}}
    ------
    {'tag': '20140417141839587706', 'data': {'fun_args': ['20140417141834578593'], 'jid': '20140417141839587706', 'return': {'tgt_type': 'glob', 'jid': '20140417141834578593', 'tgt': '*', 'pid': 2143, 'ret': '', 'user': 'sudo_vagrant', 'arg': ['sleep 6; echo hello world'], 'fun': 'cmd.run'}, 'retcode': 0, 'success': True, 'cmd': '_return', '_stamp': '2014-04-17T14:18:39.605262', 'fun': 'saltutil.find_job', 'id': 'salt-minion-01.example.com'}}
    ------
    {'tag': 'salt/job/20140417141839587706/ret/salt-minion-01.example.com', 'data': {'fun_args': ['20140417141834578593'], 'jid': '20140417141839587706', 'return': {'tgt_type': 'glob', 'jid': '20140417141834578593', 'tgt': '*', 'pid': 2143, 'ret': '', 'user': 'sudo_vagrant', 'arg': ['sleep 6; echo hello world'], 'fun': 'cmd.run'}, 'retcode': 0, 'success': True, 'cmd': '_return', '_stamp': '2014-04-17T14:18:39.605321', 'fun': 'saltutil.find_job', 'id': 'salt-minion-01.example.com'}}
    ------
    {'tag': '20140417141834578593', 'data': {'fun_args': ['sleep 6; echo hello world'], 'jid': '20140417141834578593', 'return': 'hello world', 'retcode': 0, 'success': True, 'cmd': '_return', '_stamp': '2014-04-17T14:18:40.604562', 'fun': 'cmd.run', 'id': 'salt-minion-01.example.com'}}
    ------
    {'tag': 'salt/job/20140417141834578593/ret/salt-minion-01.example.com', 'data': {'fun_args': ['sleep 6; echo hello world'], 'jid': '20140417141834578593', 'return': 'hello world', 'retcode': 0, 'success': True, 'cmd': '_return', '_stamp': '2014-04-17T14:18:40.604628', 'fun': 'cmd.run', 'id': 'salt-minion-01.example.com'}}
    ------

除了之前test.ping测试类似的输出外, 可以看到tag为 *new_job*
的event产生后的5秒, 自动产生了一个fun值为 *saltutil.find_job*,
其arg为之前new_job的jid的event. 然后minion返回之前运行的fun值为
*cmd.run* 对应的进行运行信息(pid等信息, 已确保任务正在被执行).

Salt对应的处理机制是master在下发指令后,如果在设置的timeout时间内,
所有minion均返回了结果, 则直接退出. 如果达到timeout时间后,
依然有minion没有返回结果, 则自动触发一个 *saltutil.find_job* 的任务,
去所有minion上查询该任务是否在执行. 如果minion返回任务当前正在执行中,
则等待一个新的timeout周期, 如果期间所有minion均返回了结果, 则退出;
依次类推, 一直等到直到所有minion均返回结果. 如果期间在触发
*saltutil.find_job* 时minion并没有返回任务的执行状况,
且之前并没有返回结果, 则认为minion出现问题, 就会输出&quot;Minion did not
return&quot; 字样(可以通过salt -v参数查询到).

从该机制中可以知道, 如果经常出现minion无法返回结果的情况,
对于某些场景如规模较大或minion高负载的情况下, 达到设置的timeout时间时,
自动触发 *saltutil.find_job* 任务,
而minion此时并没有开始运行之前下发的任务. 导致master直接认为&quot;Minion
did not return&quot;.
此时需要增大timeout的值(可以修改master的配置文件中的timeout选项)

同时由于master会自动触发 *saltutil.find_job* 任务,
而该任务也会记入Event系统, 所以对于如Halite等第三方系统,
执行长时间的任务时, 你会发现大量的 *saltutil.find_job* 操作,
此为正常现象, 无需处理(当然, 有洁癖的同学可能会不爽).

## 总结

Salt提供了强大的Event系统, 第三方程序可以轻松插入Event系统,
捕获当前Salt的运行状态, 易于扩展Salt功能.
