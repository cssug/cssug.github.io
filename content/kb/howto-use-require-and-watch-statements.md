Title: 在SaltStack中如何使用require及watch语法
Date: 2014-03-16 18:40
Tags: SaltStack, 入门
Slug: howto-use-require-and-watch-statements
Summary: pengyao翻译的<在SaltStack中如何使用require及watch语法>

* 原文出处: <http://pengyao.org/howto_to_use_require_and_watch_statements.html>
* 英文原文出处: <http://intothesaltmine.org/how_to_use_require_and_watch_statements.html>
* 译者: [pengyao](http://pengyao.org/)

在SaltStack配置关系系统中支持许多强大的选项。无论是简单的如软件包的安装还是使用模板和条件语句. SaltStack States可以从小巧逐步变得很复杂。幸运的是SaltStack提供一种用于解决States间依赖关系的方法. 本小节将讲述如何使用 `require`、@require_in@、@watch@、@watch_in@

## Requisites

在SaltStack的世界中，requisites(译者注: 该词没找到合适的中文翻译，暂时使用英文原词)有两种类型，直接的requisites和&quot;requisite_ins&quot;。这些requisites是方向性的(directional)，用于指定说&quot;我依赖于某些东西&quot;或&quot;一些东西依赖于我&quot;

### require

下边是使用 `require` 语法的例子:

    vim:
      pkg.installed

    /etc/vimrc:
      file.managed:
        - source: salt://edit/vimrc
        - require:
          - pkg: vim

在这个例子中， `/etc/vimrc` 文件并不会被placed(managed)，直到 `vim` 软件包已安装

### require_in

下边是同样的例子，只是这次使用了 `require_in` :

    vim:
      pkg.installed:
        - require_in:
          - file: /etc/vimrc

    /etc/vimrc:
      file.managed:
        - source: salt://edit/vimrc

这个例子的效果是相同的，在 `vim` 中指定了 `/etc/vimrc` 依赖于我

在最后，将会创建一个从属(dependency)map，并以有限的(finite)及可预见的(predictable)顺序执行.

### watch

下面将以 `watch` 语法举例，在本例中，运行中的 `ntpd` 服务将会关注 `/etc/ntp.conf` 文件的变化，如果发生变化，将会触发重启服务的操作.

    ntpd:
      service.running:
        - watch:
          - file: /etc/ntp.conf

    /etc/ntp.conf:
      file.managed:
        - source: salt://ntp/files/ntp.conf

### watch_in

在接下来例子中， `/etc/ntp.conf` 声明(declaring)它应该被 `ntpd` 服务watch

    ntpd:
      service.running

    /etc/ntp.conf:
      file.managed:
        - source: salt://ntp/files/ntp.conf
        - watch_in:
          - service: ntpd

## 总结(Conclusion)

在State规则中，你可以通过强大的 `require` 、 `require_in` 、 `watch` 及 `watch_in` 指定state间的依赖关系. 无论是一个服务应该watch一个文件的变化，还是一个服务运行前必须确保软件包已安装都可以通过它们来指定state的逻辑执行顺序.
