Title: Salt States概览
Date: 2014-03-16 18:18
Tags: SaltStack, 入门
Slug: starting-states
Summary: 	yinchuan分享的Salt States概览

* 原文出处: <http://www.ituring.com.cn/article/42238>
* 作者: yinchuan

## 作者言

我也只是SaltStack的初学者，如果文中有错误的地方，请不吝赐教。

在学习的过程，我也做了不少实验，犯了不少错，积累了一些经验，对SaltStack的运行也有一定了解，如果有什么问题，或是不太理解的地方，非常欢迎留言交流！

## Salt States

参考链接：[官方文档](http://docs.saltstack.com/topics/tutorials/starting_states.html)

简洁，简洁，简洁

众多强大而有力的设计都建立在简单的原则之上。Salt SLS系统也努力向K.I.S.S看齐。（Keep It Stupidly Simple）

SLS（代表SaLt State文件）是Salt State系统的核心。SLS描述了系统的目标状态，由格式简单的数据构成。这经常被称作配置管理。

    Note

    这篇文章从整体上介绍了Salt States，以后还会增加对各组件的深入介绍。

## 只是数据而已

深入学习之前，明白SLS文件只是结构化的数据而已是很有用的。看懂和编写SLS文件不需要理解这一点，但会让你体会到SLS系统的强大。

SLS文件本质上只是一些@dictionaries@，@lists@，@strings@和@numbers@。这种设计让SLS文件非常灵活，可以满足开发者的各种需求，而且可读性很高。写得越多，就越清楚到底写得是什么。

## 默认的数据 - YAML

Salt默认使用能找到的最简单的序列化数据格式 — — YAML，来表达SLS数据。典型的SLS文件如下：

    apache:
       pkg:
         - installed
       service:
         - running
         - require:
           - pkg: apache

这些数据确保名为@apache@的软件包处于已安装状态（如果不是，那么就安装@apache@），服务进程@apache@处于运行状态。这些数据简洁，易于理解。下面简单解释一下：
 第1行是这段数据的ID，被称作ID声明。这个ID是将要执行的这些命令的名字。
 第2行和第4行表示State声明开始，使用了pkg和service这两个states。pkg使用系统本地的软件包管理器管理将要安装的软件，service管理系统守护进程。
 第3行和第5行是要执行的function。这些function定义了名字为ID的软件包和服务的目标状态。此例中，软件包应当处于已安装状态，服务必须运行。
 最后，第6行是关键字require。这被称为必要语句（Requisite），它确保了apache服务只有在成功安装软件包后才会启动。

## 添加配置文件和用户

部署像apache这样的web服务器时，还需要添加其他的内容。需要管理apache的配置文件，需要添加运行apache服务的用户和组。

    apache:
       pkg:
         - installed
       service:
         - running
         - watch:
           - pkg: apache
           - file: /etc/httpd/conf/httpd.conf
           - user: apache
       user.present:
         - uid: 87
         - gid: 87
         - home: /var/www/html
         - shell: /bin/nologin
         - require:
           - group: apache
       group.present:
         - gid: 87
         - require:
           - pkg: apache

     /etc/httpd/conf/httpd.conf:
       file.managed:
         - source: salt://apache/httpd.conf
         - user: root
         - group: root
         - mode: 644

这个SLS大大扩展了上面的例子，增加了配置、用户、组，还有一个新的必要语句：watch。

user和group这两个state添加在apache这个ID下，所以增加的user和group名字都是apache。require语句确保了只有在apache这个group存在时才建立user，只有在apache这个package成功安装后才会建立group。

service中的require语句换成了watch，从需要1个软件包改为监视3个state（分别是pkg、file和user）。watch语句和require很相似，都能保证被监视或需要的state在自己之前执行，但是watch还有其他作用。在被监视的state发生变化时，定义watch语句的state会执行自己的watcher函数。也就是说，更新软件包，修改配置文件，修改apache用户的uid都会触发service state的watcher函数。在这个例子中，service state的watcher会重启apache服务。

    Note

    Salt的watcher概念非常有意思。Puppet中功能类似的是notify，也可以触发服务重启。Salt的watcher非常灵活，watcher本质上是在state的代码中定义的名为mod_watch()的函数，
    在这个函数中想做什么事情完全就看你的需求了。我没有仔细看Puppet的notify如何实现，不知道是否有这么灵活。

## 多个SLS文件

在更有扩展性的部署Salt State时，需要用到不只一个SLS。上面的例子中只使用1个SLS文件，2个或多个SLS文件可以结合形成State Tree。上面的例子还使用了一个奇怪的文件来源 — `salt://apache/httpd.conf`，这个文件究竟在什么位置呢？

SLS文件以一定的目录结构分布在master上；SLS和要下发到minion上的文件都只是普通文件。

上面的例子中的文件在Salt的根目录（见[SaltStack中的文件服务器](http://www.ituring.com.cn/article/41632)）分布如下：

    apache/init.sls
    apache/httpd.conf

httpd.conf只是apache目录下的一个普通文件，可以直接引用。 使用多个SLS文件可以更加灵活方便，以SSH为例：

ssh/init.sls:

    openssh-client:
       pkg.installed

     /etc/ssh/ssh_config:
       file.managed:
         - user: root
         - group: root
         - mode: 644
         - source: salt://ssh/ssh_config
         - require:
           - pkg: openssh-client

ssh/server.sls:

    include:
       - ssh

     openssh-server:
       pkg.installed

     sshd:
       service.running:
         - require:
           - pkg: openssh-client
           - pkg: openssh-server
           - file: /etc/ssh/banner
           - file: /etc/ssh/sshd_config

     /etc/ssh/sshd_config:
       file.managed:
         - user: root
         - group: root
         - mode: 644
         - source: salt://ssh/sshd_config
         - require:
           - pkg: openssh-server

     /etc/ssh/banner:
       file:
         - managed
         - user: root
         - group: root
         - mode: 644
         - source: salt://ssh/banner
         - require:
           - pkg: openssh-server

    Note

    在ssh/server.sls中，用了两种不同的方式来表示用Salt管理一个文件。在ID为/etc/ssh/sshd_config段中，直接使用file.managed作为state声明，
    而在ID为/etc/ssh/banner段中，使用file作为state声明，附加一个managed属性。两种表示方法的含义与结果完全一样，只是写法不同。

现在State Tree如下（有些被引用的文件没有给出内容，不影响理解）：

    apache/init.sls
    apache/httpd.conf
    ssh/init.sls
    ssh/server.sls
    ssh/banner
    ssh/ssh_config
    ssh/sshd_config

ssh/server.sls中使用了include语句。include将别的SLS添加到当前文件中，所以可以require或watch被引用的SLS中定义的内容，还可以extend其内容（马上讲到）。include语句使得state可以跨文件引用。使用include相当于把被引用的内容文件添加到自身。

## 扩展被引用的SLS数据 Extend

扩展是什么意思呢？比如在ssh/server.sls中定义了一个apache通用的服务器，现在要增加一个带mod\_python模块的apache，不需要重头写新的SLS，直接include原来的server.sls，然后增加安装mode\_python的state，再在apache service的watch列表中增加mod\_python即可。python/mod\_python.sls内容如下：

     include:
       - apache

     extend:
       apache:
         service:
           - watch:
             - pkg: mod_python

     mod_python:
       pkg.installed

这个例子中，先将apache目录下的init.sls文件包含进来（在include一个目录时，Salt会自动查找init.sls文件），然后扩展了ID为apache下的service state中的watch列表。

也可以在Extending中修改文件的下载位置。ssh/custom-server.sls:

    include:
       - ssh.server

     extend:
       /etc/ssh/banner:
         file:
           - source: salt://ssh/custom-banner

Extend使得Salt的SLS更加灵活。为什么SLS能够做Extend呢？文章一开始最强调了，SLS中的文件仅仅是结构化的data而已，在处理SLS时，会将其中的内容解析成Python中的dict（当然这个dict中会嵌套dict和list）。修改apache watch的内容，相当于往list里面添加一个元素；修改banner文件的下载路径相当于修改dict中的某个key对应的值。在extending时，会附加加require/watch的内容，而不是覆盖。

## 理解渲染系统 Render System

因为SLS仅仅是data，所以不是非得用YAML来表达。Salt默认使用YAML，只是因为易学易用。只要有对应的renderer，SLS文件可以用任何方式表达（Salt关心的是最终解析出来的数据结构，只要你的renderer能够按要求返回这个数据结构，Salt干嘛关心你如何书写源文件呢？）。

Salt默认使用yaml\_jinja渲染器。yaml\_jinjia先用jinja2模板引擎处理SLS，然后再调用YAML解析器。这种设计的好处是，可以在SLS文件使用所有的编程结构（jinja2能怎么用，这里就能怎么用。条件，循环，Python代码，什么都可以）。

其他可用的渲染器还包括：yaml\_mako，使用Mako模板引擎；yaml\_wempy，使用Wempy模板引擎；py，直接使用Python写SLS文件；pydsl，建立在Python语法基础上的描述语言。

## 简单介绍默认的渲染器—yaml\_jinja

关于jinja模板引擎的使用请参考其[官方文档](http://jinja.pocoo.org/docs)

在基于模板引擎的渲染器里，可以从3个组件中获取需要的数据：salt，grains和pilla。在模板文件中，可以用salt对象执行任意的Salt function，使用grains访问Grains数据。示例如下：
 apache/init.sls:

    apache:
       pkg.installed:
         {% if grains['os'] == 'RedHat'%}
         - name: httpd
         {% endif %}
       service.running:
         {% if grains['os'] == 'RedHat'%}
         - name: httpd
         {% endif %}
         - watch:
           - pkg: apache
           - file: /etc/httpd/conf/httpd.conf
           - user: apache
       user.present:
         - uid: 87
         - gid: 87
         - home: /var/www/html
         - shell: /bin/nologin
         - require:
           - group: apache
       group.present:
         - gid: 87
         - require:
           - pkg: apache

     /etc/httpd/conf/httpd.conf:
       file.managed:
         - source: salt://apache/httpd.conf
         - user: root
         - group: root
         - mode: 644

这个例子很容易理解，用到了jinja中的条件结构，如果grains中的os表明minion的操作系统是Red Hat，那么Apache的软件包名和服务名应当是httpd。

再来一个更NB的例子，用到了jinja的循环结构，在设置MooseFs分布式chunkserver的模块中：
 moosefs/chunk.sls:

    include:
       - moosefs

     {% for mnt in salt['cmd.run']('ls /dev/data/moose*').split() %}
     /mnt/moose{{ mnt[-1] }}:
       mount.mounted:
         - device: {{ mnt }}
         - fstype: xfs
         - mkmnt: True
       file.directory:
         - user: mfs
         - group: mfs
         - require:
           - user: mfs
           - group: mfs
     {% endfor %}

     '/etc/mfshdd.cfg':
       file.managed:
         - source: salt://moosefs/mfshdd.cfg
         - user: root
         - group: root
         - mode: 644
         - template: jinja
         - require:
           - pkg: mfs-chunkserver

     '/etc/mfschunkserver.cfg':
       file.managed:
         - source: salt://moosefs/mfschunkserver.cfg
         - user: root
         - group: root
         - mode: 644
         - template: jinja
         - require:
           - pkg: mfs-chunkserver

     mfs-chunkserver:
       pkg:
         - installed
     mfschunkserver:
       service:
         - running
         - require:
     {% for mnt in salt['cmd.run']('ls /dev/data/moose*') %}
           - mount: /mnt/moose{{ mnt[-1] }}
           - file: /mnt/moose{{ mnt[-1] }}
     {% endfor %}
           - file: /etc/mfschunkserver.cfg
           - file: /etc/mfshdd.cfg
           - file: /var/lib/mfs

这个例子展示了jinja的强大，多个for循环用来动态地检测并挂载磁盘，多次使用salt对象（这里使用了cmd.run这个执行模块）执行shell命令来收集数据。

## 简单介绍Python和PyDSL渲染器

在任务逻辑非常复杂时，默认的yaml\_jinja渲染器不一定满足要求，这时可以使用Python渲染器。如何在State tree中添加使用py渲染器的SLS文件呢？简单。 一个非常简单的基本Python SLS文件： python/django.sls:

    #!py

     def run():
         '''
         Install the django package
         '''
         return {'include': ['python'],
                 'django': {'pkg': ['installed']}}

这个例子也很好理解，第1行告诉Salt不使用默认的渲染器，而是用py。接着定义了函数run，这个函数的返回值必须符合Salt的要求，即HighState数据结构（我接下来就写关于HighState的文章，现在不必关心其细节，反正就是一个dict，key和value都有规定好的含义）。 如果换用pydsl渲染器，上面的例子会更简洁：
 python/django.sls:

    #!pydsl

    include('python', delayed=True)
    state('django').pkg.installed()

如果用YAML，会是下面这个样子：

    include:
      - python

    django:
      pkg.installed

这也可以看出，正常情况下使用YAML是非常合适的，但如果有需要时，使用纯粹的Python SLS可以非常NB。

## 运行和调试Salt States

写好的SLS如何才能应用到minion呢？在SaltStack中，远程执行是一切的基础。执行命令@salt ‘\*’ state.highstate@会让所有的minion到master上来取走自己的SLS定义，然后在本地调用对应的state module（user，pkg，service等）来达到SLS描述的状态。如果这条命令只返回minion的主机名加一个’:’，多半是哪一个SLS文件有错。如果minion是以服务进程启动，执行命令@salt-call state.highstate -l debug@可以看到错误信息，便于调试。minion还可以直接在前台以debug模式运行：@salt-minion -l debug@。

## 接下来是什么？

接下来是关于Pillar的内容，官方文档[在此](http://docs.saltstack.com/topics/tutorials/pillar.html)
