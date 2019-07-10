####网络请求中的加解密

#### 网络请求一般有两种协议：HTTP 和 HTTPS。

> HTTP：只要收到请求，服务器就会响应。如果不对客户端请求和服务器的响应做加密处理。传输的数据很容易被劫持，非常不安全。

> HTTPS: HTTPS 就是 HTTP 协议加上一层 SSL 协议的加密处理。SSL 证书就是遵守 SSL 协议，由受信任的证书颁发机构在验证服务器身份后颁发给企业。

#### HTTPS 客户端与服务器交互过程：

1. 客户端发送请求，服务器返回公钥给客户端；
2. 客户端生成对称加密秘钥，用公钥对其进行加密后，返回给服务器；
3. 服务器收到后，利用私钥解开得到对称加密秘钥，保存；
4. 之后的交互都使用对称加密后的数据进行交互。

#### 加密算法简述

- 对称加密算法：加密解密都使用相同的秘钥，速度快，适合对大数据加密，方法有DES，3DES，AES等。
- 非对称加密算法: 非对称加密算法需要两个密钥：公开密钥（publickey）和私有密钥（privatekey）
  公开密钥与私有密钥是一对，可逆的加密算法，用公钥加密，用私钥解密，用私钥加密，用公钥解密，速度慢，适合对小数据加密，方法有RSA。
- 散列算法（加密后不能解密，上面都是可以解密的）: 用于密码的密文存储，服务器端是判断加密后的数据
  不可逆加密方法：MD5、SHA1、SHA256、SHA512。

[网络请求中的加解密](https://www.jianshu.com/p/623007e3ae34)

####springboot API安全设计原则

接口的安全性主要围绕Token、Timestamp和Sign三个机制展开设计，保证接口的数据不会被篡改和重复调用，下面具体来看：

**Token授权机制**：用户使用用户名密码登录后服务器给客户端返回一个Token（*通常是UUID*），并将Token-UserId以键值对的形式存放在缓存服务器中。服务端接收到请求后进行Token验证，如果Token不存在，说明请求无效。**Token是客户端访问服务端的凭证**。

**时间戳超时机制**：用户每次请求都带上当前时间的时间戳timestamp，服务端接收到timestamp后跟当前时间进行比对，如果时间差大于一定时间（*比如5分钟*），则认为该请求失效。**时间戳超时机制是防御DOS攻击的有效手段。**

**签名机制**：将 **Token** 和 **时间戳** 加上其他请求参数再用MD5或SHA-1算法（可根据情况加点盐）加密，加密后的数据就是本次请求的签名sign，服务端接收到请求后以同样的算法得到签名，并跟当前的签名进行比对，如果不一样，说明参数被更改过，直接返回错误标识。**签名机制保证了数据不会被篡改。**

**拒绝重复调用（非必须）**：客户端第一次访问时，将签名sign存放到缓存服务器中，**超时时间设定为跟时间戳的超时时间一致，**二者时间一致可以保证无论在timestamp限定时间内还是外 URL都只能访问一次。如果有人使用同一个URL再次访问，如果发现缓存服务器中已经存在了本次签名，则拒绝服务。如果在缓存中的签名失效的情况下，有人使用同一个URL再次访问，则会被时间戳超时机制拦截。这就是为什么要求时间戳的超时时间要设定为跟时间戳的超时时间一致**。拒绝重复调用机制确保URL被别人截获了也无法使用（如抓取数据）。**

| 参数 | 必选 | 类型 | 作用 |
| :----: | :----: | :----: | :----: |
| Token | 是 | String | 调用方标识，保障其身份是来自本系统认证过的，有效识别用户身份 |
| sign | 是 | String | 接口参数的key,value的记录，防止参数值被篡改，防止伪装请求 |
| timestamp | 否 | int | 时间戳，防止重放攻击 |

整个流程如下：

> 1、客户端通过用户名密码登录服务器并获取Token
>
> 2、客户端生成时间戳timestamp，并将timestamp作为其中一个参数
>
> 3、客户端将所有的参数，包括Token和timestamp按照自己的算法进行排序加密得到签名sign
>
> 4、将token、timestamp和sign作为请求时必须携带的参数加在每个请求的URL后边（http://url/request?token=123&timestamp=123&sign=123123123）
>
> 5、服务端写一个过滤器对token、timestamp和sign进行验证，只有在**token有效、timestamp未超时、缓存服务器中不存在sign**三种情况同时满足，本次请求才有效

在以上三中机制的保护下，

如果有人劫持了请求，并对请求中的参数进行了修改，签名就无法通过；

如果有人使用已经劫持的URL进行DOS攻击，服务器则会因为缓存服务器中已经存在签名或时间戳超时而拒绝服务，所以DOS攻击也是不可能的；

最后说一句，所有的安全措施都用上的话有时候难免太过复杂，在实际项目中需要根据自身情况作出裁剪，比如可以只使用签名机制就可以保证信息不会被篡改，或者定向提供服务的时候只用Token机制就可以了。如何裁剪，全看项目实际情况和对接口安全性的要求~

####项目中如何设计接口的安全性？

> api接口安全性设计原则属于正常业务逻辑之外的业务，需要在请求真正的业务逻辑之前进行预处理，如果项目架构为微服务架构，我们可以选择在网关进行相应的处理，当然如果不在网关处理，我们也可以在请求接口之前的**过滤器**中进行预处理，在请求真正的业务之前，我们对本次请求进行一道验证，对请求体的解密，验证请求签名，这样既对业务逻辑无顷入，又可实现接口的安全性，接下来我们通过代码来实现

首先是过滤器的配置，根据功能单一原则我们设计两个过滤器

- 加解密过滤器
- 验签过滤器

```java
@Configuration
@ConditionalOnWebApplication
public class WebAutoConfiguration {

    @Bean
    public SignatureVerifyFilter signatureVerifyFilter() {
        return new SignatureVerifyFilter();
    }
    @Bean
    public EncryptAndDecryptFilter encryptAndDecryptFilter() {
        return new EncryptAndDecryptFilter();
    }

    @Bean
    public FilterRegistrationBean signatureVerifyFilterRegistration() {
        FilterRegistrationBean registration = new FilterRegistrationBean();
        registration.setFilter(signatureVerifyFilter());
        registration.addUrlPatterns("/mac/*");
        registration.setName("signatureVerifyFilter");
        registration.setOrder(FilterOrder.SIGNATURE_ORDER);
        return registration;
    }

    @Bean
    public FilterRegistrationBean encryptAndDecryptFilterRegistration() {
        FilterRegistrationBean registration = new FilterRegistrationBean();
        registration.setFilter(encryptAndDecryptFilter());
        registration.addUrlPatterns(new String[]{"/security/login/*", "/mac/base/*"});
        registration.setName("encryptAndDecryptFilter");
        registration.setOrder(FilterOrder.DECRYPT_ORDER);
        return registration;
    }
}

```

创建一个接口来统一格式，提升代码可读写和维护性，具体意义看代码就可以理解，不再描述

```java
public interface IProcessor<T, S> {
	/** 判断是否需要加工处理 */
    boolean shouldProcess(S s);
	/** 传入需处理的对象，并放回处理后的对象*/
    T process(S s);
	/** 传入需处理的对象，无返回*/
    void processNoneBack(S s);
}
```

######步骤一：设计报文的加解密机制

> 概念：前端在发送报文之前进行加密（post请求，get请求没有请求报文不需加密），后台接收并解密，后台对返回结果进行加密，前端接收后进行解密，这样可以有效的防止请求及响应报文被募改，同时由于我们需要在过滤中获取请求报文，为防止后续的controller无法获取的问题，我们需要使用包装类，具体可参考[链接](springboot重包装request,response)。要点：前后端使用同样的的加解密算法及盐（key或字符串）

**加密处理实现类**

```java
@Component
public class EncryptProcessor implements IProcessor<String, HttpServletResponse> {

    @Override
    public boolean shouldProcess(HttpServletResponse response) {
        return true;
    }

    @Override
    public String process(HttpServletResponse response) {
        RewriteContentResponseWrapper responseWrapper = (RewriteContentResponseWrapper)response;
        String cipherText = "";
        try {
            byte[] content = responseWrapper.getResponseData();
            if(content.length <= 0) {
                return cipherText;
            }
            //请求上下文中存储key和算法
            SecretKey secretKey = (SecretKey) LemonContext.getFromCurrentContext(Constant.CONTEXT_SECRET_KEY);
            cipherText = AESEncryptorUtil.encryptToString(secretKey.getKey().getSecretKey(), secretKey.getKey().getOffset(), content);
        } catch (Exception e) {
            LemonException.throwLemonException(MsgEnum.ENCRYPT_ERROR, e);
        } finally {
            LemonContext.removeFromCurrentContext(Constant.CONTEXT_SECRET_KEY);
        }
        return cipherText;
    }

    @Override
    public void processNoneBack(HttpServletResponse response) {

    }
}

```

**解密处理实现类**

```java
@Component
public class DecryptProcessor implements IProcessor<byte[], HttpServletRequest> {

    @Value("${mca.filter.encrypt.encoding:UTF-8}")
    private String encoding;

    /**POST请求需要进行解密处理 */
    @Override
    public boolean shouldProcess(HttpServletRequest request) {
        return JudgeUtils.notEquals(request.getMethod(), HttpMethod.GET.name()) && JudgeUtils.isNotNull(FilterHelper.getRequestBodyToByte(request));
    }

    @Override
    public byte[] process(HttpServletRequest request) {
        SecretKey secretKey = (SecretKey) LemonContext.getFromCurrentContext(Constant.CONTEXT_SECRET_KEY);
        byte[] plaintext = null;
        try {
            plaintext = AESEncryptorUtil.decryptToByte(secretKey.getKey().getSecretKey(), secretKey.getKey().getOffset(), FilterHelper.getRequestBodyToByte(request));
        } catch (Exception e) {
            LemonException.throwLemonException(MsgEnum.FILTER_DECRYPT_FAIL, e);
        }
        return plaintext;
    }

    @Override
    public void processNoneBack(HttpServletRequest request) {
    }
}
```

**加解密过滤器实现**

```java

public class EncryptAndDecryptFilter extends OncePerRequestFilter {

    private static final Logger logger = LoggerFactory.getLogger(EncryptAndDecryptFilter.class);

    @Autowired
    private IProcessor<String, HttpServletResponse> encryptProcessor;
 	@Autowired
    private IProcessor<byte[], HttpServletRequest> decryptProcessor;
    @Autowired
    private IProcessor<KeyCapable, HttpServletRequest> keyProcessor;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        HttpServletResponse responseWrapper = new RewriteContentResponseWrapper(response);

        // 从数据库中获取加解密密钥和对应的算法，保存在请求上下文中，还可在此判断请求是否合法，例如请求地址是否存在，请求头是否正确，是否具备请求权限等
        if (keyProcessor.shouldProcess(request)) {
            keyProcessor.processNoneBack(request);
        }

        // post请求需要对请求报文进行解密，get请求直接通过
        if (!decryptProcessor.shouldProcess(request)) {
            HttpServletRequest requestWrapper = new RewriteContentRequestWrapper(request, FilterHelper.getRequestBodyToByte(request));
            filterChain.doFilter(requestWrapper, responseWrapper);
        } else {
            byte[] plaintext = decryptProcessor.process(request);
            if (logger.isDebugEnabled()) {
                logger.debug("Decrypted request body success. plaintext: {} .", plaintext);
            }
            HttpServletRequest requestWrapper = new RewriteContentRequestWrapper(request, plaintext);
            filterChain.doFilter(requestWrapper, responseWrapper);
        }

        // response encrypt
        if (!encryptProcessor.shouldProcess(responseWrapper)) {
            return;
        }
        String cipherText = encryptProcessor.process(responseWrapper);
        if (logger.isDebugEnabled()) {
            logger.debug("Encrypt response body success. ciphertext: {} .", cipherText);
        }
        PrintWriter out = null;
        try {
            out = response.getWriter();
            out.print(cipherText);
        } finally {
            if (out != null) {
                out.flush();
                out.close();
            }
        }
    }
}

```

**加解密工具类**

```java

public class AESEncryptorUtil {

    private final static String KEY_ALGORITHM = "AES";
    private final static String CIPHER_ALGORITHM = "AES/CBC/PKCS5Padding";

    public static String encryptToString(String key, String offset, String content, String encoding) throws Exception {
        return ByteUtil.byteArrayToHex(encryptToByte(key, offset, content.getBytes(encoding)));
    }

    public static String encryptToString(String key, String offset, byte[] content) throws Exception {
        return ByteUtil.byteArrayToHex(encryptToByte(key, offset, content));
    }

    public static byte[] encryptToByte(String key, String offset, byte[] content) throws Exception {
        return encryptProcess(key, offset, content);
    }

    public static String decryptToString(String key, String offset, String content, String encoding) throws Exception {
        return new String(decryptProcess(key, offset, ByteUtil.hexToByteArray(content)), encoding);
    }

    public static byte[] decryptToByte(String key, String offset, byte[] content) throws Exception {
        return decryptProcess(key, offset, content);
    }

    public static byte[] encryptProcess(String key, String offset, byte[] content) throws Exception {
        Key secretKey = new SecretKeySpec(key.getBytes(), KEY_ALGORITHM);
        IvParameterSpec iv = new IvParameterSpec(offset.getBytes());
        Cipher cipher = Cipher.getInstance(CIPHER_ALGORITHM);
        cipher.init(Cipher.ENCRYPT_MODE, secretKey, iv);
        return cipher.doFinal(content);
    }

    private static byte[] decryptProcess(String key, String offset, byte[] content) throws Exception {
        Key secretKey = new SecretKeySpec(key.getBytes(), KEY_ALGORITHM);
        IvParameterSpec iv = new IvParameterSpec(offset.getBytes());
        Cipher cipher = Cipher.getInstance(CIPHER_ALGORITHM);
        cipher.init(Cipher.DECRYPT_MODE, secretKey, iv);
        return cipher.doFinal(content);
    }
}

```



######步骤二：设计请求参数的签名机制

> 概念：对参数进行加密，防止请求被拦截中途修改参数，要点：在请求发出之前对请求参数按照一定的算法加密

**签名处理实现类**

```java
@Component
public class SignatureProcessor implements IProcessor<String, HttpServletRequest> {

    @Override
    public boolean shouldProcess(HttpServletRequest request) {
        return true;
    }

    @Override
    public String process(HttpServletRequest request) {
        SecretKey secretKey = (SecretKey) LemonContext.getFromCurrentContext(Constant.CONTEXT_SECRET_KEY);
        String signText = null;
        try {
            signText = Encodes.encodeHex(Digests.md5((FilterHelper.getSignatureContent(request) + secretKey.getKey().getSecretKey()).getBytes()));
        } catch (Exception e) {
            LemonException.throwLemonException(MsgEnum.SIGN_ENCRYPT_ERROR, e);
        }
        return signText;
    }

    @Override
    public void processNoneBack(HttpServletRequest request) {

    }
}
```

**验签过滤器**

```java
public class SignatureVerifyFilter extends OncePerRequestFilter {

    private static final Logger logger = LoggerFactory.getLogger(SignatureVerifyFilter.class);

    private final static String SIGN = "x-lemon-sign";

    @Resource
    private IProcessor<String, HttpServletRequest> signatureProcessor;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        if(signatureProcessor.shouldProcess(request)) {
            String headSign = request.getHeader(SIGN);
            String signText = signatureProcessor.process(request);
            /** 不相等说明请求被募改*/
            if(JudgeUtils.notEquals(signText, headSign)) {
                if(logger.isErrorEnabled()) {
                    SecretKey secretKey = (SecretKey) LemonContext.getFromCurrentContext(Constant.CONTEXT_SECRET_KEY);
                    logger.error("Failed to do signature verify, signed value \"{}\", content \"{}\", secure \"{}\", algorithm \"{}\", required signed value \"{}\".",
                            headSign, FilterHelper.getSignatureContent(request), secretKey.getKey().getSecretKey(), secretKey.getSignAlgorithm(), signText);
                }
                RewriteContentResponseWrapper responseWrapper = (RewriteContentResponseWrapper)response;
                responseWrapper.reset();
                responseWrapper.setResponseData(errorMsg().getBytes());
                return;
            }
        }
        filterChain.doFilter(request, response);
    }

    private String errorMsg() {
        StringBuilder msg = new StringBuilder("{");
        msg.append("\"msgCd\"").append(":\"").append(MsgEnum.SIGN_VERIFY_ERROR.getMsgCd()).append("\",")
                .append("\"msgInfo\"").append(":\"").append(MsgEnum.SIGN_VERIFY_ERROR.getMsgInfo()).append("\"}");
        return msg.toString();
    }
}
```

**签名工具类**

```java
import org.apache.commons.codec.DecoderException;
import org.apache.commons.codec.binary.Base64;
import org.apache.commons.codec.binary.Hex;
import org.apache.commons.lang3.StringEscapeUtils;

import java.io.UnsupportedEncodingException;
import java.net.URLDecoder;
import java.net.URLEncoder;

/**
 *  封装各种格式的编码解码工具类.
 * 1.Commons-Codec的 hex/base64 编码
 * 2.自制的base62 编码
 * 3.Commons-Lang的xml/html escape
 * 4.JDK提供的URLEncoder
 *
 */
public class Encodes {

	public static final String DEFAULT_URL_ENCODING = "UTF-8";
	private static final char[] BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz".toCharArray();

	/**
	 * Hex编码.
	 */
	public static String encodeHex(byte[] input) {
		return new String(Hex.encodeHex(input));
	}

	/**
	 * Hex解码.
	 */
	public static byte[] decodeHex(String input) throws DecoderException {
		return Hex.decodeHex(input.toCharArray());
	}

	/**
	 * Base64编码.
	 */
	public static String encodeBase64(byte[] input) {
		return new String(Base64.encodeBase64(input));
	}
	
	/**
	 * Base64编码.
	 */
	public static String encodeBase64(String input) throws UnsupportedEncodingException {
		return new String(Base64.encodeBase64(input.getBytes(DEFAULT_URL_ENCODING)));
	}

	/**
	 * Base64解码.
	 */
	public static byte[] decodeBase64(String input) {
		return Base64.decodeBase64(input.getBytes());
	}
	
	/**
	 * Base64解码.
	 */
	public static String decodeBase64String(String input) throws UnsupportedEncodingException {
		return new String(Base64.decodeBase64(input.getBytes()), DEFAULT_URL_ENCODING);
	}

	/**
	 * Base62编码。
	 */
	public static String encodeBase62(byte[] input) {
		char[] chars = new char[input.length];
		for (int i = 0; i < input.length; i++) {
			chars[i] = BASE62[((input[i] & 0xFF) % BASE62.length)];
		}
		return new String(chars);
	}

	/**
	 * Html 转码.
	 */
	public static String escapeHtml(String html) {
		return StringEscapeUtils.escapeHtml4(html);
	}

	/**
	 * Html 解码.
	 */
	public static String unescapeHtml(String htmlEscaped) {
		return StringEscapeUtils.unescapeHtml4(htmlEscaped);
	}

	/**
	 * Xml 转码.
	 */
	public static String escapeXml(String xml) {
		return StringEscapeUtils.escapeXml10(xml);
	}

	/**
	 * Xml 解码.
	 */
	public static String unescapeXml(String xmlEscaped) {
		return StringEscapeUtils.unescapeXml(xmlEscaped);
	}

	/**
	 * URL 编码, Encode默认为UTF-8. 
	 */
	public static String urlEncode(String part) throws UnsupportedEncodingException {
		return URLEncoder.encode(part, DEFAULT_URL_ENCODING);
	}

	/**
	 * URL 编码
	 * @param part
	 * @param encoding
	 * @return
	 * @throws UnsupportedEncodingException
	 */
	public static String urlEncode(String part, String encoding) throws UnsupportedEncodingException {
		return URLEncoder.encode(part, encoding);
	}

	/**
	 * URL 解码, Encode默认为UTF-8.
	 *
	 * @param part
	 * @return
	 * @throws UnsupportedEncodingException
	 */
	public static String urlDecode(String part) throws UnsupportedEncodingException {
		return URLDecoder.decode(part, DEFAULT_URL_ENCODING);

	}

	/**
	 * URL 解码
	 * @param part
	 * @param encoding
	 * @return
	 * @throws UnsupportedEncodingException
	 */
	public static String urlDecode(String part, String encoding) throws UnsupportedEncodingException {
		return URLDecoder.decode(part, encoding);

	}
}
```

###### 步骤三：前端的请求方式

```java
/** get方式 */
 public static void getMethod() throws Exception{
        Map<String, String> header = new HashMap<String, String>();
        header.put("Content-Type", "text/plain;charset=utf-8");
        header.put("x-auth-token", "");
        header.put("x-app-id", "");
        header.put("x-app-deviceId", "");
        header.put("x-app-ver", "");
        Map<String, String> paramMap = new HashMap<String, String>();
        paramMap.put("random", "12345126");

        String content = SignUtils.getSignData(paramMap, "") + "hjashdj2378gas";
        String sign = Encodes.encodeHex(Digests.md5(content.getBytes()));
        header.put("x-lemon-sign", sign);
        String url = BaseUrlEnum.BASE_URL + "/mca/base/v1/register/sim-token";
        String result = HttpAgent.getInstance().get(url, header, paramMap);
        System.out.println(result);
        result = AESEncryptorUtil.decryptToString("hjashdj2378gas", "NJKDsyKGHENw", result);
        System.out.println("===================分割线=======================");
        System.out.println(result);
        System.out.println("===================分割线=======================");
 }
/** post方式 */
public static void getMethod() throws Exception{
         Map<String, String> header = new HashMap<String, String>();
        header.put("Content-Type", "text/plain;charset=utf-8");
        header.put("x-auth-token", "");
        header.put("x-app-id", "");
        header.put("x-app-deviceId", "");
        header.put("x-app-ver", "");
        Map<String, String> paramMap = new HashMap<String, String>();
        paramMap.put("random", "12345126");


        String content = JsonUtil.getJsonFromObject(paramMap);
        String ciphter = AESEncryptorUtil.encryptToString("hjashdj2378gas", "NJKDsyKGHENw", content);
        String sign = Encodes.encodeHex(Digests.md5((content + "u9dYuYlGVk39kkb5").getBytes()));
        header.put("x-lemon-sign", sign);
        String url = BaseUrlEnum.BASE_URL + "/mca/base/v1/present/sim-token";
        String result = HttpAgent.getInstance().post(url, header, ciphter);
        result = AESEncryptorUtil.decryptToString("hjashdj2378gas", "NJKDsyKGHENw", result);
        System.out.println("===================分割线=======================");
        System.out.println(result);
        System.out.println("===================分割线=======================");
}
```

推荐博文：[webapi token、参数签名是如何生成的](https://blog.csdn.net/kebi007/article/details/72861532)