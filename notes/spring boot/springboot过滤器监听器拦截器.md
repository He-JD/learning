

[TOC]



####Profile注解的使用

> 如果需要在不同环境下，加载不同的bean时，可利用@Profile注解来动态激活

```java
@Profile("dev")//支持数组:@Profile({"dev","test"})
@Configuration
@Slf4j
public class ProfileBean {
	@PostConstruct
	public void init() {
		log.info("dev环境下激活");
	}	
}
```

启动时。控制台输出：

`[           main] c.l.l.springboot.chapter5.ProfileBean    : dev环境下激活`

#### spring boot过滤器实现的两种方式

- 利用WebFileter注解配置
- FilterRegisterBean方式

##### 利用利用WebFileter注解配置

> `@WebFilter`时`Servlet3.0`新增的注解，原先实现过滤器，需要在`web.xml`中进行配置，而现在通过此注解，启动时会自动扫描自动注册。

**编写Filter类：**

```java
//注册器名称为customFilter,拦截的url为所有
@WebFilter(filterName="customFilter",urlPatterns={"/*"})
@Slf4j
public class CustomFilter implements Filter{

    @Override
    public void init(FilterConfig filterConfig) throws ServletException {
        log.info("filter 初始化");
    }

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        // TODO Auto-generated method stub
        log.info("doFilter 请求处理");
        //对request、response进行一些预处理
        // 比如设置请求编码
        // request.setCharacterEncoding("UTF-8");
        // response.setCharacterEncoding("UTF-8");
        //TODO 进行业务逻辑
        
        //链路 直接传给下一个过滤器
        chain.doFilter(request, response);
    }

    @Override
    public void destroy() {
        log.info("filter 销毁");
    }
}
```

然后在启动类加入`@ServletComponentScan`注解即可

```java
@SpringBootApplication
@ServletComponentScan
@Slf4j
public class Chapter7Application {
    
    public static void main(String[] args) {
        SpringApplication.run(Chapter7Application.class, args);
        log.info("服务启动");
    }
}
```

> 当注册多个过滤器时，无法指定执行顺序的，原本使用`web。xml`配置过滤器时，是可指定执行顺序的，但使用`@WebFilter`时，没有这个配置属性的(需要配合`@Order`进行)，所以接下来介绍下通过`FilterRegistrationBean`进行过滤器的注册。

##### FilterRegistrationBean方式

> `FilterRegistrationBean`是`springboot`提供的，此类提供setOrder方法，可以为filter设置排序值，让spring在注册web filter之前排序后再依次注册。

**添加配置类**

```java
@Configuration
@ConditionalOnWebApplication
public class WebAutoConfiguration {
    @Bean
    public FilterRegistrationBean  filterRegistrationBean() {
        FilterRegistrationBean registration = new FilterRegistrationBean();
        //当过滤器有注入其他bean类时，可直接通过@bean的方式进行实体类过滤器，这样不可自动注入过滤器使用的其他bean类。
        //当然，若无其他bean需要获取时，可直接new CustomFilter()，也可使用getBean的方式。
        registration.setFilter(customFilter());
        //过滤器名称
        registration.setName("customFilter");
        //拦截路径
        registration.addUrlPatterns("/*");
        //设置顺序
        registration.setOrder(10);
        return registration;
    }

    @Bean
    public Filter customFilter() {
        return new CustomFilter();
    }
}
```

**注册多个时，就注册多个FilterRegistrationBean即可**

**小技巧–**(2018-08-25修订)

1. 通过**过滤器的java类名称**，进行顺序的约定，比如`LogFilter`和`AuthFilter`，此时`AuthFilter`就会比`LogFilter`先执行，因为首字母`A`比`L`前面。
2. 过滤器的实现除了实现Filter接口外，还可以继承 spring 过滤器 OncePerRequestFilter 实现自定义过滤器，OncePerRequestFilter，确保在[一次](https://www.baidu.com/s?wd=%E4%B8%80%E6%AC%A1&tn=24004469_oem_dg&rsv_dl=gh_pl_sl_csd)请求中只通过一次filter。OncePerRequestFilter 详解参考：<https://www.cnblogs.com/shanshouchen/archive/2012/07/31/2617412.html>

#### spring boot监听器

> Listeeshi是servlet规范中定义的一种特殊类。用于监听servletContext、HttpSession和servletRequest等域对象的创建和销毁事件。监听域对象的属性发生修改的事件。用于在事件发生前、发生后做一些必要的处理。一般是获取在线人数等业务需求。

**创建一个ServletRequest监听器(其他监听器ServletContext类似创建)**

```java
@WebListener
@Slf4j
public class Customlister implements ServletRequestListener{

    @Override
    public void requestDestroyed(ServletRequestEvent sre) {
        log.info("监听器：销毁");
    }

    @Override
    public void requestInitialized(ServletRequestEvent sre) {
        log.info("监听器：初始化");
    }

}
```

和创建过滤器一样，在启动类中加入`@ServletComponentScan`进行自动注册即可。

也可以不用@WebListener这个注解，在启动类Application中添加bean或者另外创建配置文件即可。

**添加监听器配置文件ListenerConfig**

```java
@Configuration
public class ListenerConfig {
    @Bean
    public ServletListenerRegistrationBean servletListenerRegistrationBean() {
        ServletListenerRegistrationBean slrBean = new ServletListenerRegistrationBean();
        slrBean.setListener(new Customlister());
        return slrBean;
    }
}
```

#### spring boot 拦截器

> 以上的过滤器、监听器都属于**Servlet**的api，我们在开发中处理利用以上的进行过滤web请求时，还可以使用`Spring`提供的拦截器(`HandlerInterceptor`)进行更加精细的控制。

**1.编写自定义拦截器类**

- 可通过继承HandlerInterceptorAdapter类实现
- 可通过实现HandlerInterceptor接口实现

```java
@Slf4j
public class CustomHandlerInterceptor implements HandlerInterceptor{

	@Override
	public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler)
			throws Exception {
		log.info("preHandle:请求前调用");
		//返回 false 则请求中断
		return true;
	}

	@Override
	public void postHandle(HttpServletRequest request, HttpServletResponse response, Object handler,
			ModelAndView modelAndView) throws Exception {
		log.info("postHandle:请求后调用");

	}

	@Override
	public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex)
			throws Exception {
		log.info("afterCompletion:请求调用完成后回调方法，即在视图渲染完成后回调");

	}

}
```

**2.通过继承WebMvcConfigurerAdapter注册拦截器**

```java
@Configuration
public class WebMvcConfigurer extends WebMvcConfigurerAdapter{
	@Override
	 public void addInterceptors(InterceptorRegistry registry) {
		 //注册拦截器 拦截规则
		//多个拦截器时 以此添加 执行顺序按添加顺序
		registry.addInterceptor(getHandlerInterceptor()).addPathPatterns("/*");
	 }
	
	@Bean
	public static HandlerInterceptor getHandlerInterceptor() {
		return new CustomHandlerInterceptor();
	}
}
```

**请求链路说明**

![](../images/spring boot/请求链路图.png)