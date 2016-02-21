Title: Salt相关使用
Date: 2014-03-16 18:30
Tags: SaltStack, 入门
Slug: salt-use-01
Summary: halfss分享的Salt使用经验

* 原文出处: <http://blog.halfss.com/blog/2013/06/15/saltxiang-guan-shi-yong/>
* 作者: halfss

## nodegroup

salt的命令管理在对批量的机器进行操作(如果是单个的机器进行命令操作,ssh是最直接的方法)的时候才能更显示出他的部分强大。有时候我们通过target进行各种匹配,虽然可以写的很强大,强大到我们可以匹配出任何的满足我们需求的节点,但是写这个target的时候,如果过于复杂就要花费稍微长点的时间,所以在这个时候nodegroup可以很满足我们的需求,但是呢,直接写这个group分组也是很麻烦的,有没有更好的方法呢?

**前提**: master支持部分配置的动态加载,比如nodegroup,实现的方式是动态的读取/etc/salt/master.d/\*.conf内容,我们只要去更新nodegroup中的内容就可以了

我这里有多个用户都会去操作(每个用户管理的salt的机器不一样)salt,而salt-master同一个配置只能加载一次,所以我只能去维护一个定义了nodegroup文件

实现方式:

每个salt用户(在salt服务器上也是一个用户:普通用户)的~/groups文件夹中定义了一个个文件,每个文件有一堆的minion ID列表,然后写个脚本去读取(~/groups)文件夹中的所有文件,然后生产跟文件名对应的group名

如下:

    # ls ~/groups/
    test1.txt test2.txt test3.txt

然后执行如下命令: (这个命令为自己实现)

    [halfss@salt ~]# opstack update_groups

    组更新完毕

组生成成功后:

    [halfss@salt ~]$ salt -N test1 test.ping
    minion1:
        True
    minion2:
        True
    minion3:
        True

update\_groups的代码大概(我线上部分调整后直接粘贴过来,未测试)如下:

    def update_groups():
      file_dir = '%s/groups' % os.path.expandvars('$HOME')
      groups_re = '#%s_start\n.*\n#%s_end\n' % (user,user)
      groups = ''
      for group_file in os.listdir(file_dir):
        if group_file.split('.')[-1] != 'txt':
          continue
        group_file = '%s/%s' % (file_dir,group_file)
        servers = [ server[:1] for server  file(group_file).readlines()]
        groups += " %s: L@%s\n" % (group_file.split('/')[-1].split('.')[0],','.join(servers))
      groups_tmp = '#%s_start\n%s#%s_end\n' % (user,groups,user)
      nodegroups = file('/etc/salt/master.d/nodegroups.conf','r').read()
      nodegroups,re_count = re.subn(r'%s' % groups_re, groups_tmp,node groups
      if re_count == 0:
        nodegroups += groups_tmp
      file('/etc/salt/master.d/nodegroups.conf','w').write(nodegroups)
      print "组更新完毕")

## 复杂的sls

有些时候默认的提供的sls的语法并不能满足实际需求,好在灵活强大的salt已经支持sls拓展(详情可以访问：<http://docs.saltstack.com/topics/tutorials/starting_states.html>)

可以直接写python代码,只要返回值类似yaml风格一样东西就OK

比如我要对节点的hosts中的某个域名做管理,找最近的IP去解析

实例如下:

    import os
    import re

    def run():
      hosts = [  ＃这里的IP是模拟IP
       "192.168.1.2",
       "10.0.0.1",
      ]

      hosts_time = {}
      for host in hosts:
        cmd = "ping -c 4 %s" % host
        content = os.popen(cmd).read()
        use_time = re.findall(r'time=(.*)ms',content)
        hosts_time[host] = sum([float(u) for u in use_time])
      hosts_time = sorted(hosts_time.items(),key=lambda hosts_time:hosts_time[1])
      ip = hosts_time[0][0]

      dict = {
          'download':{'host.present':[{'ip':ip,'names':['download.cn']}]}
        }
      return dict

salt会用yaml去解析返回的这个字典

## 自定义动态garins

salt中自定义的minion ID，一般遵守fqdn规范，以尽可能他提供更多的信息方便管理员进行管理，但是fqdn不是万能的，不一定能包含需要的所有信息，这个时候自定义的grains就有用了

这里自定义了个grain，会根据一个URL返回的值生产一个字典，返回给salt解析

/srv/salt/\_grains/ops\_user.py

    import urllib2

    def ops_user():
      grains = {}
      ops_user = urllib2.urlopen('https://test.com/api/opsuser').read()　　　＃这里放回的是一个以逗号分割的字符串
      ops_user = ops_user.split(',')
      grains['ops_user'] = ops_user
      return grains

    if __name__ == '__main__':
      print ops_user()

然后同步grains，之后所有的minion都会有和这个grain的属性了 saltutil.sync\_grains

不过这里有一个小问题，这个granis是静态值，除非指定节点去刷新，否则grains不会改变

## salt的拓展

salt的master和minion的交互很大程度上都和网络有关系,比如在管理多个国家的机器的时候(比如大中华局域网),这个时候,用一个master来管理,先不说体验上的问题,本身就是不现实的,这个时候怎么搞呢? 分布式

一个master控制多个master,同时被控制的master又可以控制很多的minion

这个时候咱们的问题就好处理的多了,当然不能说完全没有问题

**中心master**

指定开启syndic模式,这样消息才能发送到syndic节点上

    # grep order_masters /etc/salt/master
    order_masters: True

指定为中心master节点,启动syndic服务

**被管理的master**

    # grep syndic_master /etc/salt/master
    syndic_master: salt.lightcloud.cn

    /etc/init.d/salt-syndic start

比如总的master为master,syndic节点为syndic1

将minion1的master制定为syndic,启动minion服务

然后在syndic1节点就可以看到未接受的key,接受后,syndic就可以管理minion1了,同时master也可以管理minion1了

**问题**:key的管理这块,还是仅仅minoin直接连接的节点才可以管理,也就是说刚才minion1的接受key的那个操作,只有在syndic1才可以完成,master是不行的

## salt的用户认证管理

在salt服务器上可以用root来管理所有的minions,使用所有的功能,但是实际生产环境中,机器有很多,不是所有的人都要管理这些机器,就需要把这些机器分给不同的用户进行管理,这里可以使用salt的external\_auth模块来做处理

官方文档:<http://docs.saltstack.com/topics/eauth/index.html>

官方的例子中写的很清晰,比如master配置文件中如下的配置

    external_auth:   #制定启用认证模块
      pam:    #指定所使用的认证模块,还有其他的认证模块可以使用比如ldap
        thatch:  #指定用户名(master服务器的系统用户名)
          - 'web*':   #指定匹配的minion 这里有点操蛋的是,不能使用compund模式
            - test.*   #这里指定了可以使用那些模块,后面是并列的
            - network.*
        steve:
          - .*

这里的这个用户thatch,可以对minion id中以web开头的使用test和network模块的所有功能,而steve这个用户就NB了,可以管理所有的minion,而且可以使用说有的功能

如果在长期业务固化的系统中,这样的设定本来没什么问题,但是在业务快速迭代的系统中,业务会老是变来变去业务的负责人也同样会变来编曲,但是业务的主机名不会经常变化,这样的设定就会有问题,个人认为最好的解决方案应该是基于minion的某些属性来设定权限(可以动态的去管理这些属性);这样在业务变化的时候让这些属性也动态的去变化,权限也就动态的变化了

可是默认的salt不支持这样的功能(已经跟官方反馈,个人认为这个功能在不久的将来会加上);自己也不能干等着,于是我就个所有的minion加另一个ops\_user的属性(方法参考: 自定义动态garins),这里定义完了,怎么用呢?调整external的用户认证如下:

    external_auth:
      pam:
        halfss:
          - '*':
            - '*'
        halfss1:
          - '*':
            - '*'

这里我们看到了,我给了这２个用户halfss　halfss1所有机器的所有权限,如果这样设置的是,基本上对minion的权限管理是废了,但是还有一步,调整下salt的一段代码,如下:

调整用户权限：

    /usr/lib/python2.6/site-packages/salt
    diff client.py client.py_back
    969,971d968
    <         if self.salt_user != 'root':

    <             tgt = '%s and G@ops_user:%s' % (tgt,self.salt_user)

    <             expr_form = 'compound'
    979a977
    >

这样普通用户即使在执行　salt　’\*’　test.ping　的时候也会成功,而且仅仅是有他权限的机器执行,这样我就完成了对minion动态的分配权限.而且还带来一个好处是,普通用户的体验会更好一些,在官方的代码中,如果普通用户没有所有机器的权限,那么他直接这样执行是会报错的,官方代码中(即使是普通用户),"\*"　理解为salt-master中的所有minion,而不是改用户的所有minon(这个跟他的广播机制有关)　这个功能也已经跟官方反馈,他会在0.16中实现这个功能

## minion信息的集中获取

master默认会将minion是信息(pillar和grains)存储在/var/cache/salt/master/minions/下(以minoin　id创建一个目录,该目录下有个data.p的文件);这样的方式并不便于minoin信息是采集与管理(如果有很多的机器,然后获取所有机器的minion信息的时慢的要死,当然这个不能怪salt);我们可以把这些信息都放到一个文件中,便于信息的采集与管理,这里提供对信息统一收集的基础代码,如下:

获取minion的grain及pillar

    /usr/lib/python2.6/site-packages/salt/master.py

                cdir = os.path.join(self.opts['cachedir'], 'minions', load['id'])
                if not os.path.isdir(cdir):
                    os.makedirs(cdir)
                datap = os.path.join(cdir, 'data.p')
    +            file('/var/log/salt/minions','w+').write(str({
    +                                'minion_id':load['id'],
    +                                'grains': load['grains'],
    +                                'pillar': data})+'\n')
                with salt.utils.fopen(datap, 'w+') as fp_:
                    fp_.write(
                            self.serial.dumps(
                                {'grains': load['grains'],

## 自定义salt modules

salt中自定义modules,实在是太简单了,为了让你详细,先来个最简单的

    # cat /srv/salt/_modules/custom.py
    def test():
      return 'i am test'

同步到所有minion

    # salt '*' saltutil.sync_modules

直接就可以使用了

    [root@localhost _modules]# salt '*'  custom.test　　＃调用方法,文件名.方法名
    minion1:
        i am test

这个是最简单的;但是有时候,我们需要实现一些比较复杂的功能,而这些功能有的salt已经帮我们实现了,我们仅仅需要直接拿来用就好了;还有的我们需要使用minion的中grains或者pillar的信息;在有其他的功能,我们就需要自己是实现了,先看看刚才的２个怎么搞

**1. 调用先有的module来显现自定义module中需要的功能**

salt　salt内置的一个字典,包含了所有的salt的moudle

    [root@localhost _modules]# cat /srv/salt/_modules/custom.py
    def test(cmd):
      return __salt__['cmd.run'](cmd)

    [root@localhost _modules]# salt '*'  custom.test ls
    minion1:
        '
        anaconda-ks.cfg
        install.log
        install.log.syslog
        match.py
        salt
        test.py

是不是有点想想不到的简单?

**2. 使用gains中信息**

    [root@localhost _modules]# cat /srv/salt/_modules/custom.py
    def test():
      return  __grains__['id']

    [root@localhost _modules]# salt '*'  custom.test
    minion1:
        minion1

将自定义的modules文件放在配置文件中定义的file\_roots(默认为/srv/salt)下的 \_modules目录下,会在执行highstate的时候自动同步,或者按照如下方式,手工推送

    salt '*' saltutil.sync_modules 或者　salt '*' saltutil.sync_all
