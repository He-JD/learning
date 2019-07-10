#### springboot异常处理

> **springboot中，默认在发送异常时，会跳转值/error请求进行错误的展现，根据不同的Content-Type展现不同的错误结果，如json请求时，直接返回json格式参数。**

显然，默认的异常页是对用户或者调用者而言都是不友好的，所以一般上我们都会进行实现自己业务的异常提示信息

**创建统一的异常处理**

> 利用`@ControllerAdvice`和`@ExceptionHandler`定义一个统一异常处理类

- @ControllerAdvice：控制器增强，使@ExceptionHandler、@InitBinder、@ModelAttribute注解的方法应用到所有的 @RequestMapping注解的方法。
- @ExceptionHandler：异常处理器，此注解的作用是当出现其定义的异常时进行处理的方法

**创建异常类：CommonExceptionHandler**

```java
@ControllerAdvice
public class CommonExceptionHandler {

    /**
     *  拦截Exception类的异常
     * @param e
     * @return
     */
    @ExceptionHandler(Exception.class)
    @ResponseBody
    public Map<String,Object> exceptionHandler(Exception e){
        Map<String,Object> result = new HashMap<String,Object>();
        result.put("respCode", "9999");
        result.put("respMsg", e.getMessage());
        //正常开发中，可创建一个统一响应实体，如CommonResp
        return result; 
    }
    
   /**
     * 拦截 CommonException 的异常
     * @param ex
     * @return
     */
    @ExceptionHandler(CommonException.class)
    @ResponseBody
    public Map<String,Object> exceptionHandler(CommonException ex){
        log.info("CommonException：{}({})",ex.getMsg(), ex.getCode());
        Map<String,Object> result = new HashMap<String,Object>();
        result.put("respCode", ex.getCode());
        result.put("respMsg", ex.getMsg());
        return result; 
    }
}
```

由于工作中都是才有前后端分离开发模式，所以一般上都没有直接返回资源页的需求了，一般上都是返回固定的响应格式，如`respCode`、`respMsg`、`data`，前端通过判断`respCode`的值进行业务判断，是弹窗还是跳转页面。

#### springboot数据校验

> 在web开发时，对于请求参数，一般上都需要进行参数合法性校验的，原先的写法时一个个字段一个个去判断，这种方式太不通用了，所以java的`JSR 303: Bean Validation`规范就是解决这个问题的。

##### JSR303常用注解

| JSR提供的校验注解             | 含义                                                     |
| ----------------------------- | -------------------------------------------------------- |
| `@Null`                       | 被注释的元素必须为 null                                  |
| `@NotNull`                    | 被注释的元素必须不为 null                                |
| `@AssertTrue`                 | 被注释的元素必须为 true                                  |
| `@AssertFalse`                | 被注释的元素必须为 false                                 |
| `@Min(value)`                 | 被注释的元素必须是一个数字，其值必须大于等于指定的最小值 |
| `@Max(value)`                 | 被注释的元素必须是一个数字，其值必须小于等于指定的最大值 |
| `@DecimalMin(value)`          | 被注释的元素必须是一个数字，其值必须大于等于指定的最小值 |
| `@DecimalMax(value)`          | 被注释的元素必须是一个数字，其值必须小于等于指定的最大值 |
| `@Size(max=, min=)`           | 被注释的元素的大小必须在指定的范围内                     |
| `@Digits (integer, fraction)` | 被注释的元素必须是一个数字，其值必须在可接受的范围内     |
| `@Past`                       | 被注释的元素必须是一个过去的日期                         |
| `@Future`                     | 被注释的元素必须是一个将来的日期                         |
| `@Pattern(regex=,flag=)`      | 被注释的元素必须符合指定的正则表达式                     |


| Hibernate Validator提供的校验注解 | 含义                                   |
| --------------------------------- | -------------------------------------- |
| `@NotBlank(message =)`            | 验证字符串非null，且长度必须大于0      |
| `@Email`                          | 被注释的元素必须是电子邮箱地址         |
| `@Length(min=,max=)  `            | 被注释的字符串的大小必须在指定的范围内 |
| `@NotEmpty`                       | 被注释的字符串的必须非空               |
| `@Range(min=,max=,message=)`      | 被注释的元素必须在合适的范围内         |

*附[官方文档](https://docs.jboss.org/hibernate/stable/validator/reference/en-US/html_single/#preface)*

##### 自定义校验注解

> 自定义注解，主要时实现`ConstraintValidator`的处理类即可，这里已编写一个校验常量的注解为例：参数值只能为特定的值。

**自定义注解**

```java
@Documented
//指定注解的处理类
@Constraint(validatedBy = {ConstantValidatorHandler.class })
@Target({ METHOD, FIELD, ANNOTATION_TYPE, CONSTRUCTOR, PARAMETER })
@Retention(RUNTIME)
public @interface Constant {

   String message() default "{constraint.default.const.message}";

   Class<?>[] groups() default {};

   Class<? extends Payload>[] payload() default {};

   String value();

}
```

**注解处理类**

```java
 public class ConstantValidator implements ConstraintValidator<Constant, DemoDTO> {

        @Override
        public void initialize(DemoCheck constraintAnnotation) {

        }
        @Override
        public boolean isValid(DemoDTO value, ConstraintValidatorContext context) {
            if(JudgeUtils.isNull(value)){
                return  true;
            }
            if(!isPhone(StringUtils.toString(value.getMblNo()))){
                context.disableDefaultConstraintViolation();
                context.buildConstraintViolationWithTemplate(MsgCodeEnum.PHONEFORMAT_IS_INVALIDATE.getMsgCd())
                        .addConstraintViolation();
                return false;
            }
            return true;
        }

        public static boolean isPhone(String phone) {
            String regex = "^((13[0-9])|(14[5,7,9])|(15([0-3]|[5-9]))|(166)|(17[0,1,3,5,6,7,8])|(18[0-9])|(19[8|9]))\\d{8}$";
            if (phone.length() != 11) {
                return false;
            } else {
                Pattern p = Pattern.compile(regex);
                Matcher m = p.matcher(phone);
                boolean isMatch = m.matches();
                return isMatch;
            }

        }
    }

```

**大家看到在校验不通过时，返回的异常信息是不友好的，此时可利用统一异常处理，对校验异常进行特殊处理，特别说明下，对于异常处理类共有以下几种情况(被@RequestBody和@RequestParam注解的请求实体，校验异常类是不同的)**

```java
@ExceptionHandler(MethodArgumentNotValidException.class)
    public Map<String,Object> handleBindException(MethodArgumentNotValidException ex) {
        FieldError fieldError = ex.getBindingResult().getFieldError();
        log.info("参数校验异常:{}({})", fieldError.getDefaultMessage(),fieldError.getField());
        Map<String,Object> result = new HashMap<String,Object>();
        result.put("respCode", "01002");
        result.put("respMsg", fieldError.getDefaultMessage());
        return result;
    }

    @ExceptionHandler(BindException.class)
    public Map<String,Object> handleBindException(BindException ex) {
        //校验 除了 requestbody 注解方式的参数校验 对应的 bindingresult 为 BeanPropertyBindingResult
        FieldError fieldError = ex.getBindingResult().getFieldError();
        log.info("必填校验异常:{}({})", fieldError.getDefaultMessage(),fieldError.getField());
        Map<String,Object> result = new HashMap<String,Object>();
        result.put("respCode", "01002");
        result.put("respMsg", fieldError.getDefaultMessage());
        return result;
    }
```

