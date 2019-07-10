[TOC]



#### springboot注解自定义响应数据

> 主要讲 Spring MVC 如何动态的去返回 Json 数据 在我们做 Web 接口开发的时候， 经常会遇到需要定制的返回数据字段，有的字段需要返回，有的字段不需要返回，Spring MVC 默认使用转json框架是 jackson。 大家也知道， jackson 可以在实体类内加注解，来指定序列化规则，但是那样比较不灵活，不能实现我们目前想要达到的这种情况。我们要做的就是通过自定义注解，来更加灵活，细粒化控制 json 格式的转换。

#####原生jackson 编程式过滤字段

jackson 中， 我们可以在实体类上加上 @JsonFilter 注解，并且通过 ObjectMapper.setFilterProvider 来进行过滤规则的设置。 这里简单介绍一下 setFilterProvider 的使用

```java
@JsonFilter("ID-TITLE")
class Article {
 private String id;
 private String title;
 private String content;
 // ... getter/setter
}
 
class Demo {
 public void main(String args[]) {
  ObjectMapper mapper = new ObjectMapper();
  // SimpleBeanPropertyFilter.filterOutAllExcept("id,title")
  // 过滤除了 id,title 以外的所有字段，也就是序列化的时候，只包含 id 和 title
  mapper.setFilterProvider(new SimpleFilterProvider().addFilter("ID-TITLE",
          SimpleBeanPropertyFilter.filterOutAllExcept("id,title"))); 
 
  String filterOut = mapper.writeValueAsString(new Article());
  mapper = new ObjectMapper();
  // SimpleBeanPropertyFilter.serializeAllExcept("id,title")
  // 序列化所有字段，但是排除 id 和 title，也就是除了 id 和 title之外，其他字段都包含进 json
  mapper.setFilterProvider(new SimpleFilterProvider().addFilter("ID-TITLE",
      SimpleBeanPropertyFilter.serializeAllExcept(filter.split("id,title"))));
 
  String serializeAll = mapper.writeValueAsString(new Article());
 
  System.out.println("filterOut:" + filterOut);
  System.out.println("serializeAll :" + serializeAll);  
 }
}

```

输出结果

```java
filterOut:{id: "", title: ""}
serializeAll:{content:""}
```

##### 自定义注解过滤字段

**步骤一：封装json转换**

通过上面的代码，我们发现，可以使用 setFilterProvider 来灵活的处理需要过滤的字段。不过上面的方法还有一些缺陷就是，还是要在 原来的 model 上加注解，这里我们使用 ObjectMapper.addMixIn(Class<?> type, Class<?> mixinType) 方法，这个方法就是讲两个类的注解混合，让第一个参数的类能够拥有第二个参数类的注解。让需要过滤的 model 和 @JsonFilter 注解解除耦合

```java
package com.cmpay.mca.jackson;

import com.cmpay.lemon.common.utils.StringUtils;
import com.cmpay.mca.enums.FilterMode;
import com.fasterxml.jackson.annotation.JsonFilter;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.ser.impl.SimpleBeanPropertyFilter;
import com.fasterxml.jackson.databind.ser.impl.SimpleFilterProvider;

/**
 * 序列化字段过滤
 *
 */
public class JsonFilterSerializer {

    private static final String INCLUDE = "INCLUDE";
    private static final String EXCLUDE = "EXCLUDE";

    private ObjectMapper mapper;

    public JsonFilterSerializer(ObjectMapper mapper) {
        this.mapper = mapper;
    }

    /**
     * @param fields
     * @param mode
     */
    public void filter(Class clz, String[] fields, FilterMode mode) {
        if (FilterMode.INCLUDE.equals(mode)) {
            mapper.setFilterProvider(new SimpleFilterProvider().addFilter(INCLUDE,
                    SimpleBeanPropertyFilter.filterOutAllExcept(fields)));
            mapper.addMixIn(clz, Include.class);
        } else if (FilterMode.EXLUDE.equals(mode)) {
            mapper.setFilterProvider(new SimpleFilterProvider().addFilter(EXCLUDE,
                    SimpleBeanPropertyFilter.serializeAllExcept(fields)));
            mapper.addMixIn(clz, Exclude.class);
        }
    }

    public String writeValueAsString(Object object) throws JsonProcessingException {
        return mapper.writeValueAsString(object);
    }

    @JsonFilter(EXCLUDE)
    interface Exclude{

    }
    @JsonFilter(INCLUDE)
    interface Include{

    }
}

```

**步骤二：自定义注解**

我们需要实现文章开头的那种效果。这里我自定义了一个注解，可以加在方法上，这个注解是用来携带参数给 JsonFilterSerializer.filter 方法的，就是某个类的某些字段需要过滤或者包含。

```java
package com.cmpay.mca.jackson;

import com.cmpay.mca.enums.FilterMode;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

 
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface FieldsFilter {
    Class type();
    String[] fields() default {};
    FilterMode mode() default FilterMode.EXLUDE;
}

```

**步骤三：实现 Spring MVC 的 HandlerMethodReturnValueHandler**

HandlerMethodReturnValueHandler 接口 Spring MVC 用于处理请求返回值 。 看一下这个接口的定义和描述，接口有两个方法supportsReturnType 用来判断 处理类 是否支持当前请求， handleReturnValue 就是具体返回逻辑的实现。

```java
package com.cmpay.mca.mvc;

import com.cmpay.mca.jackson.FieldsFilter;
import com.cmpay.mca.jackson.JsonFilterSerializer;
import org.springframework.core.MethodParameter;
import org.springframework.web.context.request.NativeWebRequest;
import org.springframework.web.method.support.HandlerMethodReturnValueHandler;
import org.springframework.web.method.support.ModelAndViewContainer;

import javax.servlet.http.HttpServletResponse;
import java.util.Optional;


public class ResponseFieldsFilterHandler implements HandlerMethodReturnValueHandler {

    private JsonFilterSerializer jsonSerializer;
    private final static String[] DEFAULT_FIELDS = {"msgId", "startDateTime", "locale", "entryTx", "business", "svrNm", "txCd", "sch", "stf", "stp", "ect", "clientIp", "stm", "psn", "csn", "tsn", "ver", "gwa", "transactionContext"};

    public ResponseFieldsFilterHandler(JsonFilterSerializer jsonSerializer) {
        this.jsonSerializer = jsonSerializer;
    }

    @Override
    public boolean supportsReturnType(MethodParameter methodParameter) {
        return methodParameter.hasMethodAnnotation(FieldsFilter.class);
    }

    @Override
    public void handleReturnValue(Object o, MethodParameter methodParameter,
                                  ModelAndViewContainer modelAndViewContainer,
                                  NativeWebRequest nativeWebRequest) throws Exception {
        modelAndViewContainer.setRequestHandled(true);

        HttpServletResponse response = nativeWebRequest.getNativeResponse(HttpServletResponse.class);
        Optional.ofNullable(methodParameter.getMethodAnnotation(FieldsFilter.class)).ifPresent(s -> {
            jsonSerializer.filter(s.type(), s.fields().length > 0 ? s.fields() : DEFAULT_FIELDS, s.mode());
        });
        response.getWriter().write(jsonSerializer.writeValueAsString(o));
    }
}

```

**步骤四：自定义的ResponseFieldsFilterHandler替换原有的RequestResponseBodyMethodProcessor **

```java
@Configuration
public class WebMvcConfiguration {

    @Autowired
    private RequestMappingHandlerAdapter adapter;
    @Autowired
    private ObjectMapper objectMapper;

    @Bean
    public JsonFilterSerializer jsonFilterSerializer() {
        return new JsonFilterSerializer(objectMapper);
    }

    @Bean
    public ResponseFieldsFilterHandler jsonIgnoreHandler() {
        return new ResponseFieldsFilterHandler(jsonFilterSerializer());
    }

    @PostConstruct
    public void init() throws Exception {
        final List<HandlerMethodReturnValueHandler> originalHandlers = new ArrayList<>(
                adapter.getReturnValueHandlers());
        final int deferredPos = obtainValueHandlerPosition(originalHandlers, HttpEntityMethodProcessor.class);
        originalHandlers.add(deferredPos - 1, jsonIgnoreHandler());
        originalHandlers.add(jsonIgnoreHandler());
        adapter.setReturnValueHandlers(originalHandlers);
    }
		
  // 将顺序定位在RequestResponseBodyMethodProcessor之前处理，这样就会使用我们自定义的处理放回
    private int obtainValueHandlerPosition(final List<HandlerMethodReturnValueHandler> originalHandlers, Class<?> handlerClass) {
        for (int i = 0; i < originalHandlers.size(); i++) {
            final HandlerMethodReturnValueHandler valueHandler = originalHandlers.get(i);
            if (handlerClass.isAssignableFrom(valueHandler.getClass())) {
                return i;
            }
        }
        return -1;
    }
}
```

最终实现效果如下:

```java
@FieldsFilter(type = GenericRspDTO.class)
    @PostMapping("/path")
    public GenericRspDTO<RspNobodyDTO> mblAsyncObtain(@Validated @RequestBody ReqDTO reqDTO){
        return GenericRspDTO.newInstance(MsgEnum.SUCCESS, new RspNobodyDTO());
    }
```

推荐博文：

- [Spring MVC 更灵活的控制 json 返回问题（自定义过滤字段）](<https://www.jb51.net/article/105633.htm>)
- <https://www.jianshu.com/p/bad06d4fe9df>

