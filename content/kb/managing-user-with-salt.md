Title: 使用Salt管理用户
Date: 2014-03-16 18:35
Tags: SaltStack, 入门
Slug: managing-user-with-salt
Summary: pengyao翻译的使用<Salt管理用户>

* 原文出处: <http://pengyao.org/managing_user_with_salt.html>
* 英文原文出处: <http://intothesaltmine.org/blog/html/2012/12/11/managing_users_with_salt.html>
-   译者: [pengyao](http://pengyao.org/)


使用Salt在多平台进行用户管理将变得非常简单。 user模块允许管理员管理(原文为present)账户各个方面和删除(absent)账户。本篇文章将描述user模块的各个组件，并将给出一个管理账户的state例子.

## user.present

*user.present*: 确保指定的账户名存在,并指定其对应的属性. 这些属性包括如下内容:

**name**: 指定需要管理的账户名.

**uid**: 指定uid, 如果不设置将配自动分配下一个有效的uid.

**gid**: 指定默认的组id(group id)

**gid_from_name**: 如果设置为_True_，默认的组id将自动设置为和本用户同名的组id

**groups**: 分配给该用户的组列表(a list of groups). 如果组在minion上不存在，则本state会报错. 如果设置会空，将会删除本用户所属的除了默认组之外的其他组

**optional_groups**: 分配给用户的组列表。 如果组在minion上不存在，则state会忽略它.

**home**: 关于用户的家目录(home directory).

**password**: 设置用户hash之后的密码.

**enforce_password**: 当设置为_False_时，如果设置的_password_与用户原密码不同，将保持原密码不做更改.如果没有设置_password_选项，该选项将自动忽略掉.

**shell**: 指定用户的login shell。 默认将设置为系统默认shell。

**unique**: UID唯一，默认为True.

**system**: 从_FIRST_SYSTEM_UID_和_LAST_SYSTEM_UID_间选择一个随机的UID.

------------------------------------------------------------------------

用户描述选项(GECOS)支持(当前只支持Linux和FreeBSD系统):

**fullname**: 指定用户全名(full name).

**roomnumber**: 指定用户的房间号.

**workphone**: 指定用户的工作电话号码.

**homephone**: 指定用户的家庭电话号码.

## user.absent

-   本部分为译者依据官方手册进行的补充，原文中并没有相关内容

*user.absent* 用于删除用户.其有以下选项:

**name**: 指定需要删除的用户名.

**purge**: 设置清除用户的文件(家目录)

**force**: 如果用户当前已登录，则absent state会失败. 设置_force_选项为True时，就算用户当前处于登录状态也会删除本用户.

当管理用户时，至少需要指定_user.present_或_user.absent_。 其他选项是可选的，比如_uid_、_gid_、_home_等选项没有指定是，将自动使用下一个有效的或者系统默认的.

## users.sls

下面将列出一个管理_cedwards_用户的state声明例子. 本state中定义了_fullname_、_shell_、_home_、_uid_、_gid_和_groups_列:

    cedwards:
      user.present:
        - fullname: Christer Edwards
        - password: '$6$JyhDBiOi5ZyvaDWm$.5QKIgCtYOLXpLDCc9HMJ8fnAq.c3enJ32BIWGcuKt/y2awHL3w2PlNLxJD9gHE/FtKkG348P8HArXGSkd5uC/'
        - shell: /usr/local/bin/bash
        - home: /home/cedwards
        - uid: 1001
        - gid: 1001
        - groups:
          - wheel

    jdoe:
      user.absent

(尽管本例中指定的密码并不是我真实的密码，不过例子中出现的密码hash串并不是一个好主意)
