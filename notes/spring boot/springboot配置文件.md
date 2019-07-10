###springboot配置文件

#### 一、配置文件

SpringBoot使用一个全局的配置文件，配置文件名是固定的；

•application.properties

•application.yml

配置文件的作用：修改SpringBoot自动配置的默认值；SpringBoot在底层都给我们自动配置好；

官方语法规

YAML（YAML Ain’t Markup Language）

	YAML A Markup Language：是一个标记语言
	YAML isn’t Markup Language：不是一个标记语言；

标记语言：

	以前的配置文件；大多都使用的是 xxxx.xml文件；
	YAML：以数据为中心，比json、xml等更适合做配置文件；
	YAML：配置例子

YAML：配置例子

```yaml
server:
  port: 8081
12
```

​	相当于XML：

```xml
<server>
	<port>8081</port>
</server>
```

#### 二、YAML语法

#####1、基本语法

k:(空格)v：表示一对键值对（空格必须有）；

以**空格**的缩进来控制层级关系；只要是左对齐的一列数据，都是同一个层级的

```yaml
server:
    port: 8081
    path: /hello
```

属性和值也是大小写敏感；

#####2、值的写法

######字面量：普通的值（数字，字符串，布尔）
k: v：字面直接来写；

	字符串默认不用加上单引号或者双引号；
	
	“”：双引号；不会转义字符串里面的特殊字符；特殊字符会作为本身想表示的意思
	
	name: “zhangsan \n lisi”：输出；zhangsan 换行 lisi
	
	‘’：单引号；会转义特殊字符，特殊字符最终只是一个普通的字符串数据
	
	name: ‘zhangsan \n lisi’：输出；zhangsan \n lisi

######对象、Map（属性和值）（键值对）

​	k: v：在下一行来写对象的属性和值的关系；注意缩进

​	对象还是k: v的方式

```java
friends:
		lastName: zhangsan
		age: 20
```

行内写法：

```yaml
friends: {lastName: zhangsan,age: 18}
```

######数组（List、Set）：

用- 值表示数组中的一个元素

```yaml
pets:
 - cat
 - dog
 - pig
```

行内写法

```yaml
pets: [cat,dog,pig]
```

####三、配置文件值注入

配置文件 application.yml

```yaml
person:
    lastName: hello
    age: 20
    boss: true
    birth: 2018/03/18
    maps: {k1: v1,k2: 12}
    lists:
      - hfbin
      - zhaoliu
    dog:
      name: dog
      age: 12

```

javaBean：

```java
/**
 * 将配置文件中配置的每一个属性的值，映射到这个组件中
 * @ConfigurationProperties：告诉SpringBoot将本类中的所有属性和配置文件中相关的配置进行绑定；
 *      prefix = "person"：配置文件中哪个下面的所有属性进行一一映射
 *
 * 只有这个组件是容器中的组件，才能容器提供的@ConfigurationProperties功能；
 *
 */
@Component
@ConfigurationProperties(prefix = "person")
public class Person {

    private String lastName;
    private Integer age;
    private Boolean boss;
    private Date birth;

    private Map<String,Object> maps;
    private List<Object> lists;
    private Dog dog;

}
```

###### 1、@Value获取值和@ConfigurationProperties获取值比较

@Value是以前spring底层的，使用@Value需要一个一个参数指定，@ConfigurationProperties批量注入配置文件中的属性。更多比较如下：

| @ConfigurationProperties |          @Value          |            |
| :----------------------: | :----------------------: | :--------: |
|           功能           | 批量注入配置文件中的属性 | 一个个指定 |
|   松散绑定（松散语法）   |           支持           |   不支持   |
|           SpEL           |          不支持          |    支持    |
|      JSR303数据校验      |           支持           |   不支持   |
|       复杂类型封装       |           支持           |   不支持   |

配置文件yml还是properties他们都能获取到值；

如果说，我们只是在某个业务逻辑中需要获取一下配置文件中的某项值，使用@Value；

如果说，我们专门编写了一个javaBean来和配置文件进行映射，我们就直接使用@ConfigurationProperties；

######2、配置文件注入值数据校验

@Validated

@ConfigurationProperties支持JSR303数据校验，@Value不支持JSR303数据校验。

```java
@Component
@ConfigurationProperties(prefix = "person")
@Validated
public class Person {

 /**
     * <bean class="Person">
     *      <property name="lastName" value="字面量/${key}从环境变量、配置文件中获取值/#{SpEL}"></property>
     * <bean/>
     */

   //lastName必须是邮箱格式
   // @Email
    //@Value("${person.last-name}")
    private String lastName;
    //@Value("#{11*2}")
    private Integer age;
    //@Value("true")
    private Boolean boss;
}
```

######3、@PropertySource&@ImportResource&@Bean

@**PropertySource**：加载指定的配置文件；

person.properties

```ymal
person.last-name=hfbin
person.age=23
person.boss=true
```

Person.java

```java
@PropertySource(value = {"classpath:person.properties"})
@Component
@ConfigurationProperties(prefix = "person")
public class Person {

    private String lastName;
    private Integer age;
    private Boolean boss;
}
```

**@ImportResource**：导入Spring的配置文件，让配置文件里面的内容生效；

Spring Boot里面没有Spring的配置文件，我们自己编写的配置文件，也不能自动识别；

想让Spring的配置文件生效，加载进来；@ImportResource标注在一个配置类上

```java
@ImportResource(locations = {"classpath:beans.xml"})
导入Spring的配置文件让其生效
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">


    <bean id="helloService" class="cn.hfbin.demo01.service.HelloService"></bean>
</beans>

```

SpringBoot推荐给容器中添加组件的方式；推荐使用全注解的方式

1、配置类**@Configuration**------>Spring配置文件

2、使用**@Bean**给容器中添加组件

```java
/**
 * @Configuration：指明当前类是一个配置类；就是来替代之前的Spring配置文件
 *
 * 在配置文件中用<bean><bean/>标签添加组件
 *
 */
@Configuration
public class MyAppConfig {

    //将方法的返回值添加到容器中；容器中这个组件默认的id就是方法名
    @Bean
    public HelloService helloService02(){
        System.out.println("配置类@Bean给容器中添加组件了...");
        return new HelloService();
    }
}
```

#### 四、Profile

Profile是Spring对不同环境提供不同配置功能的支持，可以通过激活、 指定参数等方式快速切换环境 。

#####1、多Profile文件
我们在主配置文件编写的时候，文件名可以是 application-{profile}.properties/yml

比如开发环境：application-dev.properties

生产环境 ：application-prod.properties

默认使用application.properties的配置；

#####2、yml支持多文档块方式

```yml
server:
  port: 8081
spring:
  profiles:
    active: prod

---
server:
  port: 8083
spring:
  profiles: dev


---

server:
  port: 8084
spring:
  profiles: prod  #指定属于哪个环境

```

#####3、激活指定profile
​	1、在配置文件application.properties中指定 spring.profiles.active=dev

```shell
2、命令行：

java -jar spring-boot-02-config-0.0.1-SNAPSHOT.jar --spring.profiles.active=dev；

可以直接在测试的时候，配置传入命令行参数

3、虚拟机参数；

-Dspring.profiles.active=dev
```
*还可以使用@profile*注解是spring提供的一个用来标明当前运行环境的注解

#### 五、配置文件加载位置

springboot 启动会扫描以下位置的application.properties或者application.yml文件作为Spring boot的默认配置文件

–file:./config/

–file:./

–classpath:/config/

–classpath:/

优先级由高到底，高优先级的配置会覆盖低优先级的配置；

SpringBoot会从这四个位置全部加载主配置文件；互补配置；

我们还可以通过spring.config.location来改变默认的配置文件位置

项目打包好以后，我们可以使用命令行参数的形式，启动项目的时候来指定配置文件的新位置；指定配置文件和默认加载的这些配置文件共同起作用形成互补配置；

java -jar spring-boot-02-config-02-0.0.1-SNAPSHOT.jar --spring.config.location=G:/application.properties

这个对运维方面起到很大作用

####六、springboot配置文件的读取

在springboot工程中读取配置文件常见两种形式

**@value:**

这种形式比较简单，只需要在application.yml中用名称相同的变量配置值即可，在对应bean中用@value标注对应变量。 调用简单，但是功能不强，对复杂数据结构例如list，map，list，map等形式就配置起来较为复杂

**ConfigurationProperties方式：**

这种方式可以读取array，list，map，单值，及其组合。相应的配置也较为复杂。 首先在application.yml中添加相关配置

```yml
config-attributes:
  value: 345                          #对应单个值
  valueArray: 1,2,3,4,5,6,7,8,9      #对应数组
  valueList:                         #对应list
    -13579
    -246810
  valueMap:                          #对应map
    name: lili
    age: 20
    sex: female
  valueMapList:                      #对应list<map>
    - name: bob
      age: 21
    - name: caven
      age: 31
```

然后主类中添加注解@ConfigurationProperties

```java
@SpringBootApplication
@ConfigurationProperties
public class Configtest1Application {
	public static void main(String[] args) {
		SpringApplication.run(Configtest1Application.class, args);
	}
}
```

注意需要再pom中添加依赖（我用 的时springboot2.0.2版本，网上有人用其他版本的，据说可以不添加这个依赖）

```xml
<dependency>
        <groupId>org.springframework.boot</groupId>
	<artifactId>spring-boot-configuration-processor</artifactId>
	<optional>true</optional>
</dependency>

```

然后我们需要一个专用的bean来读取这个配置。

```java
@Component
@Getter
@Setter
@ConfigurationProperties(prefix = "config-attributes")
@ToString
public class Config {
    private String value;
    private String[] valueArray;
    private List<String> valueList;
    private HashMap<String, String> valueMap;
    private List<Map<String, String>> valueMapList;
}


```

其中的value，valuelist，valuemap分别对应配置文件中的相关内容
 注意@ConfigurationProperties(prefix = "config-attributes")中的config-attributes 对应application.yml中的前缀。
 随后再我们需要使用配置的值的地方，注入这个bean即可

```java
@RestController
public class ConfigController {

    @Autowired
    private Config config;

    @GetMapping("/config")
    public String getConfig() {
        return config.toString();
    }
}
```

推荐博文

- [Spring Boot 配置文件 yml与properties](<https://blog.csdn.net/qq_33524158/article/details/79600434#ListSet_98>)

- [springboot读取配置文件](<https://juejin.im/post/5b0440a5f265da0b886dc2e9>)

