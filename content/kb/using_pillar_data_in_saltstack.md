Title: 【翻译】在SaltStack中使用Pillar
Date: 2013-04-19
Slug: using_pillar_data_in_saltstack
Tags: SaltStack, 进阶
Summary: 在SaltStack中，Pillar作为一个定义minion全局数据的接口，由于pillar数据只会存放在匹配的minion上，所以常用pillar来存放敏感类的数据。 本文将带你学习在SaltStack中如何利用Pillar。

* 原文出处: <http://pengyao.org/using_pillar_data_in_saltstack.html>
* 英文原文: <http://intothesaltmine.org/blog/html/2013/02/28/using_pillar_data_in_saltstack.html>
* 译者: [pengyao](http://pengyao.org/)

Pillar做为一允许你分发定义的全局数据到目标minion上的接口，Pillar的数据只在匹配的minions上有效。 所以该特性使Pillar常常用于存储敏感类数据.

本文通过例子带你了解如何使用和存储Pillar数据.

## /etc/salt/master - Pillar Roots ##

需要在master配置文件中定义*pillar_roots*，其用来指定Pillar data存储在哪个目录,默认是*/srv/pillar*.

    pillar_root:
      base:
        - /srv/pillar

## /srv/pillar/top.sls ##

和State系统一样，需要先定义一个*top.sls*文件作为入口，用来指定数据对哪个minion有效.

    base:
      '*':
        - packages
      'alpha':
        - database

上边的例子定义了*packages*对所有的minion有效，*database*只对名字为'alpha'的minion有效.

## /srv/pillar/packages.sls - Pillar Data 

通过例子*packages*文件定义不同Linux发行版的软件包名字，通过Pillar进行中心控制它们，这样就可以在State文件中引用Pillar数据使State看起来更简单.

    {% if grains['os'] == 'RedHat' %}
    apache: httpd
    {% elif grains['os'] == 'Debian' %}
    apache: apache2
    {% endif %}

## /srv/states/apache.sls - State Data ##

如上，在State文件中将可以引用Pillar数据，是State更为简单. 线面是*apache.sls* State文件例子:

    apache:
      pkg:
        - installed
        - name: {{ pillar['apache'] }}


## /srv/pillar/database.sls - Pillar Data ##

另一个定义Pillar Data的例子是定义服务连接数据库的权限的配置参数:

    dbname: project
    dbuser: username
    dbpass: password
    dbhost: localhost

## website.conf - template ##

    // MySQL settings
    define('DB_NAME', '{{ pillar['dbname'] }}');
    // MySQL database username
    define('DB_USER', '{{ pillar['dbuser'] }}');
    // MySQL database password
    define('DB_PASSWORD', '{{ pillar['dbpass'] }}');
    // MySQL hostname
    define('DB_HOST', '{{ pillar['dbhost'] }}');


## 总结 ##

有许多方法使用Pillar data. 作为另一种基础数据结构，Pillar是优美的. 可以用它定义所有minion上的自定义数据，也可以简单的定义包的名字，或者定义服务凭据(service credentials)，Pillar都可以满足.
