Title: SaltStack初探
Date: 2014-03-09 11:22
Tags: SaltStack, 入门
Slug: salt-first-view
Summary: 转载翻译的一篇saltstack介绍文章，推荐初学者一读

-   文章来源: [http://www.oschina.net/translate/getting-started-salt-stack-other-configuration-management-system-built-python](http://www.oschina.net/translate/getting-started-salt-stack-other-configuration-management-system-built-python)
-   原文: [http://www.linuxjournal.com/content/getting-started-salt-stack-other-configuration-management-system-built-python](http://www.linuxjournal.com/content/getting-started-salt-stack-other-configuration-management-system-built-python)
-   译者: 葱油拌面 Lax

不久前的一天，当我自豪穿着SaltStack 文化衫的时候，我的女儿看到后就当面问我，“Salt Stack 是什么呀？” 于是，我开始了作出了如下的解释，假如你有很多台服务器而且想要操作这些服务器，你也许需要一台一台的登录这些服务器，每次作出一次操作变更。这些操作可能是相当简单的，比如重启他们或者检查他们已经运行了多久，更或者，你想要做些更复杂的事情，比如安装软件和按照你的特殊需求来配置他们，也许你只是想要增加用户并且配置他们的权限。

假如你有百十来台服务器，你应该怎么做？想象一下你每次一台一台的登陆这些服务器，执行同样的命令在这些100台的服务器中并且编辑同一个配置文件，你可以想象吗？这是多么的苦逼！仅仅更新一下用户的密码策划就要用掉数天的时间，并且你可能出现错误的操作，怎么样通过一个命令一次完成所有服务器的操作？怎么解决？答案就是，SaltStack！

和我女儿一样，你也许还没有听说过[SaltStack](http://saltstack.org)，但是你可能比较熟悉[Puppet](http://puppetlabs.com) 和[Chef](http://opscode.com.Salt) 跟他们差不多，但是Salt 是用Python写的，且对于设备的要求是相当轻量级的，使用起来相当容易(在我看来)，Salt 通讯层使用[0MQ](http://www.zeromq.org)，这是使得它很快速。并且它是完全开源的，遵守[Apache2](http://www.apache.org/licenses/LICENSE-2.0)开源协议.拥有一个活跃和高效的开源社区。
目前，他们没有任何计划来发布一个残缺的社区版本或一个功能丰富的商业版本，对于Salt，你当前获得的这个版本是任何人都可以获得的，不论你是否付过钱。当然他们有发行商业版本的计划，不过它将是紧密的社区版本，且通过更多的测试和质量保证，以及相关的培训。

Salt和Puppet Chef 一样可以让你同时在多台服务器上执行命令也包括安装和配置软件。Salt 有两个主要的功能：配置管理和远程执行。

Salt Stack 是一个命令行工具，这里没有任何地方需要你点击你的鼠标，执行的结果也会像字符界面一样反馈到你的屏幕上。这很好吧，它使得事情变得简单，并且很多服务器不需要一个图形界面。(注解：我使用Salt 条款在本文中，他们指的是同一个东西在上下文中)

在本文，Salt 包含两个工具，第一个是远程执行，虽然没有一个清晰的描述，但是假如你想要一个配置管理和远程执行的工具，在Salt中你可以找到很多方法。这可以让你登陆一台主服务器然后同时执行命令在一台或者多台服务器上。使用Salt，你仅仅需要在主服务器上输入命令，它会在每台机器上甚至一个服务器群组执行。

第二，Salt 能够存储配置指令，然后引导其他机器按照这些指令作出动作，如，安装软件，更改软件的配置，反馈这个任务成功执行与否。
接下来，我来演示使用Salt 安装一个额外的包，并且仅仅通过一个命令配置这个包。

## 安装 Salt

Salt 是不断变更的，也许当你读到本文时，有些事情已经改变，你可以在这里找到最新的文档：http://docs.saltstack.com/en/latest/index.html

在安装Salt之前，你需要一些简单的准备工作：

* 一台Linux 服务器
* sudo 或者root密码
* 这台服务器能够连接因特网
* 知道你的服务器的IP地址(可以是公网或私网IP)。

虽然Salt被设计为能够连接多台服务器，但在本文中，你可以在一台服务器上完成这些操作。
使用你的包管理器来安装Salt，你可以根据你系统版本分支找到相关的[安装手册](http://docs.saltstack.org/en/latest/topics/installation/index.html),你也需要sudo或者root权限，来安装和使用salt

使用包管理的好处或者从在线的源代码安装是一个无法结束的争论，根据你的系统版本分支，选择更好的安装方法。
假如你倾向于使用源代码来安装，你可以在Salt 项目Github版本库里找到最新的[Salt源码文件](https://github.com/saltstack/salt).

安装完成Salt-master和salt-minion后，希望一切运行正常且你没有收到错误信息。假如Salt并没有正常运行，你可以在到[SaltStack的邮件列表](http://saltstack.org/learn/#tab-mailinglist)和Salt IRC频道寻求帮助。

## 配置主服务器和从服务器

主服务器和从服务器指的是控制器和被控制的服务器，这个主服务器本质上是中央协调中心对所有的从服务器，从服务器类似client/server配置，这里的主服务器是server，从服务器是client.

### 从服务器配置

在本文中，我配置salt-master和salt-minion 命令在同一台机器上，假如你在配置多台服务器，挑选其中一个为master，剩下的成为minions.根据你的需要来配置master和minion，接下来的我会解释如何配置一台服务器为master和另外的机器为minions.

Salt的配置文件在/etc/salt目录下，默认，这些文件被命名为minion和master，假如你在同一台机器安装了salt-master和salt-minion，你会看到不同的两个文件，master和minion

首先，你需要告诉你的minion怎样找到并连接你的Master服务器。即使你运行minion和Master在同一台服务器上，你仍然要告诉minion你的master在哪儿。

1，使用你最喜欢的文本编辑器，打开minion配置文件

2，取消注释行\#master，移除\# 替换为你的Master服务器的IP地址，应该是这样:master:你的master IP地址。（假如以上操作，在同一台服务器，此时增加 127.0.0.1)

3,命名一个昵称给你的服务器，查找到\#id行，再一次移除\#号，增加一个nameid：1st-salt-minion，（这个名字可以是任何字符串的）

4，为了重新加载新的配置，你需要使用sudo 重启你的salt-minion进程，-d 选项，启动salt-minion为一个后台进程，这样子的话，你可以访问您的命令行发布更多的命令。

### 认证 Minion Keys

现在你的minion 已经知道到master在哪里，接下来让他们进行彼此验证，Salt使用公共密钥加密来确保master和minions的安全通信。你需要通过在master端验证minion的证书来明确master和minion之间的是授信的。

认证minion的证书使用salt-key命令，Salt自动生成这些证书，你需要做的仅仅是认证你需要的证书。

1，输入salt-key -L 列出所以没有认证，认证过，拒绝认证的证书

2，你应该可以看到一个没有认证的证书1st-Salt-Minion（或者你自己选择的minion）

3,认证这个证书使用 sudo salt-key -a 1st-salt-minion

### 通信测试

现在你已经有了一台 salt-master和一台salt-minion，并且master和minion已经相互信任，你可以从master 使用一个test ping的命令来测试他们之间的连接。假如你的master能够连接到minion，将会返回一个“return”.输入’‘’salt ’\*‘ test.ping’’’,它应该有如下输出:

    >{1st-Salt-Minion: True}

注意，通配符 \*代表所有minion，因为这里你只有一台服务器，算是一个简单的模拟测试（要比salt ‘1st-salt-Minion’ test ping 快多了）

假如你收到“True”，证明你已经成功安装和配置完成salt stack。

如果没有的话，你也许需要重启你的master和minion 不带-d参数，这样子的话，你能够获取到更多输出信息，更多的参考资料，请查看Salt 官方文档http://docs.saltstack.org/en/latest/topics/configuration.html

Salt的语法结构，包括命令，目标和动作，举个例子，\* 指任何主机（\* 是一个通配符），test.ping 是动作。

你可以在已经链接和信任的主机上执行任何可用的命令，关键提示:这些需要执行的命令在目标主机上必须可用，例如，如下命令：

    sudo salt '*' cmd.run "service apache2 restart"

这个命令只会在已经安装了apach2e web服务器的主机上执行，另外，你也可以使用这样的命令：

    sudo salt '*' cmd.run "service httpd restart"

另外一个例子，也许你想要查询你的主机已经运行了多长时间，你可以这样子做：

    sudo salt '*' cmd.run "uptime"

在举另外一个例子，假如你的Apache Bench(译者注：一个apche 开源压力测试工具)安装在master上而没有安装在minion上，下面的命令：

    sudo salt '*' cmd.run "ab -n 10 -c 2 http://www.google.com:80/index.html"

如果你尝试在minion上执行，你将会失败，因为Apache Bench 没有安装在minion上。

在这里一切皆有可能，你可以在一个终端中一次重启你所有的机器，升级系统软件或者是检查你的机器状态，而不是像以前一样登陆这些机器一遍一遍的执行这些命令。

你也可以根据你自己的需求，执行一些命令在特定的目标群组上。参考-G 参数，从官网文档中获取更多细节http://saltstack.org

从此以后你不需要再登陆minion，所有的配置和执行能够快速高效的远程执行。

既然你已经安装了Salt并且能够执行一些远程的命令，为什么停步于此那？

## Salt的强大源自于配置管理工具

假如你之前没有使用过其他的配置管理系统，下面是一个简单的例子，比如说你有一组配置和相关的包，需要安装在每个WEB服务器上。你保留这些配置指令在一个文本文件中，然后引导你的服务器以你需要的方式安装和配置他们，每次你创建一个新的服务器。你也可以使用配置管理来保持你所有的服务器更新,一旦他们被创造和变化的反馈到新的包装或配置
安装了lib pam-crack 包，你可以有添加额外的要求用户密码。之所以选择这个包，是因为它对所有连接到因特网的服务器是有用的。它允许你设置一个额外长度的密码，并且会要求你密码中包含特殊字符或者数字，你也可以比较容易的选择特殊的包。但是这些包和例子必须在你的系统中可用。

### 配置指令的存储

一般来讲，Salt的配置管理指令和文件保存在/srv/salt目录下，这里存放着所有的配置文件，和一些你想要拷贝到从服务器的文件。Salt的特点之一是包含一个文件服务器。虽然Salt不会在你的主服务器创建系统文件，但是所有的配置管理发生在/srv/salt目录中。

默认，Salt使用PyAMl语法(http://pyyaml.org) 作为它的模板文件的格式，但是其他很多模板语言在Salt中是可以使用的。一定要按照正确的格式书写YAML,比如它使用到两个空格代替tab。如果YAML文件出现不可预知的错误，你可以使用一个在线的debug工具(http://yaml-online-parser.appspot.com )。

### 启动配置管理

在启动配置管理功能之前，你需要再一次编辑你的master配置文件，在/etc/salt下。打开master配置文件，找到file\_roots行，缺省配置文件中，这一行在第156行。现在，取消注释即删除\#号，配置如下：

    file_roots:
      base:
        - /srv/salt

这样子就可以告诉Salt你的配置管理文件在哪里。根据你是如何安装Salt，有时你需要自己创建/srv/salt目录

### 创建一个Top文件/Roadmap

基础配置文件也叫做Top文件，在/srv/salt目录下。我们来创建这个文件。这个文件提供了其它文件的映射。可以用于作为其它服务器的基础配置文件。再次使用你最喜欢的编辑器，在/srv/salt目录创建一个top.sls文件。你可以把它作为指向不同目录的路线图。在top.sls中加入一下行：

    base:
      '*':
        - servers

base语法告诉Salt这是基础配置文件，可以应用在所有机器上。通配符’\*‘的目标是所有机器。’- servers’指令可以是任意值，运行你识别哪些质量可以使用。再选择一些其它有用的配置。这个条目还指向一个特别的配置，用于安装libpam-cracklib。

### 创建一个特定服务器的配置文件

保存top.sls后，在/srv/salt目录下创建servers.sls文件。这个文件包含特定的配置，包括安装包的名称，也可指向另外的配置文件。在servers.sls中，加入如下行：

    libpam-cracklib:
      pkg:
        - installed

第一行是包管理工具可识别的软件包名称。以Apache HTTP server为例，在基于apatitude的包管理中叫做apache2，而在基于yum的包管理中叫做httpd。确保针对包管理工具使用正确的名字。也可以使用Salt的grains进行包管理。查看参考文档以获得更多信息，以及在SLS文件使用grains的例子(http://salt.readthedocs.org/en/latest/topics/tutorials/states\_pt3.html\#using-grains-in-sls-modules).

第2和第3行告诉Salt如何处理这个包——本例是安装这个包。要删除一个包，你只需要修改’- installed’为’- removed’即可。记住，空格很重要！第二行’pkg:‘前有两个空格，第三行’- installed’前有四个空格。如果遇到任何错误，请通过在线YAML解析器检查语法。

### 特定包的配置文件

安装libpam-cracklib包，你仅仅需要写三行配置即可。到此时的话，默认包管理器会安装libpam-cracklib包。然后您将需要登录到计算机上安装和配置它为您的特定需求。即使安装失败，Salt也会提供一个好的方案来解决。

Salt作为一个安全文件服务器，并把文件拷贝到远程的从服务器上。在servers.sls增加如下行：

    /etc/pam.d/common-password:
      file:
        - managed
        - source: salt://servers/common-password
        - require:
          - pkg: libpam-cracklib

注意第四行，它告诉Salt你的特殊文件的位置，这一行后面的行，即第5行，告诉Salt这个包的依赖包。
这行salt://映射到你的主服务器/srv/salt目录。

保存了server.sls文件后，在/srv/salt 目录下创建servers目录。这里用来存储libpam-cracklib包的配置文件。

当你在安装软件和配置文件的时，有时候你想要在测试服务器上先行安装，然后以你的需要配置。你可以拷贝配置文件到/srv/salt目录，这样子，你可以在部署到生成环境之前测试他们。
现在你的配置测试通过，现在你可以把配置文件随着安装libpam-cracklib 分发到每天从机器上了。/srv/salt 目录应该如下：

    /srv/salt
        top.sls
        servers.sls
        /servers
           common-password

这里我把libpam-cracklib的配置作为一个例子，所有的其他软件配置都和这样差不多。例如，你可以比较容易的通过修改httpd.conf 来实现虚拟主机和主机头的配置。

所有的sls文件准备好以后，最后一步是告诉Salt配置远程机器。state.highstate 是触发这些同步的命令。使用先前的语法格式，目标位所有机器，键入以下格式的命令：

    sudo salt '*' state.highstate

片刻后，从服务会反馈像如下成功的信息：

    >>
      State: - pkg
      Name:      libpam-cracklib
      Function:  installed
          Result:    True
          Comment:   Package libpam-cracklib installed
          Changes:   wamerican: {'new': '7.1-1', 'old': ''}
                     cracklib-runtime: {'new': '2.8.18-3build1', 'old': ''}
                     libcrack2: {'new': '2.8.18-3build1', 'old': ''}
                     libpam-cracklib: {'new': '1.1.3-7ubuntu2', 'old': ''}

    ----------
      State: - file
      Name:      /etc/pam.d/common-password
      Function:  managed
          Result:    True
          Comment:   File /etc/pam.d/common-password updated
          Changes:   diff: ---
    +++
    @@ -22,7 +22,7 @@
     # pam-auth-update(8) for details.

     # here are the per-package modules (the "Primary" block)
    -password   requisite   pam_cracklib.so retry=3 minlen=8 difok=3
    +password   requisite   pam_cracklib.so retry=3 minlen=14 difok=3 dcredit=1 ucredit=1 lcredit=1 ocredit=1
     password   [success=1 default=ignore]   pam_unix.so obscure use_authtok try_first_pass sha512
     # here's the fallback if no module succeeds
     password   requisite   pam_deny.so

如你所见，Salt成功安装了libpam-cracklib并且从主服务器下载了一个common-password到从服务器的/etc/pam.d/ 目录。

本例中只有一台从服务器，相对来说是一个简单的例子，但是想象一下，假如你使用Salt配置管理安装了LAMP web服务器，你省了多长时间呀。把这些配置放在文本文件中，使得你快速高效的创建同样的服务器。

## 总结

现在你有能力一次在很多台机器上执行远程命令并且能够把配置文件存储在易维护的文本中。也可以安装特殊的软件包。

刚开始的时候，多花点心思。您可以根据自己的特定配置创建一个或多个服务器，并且下载不同的包到每台机器上。Salt 也可以不按顺序执行，有些命令会同时执行，假如其中一台执行失败，其他依然不受影响继续执行。

虽然在安装Salt比较费时，但是你以后会得到极大的好处，特别是可以让你创建特定的服务器和可重复使用的配置。

访问Salt项目得到更多的细节，多关注邮件列表和用户文档以及一些例子。你会发现社区会非常热心的帮助你处理问题。