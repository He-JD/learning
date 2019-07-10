#### springboot异步开发之异步调用

> 我们知道了如何进行异步请求的处理。除了异步请求，一般上我们用的比较多的应该是异步调用。通常在开发过程中，会遇到一个方法是和实际业务无关的，没有紧密性的。比如记录日志信息等业务。这个时候正常就是启一个新线程去做一些业务处理，让主线程异步的执行其他业务。所以，本章节重点说下在`SpringBoot`中如何进行异步调用及其相关知识和注意点

> 概念：说`异步调用`前，我们说说它对应的`同步调用`。通常开发过程中，一般上我们都是`同步调用`，即：程序按定义的顺序依次执行的过程，每一行代码执行过程必须等待上一行代码执行完毕后才执行。而`异步调用`指：程序在执行时，无需等待执行的返回值可继续执行后面的代码。显而易见，同步有依赖相关性，而异步没有，所以异步可`并发`执行，可提高执行效率，在相同的时间做更多的事情。
>
> **题外话：**处理`异步`、`同步`外，还有一个叫`回调`。其主要是解决异步方法执行结果的处理方法，比如在希望异步调用结束时返回执行结果，这个时候就可以考虑使用回调机制。



#####Async异步调用

> 在`SpringBoot`中使用异步调用是很简单的，只需要使用`@Async`注解即可实现方法的异步调用。

注意：需要在启动类加入`@EnableAsync`使异步调用`@Async`注解生效。

```java
@SpringBootApplication
@EnableAsync
@Slf4j
public class Chapter21Application {

    public static void main(String[] args) {
        SpringApplication.run(Chapter21Application.class, args);
        log.info("Chapter21启动!");
    }
}
```

**@Async的使用**

使用`@Async`很简单，只需要在需要异步执行的方法上加入此注解即可。这里创建一个控制层和一个服务层，进行简单示例下。

```java

@Component
public class SyncService {
    
    @Async
    public void asyncEvent() throws InterruptedException {
        //休眠1s
        Thread.sleep(1000);
        //log.info("异步方法输出：{}!", System.currentTimeMillis());
    }
    
    public void syncEvent() throws InterruptedException {
        Thread.sleep(1000);
        //log.info("同步方法输出：{}!", System.currentTimeMillis());
    }
}
```

应用启动后，可以看见控制台输出:

```java
2018-08-16 22:21:35.949  INFO 17152 --- [nio-8080-exec-5] c.l.l.s.c.controller.AsyncController     : 方法执行开始：1534429295949
2018-08-16 22:21:36.950  INFO 17152 --- [nio-8080-exec-5] c.l.l.s.c.controller.AsyncController     : 同步方法用时：1001
2018-08-16 22:21:36.950  INFO 17152 --- [nio-8080-exec-5] c.l.l.s.c.controller.AsyncController     : 异步方法用时：0
2018-08-16 22:21:36.950  INFO 17152 --- [nio-8080-exec-5] c.l.l.s.c.controller.AsyncController     : 方法执行完成：1534429296950!
2018-08-16 22:21:37.950  INFO 17152 --- [cTaskExecutor-3] c.l.l.s.chapter21.service.SyncService    : 异步方法内部线程名称：SimpleAsyncTaskExecutor-3!
```

可以看出，调用异步方法时，是立即返回的，基本没有耗时。

**这里有几点需要注意下：**

1. 在默认情况下，未设置`TaskExecutor`时，默认是使用`SimpleAsyncTaskExecutor`这个线程池，但此线程不是真正意义上的线程池，因为线程不重用，每次调用都会创建一个新的线程。可通过控制台日志输出可以看出，每次输出线程名都是递增的。
2. 调用的异步方法，不能为`同一个类`的方法，简单来说，因为`Spring`在启动扫描时会为其创建一个代理类，而同类调用时，还是调用本身的代理类的，所以和平常调用是一样的。其他的注解如`@Cache`等也是一样的道理，说白了，就是`Spring`的代理机制造成的。
3. @Async所修饰的函数不要定义为static类型，这样异步调用不会生效

#####自定义线程池

> 前面有提到，在默认情况下，系统使用的是默认的`SimpleAsyncTaskExecutor`进行线程创建。所以一般上我们会自定义线程池来进行线程的复用。

```java
@Configuration
public class Config {

    /**
     * 配置线程池
     * @return
     */
    @Bean(name = "asyncPoolTaskExecutor")
    public ThreadPoolTaskExecutor getAsyncThreadPoolTaskExecutor() {
        ThreadPoolTaskExecutor taskExecutor = new ThreadPoolTaskExecutor();
        taskExecutor.setCorePoolSize(20);
        taskExecutor.setMaxPoolSize(200);
        taskExecutor.setQueueCapacity(25);
        taskExecutor.setKeepAliveSeconds(200);
        taskExecutor.setThreadNamePrefix("oKong-");
        // 线程池对拒绝任务（无线程可用）的处理策略，目前只支持AbortPolicy、CallerRunsPolicy；默认为后者
        taskExecutor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        //调度器shutdown被调用时等待当前被调度的任务完成
        taskExecutor.setWaitForTasksToCompleteOnShutdown(true);
        //等待时长
        taskExecutor.setAwaitTerminationSeconds(60);
        taskExecutor.initialize();
        return taskExecutor;
    }
}
```

此时，使用的是就只需要在`@Async`加入线程池名称即可：

```java
    @Async("asyncPoolTaskExecutor")
    public void asyncEvent() throws InterruptedException {
        //休眠1s
        Thread.sleep(1000);
        log.info("异步方法内部线程名称：{}!", Thread.currentThread().getName());
    }
```

再次启动应用，就可以看见已经是使用自定义的线程了。

```java
2018-08-16 22:32:02.676  INFO 4516 --- [nio-8080-exec-1] c.l.l.s.c.controller.AsyncController     : 方法执行开始：1534429922676
2018-08-16 22:32:03.681  INFO 4516 --- [nio-8080-exec-1] c.l.l.s.c.controller.AsyncController     : 同步方法用时：1005
2018-08-16 22:32:03.693  INFO 4516 --- [nio-8080-exec-1] c.l.l.s.c.controller.AsyncController     : 异步方法用时：12
2018-08-16 22:32:03.693  INFO 4516 --- [nio-8080-exec-1] c.l.l.s.c.controller.AsyncController     : 方法执行完成：1534429923693!
2018-08-16 22:32:04.694  INFO 4516 --- [        oKong-1] c.l.l.s.chapter21.service.SyncService    : 异步方法内部线程名称：oKong-1!
```

#####异步回调及超时处理

> 对于一些业务场景下，需要异步回调的返回值时，就需要使用异步回调来完成了。主要就是通过`Future`进行异步回调。

**异步回调**

修改下异步方法的返回类型，加入`Future`。

```java
@Async("asyncPoolTaskExecutor")
public Future<String> asyncEvent() throws InterruptedException {
    //休眠1s
    Thread.sleep(1000);
    log.info("异步方法内部线程名称：{}!", Thread.currentThread().getName());
    return new AsyncResult<>("异步方法返回值");
}
```

其中`AsyncResult`是`Spring`提供的一个`Future`接口的子类。

然后通过`isDone`方法，判断是否已经执行完毕。

```java
@GetMapping("/async")
    public String doAsync() throws InterruptedException {
        long start = System.currentTimeMillis();
        log.info("方法执行开始：{}", start);
        //调用同步方法
        syncService.syncEvent();
        long syncTime = System.currentTimeMillis();
        log.info("同步方法用时：{}", syncTime - start);
        //调用异步方法
        Future<String> doFutrue = syncService.asyncEvent();
        while(true) {
            //判断异步任务是否完成
            if(doFutrue.isDone()) {
                break;
            }
            Thread.sleep(100);
        }
        long asyncTime = System.currentTimeMillis();
        log.info("异步方法用时：{}", asyncTime - syncTime);
        log.info("方法执行完成：{}!",asyncTime);
        return "async!!!";
    }
```



此时，控制台输出：

```java
2018-08-16 23:10:57.021  INFO 9072 --- [nio-8080-exec-1] c.l.l.s.c.controller.AsyncController     : 方法执行开始：1534431237020
2018-08-16 23:10:58.025  INFO 9072 --- [nio-8080-exec-1] c.l.l.s.c.controller.AsyncController     : 同步方法用时：1005
2018-08-16 23:10:59.037  INFO 9072 --- [        oKong-1] c.l.l.s.chapter21.service.SyncService    : 异步方法内部线程名称：oKong-1!
2018-08-16 23:10:59.040  INFO 9072 --- [nio-8080-exec-1] c.l.l.s.c.controller.AsyncController     : 异步方法用时：1015
2018-08-16 23:10:59.040  INFO 9072 --- [nio-8080-exec-1] c.l.l.s.c.controller.AsyncController     : 方法执行完成：1534431239040!
```



所以，当某个业务功能可以同时拆开一起执行时，可利用异步回调机制，可有效的减少程序执行时间，提高效率。

**超时处理**

> 对于一些需要异步回调的函数，不能无期限的等待下去，所以一般上需要设置超时时间，超时后可将线程释放，而不至于一直堵塞而占用资源。

对于`Future`配置超时，很简单，通过`get`方法即可，具体如下：

```java
//get方法会一直堵塞，直到等待执行完成才返回
//get(long timeout, TimeUnit unit) 在设置时间类未返回结果，会直接排除异常TimeoutException，messages为null
String result = doFutrue.get(60, TimeUnit.SECONDS);//60s
```

超时后，会抛出异常`TimeoutException`类，此时可进行统一异常捕获即可。

> 本章节主要是讲解了`异步请求`的使用及相关配置，如超时，异常等处理。在剥离一些和业务无关的操作时，就可以考虑使用`异步调用`进行其他无关业务操作，以此提供业务的处理效率。或者一些业务场景下可拆分出多个方法进行同步执行又互不影响时，也可以考虑使用`异步调用`方式提供执行效率

推荐博文：[springboot异步开发之异步调用](https://blog.lqdev.cn/2018/08/17/springboot/chapter-twenty-one/)

