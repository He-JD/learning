### springboot唯一上下文

>  在一次请求中，即一个线程内，若是需要为每次请求分别存储一些数据，各请求的数据可能不相同，我们可以怎么做呢，我们可以通过数据库或缓存实现持久化，但这样做无疑是增加数据库读写压力，也增加缓存的量，所以我们还可以通过请求上下文来实现，为了保证并发和每个线程都可以独立用户该线程的数据，互不影响我们可以使用，ThreadLocal

####ThreadLocal是什么

ThreadLocal是一个关于创建线程局部变量的类。

通常情况下，我们创建的变量是可以被任何一个线程访问并修改的。而使用ThreadLocal创建的变量只能被当前线程访问，其他线程则无法访问和修改

**使用场景**

- 实现单个线程单例以及单个线程上下文信息存储，比如交易id等
- 实现线程安全，非线程安全的对象使用ThreadLocal之后就会变得线程安全，因为每个线程都会有一个对应的实例
- 承载一些线程相关的数据，避免在方法中来回传递参数

> 关于ThreadLocal更详细的内容可参考文末链接

#### 创建请求唯一上下文工具类

```java

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;


public class LemonContext extends ConcurrentHashMap<Object, Object>{
    private static final long serialVersionUID = 2729826264846708794L;
    private static final Logger logger = LoggerFactory.getLogger(LemonContext.class);
    
    private static final ThreadLocal<LemonContext> currentContextHolder = new ThreadLocal<LemonContext>(){
        protected LemonContext initialValue() {
            if (logger.isDebugEnabled()) {
                logger.debug("Initializing 'LemonContext' by thread-bound.");
            }
            return new LemonContext();
        }
    };
    
    public static LemonContext getCurrentContext() {
        return currentContextHolder.get();
    }
    
    public static void setCurrentContext(LemonContext lemonContext) {
        if (logger.isDebugEnabled()) {
            logger.debug("Bound lemon context {} to thread.", lemonContext);
        }
        currentContextHolder.set(lemonContext);
    }

    public static void putToCurrentContext(Object key, Object value) {
        getCurrentContext().put(key, value);
    }

    public static Object getFromCurrentContext(Object key) {
        return getCurrentContext().get(key);
    }

    public static void removeFromCurrentContext(Object key) {
        getCurrentContext().remove(key);
    }

    public static void clearCurrentContext() {
        currentContextHolder.remove();
        if (logger.isDebugEnabled()) {
            logger.debug("Cleared thread-bound lemon context.");
        }
    }

    /**
     * clear form thread locale
     */
    public void clear() {
        currentContextHolder.remove();
        if (logger.isDebugEnabled()) {
            logger.debug("Cleared thread-bound lemon context.");
        }
    }

    /**
     *
     * @param key
     * @param defaultVal
     * @return
     * @deprecated as of lemon 2.0.0, in favor of using {@link #getBoolean}
     */
    @Deprecated
    public boolean getBooleanOrDefault(Object key, boolean defaultVal) {
        return Optional.ofNullable(get(key)).map(Boolean.class::cast).orElse(defaultVal);
    }

    /**
     *
     * @param key
     * @param defaultValue
     * @return
     */
    public Boolean getBoolean(Object key, Boolean defaultValue) {
        return Optional.ofNullable(get(key)).map(Boolean.class::cast).orElse(defaultValue);
    }

    /**
     *
     * @param key
     * @return
     */
    public Boolean getBoolean(Object key) {
        return Optional.ofNullable(get(key)).map(Boolean.class::cast).orElse(null);
    }

    /**
     *
     * @param key
     * @param defaultValue
     * @return
     */
    public String getString(Object key, String defaultValue) {
        return Optional.ofNullable(get(key)).map(String::valueOf).orElse(defaultValue);
    }

    /**
     *
     * @param key
     * @return
     */
    public String getString(Object key) {
        return Optional.ofNullable(get(key)).map(String::valueOf).orElse(null);
    }

    /**
     *
     * @param key
     * @param defaultValue
     * @return
     */
    public Integer getInteger(Object key, Integer defaultValue) {
        return Optional.ofNullable(get(key)).map(Integer.class::cast).orElse(defaultValue);
    }

    /**
     *
     * @param key
     * @return
     */
    public Integer getInteger(Object key) {
        return Optional.ofNullable(get(key)).map(Integer.class::cast).orElse(null);
    }

    /**
     *
     * @param key
     * @return
     */
    public Long getLong(Object key) {
        return Optional.ofNullable(get(key)).map(Long.class::cast).orElse(null);
    }

    /**
     *
     * @param key
     * @param defaultValue
     * @return
     */
    public Long getLong(Object key, Long defaultValue) {
        return Optional.ofNullable(get(key)).map(Long.class::cast).orElse(defaultValue);
    }

    /**
     *
     * @param key
     * @return
     */
    public Double getDouble(Object key) {
        return Optional.ofNullable(get(key)).map(Double.class::cast).orElse(null);
    }

    /**
     *
     * @param key
     * @param defaultValue
     * @return
     */
    public Double getDouble(Object key, Double defaultValue) {
        return Optional.ofNullable(get(key)).map(Double.class::cast).orElse(defaultValue);
    }

    /**
     *
     * @param key
     * @return
     */
    public LocalDateTime getLocalDataTime(Object key) {
        return Optional.ofNullable(get(key)).map(LocalDateTime.class::cast).orElse(null);
    }

    /**
     *
     * @param key
     * @param defaultValue
     * @return
     */
    public LocalDateTime getLocalDataTime(Object key, LocalDateTime defaultValue) {
        return Optional.ofNullable(get(key)).map(LocalDateTime.class::cast).orElse(defaultValue);
    }

}

```



推荐博文：

- [ 理解Java中的ThreadLocal](https://droidyue.com/blog/2016/03/13/learning-threadlocal-in-java/)
- [关于ConcurrentHashMap，你必须知道的事](https://www.jianshu.com/p/1a01d15df3f0)