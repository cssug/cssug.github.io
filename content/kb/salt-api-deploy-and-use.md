Title: Salt-API安装配置及使用
Date: 2014-03-09 15:21
Tags: SaltStack, 进阶
Slug: salt-api-deploy-and-use
Summary: pengyao分享的《Salt-API安装配置及使用》文章

* 原文出处: <http://pengyao.org/salt-api-deploy-and-use.html>
* 作者: [pengyao](/pengyao)


[SaltStack](http://saltstack.com/) 官方提供有REST API格式的
[salt-api](https://github.com/saltstack/salt-api)
项目，将使Salt与第三方系统集成变得尤为简单。本文讲带你了解如何安装配置Salt-API,
如何利用Salt-API获取想要的信息。

## 前置阅读

-   [salt-api手册](http://salt-api.readthedocs.org/en/latest/)
-   [Salt External Authentication
    System](http://docs.saltstack.com/topics/eauth/index.html)

## 环境说明

-   操作系统环境: CentOS 6.4，已配置EPEL源
-   Salt Master/Minion版本: 0.17.2, Master IP地址为 *192.168.3*,
    用于本次测试的Minion ID为 *minion-01.example.com*

## 开工

Note

以下操作如非特别注明，均在Master上进行

### 安装Salt-API

Note

当前EPEL中的salt-api版本为0.8.2, 存在几处bug,
本文讲使用pip方式安装0.8.3版本

    # 安装salt-api
    pip install salt-api

    # 下载服务维护脚本
    wget https://raw.github.com/saltstack/salt-api/develop/pkg/rpm/salt-api -O /etc/init.d/salt-api
    chmod +x /etc/init.d/salt-api
    chkconfig salt-api on

### 配置Salt-API

#### 生成自签名证书(用于ssl)

    cd  /etc/pki/tls/certs
    # 生成自签名证书, 过程中需要输入key密码及RDNs
    make testcert
    cd /etc/pki/tls/private/
    # 解密key文件，生成无密码的key文件, 过程中需要输入key密码，该密码为之前生成证书时设置的密码
    openssl rsa -in localhost.key -out localhost_nopass.key

#### Salt-API配置

-   创建用于salt-api的用户

<!-- -->

    useradd -M -s /sbin/nologin pengyao
    echo "pengyao_pass" | passwd pengyao —stdin

-   配置eauth, */etc/salt/master.d/eauth.conf*

<!-- -->

    external_auth:
      pam:
        pengyao:
          - .*

-   配置Salt-API, */etc/salt/master.d/api.conf*

<!-- -->

    rest_cherrypy:
      port: 8000
      ssl_crt: /etc/pki/tls/certs/localhost.crt
      ssl_key: /etc/pki/tls/private/localhost_nopass.key

-   启动Salt-API

<!-- -->

    service salt-api start

Salt-API使用
------------

-   测试工具为操作系统自带的 *curl*

### Login

-   Request

<!-- -->

    curl -k https://192.168.38.10:8000/login -H "Accept: application/x-yaml" \
         -d username='pengyao' \
         -d password='pengyao_pass' \
         -d eauth='pam'

-   Response

<!-- -->

    return:
    - eauth: pam
      expire: 1385579710.806725
      perms:
      - .*
      start: 1385536510.8067241
      token: 784ee23c63794576a50ca5d3d890eb71efb0de6f
      user: pengyao

其中 *token*
后边的串为认证成功后获取的token串，之后可以不用再次输入密码，直接使用本Token即可

### 查询Minion(minion-01.example.com)的信息

-   Request

<!-- -->

    curl -k https://192.168.38.10:8000/minions/minion-01.example.com \
         -H "Accept: application/x-yaml" \
         -H "X-Auth-Token: 8e211da5d6bbb51fbffe6468a3ca0c6a24b3e535"

其中 *X-Auth-Token* 后边的串为之前Login获取到的Token串,
如果请求的URL不包含 *minion-01.example.com* ，则请求的为所有Minion的信息

-   Response

<!-- -->

    return:
    - minion-01.example.com:
        cpu_flags:
        - fpu
        - vme
        - de
        ......

### job管理

#### 获取缓存的jobs列表

-   Request

<!-- -->

    curl -k https://192.168.38.10:8000/jobs/ \
         -H "Accept: application/x-yaml" \
         -H "X-Auth-Token: 8e211da5d6bbb51fbffe6468a3ca0c6a24b3e535"

-   Response

<!-- -->

    return:
    - '20131127065003726179':
        Arguments: []
        Function: test.ping
        Start Time: 2013, Nov 27 06:50:03.726179
        Target: '*'
        Target-type: glob
        User: sudo_vagrant

#### 查询指定的job

-   Request

<!-- -->

    curl -k https://192.168.38.10:8000/jobs/20131127065003726179 \
         -H "Accept: application/x-yaml" \
         -H "X-Auth-Token: 8e211da5d6bbb51fbffe6468a3ca0c6a24b3e535"

-   Response

<!-- -->

    return:
    - minion-01.example.com: true

### 远程执行模块

-   Request

<!-- -->

    curl -k https://192.168.38.10:8000/ \
         -H "Accept: application/x-yaml" \
         -H "X-Auth-Token: 8e211da5d6bbb51fbffe6468a3ca0c6a24b3e535" \
         -d client='local' \
         -d tgt='*' \
         -d fun='test.ping' \

也可以请求 *https://192.168.38.10:8000/run*
，不过该方法为一次性使用，无法使用Token, 只能使用username和password

-   Response:

<!-- -->

    return:
    - minion-01.example.com: true

### 运行runner

-   Request

<!-- -->

    curl -k https://192.168.38.10:8000/ \
         -H "Accept: application/x-yaml" \
         -H "X-Auth-Token: 8e211da5d6bbb51fbffe6468a3ca0c6a24b3e535" \
         -d client='runner' \
         -d fun='manage.status'

-   Response

<!-- -->

    return:
    - down: []
      up:
      - minion-01.example.com

### Targeting

谢谢 *苦咖啡* 提供

如果想在api中使用salt的
[Targeting](http://docs.saltstack.com/topics/targeting/)
功能，可以在Request的Post Data中增加 *expr\_form* (默认是 *glob*
)及值即可:

依然以curl为例:

    curl -k https://192.168.38.10:8000/ \
         -H "Accept: application/x-yaml" \
         -H "X-Auth-Token: 8e211da5d6bbb51fbffe6468a3ca0c6a24b3e535" \
         -d client='local' \
         -d tgt='webcluster' \
         -d expr_form='nodegroup' \
         -d fun='test.ping'

将利用
[nodegroup](http://docs.saltstack.com/topics/targeting/nodegroups.html)
匹配到名为 *webcluster* 的target。

## 总结

Salt
API几乎涵盖了所有的salt操作，功能强劲，尤其是需要salt和第三方系统集成的场景，值得拥有。
