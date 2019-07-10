###Redis5集群搭建

####1、简要说明

2018年十月 Redis 发布了稳定版本的 5.0 版本，推出了各种新特性，其中一点是放弃 Ruby的集群方式，改为 使用 C语言编写的 redis-cli的方式，是集群的构建方式复杂度大大降低。关于集群的更新可以在 Redis5 的版本说明中看到，如下：

> The cluster manager was ported from Ruby (redis-trib.rb) to C code inside redis-cli. check `redis-cli --cluster help ` for more info.

可以查看Redis官网查看集群搭建方式，连接如下

https://redis.io/topics/cluster-tutorial

以下步骤是在一台 Linux 服务器上搭建有6个节点的 Redis集群。

####2、创建集群步骤

#####1、创建目录

​        新建目录：/root/software/redis-cluster

#####2、下载源码并解压编译

```
wget http://download.redis.io/releases/redis-5.0.0.tar.gz
tar xzf redis-5.0.0.tar.gz
cd redis-5.0.0
make
```

#####3、创建6个Redis配置文件

​    6个配置文件不能在同一个目录，此处我们定义如下：

```
/root/software/redis-cluster/redis-cluster-conf/7001/redis.conf
/root/software/redis-cluster/redis-cluster-conf/7002/redis.conf
/root/software/redis-cluster/redis-cluster-conf/7003/redis.conf
/root/software/redis-cluster/redis-cluster-conf/7004/redis.conf
/root/software/redis-cluster/redis-cluster-conf/7005/redis.conf
/root/software/redis-cluster/redis-cluster-conf/7006/redis.conf
```

配置文件的内容为：

```shell
port 7001
cluster-enabled yes
cluster-config-file nodes_7001.conf
cluster-node-timeout 5000
appendonly yes
daemonize yes
protected-mode no
pidfile  /var/run/redis_7001.pid
```

其中 port 和 pidfile以及nodes 需要随着 文件夹的不同调增。

#####4、启动节点

```shell
redis-server ./7001/redis.conf
redis-server ./7002/redis.conf
redis-server ./7003/redis.conf
redis-server ./7004/redis.conf
redis-server ./7005/redis.conf
redis-server ./7006/redis.conf
```

#####5、启动集群

```shell
redis-cli --cluster create 127.0.0.1:7001 127.0.0.1:7002 127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 127.0.0.1:7006 --cluster-replicas 1
```

**我们也可以通过脚本的方式来一键启动**

> touch redis-cluster.sh

```
redis-server ./7001/redis.conf
redis-server ./7002/redis.conf
redis-server ./7003/redis.conf
redis-server ./7004/redis.conf
redis-server ./7005/redis.conf
redis-server ./7006/redis.conf

redis-cli --cluster create 127.0.0.1:7001 127.0.0.1:7002 127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 127.0.0.1:7006 --cluster-replicas 1
```

启动后，可看到成功信息，如下：

```
hejd@hejindadeMacBook-Pro  ~/Software/reids-cluster/redis-cluster-conf  redis-cli --cluster create 127.0.0.1:7001 127.0.0.1:7002 127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 127.0.0.1:7006 --cluster-replicas 1
>>> Performing hash slots allocation on 6 nodes...
Master[0] -> Slots 0 - 5460
Master[1] -> Slots 5461 - 10922
Master[2] -> Slots 10923 - 16383
Adding replica 127.0.0.1:7004 to 127.0.0.1:7001
Adding replica 127.0.0.1:7005 to 127.0.0.1:7002
Adding replica 127.0.0.1:7006 to 127.0.0.1:7003
>>> Trying to optimize slaves allocation for anti-affinity
[WARNING] Some slaves are in the same host as their master
M: e7d4b509d94a396d628cfec89a6a4607d1bd93dc 127.0.0.1:7001
   slots:[0-5460] (5461 slots) master
M: 2287a514fc378b8dee4b91dd9130b9bc5d9074a8 127.0.0.1:7002
   slots:[5461-10922] (5462 slots) master
M: f068172df2dafdc2d48e8a88414d3455c5e279c1 127.0.0.1:7003
   slots:[10923-16383] (5461 slots) master
S: dbe61da8d10f469d79cc45149fa201a0a820ed66 127.0.0.1:7004
   replicates 2287a514fc378b8dee4b91dd9130b9bc5d9074a8
S: 924e5d366b56d93d32b5391a14a28db95b44ba6e 127.0.0.1:7005
   replicates f068172df2dafdc2d48e8a88414d3455c5e279c1
S: 12c8510a16e1e98668b2662804119ab69ef8c403 127.0.0.1:7006
   replicates e7d4b509d94a396d628cfec89a6a4607d1bd93dc
Can I set the above configuration? (type 'yes' to accept): yes
>>> Nodes configuration updated
>>> Assign a different config epoch to each node
>>> Sending CLUSTER MEET messages to join the cluster
Waiting for the cluster to join
...
>>> Performing Cluster Check (using node 127.0.0.1:7001)
M: e7d4b509d94a396d628cfec89a6a4607d1bd93dc 127.0.0.1:7001
   slots:[0-5460] (5461 slots) master
   1 additional replica(s)
M: 2287a514fc378b8dee4b91dd9130b9bc5d9074a8 127.0.0.1:7002
   slots:[5461-10922] (5462 slots) master
   1 additional replica(s)
S: 12c8510a16e1e98668b2662804119ab69ef8c403 127.0.0.1:7006
   slots: (0 slots) slave
   replicates e7d4b509d94a396d628cfec89a6a4607d1bd93dc
S: dbe61da8d10f469d79cc45149fa201a0a820ed66 127.0.0.1:7004
   slots: (0 slots) slave
   replicates 2287a514fc378b8dee4b91dd9130b9bc5d9074a8
S: 924e5d366b56d93d32b5391a14a28db95b44ba6e 127.0.0.1:7005
   slots: (0 slots) slave
   replicates f068172df2dafdc2d48e8a88414d3455c5e279c1
M: f068172df2dafdc2d48e8a88414d3455c5e279c1 127.0.0.1:7003
   slots:[10923-16383] (5461 slots) master
   1 additional replica(s)
[OK] All nodes agree about slots configuration.
>>> Check for open slots...
>>> Check slots coverage...
[OK] All 16384 slots covered.
```

至此，Reids5 集群搭建完成。

####3、Redis Cluster集群的测试

#####1 、测试存取值

​         客户端连接集群redis-cli需要带上 -c ，redis-cli -c -p 端口号

```shell
hejd@hejindadeMacBook-Pro  ~/Software/reids-cluster/redis-cluster-conf  redis-cli -c -p 7001
127.0.0.1:7001> set name tom
-> Redirected to slot [5798] located at 127.0.0.1:7002
OK
127.0.0.1:7002> get name
"tom"
```

​         根据redis-cluster的key值分配，name应该分配到节点7002[5461-10922]上，上面显示redis cluster自动从7001跳转到了7002节点。

​       我们可以测试一下7006从节点获取name值

```shell
hejd@hejindadeMacBook-Pro  ~/Software/reids-cluster/redis-cluster-conf  redis-cli -c -p 7006
127.0.0.1:7006> get name
-> Redirected to slot [5798] located at 127.0.0.1:7002
"tom"
```

7006位7003的从节点，从上面也是自动跳转至7002获取值，这也是redis cluster的特点，它是去中心化，每个节点都是对等的，连接哪个节点都可以获取和设置数据。

推荐博文：

- [一文看懂 Redis5 搭建集群](https://my.oschina.net/ruoli/blog/2252393)