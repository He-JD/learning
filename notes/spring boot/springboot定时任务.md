[TOC]

###springboot定时任务

在`JAVA`开发领域，目前可以通过以下几种方式进行定时任务:

- Timer：jdk中自带的一个定时调度类，可以简单的实现按某一频度进行任务执行。提供的功能比较单一，无法实现复杂的调度任务。
- ScheduledExecutorService：也是jdk自带的一个基于线程池设计的定时任务类。其每个调度任务都会分配到线程池中的一个线程执行，所以其任务是并发执行的，互不影响。
- Spring Task：`Spring`提供的一个任务调度工具，支持注解和配置文件形式，支持`Cron`表达式，使用简单但功能强大。
- Quartz：一款功能强大的任务调度器，可以实现较为复杂的调度功能，如每月一号执行、每天凌晨执行、每周五执行等等，还支持分布式调度，就是配置稍显复杂。

####基于JDK方式实现简单定时

> 刚刚有介绍过，基于`JDK`方式一共有两种：`Timer`和`ScheduledExecutorService`。接下来，就简单讲解下这两种方式。

#####Timer方式

> `Timer`是jdk提供的`java.util.Timer`类。

**简单示例：**

```java
@GetMapping("/timer")
public String doTimer() {
    Timer timer = new Timer();
    timer.schedule(new TimerTask() {
        
        @Override
        public void run() {
            log.info("Timer定时任务启动：" + new Date());
            
        }
    }, 1000,1000);//延迟1秒启动，每1秒执行一次
    return "timer";
```

启动后，访问即可看见控制台周期性输出信息了：

```java
2018-08-18 21:30:35.171  INFO 13352 --- [        Timer-0] c.l.l.s.c.controller.TaskController      : Timer定时任务启动：Sat Aug 18 21:30:35 CST 2018
2018-08-18 21:30:36.173  INFO 13352 --- [        Timer-0] c.l.l.s.c.controller.TaskController      : Timer定时任务启动：Sat Aug 18 21:30:36 CST 2018
2018-08-18 21:30:37.173  INFO 13352 --- [        Timer-0] c.l.l.s.c.controller.TaskController      : Timer定时任务启动：Sat Aug 
......
```

**相关API简单说明：**

1、在特定时间执行任务，只执行一次

```java
public void schedule(TimerTask task,Date time)
```

2、在特定时间之后执行任务，只执行一次

```java
public void schedule(TimerTask task,long delay)
```

3、指定第一次执行的时间，然后按照间隔时间，重复执行

```java
public void schedule(TimerTask task,Date firstTime,long period)
```

4、在特定延迟之后第一次执行，然后按照间隔时间，重复执行

```java
public void schedule(TimerTask task,long delay,long period)
```

5、第一次执行之后，特定频率执行，与3同

```java
public void scheduleAtFixedRate(TimerTask task,Date firstTime,long period)
```

6、在delay毫秒之后第一次执行，后按照特定频率执行

```java
public void scheduleAtFixedRate(TimerTask task,long delay,long period)
```

参数：

- delay： 延迟执行的毫秒数，即在delay毫秒之后第一次执行
- period：重复执行的时间间隔

取消任务使用：`timer.cancel()`方法即可注销任务。

此类相对用的较少了，简单了解下。

#####ScheduledExecutorService方式

> `ScheduledExecutorService`可以说是`Timer`的替代类，因为`Timer`不支持多线程，任务是串行的，而且也不捕获异常，假设某个任务异常了，整个`Timer`就无法运行了。

**简单示例：**

```java
@GetMapping("/executor")
public String ScheduledExecutorService() {
    //
    ScheduledExecutorService service = Executors.newScheduledThreadPool(10);
    service.scheduleAtFixedRate(new Runnable() {
        
        @Override
        public void run() {
            log.info("ScheduledExecutorService定时任务执行：" + new Date());                
        }
    }, 1, 1, TimeUnit.SECONDS);//首次延迟1秒，之后每1秒执行一次
    log.info("ScheduledExecutorService定时任务启动：" + new Date());    
    return "ScheduledExecutorService!";        
}
```

启动后，可看见控制台按设定的频率输出：

```java
2018-08-18 22:03:24.840  INFO 6752 --- [nio-8080-exec-1] c.l.l.s.c.controller.TaskController      : ScheduledExecutorService定时任务启动：Sat Aug 18 22:03:24 CST 2018
2018-08-18 22:03:25.841  INFO 6752 --- [pool-1-thread-1] c.l.l.s.c.controller.TaskController      : ScheduledExecutorService定时任务执行：Sat Aug 18 22:03:25 CST 2018
2018-08-18 22:03:26.842  INFO 6752 --- [pool-1-thread-1] c.l.l.s.c.controller.TaskController      : ScheduledExecutorService定时任务执行：Sat Aug 18 22:03:26 CST 2018
```

可同时设置多个任务，只需再次设置`scheduleAtFixedRate`即可。

**常用方法说明：**

- ScheduleAtFixedRate：

```java
public ScheduledFuture<?> scheduleAtFixedRate(Runnable command,long initialDelay,long period,TimeUnit unit);
```

参数说明：

1. command：执行线程
2. initialDelay：初始化延时
3. period：两次开始执行最小间隔时间
4. unit：计时单位

- ScheduleWithFixedDelay：

```java
public ScheduledFuture<?> scheduleWithFixedDelay(Runnable command,long initialDelay,long delay,TimeUnit unit);
```

参数说明：

1. command：执行线程
2. initialDelay：初始化延时
3. delay：前一次执行结束到下一次执行开始的间隔时间（间隔执行延迟时间）
4. unit：计时单位

**其他的方法大家可自行谷歌下。**

####基于SpingTask实现定时任务

> 使用`SpringTask`在`SpringBoot`是很简单的，使用`@Scheduled`注解即可轻松搞定。

0.启动类，加入`@EnableScheduling`让注解`@Scheduled`生效。

```java
`@SpringBootApplication@EnableScheduling@Slf4jpublic class Chapter22Application {    public static void main(String[] args) {        SpringApplication.run(Chapter22Application.class, args);        log.info("Chapter22启动!");    }}`
```

1.编写一个调度类，系统启动后自动扫描，自动执行。

```java
@Component
@Slf4j
public class ScheduledTask {

    /**
     * 自动扫描，启动时间点之后5秒执行一次
     */
    @Scheduled(fixedRate=5000)
    public void getCurrentDate() {
        log.info("Scheduled定时任务执行：" + new Date());
    }
}
```

2.启动后，控制台可就看见每5秒一次输出了：

```java
2018-08-18 22:23:09.735  INFO 13812 --- [pool-1-thread-1] c.l.l.s.c.controller.ScheduledTask       : Scheduled定时任务执行：Sat Aug 18 22:23:09 CST 2018
2018-08-18 22:23:14.734  INFO 13812 --- [pool-1-thread-1] c.l.l.s.c.controller.ScheduledTask       : Scheduled定时任务执行：Sat Aug 18 22:23:14 CST 2018
2018-08-18 22:23:19.735  INFO 13812 --- [pool-1-thread-1] c.l.l.s.c.controller.ScheduledTask       : Scheduled定时任务执行：Sat 
......
```

使用都是简单的，现在我们来看看注解`@Scheduled`的参数意思：

1. fixedRate：定义一个按一定频率执行的定时任务
2. fixedDelay：定义一个按一定频率执行的定时任务，与上面不同的是，改属性可以配合`initialDelay`， 定义该任务延迟执行时间。
3. cron：通过表达式来配置任务执行时间

#####Cron表达式详解

> 一个`cron`表达式有至少6个（也可能7个）有空格分隔的时间元素。

依次顺序如下表所示：

| 字段       | 允许值          | 允许的特殊字符  |
| ---------- | --------------- | --------------- |
| 秒         | 0~59            | , - * /         |
| 分         | 0~59            | , - * /         |
| 小时       | 0~23            | , - * /         |
| 日期       | 1-31            | , - * ? / L W C |
| 月份       | 1~12或者JAN~DEC | , - * /         |
| 星期       | 1~7或者SUN~SAT  | , - * ? / L C # |
| 年（可选） | 留空，1970~2099 | , - * /         |

**简单举例：**

- 0/1 * * * * ?：每秒执行一次
- 0 0 2 1 * ? ： 表示在每月的1日的凌晨2点调整任务
- 0 0 10,14,16 ? ：每天上午10点，下午2点，4点
- 0 0 12 * * ? ： 每天中午12点触发
- 0 15 10 ? * MON-FRI ： 周一至周五的上午10:15触发

更多表达式，可访问：<http://cron.qqe2.com/> 进行在线表达式编写。简单明了。

#####自定义线程池

> 从控制台输出可以看见，多任务使用的是同一个线程。可结合上章节的异步调用来实现不同任务使用不同的线程进行任务执行。

0.编写配置类,同时启用`@Async`注解：

```java
@Configuration
@EnableAsync
public class Config {
    /**
     * 配置线程池
     * @return
     */
    @Bean(name = "scheduledPoolTaskExecutor")
    public ThreadPoolTaskExecutor getAsyncThreadPoolTaskExecutor() {
        ThreadPoolTaskExecutor taskExecutor = new ThreadPoolTaskExecutor();
        taskExecutor.setCorePoolSize(20);
        taskExecutor.setMaxPoolSize(200);
        taskExecutor.setQueueCapacity(25);
        taskExecutor.setKeepAliveSeconds(200);
        taskExecutor.setThreadNamePrefix("oKong-Scheduled-");
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

1.调度类上加入`@Async`。

```java
@Component
@Slf4j
public class ScheduledTask {

    /**
     * 自动扫描，启动时间点之后5秒执行一次
     */
    @Async("scheduledPoolTaskExecutor")
    @Scheduled(fixedRate=5000)
    public void getCurrentDate() {
        log.info("Scheduled定时任务执行：" + new Date());
    }
}
```

再次启动程序，可看见控制台输出，任务已经是不同线程下执行了：

```java
2018-08-18 22:47:13.313  INFO 14212 --- [ong-Scheduled-1] c.l.l.s.c.controller.ScheduledTask       : Scheduled定时任务执行：Sat Aug 18 22:47:13 CST 2018
2018-08-18 22:47:13.343  INFO 14212 --- [           main] s.b.c.e.t.TomcatEmbeddedServletContainer : Tomcat started on port(s): 8080 (http)

```

####动态添加定时任务

> 使用注解的方式，无法实现动态的修改或者添加新的定时任务的，这个使用就需要使用编程的方式进行任务的更新操作了。可直接使用`ThreadPoolTaskScheduler`或者`SchedulingConfigurer`接口进行自定义定时任务创建。

#####ThreadPoolTaskScheduler

> `ThreadPoolTaskScheduler`是`SpringTask`的核心实现类，该类提供了大量的重载方法进行任务调度。这里简单示例下，具体的大家自行搜索下，用的少不太了解呀。

0.创建一个`ThreadPoolTaskScheduler`类。

```java
@Bean("taskExecutor")
public TaskScheduler taskExecutor() {
    ThreadPoolTaskScheduler executor = new ThreadPoolTaskScheduler();
    executor.setPoolSize(20);
    executor.setThreadNamePrefix("oKong-taskExecutor-");
    executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
    //调度器shutdown被调用时等待当前被调度的任务完成
    executor.setWaitForTasksToCompleteOnShutdown(true);
    //等待时长
    executor.setAwaitTerminationSeconds(60);
    return executor;
}
```

1.编写一个控制类，动态设置定时任务：

```java
@Autowired
TaskScheduler taskScheduler;

@GetMapping("/poolTask")
public String threadPoolTaskScheduler() {

    taskScheduler.schedule(new Runnable() {
        
        @Override
        public void run() {
            log.info("ThreadPoolTaskScheduler定时任务：" + new Date());
        }
    }, new CronTrigger("0/3 * * * * ?"));//每3秒执行一次
    return "ThreadPoolTaskScheduler!";
}
```

2.启动后，访问接口，即可看见控制台每3秒输出一次：

```java
2018-08-18 23:20:39.002  INFO 9120 --- [Kong-Executor-1] c.l.l.s.c.controller.TaskController      : ThreadPoolTaskScheduler定时任务：Sat Aug 18 23:20:39 CST 2018
2018-08-18 23:20:42.000  INFO 9120 --- [Kong-Executor-1] c.l.l.s.c.controller.TaskController      : ThreadPoolTaskScheduler定时任务：Sat Aug 18 23:20:42 CST 2018

```

**SchedulingConfigurer**

> 此类十个接口，直接实现其`configurerTasks`方法即可。

0.编写配置类：

```java
@Configuration
@Slf4j
public class ScheduleConfig implements SchedulingConfigurer {

    @Override
    public void configureTasks(ScheduledTaskRegistrar taskRegistrar) {
        taskRegistrar.setTaskScheduler(taskExecutor());
        taskRegistrar.getScheduler().schedule(new Runnable() {
            
            @Override
            public void run() {
                log.info("SchedulingConfigurer定时任务：" + new Date());
            }
        }, new CronTrigger("0/3 * * * * ?"));//每3秒执行一次
    }
    
    @Bean("taskExecutor")
    public TaskScheduler taskExecutor() {
        ThreadPoolTaskScheduler executor = new ThreadPoolTaskScheduler();
        executor.setPoolSize(20);
        executor.setThreadNamePrefix("oKong-Executor-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        //调度器shutdown被调用时等待当前被调度的任务完成
        executor.setWaitForTasksToCompleteOnShutdown(true);
        //等待时长
        executor.setAwaitTerminationSeconds(60);
        return executor;
    }

}
```

1.启动后，控制台也可以看见每3秒输出一次：

```java
2018-08-18 23:24:39.001  INFO 868 --- [Kong-Executor-1] c.l.l.s.chapter22.config.ScheduleConfig  : SchedulingConfigurer定时任务：Sat Aug 18 23:24:39 CST 2018
2018-08-18 23:24:42.001  INFO 868 --- [Kong-Executor-1] c.l.l.s.chapter22.config.ScheduleConfig  : SchedulingConfigurer定时任务：Sat Aug 18 23:24:42 CST 2018
2018-08-18 23:24:45.000  INFO 868 --- [Kong-Executor-2] c.l.l.s.chapter22.config.ScheduleConfig  : SchedulingConfigurer定时任务：Sat Aug 18 23:24:45 CST 2018
```

推荐博文：

- [SpringBoot结合Quartz集群](https://www.jianshu.com/p/9facdd9d758d)

- [定时任务的使用](https://blog.lqdev.cn/2018/08/19/springboot/chapter-twenty-two/)

- [spring boot下定时任务quartz的集群使用](https://blog.csdn.net/KokJuis/article/details/78526709)

  

