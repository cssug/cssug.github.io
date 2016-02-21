Title: Salt Runners manage学习
Date: 2014-03-16 19:26
Tags: SaltStack, 进阶
Slug: salt-runners-manage-01
Summary: pengyao分享的<Salt Runners manage学习>

* 原文出处: <http://pengyao.org/salt_runners_manage_01.html>
* 作者: pengyao

-   Salt Runners manage手册:
    <http://docs.saltstack.com/ref/runners/all/salt.runners.manage.html?highlight=manage#salt.runners.manage>
-   Salt Runners manage源码:
    <https://github.com/saltstack/salt/blob/develop/salt/runners/manage.py>

下午灿哥在群里边分享了`salt-run
manage.status`的用法，用于检查minion当前是否存活(可连接).
这个功能果然不错，索性就打开对应的源码，对manage所有的方法进行一次学习

-   版本: 0.16.3

## status

-   使用方法: `salt-run manage.status`
-   功能: 输出所有已知的minions的状态, 以up和down分组输出
-   核心代码及补充的代码说明:

<!-- -->

    client = salt.client.LocalClient(__opts__['conf_file'])
    minions = client.cmd('*', 'test.ping', timeout=__opts__['timeout'])   #利用client.cmd对所有的minion发送test.ping指令,用于探测minion是否存活
    key = salt.key.Key(__opts__)
    keys = key.list_keys()                  # 利用salt.key获取当前master上有多少minion的key，即获取到完整的minion列表

    ret = {}
    ret['up'] = sorted(minions)         # 将执行test.ping有返回值的minion即存活的minion的ID放入up中
    ret['down'] = sorted(set(keys['minions']) - set(minions))   #完整的minion列表减去存活的minion就是down掉/无法连接的minion喽
    if output:
        salt.output.display_output(ret, '', __opts__)    # 输出
    return ret

-   总结: 该方法果然很给力，从此妈妈再也不担心不知道minion是否存活喽

## key_regen

-   使用方法: `salt-run manage.key_regen`
-   功能: 重新生成环境下的所有key (副作用甚强，慎用，慎用,
    除非你知道在做什么)
-   核心代码及补充的代码说明:

<!-- -->

    minions = client.cmd('*', 'saltutil.regen_keys')     # 执行saltutil.regen_keys，重新生成key

-   总结： 慎用，慎用，慎用

## down

-   使用方法: `salt-run manage.down`
-   功能: 输出down掉/无法连接的minion
-   核心代码及补充的代码说明:

<!-- -->

    ret = status(output=False).get('down', [])   # 直接用之前的status方法，然后获取down的minion列表

-   总结:
    函数编程果然是王道，省时省力，直接通过该方法查询down掉的minion，再也不麻烦了

## up

-   使用方法: `salt-run manage.up`
-   功能: 输出存活的minion
-   核心代码及补充的代码说明:

<!-- -->

    ret = status(output=False).get('up', [])   # 和上边直接down一样，不过这次的需求变成了up而已

-   总结: 和楼上类似

## versions

-   使用方法: `salt-run manage.versions`
-   功能: 输出所有存活的minion的版本和master的版本对比情况
-   核心代码及补充的代码说明:

<!-- -->

    minions = client.cmd('*', 'test.version', timeout=__opts__['timeout'])  # 通过client.cmd方法下发所有minion需要执行test.version(输出版本号)的指令

    labels = {                        # 定义版本对比的描述
        -1: 'Minion requires update',
        0: 'Up to date',
        1: 'Minion newer than master',
    }

    version_status = {}

    comps = salt.__version__.split('-')    # 获取master version
    if len(comps) == 3:
        master_version = '-'.join(comps[0:2])
    else:
        master_version = salt.__version__
    for minion in minions:
        comps = minions[minion].split('-')
        if len(comps) == 3:
            minion_version = '-'.join(comps[0:2])
        else:
            minion_version = minions[minion]
        ver_diff = cmp(minion_version, master_version)   # 通过python的cmp方法对版本号进行对比

        if ver_diff not in version_status:
            version_status[ver_diff] = []
        version_status[ver_diff].append(minion)

    ret = {}
    for key in version_status:
        for minion in sorted(version_status[key]):
            ret.setdefault(labels[key], []).append(minion)

    salt.output.display_output(ret, '', __opts__)
    return ret

-   总结: 利用本方法，哪些minion需要升级立马得知，谁用谁知道啊!
