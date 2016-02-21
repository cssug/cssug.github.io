Title: Salt实战之自动安装部署MooseFS
Date: 2014-03-16
Tags: SaltStack, 进阶
Slug: salt-auto-deploy-moosefs
Summary: Rainbow+分享的使用salt自动部署MooseFS案例

* 作者: Rainbow+

暮然回首，我做运维已经有六年多了，从最开始那个一无所知的菜鸟，到现在能够胸有成竹的管理公司几百台服务器，中间走了不少的弯路。

就拿批量管理服务器这块儿来说吧，几年前自己只会Shell脚本，在服务器不多的时候，感觉还忙的过来，到后来服务器越来越多的时候就不行了。写了很多的脚本放到计划任务中定期执行，能解决一部分工作，但效率还是很低下，因为服务器太多了，每次脚本有变动就需要在所有服务器上都更新一遍，非常痛苦，后来我学会了用expect来处理交互，但效率依然很低下，等脚本自动登录完所有的机器并执行完相关命令，至少30分钟过去了。

然后，我加入了一些技术群，了解到了像Func，Puppet以及Chef这样的工具，并试着使用它们来管理服务器，效果真的很好。

就在几个星期以前，在Puppet群里面，我听到了Salt这个词，“绿肥”天天在群里“拉客”，号称是Func+Puppet，用Python实现的，由于我对Python很有好感，也还算有点基础，于是就试着用了用Salt。

学一个东西最快的方法就是用它去解决现有的实际问题，我选择了使用Salt来自动安装部署一套MooseFS分布式文件系统，结果，我花了1天的时间就完成了整个工作，同时对Salt好感也超越了Puppet，说实话，我现在非常愿意将线上所有Puppet相关的代码都用Salt来重写一遍，其中包括整个Hadoop集群的自动部署。

好了，废话不多说，下面开始讲解整个实战过程！

Salt其实也仅仅只是一个工具，解决问题的关键是我们的思路，正比如我能够用Salt来实现自动安装部署MooseFS，那么前提肯定是我了解手动安装部署MooseFS的整个过程。因此，建议大家先阅读我的《在CentOS上安装部署MooseFS分布式文件系统》<http://heylinux.com/archives/2467.html>
这篇文章，了解如何通过手动的方式来安装部署MooseFS。

接下来，我们首先要对Salt的基础进行一系列的学习，这里，我强烈推荐官网的Tutorial：<http://docs.saltstack.com/topics/tutorials/walkthrough.html>
在完成了整个Tutorial之后，通过Module
Index页面，我们能够快速查阅Salt所有模块的功能与用法：<http://docs.saltstack.com/py-modindex.html>

我的整个Salt代码结构如下：

    $ tree
    .
    ├── pillar
    │   ├── moosefs
    │   │   └── params.sls
    │   ├── _salt
    │   │   └── params.sls
    │   ├── schedules
    │   │   └── params.sls
    │   ├── top.sls
    │   └── users
    │       └── lists.sls
    ├── README.md
    ├── salt
    │   ├── moosefs
    │   │   ├── files
    │   │   │   └── index.html
    │   │   ├── states
    │   │   │   ├── chunkserver.sls
    │   │   │   ├── client.sls
    │   │   │   ├── common.sls
    │   │   │   ├── master.sls
    │   │   │   └── metalogger.sls
    │   │   └── templates
    │   │       ├── httpd.conf
    │   │       ├── mfschunkserver.cfg
    │   │       ├── mfsexports.cfg
    │   │       ├── mfshdd.cfg
    │   │       ├── mfsmaster.cfg
    │   │       └── mfsmetalogger.cfg
    │   ├── _roles
    │   │   ├── backup.sls
    │   │   ├── datanode.sls
    │   │   └── master.sls
    │   ├── _salt
    │   │   ├── states
    │   │   │   └── minion.sls
    │   │   └── templates
    │   │       └── minion
    │   ├── top.sls
    │   └── users
    │       └── states
    │           └── create.sls
    └── tools
        ├── install_salt_minion.sh
        └── tips.txt

Salt的默认配置需要存放在/srv下，在/srv/pillar中主要存放的是各类“参数”，而在/srv/salt下存放的是具体的state“代码文件”，以及配置文件的“模板”。

Salt的入口文件分别是/srv/pillar/top.sls 与
/srv/salt/top.sls，入口文件的意思就是，在minion“客户端”上，每次请求服务端配置的时候，它们实际上所请求的是这两个文件，虽然在上面有很多的文件，但其实它们都是通过这两个文件所关联起来的。

比如在/srv/pillar/top.sls文件的内容是：

    base:
      '*':
        - _salt.params
        - schedules.params
        - moosefs.params
        - users.lists

即针对所有的服务器(‘\*’)，引用\_salt，schedules以及moosefs目录下params.sls中的配置和users目录下lists.sls的配置。

而/srv/salt/top.sls文件的内容是：

    base:
      '*':
        - _salt.states.minion
        - users.states.create

      'ip-10-197-29-251.us-west-1.compute.internal':
        - _roles.master
        - _roles.datanode

      'ip-10-196-9-188.us-west-1.compute.internal':
        - _roles.backup
        - _roles.datanode

      'ip-10-197-62-239.us-west-1.compute.internal':
        - _roles.datanode

即针对所有的服务器(‘\*’)，引用\_salt/states目录下minion.sls中的配置，以及users/states目录下create.sls中的配置；针对服务器ip-10-197-29-251.us-west-1.compute.internal，引用\_roles目录下master.sls中的配置，其余两个主机类似。

而\_roles/master.sls文件的内容是：

    include:
      - moosefs.states.master

即引用 moosefs/states 目录下 master.sls的配置，进一步查看 master.sls
的配置，就可以看到如下内容：

    include:
      - moosefs.states.common

    mfsmaster:
      service:
        - running
        - require:
          - cmd.run: mfsmaster
      cmd.run:
        - name: 'cp metadata.mfs.empty metadata.mfs'
        - cwd: /var/mfs/
        - user: daemon
        - unless: 'test -e metadata.mfs.back'
        - require:
          - file: /etc/mfs/mfsmaster.cfg

    mfs-cgi:
      pkg.installed:
        - require:
          - pkg: httpd
    ...

    /etc/httpd/conf/httpd.conf:
      file.managed:
        - source: salt://moosefs/templates/httpd.conf
        - template: jinja
        - user: root
        - group: root
        - mode: 644
        - require:
          - pkg: httpd
    ...

即具体的配置步骤，包括了mfsmaster的service启动，初始化数据文件，修改httpd.conf配置文件等，而这一部分的具体配置，大家可以在我的[GitHub](/GitHub站点上看到所有详细的代码：)
<https://github.com/mcsrainbow/HeyDevOps/tree/master/Salt>

Salt默认的很多示例，目录结构非常简单，而我因为有“分类强迫症”，不喜欢将各类不同类型的文件放在同一个目录下，所以我创建了states和files以及templates目录来分别存放states，普通文件和配置文件。而创建\_roles目录并在top.sls中引用，而不是通过直接引用moosefs.states.master这种方式，原因是我手里的服务器全是EC2上的云主机，主机名默认已经固定了，不方便自定义的规划，因此我在\_roles目录下根据自身需要，根据线上服务器的角色创建了一些文件，在这些文件中再去引用相关的配置，这样，今后每台服务器就需要绑定好它对应的角色就可以了，更新\_roles目录下的文件就可以更新所有对应的服务器。

当然，这些都是我实际环境中遇到的问题，也是我所构思出来的解决方法，我在本文中着重讲解了我的思路，以及Salt的工作流程，是因为我发现在我学习的过程中，它们给我带来的困扰和疑惑是最大的。具体的states实现，大家可以通过我在[GitHub](/GitHub中分享的代码"https://github.com/mcsrainbow/HeyDevOps/tree/master/Salt":https://github.com/mcsrainbow/HeyDevOps/tree/master/Salt，参考"《在CentOS上安装部署MooseFS分布式文件系统》":http://heylinux.com/archives/2467.html文章中的步骤，来学习和理解。)
