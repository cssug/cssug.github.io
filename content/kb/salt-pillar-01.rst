Salt中Pillar那点事
#####################

:date: 2014-06-08
:tags: SaltStack, 进阶
:slug: salt-pillar-01
:author: pengyao
:summary: 在 `SaltStack`_ 中, Pillar作为定义minion全局数据的接口. 那么在Salt内部, Pillar是如何工作的? 在哪些情况下, 使用Pillar需要先执行刷新操作? 而哪些又不需要?

* 原文出处: `http://pengyao.org/salt-pillar-01.html <http://pengyao.org/salt-pillar-01.html>`_
* 作者: `pengyao <http://pengyao.org/>`_

基本简介
****************

在 `SaltStack`_ 中, Pillar作为定义minion全局数据的接口. 默认存储在master端, Minion启动时会连接master获取最新的pillar数据. Pillar使用类似于State Tree的结构, 默认使用 `YAML` 作为其描述格式, 在Minion内部最终转换成 `Python字典 <https://docs.python.org/2/tutorial/datastructures.html#dictionaries>`_ .

那么在Salt内部, Pillar是如何工作的? 在哪些情况下,需要先执行刷新Pillar操作? 而哪些又不需要?

本文基于 `Salt 2014.1.4 <http://docs.saltstack.com/en/latest/topics/releases/2014.1.4.html>`_

配置文件中的Pillar
*********************

pillar_roots
  存在于master/minion配置文件中. 指定Pillar roots对应环境的目录, 其布局类似于State Tree. 在minion配置文件中配置该选项, 只有当 *file_client* 为 *local* 时才生效.

state_top
  存在于master/minion配置文件中, 默认值为top.sls. 官方描述为用于state system, 用于告诉minion使用哪个环境并且需要执行哪些模块. 其实该选项也应用在pillar system中, 作用和state system类似. 所以如果更改了本选项, pillar system对应的top.sls也需要变更. 在minion配置文件中配置该选项, 只有当 *file_client* 为 *local* 时才生效.

file_client
  存在于minion配置文件中, 默认值为remote. 用于指定去哪里查找文件. 有效值是 *remote* 和 *local*. *remote* 表示使用master, *local* 用于 `Masterless <http://docs.saltstack.com/en/latest/topics/tutorials/quickstart.html#telling-salt-to-run-masterless>`_ 的情况. 

pillar_opts
  存在于master配置文件中, 默认值为True. 指定是否将master配置选项作为pillar. 如果该选项为True, 修改了master配置选项时, 需要重启master, 才能在pillar中得到最新的值. 

Minion中的Pillar实现
***********************

Minion中pillar为Python字典, Minion启动时, 默认会连接master获取最新的pillar数据, 存储在 *self.opts['pillar']* 中. `对应代码 <https://github.com/saltstack/salt/blob/v2014.1.4/salt/minion.py#L520>`__ 如下:

.. code-block:: python

  class Minion(MinionBase):
      '''
      This class instantiates a minion, runs connections for a minion,
      and loads all of the functions into the minion
      '''
      def __init__(self, opts, timeout=60, safe=True):
          '''
          Pass in the options dict
          '''
          ......
          self.opts['pillar'] = salt.pillar.get_pillar(
              opts,
              opts['grains'],
              opts['id'],
              opts['environment'],
          ).compile_pillar()
          ......

那么 *salt.pillar.get_pillar* 是如何工作的? `对应代码 <https://github.com/saltstack/salt/blob/v2014.1.4/salt/pillar/__init__.py#L28>`__ 如下:

.. code-block:: python

  def get_pillar(opts, grains, id_, saltenv=None, ext=None, env=None):
      '''
      Return the correct pillar driver based on the file_client option
      '''
      if env is not None:
          salt.utils.warn_until(
              'Boron',
              'Passing a salt environment should be done using \'saltenv\' '
              'not \'env\'. This functionality will be removed in Salt Boron.'
          )
          # Backwards compatibility
          saltenv = env

      return {
              'remote': RemotePillar,
              'local': Pillar
              }.get(opts['file_client'], Pillar)(opts, grains, id_, saltenv, ext)

也可以从代码中获知, 会从opts中获取 *file_client* 值, 如果是remote, 则对应的对象为RemotePillar, 如果是local, 则为Pillar, 进行后续处理

如果Minion在运行过程中, 接受到的指令以 *refresh_pillar* 字符串开头, 则执行 *pillar_refresh* 操作. `对应代码 <https://github.com/saltstack/salt/blob/v2014.1.4/salt/minion.py#L1376>`__ 如下:

.. code-block:: python

  if package.startswith('module_refresh'):
      self.module_refresh()
  elif package.startswith('pillar_refresh'):
      self.pillar_refresh()

那么 *pillar_refresh()* 都进行了哪些工作? `对应代码 <https://github.com/saltstack/salt/blob/v2014.1.4/salt/minion.py#L1090>`__ 如下:

.. code-block:: python

  def pillar_refresh(self):
      '''
      Refresh the pillar
      '''
      self.opts['pillar'] = salt.pillar.get_pillar(
          self.opts,
          self.opts['grains'],
          self.opts['id'],
          self.opts['environment'],
      ).compile_pillar()
      self.module_refresh()

从代码中得知, pillar_refresh操作, 除了从Master端/Minion本地获取最新的pillar信息外, 也会执行模块刷新(module_refresh)工作. 可以将minion本地的日志级别调整为 *trac*, 然后执行 *saltutil.refresh_pillar* 操作, 然后观察minion日志, 是否会刷新模块进行验证.

Target中的Pillar
*********************

Salt指令发送底层网络, 采用ZeroMQ PUB/SUB结构. Minion会监听SUB接口, Master会将指令发送到本地的PUB接口, 然后所有Minion均会收到该指令, 然后在Minion本地判断自己是否需要执行该指令(即Target). 当前版本中, 已经支持pillar作为Target(通过"-I"选项指定). `对应代码 <https://github.com/saltstack/salt/blob/v2014.1.4/salt/minion.py#L1809>`__ 如下:

.. code-block:: python

  def pillar_match(self, tgt, delim=':'):
      '''
      Reads in the pillar glob match
      '''
      log.debug('pillar target: {0}'.format(tgt))
      if delim not in tgt:
          log.error('Got insufficient arguments for pillar match '
                    'statement from master')
          return False
      return salt.utils.subdict_match(self.opts['pillar'], tgt, delim=delim)

可以看出, 其匹配使用的是 *self.opts['pillar']* 即当前Minion内存中的Pillar的数据. 因此如果在Master/Minion(当 *file_client* 为 *local* 时)修改了Pillar数据后, 想要使用最新的Pillar来做Target操作, 需要在执行前先手动执行 *saltutil.refresh_pillar* 操作, 以刷新Minion内存中的Pillar数据.

远程执行模块中的Pillar
*************************

pillar.items
^^^^^^^^^^^^^^^^^

`对应代码 <https://github.com/saltstack/salt/blob/v2014.1.4/salt/modules/pillar.py#L42>`__ 如下:

.. code-block:: python

  pillar = salt.pillar.get_pillar(
      __opts__,
      __grains__,
      __opts__['id'],
      __opts__['environment'])

  return pillar.compile_pillar()


会连接Master/Minion(当 *file_client* 为 *local* 时)获取最新的pillar数据并返回. 但并不会刷新Minion本地的缓存. 也就是说, 在master端修改了Pillar Tree, 在刷新pillar(saltutil.refresh_pillar)前, 可以先使用 *pillar.items* 来验证其数据是否达到预期.

pillar.data
^^^^^^^^^^^^^^^^^

`对应代码 <https://github.com/saltstack/salt/blob/v2014.1.4/salt/modules/pillar.py#L67>`__ 如下:

.. code-block:: python

  data = items

只是创建了一个赋值引用, 指定data和执行items一样

pillar.item
^^^^^^^^^^^^^^^^^^

`对应代码 <https://github.com/saltstack/salt/blob/v2014.1.4/salt/modules/pillar.py#L70>`__ 如下:

.. code-block:: python

  ret = {}
  pillar = items()
  for arg in args:
      try:
          ret[arg] = pillar[arg]
      except KeyError:
          pass
  return ret

先使用pillar.items来获取最新的Master端最新的pillar数据. 然后一个for循环, 从items获取所需要的keys对应的值. 所以item可以查询多个key.

pillar.raw
^^^^^^^^^^^^^^^^^

`对应代码 <https://github.com/saltstack/salt/blob/v2014.1.4/salt/modules/pillar.py#L93>`__ 如下:

.. code-block:: python

  if key:
      ret = __pillar__.get(key, {})
  else:
      ret = __pillar__

  return ret

从当前Minion本地获取 __pillar__ (self.opts[pillar])的值. 也就是说使用 *pillar.raw* 与 *pillar.items* 不同, 获取到的是Minion内存中的pillar的值, 并非是master端定义的值. 如果指定了key, 则返回对应key的值. 如果没有, 则返回整个 __pillar__

pillar.get
^^^^^^^^^^^^^^^^

`对应代码 <https://github.com/saltstack/salt/blob/v2014.1.4/salt/modules/pillar.py#L16>`__ 如下:

.. code-block:: python

  return salt.utils.traverse_dict(__pillar__, key, default)

和 *pillar.raw* 工作方式类似, 是从 __pillar__ 中进行的取值, 用于获取pillar中对应的key值. 与 pillar.raw执行key不同的是, get递归获取内嵌字典的值(默认以":"做分隔). 从最新develop分支中看, 下一个版本(Helium)中将增加merge功能.

pillar.ext
^^^^^^^^^^^^^

与pillar.items工作方式类似, 用于获取ext pillar的值

saltutil.refresh_pillar
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`对应代码 <https://github.com/saltstack/salt/blob/v2014.1.4/salt/modules/saltutil.py#L335>`__ 如下:

.. code-block:: python

  __salt__['event.fire']({}, 'pillar_refresh')

在Minion本地Event接口上产生一个 *pillar_refresh* event. 之前在Minion中的Pillar中, Minion本地会监听本地Event接口, 如果捕捉到以 *pillar_refresh* 开始的指令, 会刷新本地pillar.


配置管理中的Pillar
***********************

在SLS中使用Pillar
^^^^^^^^^^^^^^^^^^^^

在SLS中, 可以直接使用pillar. 如pillar['pkg'], 其直接使用的是Minion当前内存中pillar的值(self.opts['pillar']). 

state.sls & state.highstate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

将这两个远程执行模块方法放到配置管理中, 因为其功能是用于向Minions发送配置管理指令.

state.sls及state.highstate在代码中, 均为 `salt.state.HighState <https://github.com/saltstack/salt/blob/v2014.1.4/salt/state.py#L2574>`_ 对象. 在执行时为 `State <https://github.com/saltstack/salt/blob/v2014.1.4/salt/state.py#L526>`_ 对象. State类在实例化时,则会刷新pillar, `对应代码 <https://github.com/saltstack/salt/blob/v2014.1.4/salt/state.py#L530>`__ 如下:

.. code-block:: python

  class State(object):
      '''
      Class used to execute salt states
      '''
      def __init__(self, opts, pillar=None, jid=None):
          if 'grains' not in opts:
              opts['grains'] = salt.loader.grains(opts)
          self.opts = opts
          self._pillar_override = pillar
          self.opts['pillar'] = self._gather_pillar()

而_gather_pillar `对应代码 <https://github.com/saltstack/salt/blob/v2014.1.4/salt/state.py#L544>`__ 如下:

.. code-block:: python

  def _gather_pillar(self):
      '''
      Whenever a state run starts, gather the pillar data fresh
      '''
      pillar = salt.pillar.get_pillar(
              self.opts,
              self.opts['grains'],
              self.opts['id'],
              self.opts['environment'],
              )
      ret = pillar.compile_pillar()
      if self._pillar_override and isinstance(self._pillar_override, dict):
          ret.update(self._pillar_override)
      return ret

_gather_pillar从Master上获取Minion对应的最新pillar数据, __init__方法中的 *self.opts['pillar'] = self._gather_pillar()* 将该数据赋值给self.opts['pillar']以完成Minion本地内存中Pillar数据的刷新操作. 这就是为什么修改了Master上的Pillar的值, 而无需执行刷新操作(saltutil.refresh_pillar), 因为在执行state.highstate及state.sls时会自动应该最新的值.

ext_pillar
***************

Salt支持从第三方系统中获取Pillar信息,使Salt易于与现有的CMDB系统进行数据整合. 对应的配置是master配置文件中的ext_pillar选项. 官方当前已经提供了 `若干驱动 <http://docs.saltstack.com/en/latest/ref/pillar/all/>`_ . 

如果已经提供的驱动并不满足需求, 自定义ext_pillar驱动也非常简单. 只需要驱动文件放到master端salt代码中pillar目录下即可, 驱动为python代码, 其中包含ext_pillar函数, 且该函数第一个参数是minion_id, 第二个参数为pillar, 其返回值是一个标准的 `Python字典`_ 即可. 可以参照 `cobbler的ext_pillar <https://github.com/saltstack/salt/blob/v2014.1.4/salt/pillar/cobbler.py>`_ 进行编写.

.. _SaltStack: http://saltstack.com/
.. _YAML: http://yaml.org/
