#### springboot装饰着模式重包装request,response

> 在很多业务场景下，我们都需要获取请求中的请求参数，比如记录日志，加解密，验证签名等，如果在Filter中使用request.getInputStream()来获取流来得到body中的信息，可以达到预期效果，但是流的获取只能获取一次，之后再获取就获取不到了，导致controller无法拿到参数。
>
> 解决办法：HttpServletRequestWrapper,该类是HttpServletRequest的封装类，我们可以自定义一个类，继承HttpServletRequestWrapper，重写其中的getInputStream方法，让其可以重复获取我们想要的流,并且在Filter中的filterChain.doFilter(ServlerRequest, ServletResponse)方法中，传入我们的自定义类的实例，而不是原来的HttpServletRequest对象，由于我们的类是继承自HttpServletRequestWrapper类，所以当参数传入此方法是没有问题的。由于我们自定义类中的getInputStream方法已经被重写为可多次获取的版本，所以也就不用担心controller无法获取到数据。

**步骤一：自定义包装类继承HttpServletRequestWrapper**

```java
package com.cmpay.mca.filter.wrapper;

import javax.servlet.ReadListener;
import javax.servlet.ServletInputStream;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletRequestWrapper;
import java.io.*;


public class RewriteContentRequestWrapper extends HttpServletRequestWrapper {
    //保存流中的数据
    private byte[] content = null;
    HttpServletRequest req = null;

    public RewriteContentRequestWrapper(HttpServletRequest request) {
        super(request);
        this.req = request;
    }

    public RewriteContentRequestWrapper(HttpServletRequest request, byte[] requestBody) {
        super(request);
        this.content = requestBody;
        this.req = request;
    }

    /*
     * (non-Javadoc)
     *
     * @see javax.servlet.ServletRequestWrapper#getReader()
     */
    @Override
    public BufferedReader getReader() throws IOException {
        return new BufferedReader(new InputStreamReader(getInputStream()));
    }

    @Override
    public int getContentLength() {
        return content.length;
    }

    /*
     * (non-Javadoc)
     * 在调用getInputStream函数时，创建新的流，包含原先数据流中的信息，然后返回
     * @see javax.servlet.ServletRequestWrapper#getInputStream()
     */
    @Override
    public ServletInputStream getInputStream() throws IOException {
        return new ServletInputStream() {
            @Override
            public boolean isFinished() {
                return false;
            }

            @Override
            public boolean isReady() {
                return false;
            }

            @Override
            public void setReadListener(ReadListener readListener) {

            }

            private InputStream in = new ByteArrayInputStream(content);

            @Override
            public int read() throws IOException {
                return in.read();
            }
        };
    }
}

```

> 同样的，在有的业务场景下，除了需要重写HttpServletRequest之外可能还需要重写HttpServletResponse，比如在例如返回数据加密或者压缩等需求时，我们需要获取放回数据并进行相应的处理，所以我们可以用同样的方式对HttpServletResponse包装重写，代码如下

**步骤二：自定义包装类继承HttpServletResponseWrapper**

```java
package com.cmpay.mca.filter.wrapper;

import javax.servlet.ServletOutputStream;
import javax.servlet.WriteListener;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpServletResponseWrapper;
import java.io.*;

public class RewriteContentResponseWrapper extends HttpServletResponseWrapper {
    private ByteArrayOutputStream buffer = null;
    private ServletOutputStream out = null;
    private PrintWriter writer = null;

    /**
     * Constructs a response adaptor wrapping the given response.
     *
     * @param response
     * @throws IllegalArgumentException if the response is null
     */
    public RewriteContentResponseWrapper(HttpServletResponse response) throws IOException {
        super(response);
        buffer = new ByteArrayOutputStream();
        out = new WapperedOutputStream(buffer);
        writer = new PrintWriter(new OutputStreamWriter(buffer,
                this.getCharacterEncoding()));
    }

    @Override
    public ServletOutputStream getOutputStream() throws IOException {
        return out;
    }
   
    /**
     * 重写父类的 getWriter() 方法，将响应数据缓存在 PrintWriter 中
     */
    @Override
    public PrintWriter getWriter() throws UnsupportedEncodingException {
        return writer;
    }

    @Override
    public void flushBuffer() throws IOException {
        if (out != null) {
            out.flush();
        }
        if (writer != null) {
            writer.flush();
        }
    }

    @Override
    public void reset() {
        buffer.reset();
    }
    //获取缓存在 PrintWriter 中的响应数据
    public byte[] getResponseData() throws IOException {
        flushBuffer();
        return buffer.toByteArray();
    }

    public void setResponseData(byte[] content) throws IOException {
        buffer.write(content);
    }

    private class WapperedOutputStream extends ServletOutputStream {
        private ByteArrayOutputStream bos = null;

        public WapperedOutputStream(ByteArrayOutputStream stream)
                throws IOException {
            bos = stream;
        }
		//将数据写到 stream　中
        @Override
        public void write(int b) throws IOException {
            bos.write(b);
        }

        @Override
        public void write(byte[] b) throws IOException {
            bos.write(b, 0, b.length);
        }

        @Override
        public boolean isReady() {
            return false;
        }

        @Override
        public void setWriteListener(WriteListener writeListener) {

        }
    }
}

```

**步骤三：在过滤器中进行业务前处理或业务后处理**

> 在大多数场景下，重写HttpServletRequest是需要在请求业务之前进行处理，例如解密，验签，同样的重写HttpServletResponset是需要在请求业务之后进行处理，例如压缩，加密，显而易见这正好与过滤器结合使用，实际上绝大多数场景都是如此

**1.我们可以先创建一个工具类FilterHelper**

```java
package com.cmpay.mca.filter.support;

import com.cmpay.lemon.common.HttpMethod;
import com.cmpay.lemon.common.exception.LemonException;
import com.cmpay.lemon.common.utils.IOUtils;
import com.cmpay.lemon.common.utils.JudgeUtils;
import com.cmpay.mca.utils.ByteUtil;

import javax.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.io.InputStream;
import java.net.URLDecoder;
import java.util.Arrays;

public class FilterHelper {

    public static final String REQUEST_ATTRIBUTE_BODY = "REQUEST_ATTRIBUTE_BODY";
    public static final String REQUEST_BYTE_BODY = "REQUEST_BYTE_BODY";


    public static final Object NULL_OBJECT = new Object();

    /**
     * 获取非get请求报文体<String>
     *
     * @param request
     * @return
     */
    public static String getRequestBodyToString(HttpServletRequest request) {
        if (null != request.getAttribute(REQUEST_ATTRIBUTE_BODY)) {
            return request.getAttribute(REQUEST_ATTRIBUTE_BODY) == NULL_OBJECT ? null : (String) request.getAttribute(REQUEST_ATTRIBUTE_BODY);
        }

        String body = IOUtils.toStringIgnoreException(getRequestInputStream(request));
        request.setAttribute(REQUEST_ATTRIBUTE_BODY, body == null ? NULL_OBJECT : body);
        return body;
    }

    /**
     * 非get请求获取报文体<byte>
     *
     * @param request
     * @return
     */
    public static byte[] getRequestBodyToByte(HttpServletRequest request) {
        if (null != request.getAttribute(REQUEST_BYTE_BODY)) {
            return request.getAttribute(REQUEST_BYTE_BODY) == NULL_OBJECT ? null : (byte[]) request.getAttribute(REQUEST_BYTE_BODY);
        }
        try {
            byte[] body = ByteUtil.hexToByteArray(IOUtils.toStringIgnoreException(getRequestInputStream(request)));
            request.setAttribute(REQUEST_BYTE_BODY, body == null ? NULL_OBJECT : body);
            return body;
        } catch (Exception ex) {
            throw LemonException.create(ex);
        }
    }

    /**
     * 获取签名源串
     *
     * @param request
     * @return
     */
    public static String getSignatureContent(HttpServletRequest request) {
        if (request.getMethod().equals(HttpMethod.GET.name())) {
            try {
                String queryString = request.getQueryString();
                String[] array = queryString.split("&");
                if (JudgeUtils.isBlank(queryString) || queryString.indexOf("&") < 1) {
                    return queryString;
                }
//                 先拆分再对字段进行decode后再重新赋值
                for (int i = 0; i < array.length; i++) {
                    array[i] = URLDecoder.decode(array[i], "UTF-8");
                }
                Arrays.sort(array);
                StringBuffer buffer = new StringBuffer();
                for (int i = 0; i < array.length; i++) {
                    buffer.append(array[i]).append("&");
                }
                return buffer.substring(0, buffer.length() - 1);
            } catch (Exception e) {
                throw new LemonException(e);
            }
        }
        return getRequestBodyToString(request);
    }

    public static InputStream getRequestInputStream(HttpServletRequest request) {
        try {
            return request.getInputStream();
        } catch (IOException ex) {
            throw LemonException.create(ex);
        }
    }
}

```

**2.在过滤器中进行使用处理**

> 为了防止重复加解密或验签名，我们过滤器通过继承OncePerRequestFilter来实现

```java
package com.cmpay.mca.filter;

import com.cmpay.mca.core.IProcessor;
import com.cmpay.mca.core.KeyCapable;
import com.cmpay.mca.filter.support.FilterHelper;
import com.cmpay.mca.filter.wrapper.RewriteContentRequestWrapper;
import com.cmpay.mca.filter.wrapper.RewriteContentResponseWrapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.annotation.Resource;
import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;

@WebFilter(filterName="customFilter",urlPatterns={"/*"})
public class SampleFilter extends OncePerRequestFilter {

    private static final Logger logger =          LoggerFactory.getLogger(SampleFilterclass);

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        HttpServletResponse responseWrapper = new RewriteContentResponseWrapper(response);
        HttpServletRequest requestWrapper = new RewriteContentRequestWrapper(request, FilterHelper.getRequestBodyToByte(request));
            //前置业务处理
            filterChain.doFilter(requestWrapper, responseWrapper);
            //后置业务处理
        	responseWrapper.getResponseData();
        
    }
}

```

