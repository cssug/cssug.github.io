Title: Salt-ssh安装配置
Date: 2014-03-16 18:30
Tags: SaltStack, 入门
Slug: salt-ssh-install-and-config
Summary: clavinli同学分享的salt-ssh安装配置文章

* 原文出处: <http://clavinli.github.io/2013/10/22/saltstack-salt-ssh/>
* 作者: clavinli

## salt-ssh介绍

salt-ssh 是 0.17.0 新出现的一个功能，一听这名字就知道它是依赖 ssh
来进行远程命令执行的工具，好处就是你不需要在客户端安装
minion，也不需要安装 master（直接安装 salt-ssh 这个包即可），有点类似
paramiko、pssh、ansible 这类的工具，有些时候你还真的需要
salt-ssh（例如：条件不允许安装 minion、不用长期管理某台 minion）
最最重要的是 salt-ssh 并不只是单纯的 ssh 工具，它支持 salt
大部分的功能，如 grains、modules、state 等

**备注** 需要注意的是，salt-ssh 并没有继承原来的通讯架构
(ZeroMQ)，也就是说它的执行速度啥的都会比较慢

## salt-ssh安装

去 github 下载 salt 的源安装即可

    # git clone https://github.com/saltstack/salt.git
    # python setup.py install

## salt-ssh使用

salt-ssh 是通过调用 roster 配置文件来实现的，语法很简答，定义
ID、host、user、password 即可

### 1、定义 roster，让 salt-ssh 生效

默认是在 /etc/salt/roster

    # vim /etc/salt/roster
    squid1:
      host: 10.14.36.14
      user: root
      passwd: 123456
      port: 36000
      timeout: 3

设置完之后就可以进行测试了，语法跟 salt 的一样

    # salt-ssh 'squid1' test.ping
    squid1:
        True

### 2、salt-ssh 不但支持运行 shell 命令，同时它还支持 salt 本身的模块，甚至支持调用 state

执行 shell 命令

    # salt-ssh 'squid1' -r 'df -h'
    squid1:
        Filesystem            Size  Used Avail Use% Mounted on
        /dev/sda1             9.9G  1.6G  7.9G  17% /
        udev                  3.9G  200K  3.9G   1% /dev
        /dev/sda3              20G  426M   19G   3% /usr/local

    # salt-ssh 'squid1' -r 'cat /etc/SuSE-release'
    squid1:
        SUSE Linux Enterprise Server 10 (x86_64)
        VERSION = 10
        PATCHLEVEL = 1

调用 salt 本身的模块

    # salt-ssh 'squid1' disk.usage
        /usr/local:
            ----------
            1K-blocks:
                20641788
            available:
                19157644
            capacity:
                3%
            filesystem:
                /dev/sda3
            used:
                435504
        ...

获取 grains 信息

    # salt-ssh 'squid1' grains.item cpu_model
    squid1:
        ----------
        cpu_model:
            Intel(R) Xeon(R) CPU           X3440  @ 2.53GHz

调用 state 目前 0.17.1 的版本还有 bug，导致 state 调用失败，感谢 Puluto
修复了此 bug，废话少说，马上试试，[issue
7991](https://github.com/saltstack/salt/issues/7991)

    # cat temp.sls
    conf_squidinit:
      file.managed:
        - name: /tmp/squid
        - source: salt://proxy/squid/templates/squid.init
        - user: root
        - group: root
        - mode: 755

    # salt-ssh 'squid1' state.sls temp
    squid1:
        ----------
        file_|-conf_squidinit_|-/tmp/squid_|-managed:
        ----------
        __run_num__:
            0
        changes:
            ----------
            diff:
                New file
            mode:
                755
        comment:
            File /tmp/squid updated
        name:
            /tmp/squid
        result:
        True

## salt-ssh 实战

任务就是使用 salt-ssh 安装 minion 并重启，真正实现自动化 ^^

    # cat salt_install.sls
    epel_install:
      file.managed:
        - name: /root/epel-release-6-8.noarch.rpm
        - source: salt://tutorial/epel-release-6-8.noarch.rpm
        - user: root
        - group: root
      cmd.run:
        - name: rpm -ivh /root/epel-release-6-8.noarch.rpm
        - unless: test -f /etc/yum.repos.d/epel.repo
        - require:
          - file: epel_install

    conf_epel:
      file.managed:
        - name: /etc/yum.repos.d/epel.repo
        - source: salt://tutorial/epel.repo
        - user: root
        - group: root
        - mode: 644

    salt_install:
      pkg.installed:
        - name: salt-minion
      file.managed:
        - name: /etc/salt/minion
        - source: salt://tutorial/minion
      service.running:
        - name: salt-minion
        - enable: True
        - reload: True
        - watch:
          - file: salt_install

    # salt-ssh 'squid1' state.sls system.states.salt_install
    ...

    # salt-ssh 'squid1' -r '/etc/init.d/salt-minion restart'
    squid1:
        Stopping salt-minion daemon: ..done
        Starting salt-minion daemon: ..done

## 使用 salt-ssh 注意事项

salt-ssh 用的是 sshpass 进行密码交互的，所以必须安装 sshpass，salt-ssh
才能正常运行

    # rpm -qa | grep sshpass
    sshpass-1.05-1.el6.x86_64

salt-ssh
使用的范围还是比较广的，适合用于那些已经部署了其他自动化运维工具的机器，如
puppet、chef，不过我主要用于初始化 minion 环境，主要还是用 salt 比较多