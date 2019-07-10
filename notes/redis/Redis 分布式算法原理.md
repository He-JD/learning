<div id="article_content" class="article_content clearfix csdn-tracking-statistics" data-pid="blog" data-mod="popu_307" data-dsm="post">
								            <div id="content_views" class="markdown_views prism-atom-one-dark">
							<!-- flowchart 箭头图标 勿删 -->
							<svg xmlns="http://www.w3.org/2000/svg" style="display: none;"><path stroke-linecap="round" d="M5,0 0,2.5 5,5z" id="raphael-marker-block" style="-webkit-tap-highlight-color: rgba(0, 0, 0, 0);"></path></svg>
###Redis 分布式算法原理

*   传统分布式算法
*   Consistent hashing一致性算法原理
*   Hash倾斜性
*   虚拟节点
*   Consistent hashing命中率

举个栗子：[![](https://i.loli.net/2018/08/14/5b726e4cbb8cf.jpg)](https://i.loli.net/2018/08/14/5b726e4cbb8cf.jpg)

假设有一个图片 test.jpg,我们有 3 个服务器， 服务器1 ，服务器2 ，服务器3

**4 个 redis 节点** 

- Redis0 

- Redis1 

- Redis2 

- Redis3 

**20个数据** 

[![](https://i.loli.net/2018/08/14/5b726f2d18820.png)](https://i.loli.net/2018/08/14/5b726f2d18820.png) 

这上面 1-20 大家就可以认识是 对应数据 hash 之后的结果，然后对这些结果用 4 取模（因为这里有 4 个 Redis 节点）. 

`1 % 4 = 1` 所以将该数据放在 `Redis1` 

`2 % 4 = 2` 所以将该数据放在 `Redis2` 

`3 % 4 = 3` 所以将该数据放在 `Redis3` 

`4 % 4 = 0` 所以将该数据放在 `Redis0` 

同理，后面的其他数据应该这样放置，如下图

[![](https://i.loli.net/2018/08/14/5b72710c916ca.png)](https://i.loli.net/2018/08/14/5b72710c916ca.png)

**但是，突然我们发现Redis 的节点不够用了（需要增加节点），或者Redis负载非常低（需要删除节点）。** 

这里我们来增加一个节点 `Redis4`,增加之后的数据再节点上的分部如下图： 

[![](https://i.loli.net/2018/08/14/5b72724e7c4f9.png)](https://i.loli.net/2018/08/14/5b72724e7c4f9.png) 

**你会发现，只有 redis0 命中了值 20，redis1命中了1，redis2 命中了2，redis3命中了3，命中率为 4/20 = 20%**

##### 一致性算法

Consistent hashing 

我们来看一下环形 hash 空间 

通常的hash 算法是将 value 映射到一个 32 位的 key value 当中，我们将其[首尾相连](https://www.baidu.com/s?wd=%E9%A6%96%E5%B0%BE%E7%9B%B8%E8%BF%9E&amp;tn=24004469_oem_dg&amp;rsv_dl=gh_pl_sl_csd)，就形成了一个圆环，取值范围是 0- 2^32-1 如下图: 

[![](https://i.loli.net/2018/08/14/5b7274fd058d7.png)](https://i.loli.net/2018/08/14/5b7274fd058d7.png)

**将对象映射到 圆形hash空间** 

- 我们hash 4个 对象 obj1-obj4 

- 通过hash 函数计算出hash 值的key 

落在 环形 hash 空间上的情况如图 

[![](https://i.loli.net/2018/08/14/5b72763ba9684.png)](https://i.loli.net/2018/08/14/5b72763ba9684.png) 

**将cache 映射到环形 hash空间** 

- 将对象和 cache 都映射到同一个hash 空间，并且使用相同的hash 算法，如下图： 

[![](https://i.loli.net/2018/08/14/5b727719c85ec.png)](https://i.loli.net/2018/08/14/5b727719c85ec.png)

现在我们就把数据对象和cache 都映射到 hash空间上了，接下来就是要考虑如何将这个对象映射到cache 上面，看下面的图，沿着环形顺时针走，从key1开始，可将obj1 映射到keyA上，obj2 映射到keyC ，obj3映射到keyC，obj4映射到keyB上，[![](https://i.loli.net/2018/08/14/5b7278a8954e7.png)](https://i.loli.net/2018/08/14/5b7278a8954e7.png) 

下面来看看移除和添加cache 节点有什么变化  

[![](https://i.loli.net/2018/08/14/5b727b9e5dda6.png)](https://i.loli.net/2018/08/14/5b727b9e5dda6.png) 

将cacheB移除，obj4就只能顺时针找到 cacheC了，所以移除一个cache节点，影响的是从该cache节点逆时针开始碰到第一个节点的范围对象，环状的其他区域数据节点都不会影响，如图： 

[![](https://i.loli.net/2018/08/14/5b727c67e014e.png)](https://i.loli.net/2018/08/14/5b727c67e014e.png) 

在 obj2和obj3直接添加一个 cacheD ，如图，我们可以看到obj2 顺时针就会映射到cacheD上，同时受到影响的也是从添加的cache节点逆时针碰到第一个节点的范围 

[![](https://i.loli.net/2018/08/14/5b727cf4bb91b.png)](https://i.loli.net/2018/08/14/5b727cf4bb91b.png)

从上面我们可以看到，cache 的变动，对应数据对象的影响很小。 

但是呢，要知道理想和现实的差距，我们理想的环状空间是均匀分布的，如图：[![](https://i.loli.net/2018/08/14/5b727dc84c6bf.png)](https://i.loli.net/2018/08/14/5b727dc84c6bf.png) 

现实却是这样的情况： 

[![](https://i.loli.net/2018/08/14/5b727df6c915f.png)](https://i.loli.net/2018/08/14/5b727df6c915f.png) 

如果用上面的hash 算法，大量的数据对象会映射在 A 节点上，而BC节点很少，这样就导致A节点很忙，BC却很是清闲，这就是因为Hash 的倾斜性造成的。 

[![](https://i.loli.net/2018/08/14/5b727ef664833.png)](https://i.loli.net/2018/08/14/5b727ef664833.png)

如何解决Hash 倾斜性导致的问题呢？这里引入了虚拟节点 

[![](https://i.loli.net/2018/08/14/5b7280bae61e1.png)](https://i.loli.net/2018/08/14/5b7280bae61e1.png) 

比如有 obj1 和 obj 2 两个对象 对其进行 hash 计算，这里增加了 6 个虚拟节点，hash 之后分布落在了 V2，V5上，然后对虚拟节点进行 rehash ，这时 V1,V2映射在 [N1](https://www.baidu.com/s?wd=N1&amp;tn=24004469_oem_dg&amp;rsv_dl=gh_pl_sl_csd)上，V3,V4映射在N2上，V5,V6 映射在N3上，obj就映射在了 N1上，obj2映射在N3上。 

引入了 虚拟节点，现在 环状空间是什么样子的呢？看下图

[![](https://i.loli.net/2018/08/14/5b72825ff0ad7.png)](https://i.loli.net/2018/08/14/5b72825ff0ad7.png) 

ABC分别都有对应的影子节点，这时候数据对象的映射就相对均匀了，但是要知道，虚拟节点也有是hash 倾斜性的，这就要在真实节点和虚拟节点之间做一个平衡，分配一个很好的比例，随着节点越来越多，数据越来越多，那么这个分布就会越来越均匀了，在删除节点和添加节点的时候也会把影响降到最小。

命中率计算公式`(1-N/(N+M))*100%` 

服务器台数是 N，新增的服务器台数是M 。当M越大的时候，对命中率的影响很小。