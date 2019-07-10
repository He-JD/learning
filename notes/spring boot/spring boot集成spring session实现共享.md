### spring boot集成spring session实现共享

> 摘要：在这个微服务，分布式的时代，很多传统的实现方案变的不再那么适用，比如传统的web服务将session放在内存中的情况，当web服务做水平扩展部署的时候，session共享就成了需要处理的问题。目前有很多成熟的技术可供我们选择，下面简单介绍最近用到的spring-boot+spring-session实现session共享的方案。

spring-boot集成spring-session非常简单，因为spring-boot为我们完成了非常多的工作。具体集成步骤如下：

> 一、工程继承spring-boot-starter-parent

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>1.5.2.RELEASE</version>
</parent>
```

这样做的好处是我们接下来引入其他依赖包可以不需要考虑版本问题，推荐这样做，避免自己引入不当导致的兼容性问题。

> 二、引入spring-session依赖包

```xml
<dependency>
    <groupId>org.springframework.session</groupId>
    <artifactId>spring-session</artifactId>
</dependency>
```

引入之后，我们要确定我们要将session持久化到哪种介质中了。因为分布式session可以持久化到数据库、redis、nosql等中，根据存储方式不同，需要引入不同的jar包和做不同的操作。我们以redis存储为例。

> 三、引入redis依赖包

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

由于我们使用了spring-boot，所以我们只需要引入spring-boot-starter-data-redis依赖即可，这样我们可以很好的利用spring-boot开箱即用以及非常方便的配置优势。

> 四、基础配置

由于我们引入了redis，这样我们需要在application.properties或者application.yml文件中配置redis连接，使用spring-boot我们可以很方便配置单点redis，哨兵模式，集群模式等，简单起见我们配置一个单点模式的redis连接并采用连接池

```java
spring.redis.port=6379
spring.redis.host=127.0.0.1
spring.redis.password=******
spring.redis.pool.max-active=100
spring.redis.pool.max-idle=5
spring.redis.pool.max-wait=60000
```

完成以上步骤之后，我们只需要告诉spring开启redis方式的session存储即可，这里有两种方式可以实现

- 方式1、在配置文件中添加一行配置

```java
spring.session.store-type=redis
```

- 方式2、在程序启动类上添加注解

```java
@EnableRedisHttpSession
```

两种方式都可以完成开启spring-session的redis存储，是不是非常简单。因为spring-boot的特性，以前很多需要在xml中配置的都可以轻松帮我们搞定。

# 扩展

虽然我们实现了redis方式存储的分布式session，但是在实际场景中可能还有一些需要优化的地方。

> 一、修改cookies中sessionId的名字
>
> 二、修改session存放在redis中的命名空间
>
> 三、修改session超时时间

为什么要这样做呢，如果我们有两套不同系统A和B，cookies中session名称相同会导致同一个浏览器登录两个系统会造成相互的干扰，例如两个系统中我们存放在session中的用户信息的键值为user。默认情况下cookies中的session名称为JSESSIONID。当我们登录A系统后，在同一个浏览器下打开B系统，B系统B系统拿到的user实际上并非自己系统的user对象，这样会造成系统异常；而如果我们A、B系统存放用户信息的键值设置为不相同，例如userA和userB，当我们登录A系统后在登录B系统，我们打开浏览器调试模式方向两个系统只有一个sessionId，因为我们没有对二者的session名称以及存储的命名空间做区分，程序会认为就是自己可用的session。当我们推出B系统，注销session后。发现B系统的session也失效了，因为在redis中JSESSIONID对应的数据已经被设置过期了。

同理，如果两个系统想要不同的session过期时间，也存在相同的问题。所以，建议不同系统，session名称以及存储的命名空间设置为不同，*当然相同系统的水平扩展实例的情况除外*。

针对命名空间，我们可以在配置文件上添加配置解决

```
spring.session.redis.namespace=xxxx
```

如果是注解方式的也可以在注解上设置

```
@EnableRedisHttpSession(redisNamespace="xxxx")
```

这样我们查看redis中就可以看到sping-session存储的key就变成了我们设置的值。

针对超时时间，注解方式提供了响应的设置

```
@EnableRedisHttpSession(maxInactiveIntervalInSeconds = 3600)
```

但是配置文件方式并没有提供响应的直接设置。
我们可以采用javaconfig方式自定义策略来设置超时以及设置cookies名称，如下我们设置超时时间是1800秒，cookies名为MYSESSIONID

```java
@Bean
public CookieHttpSessionStrategy cookieHttpSessionStrategy(){
    CookieHttpSessionStrategy strategy=new CookieHttpSessionStrategy();
    DefaultCookieSerializer cookieSerializer=new DefaultCookieSerializer();
    cookieSerializer.setCookieName("MYSESSIONID");//cookies名称
    cookieSerializer.setCookieMaxAge(1800);//过期时间(秒)
    strategy.setCookieSerializer(cookieSerializer);
    return strategy;
}
```

# 总结

通过以上步骤，我们就完成了分布式session的集成。相对于传统的内存方式，分布式session实现能够更方便水平扩展以及系统维护。对于不想立马更改系统采用token方式来进行验证的系统来说是一种简便、快速、低成本的一种实现思路。