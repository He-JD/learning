### SpringSecurity处理注册逻辑

获取完用户信息，就跳转到了 <http://mrcode.cn/signup> ； 注册页面

为什么会跳转到注册页面呢？

我们来分析一下SocialAuthenticationFilter源码：

```java
	private Authentication doAuthentication(SocialAuthenticationService<?> authService, HttpServletRequest request, SocialAuthenticationToken token) {
		try {
			if (!authService.getConnectionCardinality().isAuthenticatePossible()) return null;
			token.setDetails(authenticationDetailsSource.buildDetails(request));
      //这里调用真正的认证过程 ，在下面代码中
			Authentication success = getAuthenticationManager().authenticate(token);
			Assert.isInstanceOf(SocialUserDetails.class, success.getPrincipal(), "unexpected principle type");
			updateConnections(authService, token, success);			
			return success;
		} catch (BadCredentialsException e) {
			// connection unknown, register new user?
			if (signupUrl != null) {
				// store ConnectionData in session and redirect to register page
        // 跳转到注册页面前把连接信息存入session，后续可通过工具类ProviderSignInUtils取出存在此处的信息
				sessionStrategy.setAttribute(new ServletWebRequest(request), ProviderSignInAttempt.SESSION_ATTRIBUTE, new ProviderSignInAttempt(token.getConnection()));
        // 跳转到注册页面，默认就是signup
				throw new SocialAuthenticationRedirectException(buildSignupUrl(request));
			}
			throw e;
		}
	}
```

```java
public Authentication authenticate(Authentication authentication) throws AuthenticationException {
		Assert.isInstanceOf(SocialAuthenticationToken.class, authentication, "unsupported authentication type");
		Assert.isTrue(!authentication.isAuthenticated(), "already authenticated");
		SocialAuthenticationToken authToken = (SocialAuthenticationToken) authentication;
		String providerId = authToken.getProviderId();
		Connection<?> connection = authToken.getConnection();
		// 如果当前社交账号没有与当前系统有对应的绑定用户
		String userId = toUserId(connection);
		if (userId == null) {
			throw new BadCredentialsException("Unknown access token");
		}

		UserDetails userDetails = userDetailsService.loadUserByUserId(userId);
		if (userDetails == null) {
			throw new UsernameNotFoundException("Unknown connected account id");
		}

		return new SocialAuthenticationToken(connection, userDetails, authToken.getProviderAccountData(), getAuthorities(providerId, userDetails));
	}
	// 查询当前数据库是否存在对应的绑定用户
	protected String toUserId(Connection<?> connection) {
		List<String> userIds = usersConnectionRepository.findUserIdsWithConnection(connection);
		// only if a single userId is connected to this providerUserId
		return (userIds.size() == 1) ? userIds.iterator().next() : null;
	}
```

在尝试认证时调用此方法，在认证的过程中，当前社交账户在当前系统中不存在关联的用户，则自动抛出异常跳转到注册页面。

#### 修改默认跳转的注册连接

```java
public class MerryyouSpringSocialConfigurer extends SpringSocialConfigurer {

    private String filterProcessesUrl;

    public MerryyouSpringSocialConfigurer(String filterProcessesUrl) {
        this.filterProcessesUrl = filterProcessesUrl;
    }

    @Override
    protected <T> T postProcess(T object) {
        SocialAuthenticationFilter filter = (SocialAuthenticationFilter) super.postProcess(object);
        filter.setFilterProcessesUrl(filterProcessesUrl);
        filter.setSignupUrl("/register");
        return (T) filter;
    }
}
```

上面配置类需要在security配置类的`protected void configure(HttpSecurity http)`方法中通过`apply(merryyouSpringSocialConfigurer)`才可生效。

#### 跳转到注册页面后，如何将获取到的第三方信息，和用户信息一起存入数据库

1. 怎么拿到用户授权后获取的用户信息?

2. 怎么让注册这个动作与social互动（也就是要把关联信息插入到数据库中）
3. 关键工具：org.springframework.social.connect.web.ProviderSignInUtils 
   目前不知道这个工具从哪里来的；

原理：原理就是把存储在session中的用户信息获取到；

```java
// 跳转到注册页面前把连接信息存入session，后续可通过工具类ProviderSignInUtils取出存在此处的信息
				sessionStrategy.setAttribute(new ServletWebRequest(request), ProviderSignInAttempt.SESSION_ATTRIBUTE, new ProviderSignInAttempt(token.getConnection()));
```

实现：

1. 提供获取用户信息的接口
2. 提供注册方法，然后使用工具类交互插入数据库，再次登录的时候就不会再次跳往注册页面了

获取用户的接口：

```java
@Controller
@Slf4j
public class UserController {

    @Autowired
    private SysUserService sysUserService;

    @Autowired
    private ProviderSignInUtils providerSignInUtils;

    /**
     * 获取第三方用户信息
     *
     * @param request
     * @return
     */
    @GetMapping("/social/info")
    public @ResponseBody
    SocialUserInfo getSocialUserInfo(HttpServletRequest request) {
        SocialUserInfo userInfo = new SocialUserInfo();
        Connection<?> connection = providerSignInUtils.getConnectionFromSession(new ServletWebRequest(request));
        userInfo.setProviderId(connection.getKey().getProviderId());
        userInfo.setProviderUserId(connection.getKey().getProviderUserId());
        userInfo.setNickname(connection.getDisplayName());
        userInfo.setHeadImg(connection.getImageUrl());
        return userInfo;
    }
  
    @PostMapping("/user/register")
    public String register(SysUser user, HttpServletRequest request, HttpServletResponse response) throws IOException {
        String userId = user.getUsername();
        SysUser result = sysUserService.findByUsername(userId);
        if (result == null) {
            //注册用户
            sysUserService.save(user);
        }
        //将业务系统的用户与社交用户绑定
        providerSignInUtils.doPostSignUp(userId, new ServletWebRequest(request));
        //跳转到index
        return "redirect:/index";
    }
  
}
```



####怎么让没有查询到userId的用户，不跳转到注册页面，默认注册一个账户？

在这样的场景下；有一部分网站是使用qq登录就默认为你注册一个账户。然后直接完成登录；

原理如下：

```java
//之前的源码中没有获取到 userId的地方 ：
org.springframework.social.security.SocialAuthenticationProvider#toUserId
protected String toUserId(Connection<?> connection) {
  List<String> userIds = usersConnectionRepository.findUserIdsWithConnection(connection);
  // only if a single userId is connected to this providerUserId
  return (userIds.size() == 1) ? userIds.iterator().next() : null;
}

org.springframework.social.connect.jdbc.JdbcUsersConnectionRepository#findUserIdsWithConnection

public List<String> findUserIdsWithConnection(Connection<?> connection) {
        ConnectionKey key = connection.getKey();
        List<String> localUserIds = jdbcTemplate.queryForList("select userId from " + tablePrefix + "UserConnection where providerId = ? and providerUserId = ?", String.class, key.getProviderId(), key.getProviderUserId());      
        if (localUserIds.size() == 0 && connectionSignUp != null) {
      // 注意这里，connectionSignUp 可以返回一个新的userid
      // 在这里就可以插入我们自己的逻辑，比如默认注册用户
            String newUserId = connectionSignUp.execute(connection);
            if (newUserId != null)
            {
                createConnectionRepository(newUserId).addConnection(connection);
                return Arrays.asList(newUserId);
            }
        }
        return localUserIds;
    }
```

实现：由于这样个性化的也属性使用方控制

```java
@Component
public class MyConnectionSignUp implements ConnectionSignUp {

    public String execute(Connection<?> connection) {
        //根据社交用户信息，默认创建用户并返回用户唯一标识
        return connection.getDisplayName();
    }
}
```

```java
@Configuration
@EnableSocial
@Order(1)
public class SocialConfig extends SocialConfigurerAdapter {

    @Autowired
    private DataSource dataSource;

    @Autowired
    private ConnectionSignUp myConnectionSignUp;

    /**
     * 社交登录配类
     *
     * @return
     */
    @Bean
    public SpringSocialConfigurer merryyouSocialSecurityConfig() {
        String filterProcessesUrl = SecurityConstants.DEFAULT_SOCIAL_PROCESS_URL;
        MerryyouSpringSocialConfigurer configurer = new MerryyouSpringSocialConfigurer(filterProcessesUrl);
        return configurer;
    }

    @Override
    public UsersConnectionRepository getUsersConnectionRepository(ConnectionFactoryLocator connectionFactoryLocator) {
        JdbcUsersConnectionRepository repository = new JdbcUsersConnectionRepository(dataSource,
                connectionFactoryLocator, Encryptors.noOpText());
        if (myConnectionSignUp != null) {
            repository.setConnectionSignUp(myConnectionSignUp);
        }
        return repository;
    }

    /**
     * 处理注册流程的工具类
     *
     * @param factoryLocator
     * @return
     */
    @Bean
    public ProviderSignInUtils providerSignInUtils(ConnectionFactoryLocator factoryLocator) {
        return new ProviderSignInUtils(factoryLocator, getUsersConnectionRepository(factoryLocator));
    }

}
```

运行查看效果：直接默认插入了一条数据到数据库中完成了默认的注册；直接认证登录成功

```sql
INSERT INTO `imooc-demo`.`imooc_userconnection` (`userId`, `providerId`, `providerUserId`, `rank`, `displayName`, `profileUrl`, `imageUrl`, `accessToken`, `secret`, `refreshToken`, `expireTime`) VALUES ('猪', 'qq', '81F03E50B76D6D829F5A4875941567A6', '1', '猪', NULL, 'http://thirdqq.qlogo.cn/qqapp/101316278/81F03E50B76D6D829F5A4875941567A6/40', '2FCF43C2BA45ECD4CA4508FC8DC2CED8', NULL, 'D5C83B6F2E95DA9B4B97849113F15972', '1541333450678');

```