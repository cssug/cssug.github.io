Title: Salt Master外部Job Cache配置
Date: 2014-11-24
Tags: SaltStack, 进阶
Slug: saltstack-master-external-job-cache-01
Summary: pengyao分享的在salt 2014.7中如何配置外部Job Cache

* 原文出处: <http://pengyao.org/saltstack-master-external-job-cache.html>
* 作者: [pengyao](http://pengyao.org/)

SaltStack 2014.7之前, Minion端的执行结果想存储在外部系统中,
需要借助returner进行配置.
而returner的工作方式是由minion端直接连接对应的returner,
在分布式环境中由于网络等限制,该方式并不友好.

而在Master端, Job Cache会以文件的形式存储在Master本地磁盘,
对第三方系统并不友好. 基于此, 之前有分享过 [基于Salt
Event系统构建Master端returner](http://pengyao.org/saltstack_master_retuner_over_event_system.html)
, 需要启动另外一个进程, 进行监听Salt Event接口,
并将结果存储在第三方系统中. 刚好看到2014.7.0中master端增加了
master\_job\_cache参数, 可以直接外放Job Cache, 就做个测试,
测试下这个功能.

## 环境说明

-   Salt Version: *2014.7.0*
-   OS: CentOS 6.5 X86\_64 (with EPEL)
-   本次测试结果将存储在MySQL中, 为了方便测试, 已在Master本地部署了MySQL
    Server

## 开工

### 前置配置

安装MySQLdb依赖:

    yum -y install MySQL-python

配置本次测试需要使用的数据库及用户:

    # 创建salt数据库
    mysql -e 'create database salt'
    # 创建用于连接salt数据库的用户
    mysql -e '"grant all on salt.* to salt@localhost identified by "salt_pass';
    # 将数据库配置添加至master配置文件中

创建用于存储Job的数据库表结构:

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

### 配置Master

将MySQL连接权限等信息添加到Salt Master配置文件中:

    echo -e "\n\n# MySQL\nmysql.host: 'localhost'\nmysql.user: 'salt'\nmysql.pass: 'salt_pass'\nmysql.db: 'salt'\nmysql.port: 3306" >> /etc/salt/master

配置master\_job\_cache选项, 以使将Job结果存储在MySQL中:

    echo -e "\n\n# Master Job Cache\nmaster_job_cache: mysql" >> /etc/salt/master

重启Salt Master, 以使配置生效:

    service salt-master restart

### 测试

对主机执行test.ping:

    salt '*' test.ping -v

输出结果:

    Executing job with jid 20141120060202308159
    -------------------------------------------

    minion-01.example.com:
        True

查询MySQL jids表数据:

    mysql salt -e 'select * from jids\G'

输出结果:

    *************************** 1. row ***************************
    jid: 20141120060202308159
    load: {"tgt_type": "glob", "jid": "20141120060202308159", "cmd": "publish", "tgt": "*", "kwargs": {"show_timeout": false, "show_jid": false}, "ret": "", "user": "sudo_vagrant", "arg": [], "fun": "test.ping"}

查询MySQL salt\_returns表数据:

    mysql salt -e 'select * from salt_returns\G'

输出结果:

    *************************** 1. row ***************************
    fun: test.ping
    jid: 20141120060202308159
    return: true
    id: minion-01.example.com
    success: 1
    full_ret: {"fun_args": [], "jid": "20141120060202308159", "return": true, "retcode": 0, "success": true, "cmd": "_return", "_stamp": "2014-11-20T06:02:02.533850", "fun": "test.ping", "id": "minion-01.example.com"}
    alter_time: 2014-11-20 06:02:02

Job执行结果已经按照之前的配置存储到了MySQL中, 达到预期效果
