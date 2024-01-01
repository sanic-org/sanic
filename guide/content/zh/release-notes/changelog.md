---
content_class: 更新日志
---

# 更新日志

:larg_orange_diamond: Current release\
:larg_blu_diamond: In support LTS release

## 版本23.12.0 :larg_orange_diamond::larg_blu_diamond:

_当前版本_

### 功能

- [#2775](https://github.com/sanic-org/sanic/pull/2775) 开始并重启任意进程
- [#2811](https://github.com/sanic-org/sanic/pull/2811)
- [#2812](https://github.com/sanic-org/sanic/pull/2812) 禁止任务在打开websocket上取消跟踪
- [#2822](https://github.com/sanic-org/sanic/pull/2822) 侦听器和信号优先级
- [#2831](https://github.com/sanic-org/sanic/pull/2831) 减少内存消耗量
- [#2837](https://github.com/sanic-org/sanic/pull/2837) 接受最佳cookies
- [#2841](https://github.com/sanic-org/sanic/pull/2841) 添加 \`websocket.handler.\<before/after/exception>" 信号
- [#2805](https://github.com/sanic-org/sanic/pull/2805) 添加更改的文件以重新载入触发监听器
- [#2813](https://github.com/sanic-org/sanic/pull/2813) 允许提供简单的信号
- [#2827](https://github.com/sanic-org/sanic/pull/2827) 改进`Sanic.event()`的功能和一致性
- [#2851](https://github.com/sanic-org/sanic/pull/2851) 允许范围请求单个字节
- [#2854](https://github.com/sanic-org/sanic/pull/2854) 为web套接字请求更好地`Request.scheme`
- [#2858](https://github.com/sanic-org/sanic/pull/2858) 将Sanic `Request` 转换为Websockets `Request` 来握手
- [#2859](https://github.com/sanic-org/sanic/pull/2859) 在 `sanic` CLI 中添加一个 REPL
- [#2870](https://github.com/sanic-org/sanic/pull/2870) 添加 Python 3.12 支持
- [#2875](https://github.com/sanic-org/sanic/pull/2875) 在多处理环境冲突中更好的例外

### 错误修正

- [#2803](https://github.com/sanic-org/sanic/pull/2803) 修复MOTD显示额外数据

### 废弃和移除

### 开发者基础设施

- [#2796](https://github.com/sanic-org/sanic/pull/2796) 重新计算单位测试案件
- [#2801](https://github.com/sanic-org/sanic/pull/2801) 在只有一个 CPU 时修复`test_fast`
- [#2807](https://github.com/sanic-org/sanic/pull/2807) 添加自动文档的约束 (旧软件包版本中的行号)
- [#2808](https://github.com/sanic-org/sanic/pull/2808) Reface GitHub Actions
- [#2814](https://github.com/sanic-org/sanic/pull/2814) 在 git 推送时运行CI 管道上
- [#2846](https://github.com/sanic-org/sanic/pull/2846) 删除旧的性能测试/基准
- [#2848](https://github.com/sanic-org/sanic/pull/2848) Makefile 清理
- [#2865](https://github.com/sanic-org/sanic/pull/2865)
  [#2869](https://github.com/sanic-org/sanic/pull/2869)
  [#2872](https://github.com/sanic-org/sanic/pull/2872)
  [#2879](https://github.com/sanic-org/sanic/pull/2879)
  添加ruff到工具链中
- [#2866](https://github.com/sanic-org/sanic/pull/2866) 修复alt svc 测试以便在本地使用显式缓存nbytes
- [#2877](https://github.com/sanic-org/sanic/pull/2877) 在部署中使用Python可信的出版商
- [#2882](https://github.com/sanic-org/sanic/pull/2882) 在测试套装中引入目标位置的动态端口灯具

### 改进文档

- [#2781](https://github.com/sanic-org/sanic/pull/2781)
  [#2821](https://github.com/sanic-org/sanic/pull/2821)
  [#2861](https://github.com/sanic-org/sanic/pull/2861)
  [#2863](https://github.com/sanic-org/sanic/pull/2863)
  用户指南转换为 SHH (Sanic, html5tagger, HTMX)
- [#2810](https://github.com/sanic-org/sanic/pull/2810) 更新README
- [#2855](https://github.com/sanic-org/sanic/pull/2855) 编辑Discord 徽章
- [#2864](https://github.com/sanic-org/sanic/pull/2864) 调整文档使用状态属性在 http/https 重定向文档

## 版本23.9.0

_由于当时的情况，v.23.9已经跳过。

## 版本 23.6.0

### 功能

- [#2670](https://github.com/sanic-org/sanic/pull/2670) 增加`KEEP_ALIVE_TIMEOUT` 默认为120秒
- [#2716](https://github.com/sanic-org/sanic/pull/2716) 在蓝图中添加允许路由覆盖选项
- [#2724](https://github.com/sanic-org/sanic/pull/2724)和[#2792](https://github.com/sanic-org/sanic/pull/2792) 为应用中任何地方提出的所有例外添加一个新的异常信号。
- [#2727](https://github.com/sanic-org/sanic/pull/2727) 为BP组添加名称前缀
- [#2754](https://github.com/sanic-org/sanic/pull/2754) 更新中间件类型的请求类型
- [#2770](https://github.com/sanic-org/sanic/pull/2770) 启动时间应用程序引发导入错误时更好的异常消息
- [#2776](https://github.com/sanic-org/sanic/pull/2776) 设置多处理开始方法
- [#2785](https://github.com/sanic-org/sanic/pull/2785) 添加自定义键入配置和 ctx 对象
- [#2790](https://github.com/sanic-org/sanic/pull/2790) 添加`request.client_ip`

### 错误修正

- [#2728](https://github.com/sanic-org/sanic/pull/2728) 修复预定结果
- [#2729](https://github.com/sanic-org/sanic/pull/2729)
- [#2737](https://github.com/sanic-org/sanic/pull/2737) 修复`JSONREspone`默认内容类型的注解
- [#2740](https://github.com/sanic-org/sanic/pull/2740) 在检查员中使用 Sanic的序列化器为 JSON 响应
- [#2760](https://github.com/sanic-org/sanic/pull/2760) 在 ASGI 模式中支持 `Request.get_current`
- [#2773](https://github.com/sanic-org/sanic/pull/2773) 蓝图路由，明确定义错误格式
- [#2774](https://github.com/sanic-org/sanic/pull/2774) 解析不同渲染器的标题
- [#2782](https://github.com/sanic-org/sanic/pull/2782) 解决pypy 兼容性问题

### 废弃和移除

- [#2777](https://github.com/sanic-org/sanic/pull/2777) 移除 Python 3.7 支持

### 开发者基础设施

- [#2766](https://github.com/sanic-org/sanic/pull/2766) 解压设置工具版本
- [#2779](https://github.com/sanic-org/sanic/pull/2779) 运行在循环中进行活化测试以获取端口。

### 改进文档

- [#2741](https://github.com/sanic-org/sanic/pull/2741) 更好的文档实例来运行 Sanic
  从该列表中，要在发行说明中高亮显示的内容：

## 版本23.3.0

### 功能

- [#2545](https://github.com/sanic-org/sanic/pull/2545)
- [#2606](https://github.com/sanic-org/sanic/pull/2606) 也在 ASGI 中解码头为 UTF-8
- [#2646](https://github.com/sanic-org/sanic/pull/2646) 单独的 ASGI 请求和有效期彩信
- [#2659](https://github.com/sanic-org/sanic/pull/2659) 使用 `FALLBACK_ERROR_FORMAT` 返回的 `empty()`
- [#2662](https://github.com/sanic-org/sanic/pull/262) 添加基本文件浏览器 (HTML页面) 和自动索引服务
- [#2667](https://github.com/sanic-org/sanic/pull/2667) 较强的追踪格式化(HTML页面)
- [#2668](https://github.com/sanic-org/sanic/pull/2668) Smarter 错误页面渲染格式选择；更多依赖于头部和“常识”默认值
- [#2680](https://github.com/sanic-org/sanic/pull/2680) 在使用 `SHUT_RDWR` 关闭之前检查套接字的状态
- [#2687](https://github.com/sanic-org/sanic/pull/267) 刷新`Request.accept` 功能，使其更加性能和符合观光。
- [#2696](https://github.com/sanic-org/sanic/pull/2696) 添加标题访问器作为属性
  ```
  示例字段: Foo, Bar
  示例字段: Baz
  ```
  ```python
  headers.example_field ="Foo, Bar,Baz"
  ```
- [#2700](https://github.com/sanic-org/sanic/pull/2700) Simple CLI 目标

  ```sh
  $ sanic path.to.module:app # 全局应用实例
  $ sanic path.to.module:create_app # 出厂模式
  sanic ./path/to/directory/ # 简单服务
  ```
- [#2701](https://github.com/sanic-org/sanic/pull/2701) API 来定义管理过程中的一些工人
- [#2704](https://github.com/sanic-org/sanic/pull/2704) 添加动态更改路由的便利。
- [#2706](https://github.com/sanic-org/sanic/pull/2706) 为cookie的创建和删除添加便利方法

  ```python
  response = text("...")
  response.add_cookie("test", "it work!", domain=".yummy-yummy-cookie.com")
  ```
- [#2707](https://github.com/sanic-org/sanic/pull/2707) 简化的 `parse_content_header` 逃避与 RFC 兼容并移除过时的 FF 哈克
- [#2710](https://github.com/sanic-org/sanic/pull/2710)
- [#2711](https://github.com/sanic-org/sanic/pull/2711) 默认使用 `DELETE` 上
- [#2719](https://github.com/sanic-org/sanic/pull/2719) 允许 `password` 传入TLS 环境
- [#2720](https://github.com/sanic-org/sanic/pull/2720) 在 `RequestCancelled` 上跳过中间件
- [#2721](https://github.com/sanic-org/sanic/pull/2721) 将访问日志格式更改为`%s`
- [#2722](https://github.com/sanic-org/sanic/pull/2722) 添加 `CertLoader` 作为直接控制 `SSLContext` 对象的应用程序选项
- [#2725](https://github.com/sanic-org/sanic/pull/2725) 工人在种族条件下同步状态容忍度

### 错误修正

- [#2651](https://github.com/sanic-org/sanic/pull/2651) ASGI websocket 来传递节点像是
- [#2697](https://github.com/sanic-org/sanic/pull/2697) 使用 `If-Modified-Since` 时修复日期时间和天真之间的比较

### 废弃和移除

- [#2666](https://github.com/sanic-org/sanic/pull/2666) Remove deprecated `__blueprintname__` property

### 改进文档

- [#2712](https://github.com/sanic-org/sanic/pull/2712) 通过使用 \`\`'https\://github.com/sanic/pull/2712改进的示例来创建重定向

## 版本22.12.0 :larg_blu_diamond:

_当前LTS版本_

### 功能

- [#2569](https://github.com/sanic-org/sanic/pull/2569) 在更新响应对象时添加 `JSONResponse` 类，并有一些方便的方法
- [#2598](https://github.com/sanic-org/sanic/pull/2598) 将 `uvloop` 要求更改为 `>=0.15.0`
- [#2609](https://github.com/sanic-org/sanic/pull/2609) 添加与 `websockets` v11.0
- [#2610](https://github.com/sanic-org/sanic/pull/2610) 在工人错误的早期杀死服务器
  - 将僵局提升到30秒
- [#2617](https://github.com/sanic-org/sanic/pull/261)
- [#2621](https://github.com/sanic-org/sanic/pull/2621)[#2634](https://github.com/sanic-org/sanic/pull/2634) 在随后的`ctrl+c`上发送`SIGKILL`，迫使工人退出
- [#2622](https://github.com/sanic-org/sanic/pull/2622) 添加 API 以重新启动多路程序的所有工人。
- [#2624](https://github.com/sanic-org/sanic/pull/2624) 默认为所有子进程的`spawn`，除非具体设置：
  ```python
  从Sanic 导入 Sanic

  Sanic.start_methods = "fork"
  ```
- [#2625](https://github.com/sanic-org/sanic/pull/2625) 格式数据/多部分文件上传文件名正常化
- [#2626](https://github.com/sanic-org/sanic/pull/2626) 移动到HTTP检查器：
  - 远程访问以检查正在运行的 Sanic 实例
  - TLS 支持给检查员的加密通话
  - 使用 API 密钥验证检查员
  - 使用自定义命令扩展检查员的能力
- [#2632](https://github.com/sanic-org/sanic/pull/2632) 重新启动操作的控制顺序
- [#2633](https://github.com/sanic-org/sanic/pull/2633) 将重新加载间隔移至类变量
- [#2636](https://github.com/sanic-org/sanic/pull/2636) 在 `register_middleware` 方法中添加 `priority`
- [#2639](https://github.com/sanic-org/sanic/pull/2639) 在 `add_route` 方法中加上“unquote\`
- [#2640](https://github.com/sanic-org/sanic/pull/2640) ASGI websockets 接收`text` 或 `bytes`

### 错误修正

- [#2607](https://github.com/sanic-org/sanic/pull/2607) 强制套接字关闭之前允许重新绑定
- [#2590](https://github.com/sanic-org/sanic/pull/2590) 在Python 3.11+中使用实际的`StrEnum`
- [#2615](https://github.com/sanic-org/sanic/pull/2615) 确保每个请求超时只执行一次中间件执行
- [#2627](https://github.com/sanic-org/sanic/pull/2627) 在生命周期失败时崩溃ASGI应用程序
- [#2635](https://github.com/sanic-org/sanic/pull/2635) 解决Windows 上低级服务器创建错误

### 废弃和移除

- [#2608](https://github.com/sanic-org/sanic/pull/2608)[#2630](https://github.com/sanic-org/sanic/pull/2630) 信号条件和在`signal.extr` 上保存的触发器
- [#2626](https://github.com/sanic-org/sanic/pull/2626) 移动到 HTTP 检查
  - 🚨 _Breaking更改_: 将检查员从一个带有自定义协议的 TCP 套接字移动到一个Sanic 应用程序
  - _DEPRECATE_: "--inspect\*" 命令已被弃用而改用 "inspect..." 命令
- [#2628](https://github.com/sanic-org/sanic/pull/2628) 替换已废弃的`dutils.strtobool`

### 开发者基础设施

- [#2612](https://github.com/sanic-org/sanic/pull/2612) 添加CI 测试Python 3.11

## 第22.9.1 版

### 功能

- [#2585](https://github.com/sanic-org/sanic/pull/2585) 没有注册应用程序时改进错误消息

### 错误修正

- [#2578](https://github.com/sanic-org/sanic/pull/2578)
- [#2591](https://github.com/sanic-org/sanic/pull/2591) 不使用 sentinel identity 来实现`spawn` 兼容性
- [#2592](https://github.com/sanic-org/sanic/pull/2592) 修复嵌套蓝图组中的属性
- [#2595](https://github.com/sanic-org/sanic/pull/2595) 在新的工人读取器上设置睡眠间隔

### 废弃和移除

### 开发者基础设施

- [#2588](https://github.com/sanic-org/sanic/pull/2588) Markdown templates on issue forms

### 改进文档

- [#2556](https://github.com/sanic-org/sanic/pull/2556) v22.9 文档
- [#2582](https://github.com/sanic-org/sanic/pull/2582) 清除Windows支持

## 版本 22.9.0

### 功能

- [#2445](https://github.com/sanic-org/sanic/pull/2445) 添加自定义负载函数
- [#2490](https://github.com/sanic-org/sanic/pull/2490) 使`WebsocketImplication` async
- [#2499](https://github.com/sanic-org/sanic/pull/2499) Sanic Server WorkerManager refacture
- [#2506](https://github.com/sanic-org/sanic/pull/2506) 使用 `pathlib` 作为路径分辨率(用于静态文件服务)
- [#2508](https://github.com/sanic-org/sanic/pull/2508) 使用 `path.parts` 而不是 `match` (用于静态文件服务)
- [#2513](https://github.com/sanic-org/sanic/pull/2513) 更好地请求取消处理
- [#2516](https://github.com/sanic-org/sanic/pull/2516) 添加HTTP方法信息的请求属性：
  - `request.is_safe`
  - `request.is_identient`
  - `request.is_cache`
  - _See_ [MDN docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) _获取更多关于何时应用的信息_
- [#2522](https://github.com/sanic-org/sanic/pull/252) 始终在ASGI 中显示服务器位置
- [#2526](https://github.com/sanic-org/sanic/pull/2526) 缓存控制支持静态文件在适当时返回 304
- [#2533](https://github.com/sanic-org/sanic/pull/2533) 重新因素`_static_request_handler`
- [#2540](https://github.com/sanic-org/sanic/pull/2540)
  - `http.handler.befor`
  - `http.handler.after `
- [#2542](https://github.com/sanic-org/sanic/pull/2542) 添加 \*[redacted]到 CLI :)
- [#2546](https://github.com/sanic-org/sanic/pull/2546) 添加废弃警告过滤器
- [#2550](https://github.com/sanic-org/sanic/pull/250) 中间件优先级和性能提高

### 错误修正

- [#2495](https://github.com/sanic-org/sanic/pull/2495) 防止目录陷阱与静态文件
- [#2515](https://github.com/sanic-org/sanic/pull/2515) 不要在蓝图中的某些静态目录中对路径使用双斜线

### 废弃和移除

- [#2525](https://github.com/sanic-org/sanic/pull/225) 在重复的路线名称上发出警告，将在 v23.3 中彻底防止发出警告。
- [#2537](https://github.com/sanic-org/sanic/pull/2537) 对于重复的例外情况发出警告和弃置通知，将在v23.3中彻底防止。

### 开发者基础设施

- [#2504](https://github.com/sanic-org/sanic/pull/2504) 清理测试套件
- [#2505](https://github.com/sanic-org/sanic/pull/2505) 从贡献工具箱中替换不支持的 Python 版本
- [#2530](https://github.com/sanic-org/sanic/pull/2530)

### 改进文档

- [#2502](https://github.com/sanic-org/sanic/pull/2502) 修复几个typos
- [#2517](https://github.com/sanic-org/sanic/pull/2517)[#2536](https://github.com/sanic-org/sanic/pull/2536) 添加一些类型的提示

## 22.6.2 版本

### 错误修正

- [#2522](https://github.com/sanic-org/sanic/pull/252) 始终在ASGI 中显示服务器位置

## 22.6.1 版本

### 错误修正

- [#2477](https://github.com/sanic-org/sanic/pull/2477) 当文件夹名称以“...”结尾时，无声静态目录失败

## 版本 22.6.0

### 功能

- [#2378](https://github.com/sanic-org/sanic/pull/2378) 在 `DEBUG` 模式中引入HTTP/3 和 TLS 证书的自动生成
  - 👶 _EARLY RELEASE FEATURE_: 通过 HTTP/3 提供Sanic 是一种提早发布功能。 它尚未完全涵盖HTTP/3 单项，而是旨在与现有的 HTTP/1.1 服务器实现功能对等。 Websockets, WebTransport, 推送响应是一些尚未实现的功能的例子。
  - 📦 _EXTRA REQUIREMENT_: 并非所有HTTP客户端都能够与 HTTP/3 服务器接口。 您可能需要安装 [HTTP 3 能够安装的客户端](https://curl.se/docs/http3.html)。
  - 📦 _EXTRA REQUIREMENT_: 若要使用 TLS 自动生成，您必须安装 [mkcert](https://github.com/FiloSottile/mkcert) 或 [trustme](https://github.com/python-trio/trustme)。
- [#2416](https://github.com/sanic-org/sanic/pull/2416) 将消息添加到 `task.cancel`
- [#2420](https://github.com/sanic-org/sanic/pull/2420) 添加异常别名以更一致地命名与标准HTTP响应类型(`BadRequest`, `MethodNotalled`, `RangeNotSatisfiable`)
- [#2432](https://github.com/sanic-org/sanic/pull/2432) 将ASGI `scope` 作为一个 `Request` 对象的属性
- [#2438](https://github.com/sanic-org/sanic/pull/2438) 更容易访问Websocket类别以获取批注: `from sanic import Websocket`
- [#2439](https://github.com/sanic-org/sanic/pull/2439) 新API用于阅读带有选项的表格值：`Request.get_form`
- [#2445](https://github.com/sanic-org/sanic/pull/2445) 添加自定义 `loads` 函数
- [#2447](https://github.com/sanic-org/sanic/pull/2447), [#2486](https://github.com/sanic-org/sanic/pull/2486) 改进API以支持设置缓存控制头部
- [#2453](https://github.com/sanic-org/sanic/pull/2453) 移动动词过滤器到记录器
- [#2475](https://github.com/sanic-org/sanic/pull/2475) 使用 `Request.get_current()` 方法显示当前请求的获取器

### 错误修正

- [#2448](https://github.com/sanic-org/sanic/pull/2448) 修正允许使用 pythonw\.exe\` 或没有 'sys.stdout' 的地方运行
- [#2451](https://github.com/sanic-org/sanic/pull/2451)在 ASGI 模式中触发`http.lifecycle.request` 信号
- [#2455](https://github.com/sanic-org/sanic/pull/2455) 解决堆叠路线定义的打字问题
- [#2463](https://github.com/sanic-org/sanic/pull/2463) Python 3.7 Websocket 处理程序中正确捕获websocket 取消错误

### 废弃和移除

- [#2487](https://github.com/sanic-org/sanic/pull/2487) v22.6 废弃和更改
  1. 可选的应用程序注册
  2. 发送部分响应后执行自定义处理程序
  3. 在 `ErrorHandler` 上配置回退处理
  4. 自定义 `LOGO` 设置
  5. `sanic.response.stream`
  6. `AsyncioServer.init`

### 开发者基础设施

- [#2449](https://github.com/sanic-org/sanic/pull/2449) 清理`black`和`isort`配置
- [#2479](https://github.com/sanic-org/sanic/pull/2479) 修复一些简易测试

### 改进文档

- [#2461](https://github.com/sanic-org/sanic/pull/2461) 更新示例以匹配当前应用程序命名标准
- [#2466](https://github.com/sanic-org/sanic/pull/2466) 更好类型`Extend`
- [#2485](https://github.com/sanic-org/sanic/pull/2485) 改进CLI 中的帮助信息

## 版本22.3.0

### 功能

- [#2347](https://github.com/sanic-org/sanic/pull/2347) 多应用程序服务器的 API
  - 🚨 _Breaking CHANGE_: 旧的 `sanic.worker.GunicornWorker` 已被删除 \*\*。 若要用 `gunicorn` 来运行Sanic，你应该使用它`uvicorn` [如他们的文件中所述](https://www.uvicorn.org/#running-with-gunicorn)。
  - 🧁 _SIDE EFFECT_: 命名后台任务现在得到支持, 甚至是 Python 3.7
- [#2357](https://github.com/sanic-org/sanic/pull/2357) Parse `Authorization` header as `Request.credentials`
- [#2361](https://github.com/sanic-org/sanic/pull/2361) 在应用程序启动时添加配置选项以跳过`Touchup` 步骤
- [#2372](https://github.com/sanic-org/sanic/pull/2372) 更新到 CLI 帮助发送消息
- [#2382](https://github.com/sanic-org/sanic/pull/2382) 降级警告到背水调试消息
- [#2396](https://github.com/sanic-org/sanic/pull/2396) 允许使用 `multidict` v0.6
- [#2401](https://github.com/sanic-org/sanic/pull/2401) 升级 CLI 捕获替代应用程序运行类型
- [#2402](https://github.com/sanic-org/sanic/pull/2402) 有条件将CLI 参数注入工厂中
- [#2413](https://github.com/sanic-org/sanic/pull/2413) 添加新的开始和停止事件监听器到阅读器进程
- [#2414](https://github.com/sanic-org/sanic/pull/2414) 移除循环作为必要的听众arg
- [#2415](https://github.com/sanic-org/sanic/pull/245)
- [sanic-routing#47](https://github.com/sanic-org/sanic-routing/pull/47) 添加一个新的退出参数类型：`<file:ext>`, `<file:ext=jpg>`, `<file:ext=jpg|png|gif|svg>`, `<file:ext=jpg|png|gif|svg> `, `<file=int:ext>`, `<file=int:ext=jpg|png|gif|svg>`, `<file=float:ext=tar.gz>`
  - 👶 _BETA FEATURE_: 此功能将无法与 `path` 类型匹配, 并且仅作为测试版发布.
- [sanic-routing#57](https://github.com/sanic-org/sanic-routing/pull/57) 更改`register_pattern` 以接受一个 `str` 或 `Pattern`
- [sanic-routing#58](https://github.com/sanic-org/sanic-routing/pull/58) 仅在非空字符串上默认匹配，以及新的 `strempty` 模式类型
  - 🚨 _Breaking变异_: 之前带有动态字符串参数的路由(`/<foo>` 或 `/<foo:str>`) 将在任何字符串上匹配, 包含空字符串。 现在**仅** 匹配一个非空字符串。 要保留旧的行为，您应该使用新的参数类型：`/<foo:strorempty>`。

### 错误修正

- [#2373](https://github.com/sanic-org/sanic/pull/2373) 在websockets上删除 `error_logger`
- [#2381](https://github.com/sanic-org/sanic/pull/2381) 修复任务注册表中新分配的`None`
- [sanic-routing#52](https://github.com/sanic-org/sanic-routing/pull/52) 添加类型铸造到regex route 匹配
- [sanic-routing#60](https://github.com/sanic-org/sanic-routing/pull/60) 在regex routing上添加要求检查(这个解析方法是多个静态目录，具有不同的`host`值)

### 废弃和移除

- [#2362](https://github.com/sanic-org/sanic/pull/2362) 22.3 废弃和更改
  1. `debug=True` 和 `--debug` 做_NOT_ 自动运行 `auto_reload`
  2. 默认错误渲染为纯文本(默认仍然获取 HTML ，因为`auto` 看着头部)
  3. `config` 是需要 `ErrorHandler.finalize`
  4. `ErrorHandler.lookup` 需要两个位置参数
  5. 未使用的 websocket 协议参数已删除
- [#2344](https://github.com/sanic-org/sanic/pull/2344) 废弃加载小写环境变量

### 开发者基础设施

- [#2363](https://github.com/sanic-org/sanic/pull/2363) 将代码覆盖范围还原到 Codecov
- [#2405](https://github.com/sanic-org/sanic/pull/2405) 升级`sanic-routing`更改测试
- [sanic-testing#35](https://github.com/sanic-org/sanic-testing/pull/35) 允许 httpx v0.22

### 改进文档

- [#2350](https://github.com/sanic-org/sanic/pull/2350) README中的 ASGI 修复链接
- [#2398](https://github.com/sanic-org/sanic/pull/2398) 文档中间件on_request 和 on_response
- [#2409](https://github.com/sanic-org/sanic/pull/2409) 添加缺失的`Request.respond `文档

### 其他事项

- [#2376](https://github.com/sanic-org/sanic/pull/2376) 修复`ListenerMixin.listener`
- [#2383](https://github.com/sanic-org/sanic/pull/2383) 在 `asyncio.wait` 中清除废弃警告。
- [#2387](https://github.com/sanic-org/sanic/pull/2387) Cleanup `__slots__` implementations
- [#2390](https://github.com/sanic-org/sanic/pull/2390) 在 `asyncio.get_event_loop` 中清除废弃警告

## 版本21.12.1

- [#2349](https://github.com/sanic-org/sanic/pull/2349) 仅在启动时显示MOTD
- [#2354](https://github.com/sanic-org/sanic/pull/2354) 忽略Python 3.7 中的名称参数
- [#2355](https://github.com/sanic-org/sanic/pull/2355) 添加config.update 支持所有配置

## 版本21.12.0

### 功能

- [#2260](https://github.com/sanic-org/sanic/pull/2260) 允许早期蓝图注册仍然应用以后添加的对象
- [No. 2262](https://github.com/sanic-org/sanic/pull/2262) 噪音异常——强制记录所有异常
- [#2264](https://github.com/sanic-org/sanic/pull/2264) 可选的`uvloop`
- [#2270](https://github.com/sanic-org/sanic/pull/2270) 使用多个TLS证书支持虚拟主机
- [#2277](https://github.com/sanic-org/sanic/pull/2277) 为提高一致性而改变信号路由
  - _购买更改_：如果你是手动路由信号，有一个破碎的变化。 信号路由器的 `get` 不再是 100% 的决定因素。 现在有一个额外的步骤来循环回来的信号，以便在要求上进行适当的匹配。 如果正在使用`app.rapoch`或`bp.poidch`发出信号'发出信号的话，则没有变化。
- [#2290](https://github.com/sanic-org/sanic/pull/2290) 添加上下文异常
- [#2291](https://github.com/sanic-org/sanic/pull/2291)
- [#2295](https://github.com/sanic-org/sanic/pull/2295)，[#2316](https://github.com/sanic-org/sanic/pull/2316)，[#2331](https://github.com/sanic-org/sanic/pull/23331) 重新调整CLI和应用程序状态，使用新的显示和更多的命令对等性
- [#2302](https://github.com/sanic-org/sanic/pull/2302) 在定义时间添加路由环境
- [#2304](https://github.com/sanic-org/sanic/pull/2304) 命名任务和新的 API 用于管理背景任务
- [#2307](https://github.com/sanic-org/sanic/pull/2307) 在应用自动重新加载时，提供已更改文件的见解。
- [#2308](https://github.com/sanic-org/sanic/pull/2308) 安装后自动扩展应用程序[Sanic Extensions](https://sanicframework.org/en/plugins/sanic-ext/getting-started.html) 并提供第一类支持访问扩展。
- [#2309](https://github.com/sanic-org/sanic/pull/2309)
- [#2313](https://github.com/sanic-org/sanic/pull/2313) 支持额外配置实现使用
- [#2321](https://github.com/sanic-org/sanic/pull/2321)
- [#2327](https://github.com/sanic-org/sanic/pull/2327) 防止对单个请求发送多个或混合的答复
- [#2330](https://github.com/sanic-org/sanic/pull/2330) 环境变量定制类型投射器
- [#2332](https://github.com/sanic-org/sanic/pull/2332) 使所有废弃通知保持一致
- [#2335](https://github.com/sanic-org/sanic/pull/2335) 允许下划线开始实例名称

### 错误修正

- [#2273](https://github.com/sanic-org/sanic/pull/2273) 替换分配给`websocket_handshake`
- [#2285](https://github.com/sanic-org/sanic/pull/2285) 修复启动日志中的IPv6 显示
- [#2299](https://github.com/sanic-org/sanic/pull/2299) 从异常处理器调度`http.lifecyle.response`

### 废弃和移除

- [#2306](https://github.com/sanic-org/sanic/pull/2306) 移除弃用的项目
  - `Sanic` 和 `Blueprint` 可能不再具有附加于它们的任意属性
  - `Sanic` 和 `Blueprint` 被迫有符合要求的名称
    - alphanumeric + `_` + `-`
    - 必须以字母或`_`开头。
  - `load_env`关键词参数 `Sanic`
  - `sanic.exceptions.abot`
  - `sanic.views.compositionView`
  - `sanic.response.StreamingHTTPResponse`
    - _注意:_ `stream()`响应方法(如果你通过了一个可调用的流媒体函数)已被弃用,将在 v22.6 中删除。 您应该将所有流媒体响应升级到新风格：https\://sanicframework.org/en/guide/advanced/streaming.html#response-串流
- [#2320](https://github.com/sanic-org/sanic/pull/2320) 从配置中删除应用实例以进行错误处理设置

### 开发者基础设施

- [#2251](https://github.com/sanic-org/sanic/pull/2251) 更改安装命令
- [#2286](https://github.com/sanic-org/sanic/pull/2286) 更改编解码复杂性阈值从 5 到 10
- [#2287](https://github.com/sanic-org/sanic/pull/2287) 更新主机测试函数名以免被覆盖
- [#2292](https://github.com/sanic-org/sanic/pull/2292) 错误故障CI
- [#2311](https://github.com/sanic-org/sanic/pull/2311) [#2324](https://github.com/sanic-org/sanic/pull/224) 不对PR草案进行测试
- [#2336](https://github.com/sanic-org/sanic/pull/2336) 从覆盖面检查中删除路径
- [#2338](https://github.com/sanic-org/sanic/pull/2338) 测试端口清理

### 改进文档

- [#2269](https://github.com/sanic-org/sanic/pull/2269)，[#2329](https://github.com/sanic-org/sanic/pull/2329)，[#2333](https://github.com/sanic-org/sanic/pull/233) 清理typos和修复语言

### 其他事项

- [#2257](https://github.com/sanic-org/sanic/pull/2257), [#2294](https://github.com/sanic-org/sanic/pull/2294), [#2341](https://github.com/sanic-org/sanic/pull/2341) 添加 Python 3.10 支持
- [#2279](https://github.com/sanic-org/sanic/pull/2279)，[#2317](https://github.com/sanic-org/sanic/pull/2317)，[#2322](https://github.com/sanic-org/sanic/pull/232) 添加/正确缺失的类型注释
- [#2305](https://github.com/sanic-org/sanic/pull/2305) 修复使用现代实现的例子

## 21.9.3 版本

- 通过清理恢复v21.9.2 \*

## 第21.9.2 版

- [#2268](https://github.com/sanic-org/sanic/pull/2268)
- [#2310](https://github.com/sanic-org/sanic/pull/2310)

## 21.9.1 版本

- [#2259](https://github.com/sanic-org/sanic/pull/2259) 允许不符合要求的错误处理

## 版本21.9.0

### 功能

- [#2158](https://github.com/sanic-org/sanic/pull/2158)，[#2248](https://github.com/sanic-org/sanic/pull/2248) 全面整修I/O至websockets
- [#2160](https://github.com/sanic-org/sanic/pull/2160) 将新的17个信号添加到服务器并请求生命周期
- [#2162](https://github.com/sanic-org/sanic/pull/2162) Smarter `auto`退回格式化异常)
- [#2184](https://github.com/sanic-org/sanic/pull/2184)
- [#2200](https://github.com/sanic-org/sanic/pull/2200) 接受标题解析
- [#2207](https://github.com/sanic-org/sanic/pull/2207) 日志远程地址如果可用
- [#2209](https://github.com/sanic-org/sanic/pull/2209) 向BP组添加方便方法
- [#2216](https://github.com/sanic-org/sanic/pull/2216) 将默认消息添加到 SanicExceptions
- [#2225](https://github.com/sanic-org/sanic/pull/2225)
- [#2236](https://github.com/sanic-org/sanic/pull/2236) 允许Falsey(但不是)从路由处理器中回复
- [#2238](https://github.com/sanic-org/sanic/pull/2238) 在蓝图组中加上“异常”装饰符
- [#2244](https://github.com/sanic-org/sanic/pull/2244) 对服务文件或目录的静态明确指令(例如: `static(..., resource_type="file")`
- [#2245](https://github.com/sanic-org/sanic/pull/2245) 在连接任务取消时关闭HTTP循环

### 错误修正

- [#2188](https://github.com/sanic-org/sanic/pull/2188) 修复对块请求结束的处理
- [#2195](https://github.com/sanic-org/sanic/pull/2195) 解决静态请求处理意外错误
- [#2208](https://github.com/sanic-org/sanic/pull/2208)
- [#2211](https://github.com/sanic-org/sanic/pull/2211) 固定用于处理异常的 asgi 应用程序调用
- [#2213](https://github.com/sanic-org/sanic/pull/2213) 修复错误，在这个错误中，没有记录除数
- [#2231](https://github.com/sanic-org/sanic/pull/2231) 清理结束任务，在战略地点使用“abort()”以避免染色套接字
- [#2247](https://github.com/sanic-org/sanic/pull/2247) 修复调试模式下自动重新加载状态记录
- [#2246](https://github.com/sanic-org/sanic/pull/2246) 为BP账户，但没有路由

### 开发者基础设施

- [#2194](https://github.com/sanic-org/sanic/pull/2194) HTTP Unit tests with raw 客户端
- [#2199](https://github.com/sanic-org/sanic/pull/2199) 切换到解码器
- [#2214](https://github.com/sanic-org/sanic/pull/2214) 尝试重启Windows 测试
- [#2229](https://github.com/sanic-org/sanic/pull/2229) 将`HttpProtocol`重新因素变成一个基准类
- [#2230](https://github.com/sanic-org/sanic/pull/2230) 重新因素`server.py`到多文件模块

### 其他事项

- [#2173](https://github.com/sanic-org/sanic/pull/2173) 删除重复的依赖关系和 PEP 517 支持
- [#2193](https://github.com/sanic-org/sanic/pull/2193)，[#2196](https://github.com/sanic-org/sanic/pull/2196)，[#2217](https://github.com/sanic-org/sanic/pull/2217)

## 版本21.6.1

**错误修复**

- [#2178](https://github.com/sanic-org/sanic/pull/2178) Update
  sanic-routing to allow for better splitting of complex URI
  templates
- [#2183](https://github.com/sanic-org/sanic/pull/2183) Proper
  处理块请求机构以解析日志中的幽灵503
- [#2181](https://github.com/sanic-org/sanic/pull/2181) 解决异常日志中的
  回归问题
- [#2201](https://github.com/sanic-org/sanic/pull/2201) 清理管道请求中的
  请求

## 版本21.6.0

**特征**

- [#2094](https://github.com/sanic-org/sanic/pull/2094) Add
  `response.eof()` method for closing a stream in a handler

- [#2097](https://github.com/sanic-org/sanic/pull/2097) 允许
  不区分大小写的 HTTP 升级标题

- [#2104](https://github.com/sanic-org/sanic/pull/2104) Explicit
  usage of CIMultiDict getters

- [#2109](https://github.com/sanic-org/sanic/pull/2109) Consistent
  use of error loggers

- [#2114](https://github.com/sanic-org/sanic/pull/2114) 新的
  `client_ip` 访问连接信息实例

- [#2119](https://github.com/sanic-org/sanic/pull/2119) Alternatate
  类实例化的`Config` 和 `Sanic.ctx`

- [#2133](https://github.com/sanic-org/sanic/pull/2133) 实现
  新版本的 AST 路由器

  - `alpha` 和 `string`param
    类型之间的适当区别
  - 添加一个 `slug` 参数类型，例如：`<foo:slug>`
  - 废弃foo:string`而改成<foo:str>`。
  - 废弃foo:number`而改成<foo:float>`。
  - Adds a `route.uri` accessor

- [#2136](https://github.com/sanic-org/sanic/pull/2136) CLI
  改进使用新的可选参数

- [#2137](https://github.com/sanic-org/sanic/pull/2137) 在 URL 生成器中添加
  `version_prefix`

- [#2140](https://github.com/sanic-org/sanic/pull/2140) 事件
  自动注册 with `EVENT_AUTORGISTER`

- [#2146](https://github.com/sanic-org/sanic/pull/2146),
  [#2147](https://github.com/sanic-org/sanic/pull/2147) Require
  stricter names on `Sanic()` and `Blueprint()`

- [#2150](https://github.com/sanic-org/sanic/pull/2150) Infinitely
  reusable and nestable `Blueprint` and `BlueprintGroup`

- [#2154](https://github.com/sanic-org/sanic/pull/2154) 将
  `websockets` 依赖关系升级为最小版本

- [#2155](https://github.com/sanic-org/sanic/pull/2155) 允许
  增加最大标题尺寸：`REQUEST_MAX_HEADER_SIZE`

- [#2157](https://github.com/sanic-org/sanic/pull/2157) 允许应用
  出厂模式在 CLI

- [#2165](https://github.com/sanic-org/sanic/pull/2165) 将 HTTP
  方法更改为enums

- [#2167](https://github.com/sanic-org/sanic/pull/2167) 允许
  自动重新加载附加目录

- [#2168](https://github.com/sanic-org/sanic/pull/2168) 添加简单的
  HTTP 服务器到 CLI

- [#2170](https://github.com/sanic-org/sanic/pull/2170) 附加的
  方法附加`HTTPMethodView`

**错误修复**

- [#2091](https://github.com/sanic-org/sanic/pull/2091) Fix
  `UserWarning` in ASGI mode for missing `__slots__`
- [#2099](https://github.com/sanic-org/sanic/pull/2099) 修复静态
  请求处理记录异常于404
- [#2110](https://github.com/sanic-org/sanic/pull/2110) 修复
  request.args.pop 去除不一致的参数
- [#2107](https://github.com/sanic-org/sanic/pull/2107) 修理
  引导load_env
- [#2127](https://github.com/sanic-org/sanic/pull/2127) 请确认
  ASGI ws 子协议是一个列表
- [#2128](https://github.com/sanic-org/sanic/pull/2128) 修复问题
  蓝图异常处理程序没有始终如一地路由到
  适当处理程序

**废弃和删除**

- [#2156](https://github.com/sanic-org/sanic/pull/2156) Remove
  config value `REQUEST_BUFFER_QUEUE_SIZE`
- [#2170](https://github.com/sanic-org/sanic/pull/2170)
  `CompositionView` 已废弃，并在21.12中标记为移除。
- [#2172](https://github.com/sanic-org/sanic/pull/2170) 废弃
  StreamingHTTPResponse

**开发者基础设施**

- [#2149](https://github.com/sanic-org/sanic/pull/2149) 删除
  Travis CI 支持GitHub 操作

**改进文档**

- [#2164](https://github.com/sanic-org/sanic/pull/2164) 修复
  文档中的类型
- [#2100](https://github.com/sanic-org/sanic/pull/2100) 移除不存在的参数的
  文档

## 21.3.2 版本

**错误修复**

- [#2081](https://github.com/sanic-org/sanic/pull/2081) 在 websocket 连接上禁用
  响应超时
- [#2085](https://github.com/sanic-org/sanic/pull/2085) Make sure
  that blueprints with no slash is maintained when applied

## 版本21.3.1

**错误修复**

- [#2076](https://github.com/sanic-org/sanic/pull/2076) 子文件夹内的静态文件
  不可访问 (404)

## 版本21.3.0

发布
笔记

**特征**

- [#1876](https://github.com/sanic-org/sanic/pull/1876) Unified
  串流服务器
- [#2005](https://github.com/sanic-org/sanic/pull/2005) New
  `Request.id` 属性
- [#2008](https://github.com/sanic-org/sanic/pull/2008) 允许
  Pathlib 路径对象传递给`app.static()`
- [#2010](https://github.com/sanic-org/sanic/pull/2010),
  [#2031](https://github.com/sanic-org/sanic/pull/2031) New
  启动-优化路由器
- [#2018](https://github.com/sanic-org/sanic/pull/2018)
  [#2064](https://github.com/sanic-org/sanic/pull/2064) 主服务器进程的侦听器
- [#2032](https://github.com/sanic-org/sanic/pull/2032) 添加原始的
  头信息以请求对象
- [#2042](https://github.com/sanic-org/sanic/pull/2042)
  [#2060](https://github.com/sanic-org/sanic/pull/2060)
  [#2061](https://github.com/sanic-org/sanic/pull/2061) Introduce
  Signals API
- [#2043](https://github.com/sanic-org/sanic/pull/2043) Add
  `__str__` and `__repr__` to Sanic and Blueprint
- [#2047](https://github.com/sanic-org/sanic/pull/2047) 启用
  版本并在蓝图组上严格闪光灯
- [#2053](https://github.com/sanic-org/sanic/pull/2053) Make
  `get_app` name 参数是可选的
- [#2055](https://github.com/sanic-org/sanic/pull/2055) JSON编码器
  通过应用程序更改
- [#2063](https://github.com/sanic-org/sanic/pull/2063) App 和
  连接级别环境对象

**错误修复**

- 解析[#1420](https://github.com/sanic-org/sanic/pull/1420)
  `url_for` ，其中`strict_slashes` 正在开启路径，结束于 `/`
- 解析[#1525](https://github.com/sanic-org/sanic/pull/1525)
  路由不正确，有一些特殊字符
- 解析[#1653](https://github.com/sanic-org/sanic/pull/1653) ASGI
  物体头
- 解析[#1722](https://github.com/sanic-org/sanic/pull/1722)
  在区块模式中使用curl
- 解析[#1730](https://github.com/sanic-org/sanic/pull/1730)
  ASGI 串流响应额外内容
- 解析[#1749](https://github.com/sanic-org/sanic/pull/1749)
  还原破损的中间件边缘案件
- Resolve [#1785](https://github.com/sanic-org/sanic/pull/1785)
  [#1804](https://github.com/sanic-org/sanic/pull/1804) Synchronous
  error handlers
- 解析[#1790](https://github.com/sanic-org/sanic/pull/1790)
  协议错误不支持 async 错误处理程序 #1790
- 解析[#1824](https://github.com/sanic-org/sanic/pull/1824)
  超时特定方法
- Resolve [#1875](https://github.com/sanic-org/sanic/pull/1875)
  Response timeout error from all routes after returning several
  timeouts from a specific route
- 解析[#1988](https://github.com/sanic-org/sanic/pull/1988)
  用身体处理安全方法
- [#2001](https://github.com/sanic-org/sanic/pull/2001) 提升
  值错误，因为cookie max-age 不是整数

**废弃和删除**

- [#2007](https://github.com/sanic-org/sanic/pull/2007)\* 配置
  使用 `from_envvar` \* 配置使用 `from_pyfile` \* 配置使用
  `from_object`
- [#2009](https://github.com/sanic-org/sanic/pull/2009) 删除Sanic
  测试客户端到自己的包
- [#2036](https://github.com/sanic-org/sanic/pull/2036),
  [#2037](https://github.com/sanic-org/sanic/pull/2037) Drop Python
  3.6
- `Request.endpoint` 已不推荐使用 `Request.name`
- 处理器类型名称前缀已删除 (静态、websocket 等)

**开发者基础设施**

- [#1995](https://github.com/sanic-org/sanic/pull/1995) Create
  FUNDING.yml
- [#2013](https://github.com/sanic-org/sanic/pull/2013) 将codeql
  添加到CI 管道中
- [#2038](https://github.com/sanic-org/pull/2038) Codecov
  配置更新
- [#2049](https://github.com/sanic-org/sanic/pull/2049) 更新
  设置，使用 `find_packes`

**改进文档**

- [#1218](https://github.com/sanic-org/sanic/pull/1218)
  文件缺失。\*
- [#1608](https://github.com/sanic-org/sanic/pull/1608) 添加
  卡车文档和 LTS
- [#1731](https://github.com/sanic-org/sanic/pull/1731) Support
  mounting application elsewhere than at root path
- [#2006](https://github.com/sanic-org/sanic/pull/2006) 升级
  类型注释并改进文档字符串和 API 文档
- [#2052](https://github.com/sanic-org/sanic/pull/2052) 修复一些
  示例和文档

**杂项**

- `Request.route` 属性
- 更好的Websocket 子协议支持
- 传递了
  时用蓝图组中的中间件解决bug
- 将蓝图和Sanic之间的通用逻辑移动到混合物
- 路由命名更改为更加一致
  - 请求端点是路由名称
  - 路由名称已完全空格
- 一些新的便利装饰符：
  - `@app.main_process_start`
  - `@app.main_process_stop`
  - `@app.befor_server_start`
  - `@app.after _server_start`
  - `@app.befor_server_stop`
  - `@app.after _server_stop`
  - `@app.on_request`
  - `@app.on_response`
- 修复不包含 `HEAD` 的 `Alle` 标题
- 在 `url_for` 中使用 "name" 关键字用于"static"路由，在那里不存在
  名称
- 不使用命名参数，无法拥有多个`app.static()`
- 在文件路径上使用 "filename" 关键字在 `url_for`
- `取消引号`而不是自动'
- `routes_all` 是导线
- 处理器参数只是 kwarg
- `request.match_info` 现在是缓存的(而不是计算的)属性
- 未知的静态文件 mimetype 以 `application/octet-stream` 格式发送
- `url_for`中的`_host`关键字
- 如果没有指定
  ，为文本和 js 内容类型添加字符集默认值到 `utf-8`
- 路由的版本可以是字符串、浮点型变量或整数
- 路由有 ctx 属性
- 应用程序有`routes_static`, `routes_dynamic`, `routes_regex`
- [#2044](https://github.com/sanic-org/sanic/pull/2044) 代码清理
  并重新排料中
- [#2072](https://github.com/sanic-org/sanic/pull/2072) 删除
  `BaseSanic` metaclass
- [#2074](https://github.com/sanic-org/sanic/pull/2074) 性能
  调整 `handle_request_`

## 第20.12.3 版

**错误修复**

- [#2021](https://github.com/sanic-org/sanic/pull/2021) 从websocket 处理器名称中删除
  前缀

## 第20.12.2版

**依赖**

- [#2026](https://github.com/sanic-org/sanic/pull/2026) 修复uvloop
  至 0.14 因为0.15 drops Python 3.6 支持
- [#2029](https://github.com/sanic-org/sanic/pull/2029) 删除旧的
  字符要求，在硬的多词要求中添加

## 第19.12.5版

**依赖**

- [#2025](https://github.com/sanic-org/sanic/pull/2025) Fix uvloop
  到 0.14 因为0.15 drops Python 3.6 支持
- [#2027](https://github.com/sanic-org/sanic/pull/2027) 删除旧的
  chardet 要求，在硬的多词要求中添加

## 版本20.12.0

**特征**

- [#1993](https://github.com/sanic-org/sanic/pull/1993) 添加禁用
  应用注册
- [#1945](https://github.com/sanic-org/sanic/pull/1945) 静态路由
  更详细，如果找不到文件
- [#1954](https://github.com/sanic-org/sanic/pull/1954) 修复静态
  路由注册在蓝图上
- [#1961](https://github.com/sanic-org/sanic/pull/1961) 添加 Python
  3.9 支持
- [#1962](https://github.com/sanic-org/sanic/pull/1962) Sanic CLI
  升级
- [#1967](https://github.com/sanic-org/sanic/pull/1967) Update
  aiofile 版本要求
- [#1969](https://github.com/sanic-org/sanic/pull/1969) Update
  multidict requirements
- [#1970](https://github.com/sanic-org/sanic/pull/1970) 添加py.typed
  文件
- [#1972](https://github.com/sanic-org/sanic/pull/1972) Speed
  optimization in request handler
- [#1979](https://github.com/sanic-org/sanic/pull/1979) 添加应用
  注册表和 Sanic 类级应用程序检索器

**错误修复**

- [#1965](https://github.com/sanic-org/sanic/pull/1965) 修正Chunked
  传输-编码在 ASGI 串流响应中

**废弃和删除**

- [#1981](https://github.com/sanic-org/sanic/pull/1981) 清理和
  删除已废弃的代码

**开发者基础设施**

- [#1956](https://github.com/sanic-org/sanic/pull/1956) 修正负载
  模块测试
- [#1973](https://github.com/sanic-org/sanic/pull/1973) Transition
  Travis从.org 到 .com
- [#1986](https://github.com/sanic-org/sanic/pull/1986) Update tox
  要求

**改进文档**

- [#1951](https://github.com/sanic-org/sanic/pull/1951)
  文档改进
- [#1983](https://github.com/sanic-org/sanic/pull/1983) 移除测试.rst 中的
  重复内容
- [#1984](https://github.com/sanic-org/sanic/pull/1984) 修复
  路由.rst

## 20.9.1 版本

**错误修复**

- [#1954](https://github.com/sanic-org/sanic/pull/1954) 修复静态
  路由注册在蓝图上
- [#1957](https://github.com/sanic-org/sanic/pull/1957) 删除ASGI流体中的
  重复标题

## 第19.12.3 版

**错误修复**

- [#1959](https://github.com/sanic-org/sanic/pull/1959) 删除ASGI流体中的
  重复的头部

## 版本20.9.0

**特征**

- [#1887](https://github.com/sanic-org/sanic/pull/1887) 在 websockets (均为sanic server and ASGI) 传递
  子协议
- [#1894](https://github.com/sanic-org/sanic/pull/1894)
  在应用实例上自动设置 `test_mode` 标志
- [#1903](https://github.com/sanic-org/sanic/pull/1903) 添加新的
  统一方法来更新应用值
- [#1906](https://github.com/sanic-org/sanic/pull/1906),
  [#1909](https://github.com/sanic-org/sanic/pull/1909) Adds
  WEBSOCKET_PING_TIMEOUT和WEBSOCKET_PING_ING_INTERVAL configuration
  值
- [#1935](https://github.com/sanic-org/sanic/pull/1935) httpx
  版本依赖关系更新，它预定在 v20.12 中被移除为
  依赖关系。
- [#1937](https://github.com/sanic-org/sanic/pull/1937) 已添加自动、
  文本和 json 回退错误处理程序(v21.3, 默认为
  更改表格为 auto)

**错误修复**

- [#1897](https://github.com/sanic-org/sanic/pull/1897) 解析流中未读字节的
  异常

**废弃和删除**

- [#1903](https://github.com/sanic-org/sanic/pull/1903)
  config.from_envar, config.from_pyfile, 和 config.from_object 是
  废弃并设置为 v21.3

**开发者基础设施**

- [#1890](https://github.com/sanic-org/sanic/pull/1890),
  [#1891](https://github.com/sanic-org/sanic/pull/1891) 更新isort
  调用以兼容新的 API
- [#1893](https://github.com/sanic-org/sanic/pull/1893) 从setup.cfg 中删除
  版本
- [#1924](https://github.com/sanic-org/sanic/pull/1924) 添加
  \--strict-markers for pytest

**改进文档**

- [#1922](https://github.com/sanic-org/sanic/pull/1922) 在README 中添加明确的
  ASGI 遵守情况

## 20.6.3 版本

**错误修复**

- [#1884](https://github.com/sanic-org/sanic/pull/1884) 还原
  更改为多处理模式

## 20.6.2 版本

**特征**

- [#1641](https://github.com/sanic-org/sanic/pull/1641) Socket
  绑定适合IPv6和UNIX套接字

## 20.6.1 版本

**特征**

- [#1760](https://github.com/sanic-org/sanic/pull/1760) 在 websocket 路由中添加版本
  参数
- [#1866](https://github.com/sanic-org/sanic/pull/1866) 添加`sanic`
  作为入口点命令
- [#1880](https://github.com/sanic-org/sanic/pull/1880) Add handler
  names for websockets for url_for usage

**错误修复**

- [#1776](https://github.com/sanic-org/sanic/pull/1776)
  主机参数问题的 Bug 修复
- [#1842](https://github.com/sanic-org/sanic/pull/1842) 修复静态
  _处理程序拾取错误
- [#1827](https://github.com/sanic-org/sanic/pull/1827) 在 OSX py38 和 Windows 上修复读取器
- [#1848](https://github.com/sanic-org/sanic/pull/1848) 反向
  named_response_midlware execution order，以匹配正常的响应Order
  中间件执行顺序
- [#1853](https://github.com/sanic-org/sanic/pull/1853) Fix pickle
  error when attempting to pickle an application which contains
  websocket routes

**废弃和删除**

- [#1739](https://github.com/sanic-org/sanic/pull/1739) 废弃
  body_bytes并入体

**开发者基础设施**

- [#1852](https://github.com/sanic-org/sanic/pull/1852) 修复CI test env Python nightlies 上的
- [#1857](https://github.com/sanic-org/sanic/pull/1857) Adjust
  websockets 版本以设置py
- [#1869](https://github.com/sanic-org/sanic/pull/1869) 包装
  run()'s "protocol" 类型注释在选项[]

**改进文档**

- [#1846](https://github.com/sanic-org/sanic/pull/1846) 更新文档
  以澄清响应中间件执行顺序
- [#1865](https://github.com/sanic-org/sanic/pull/1865) 修复正在隐藏文档的 rst
  格式问题

## 版本20.6.0

_释放但无意省略的 PR #1880，所以被
20.6.1_ 取代。

## 版本20.3.0

**特征**

- [#1762](https://github.com/sanic-org/sanic/pull/1762) Add
  `srv.start_serving()` and `srv.serve_forever()` to `AsyncioServer`
- [#1767](https://github.com/sanic-org/sanic/pull/1767) Make Sanic
  可在 `hypercorn -k trio myweb.app` 上使用
- [#1768](https://github.com/sanic-org/sanic/pull/1768) 没有
  对正常错误和预审错误页面的跟踪
- [#1769](https://github.com/sanic-org/sanic/pull/1769) 代码清理文件回复中的
- [#1793](https://github.com/sanic-org/sanic/pull/1793)和
  [#1819](https://github.com/sanic-org/sanic/pull/1819) 将
  `str.form()` 升级为f-字符串。
- [#1798](https://github.com/sanic-org/sanic/pull/1798) 允许
  MacOS 上与Python 3.8的多个工作者。
- [#1820](https://github.com/sanic-org/sanic/pull/1820) 不在异常中设置
  内容类型和内容长度标题

**错误修复**

- [#1748](https://github.com/sanic-org/sanic/pull/1748) 移除在 Python 3.8 的`asyncio.Event` 中的
  循环
- [#1764](https://github.com/sanic-org/sanic/pull/1764) Allow route
  decorators to stack up again
- [#1789](https://github.com/sanic-org/sanic/pull/1789) 使用产生错误的\`url_for'的主机修复
- [#1808](https://github.com/sanic-org/sanic/pull/1808) 修正Ctrl+C
  和Windows 测试

**废弃和删除**

- [#1800](https://github.com/sanic-org/sanic/pull/1800) 以一流的方式开始
  弃置，移除
  `body_init`, `body_pub`和`body_finish`
- [#1801](https://github.com/sanic-org/sanic/pull/1801) Complete
  deprecation from
  [#1666](https://github.com/sanic-org/sanic/pull/1666) of
  dictionary context on `request` objects.
- [#1807](https://github.com/sanic-org/sanic/pull/1807) 删除可直接从应用程序读取的
  服务器配置 args
- [#1818](https://github.com/sanic-org/sanic/pull/1818) Complete
  deprecation of `app.remove_route` and `request.raw_args`

**依赖**

- [#1794](https://github.com/sanic-org/sanic/pull/1794) Bump `httpx`
  to 0.11.1
- [#1806](https://github.com/sanic-org/sanic/pull/1806) Import
  `ASGIDispatch` from top-level `httpx` (from third-party
  deprecation)

**开发者基础设施**

- [#1833](https://github.com/sanic-org/sanic/pull/1833) 解决了
  损坏的文档版本

**改进文档**

- [#1755](https://github.com/sanic-org/sanic/pull/1755)
  `response.empty()`
- [#1778](https://github.com/sanic-org/sanic/pull/1778) Update
  README
- [#1783](https://github.com/sanic-org/sanic/pull/1783) 修复类型
- [#1784](https://github.com/sanic-org/sanic/pull/1784) 更正了
  更改了 MD 移动到 RST
  ([#1691](https://github.com/sanic-org/sanic/pull/1691))
- [#1803](https://github.com/sanic-org/sanic/pull/1803) 更新
  配置文件以匹配DEFAULT_CONFIG
- [#1814](https://github.com/sanic-org/sanic/pull/1814) 更新
  getting_started.rst
- [#1821](https://github.com/sanic-org/sanic/pull/1821) 更新到
  部署
- [#1822](https://github.com/sanic-org/sanic/pull/1822) 更新文档
  并修改于 20.3
- [#1834](https://github.com/sanic-org/sanic/pull/1834)
  侦听器顺序

## 版本19.12.0

**错误修复**

- 修复蓝图中间件应用

  目前，任何蓝图中间件都已注册，而不论
  是用哪个蓝图来注册的。 正在应用于所有由 `@app` 和 `@bluprint` 创建的
  路由。

  作为此更改的一部分，基于蓝图的中间件应用程序
  是根据它们的注册地点强制执行的。

  - If you register a middleware via `@blueprint.middleware` then it
    will apply only to the routes defined by the blueprint.
  - 如果您通过 `@bluprint_group.middleware`
    注册了一个中间软件，它将适用于所有基于蓝图的路由，这些路由属于群组的
    部分。
  - If you define a middleware via `@app.middleware` then it will be
    applied on all available routes
    ([#37](https://github.com/sanic-org/sanic/issues/37))

- Fix [url_for]{.title-ref} behavior with missing SERVER_NAME

  If the [SERVER_NAME]{.title-ref} was missing in the
  [app.config]{.title-ref} entity, the [url_for]{.title-ref} on the
  [request]{.title-ref} and [app]{.title-ref} were failing due to an
  [AttributeError]{.title-ref}. This fix makes the availability of
  [SERVER_NAME]{.title-ref} on our [app.config]{.title-ref} an
  optional behavior.
  ([No. 1707](https://github.com/sanic-org/sanic/issues/1707))

**改进文档**

- 将文档从MD移动到RST

  将所有文档从Markdown移动到调整后的文本，如
  的其他文档，统一方案并使它在未来更容易地更新到
  更新文档。
  ([#1691](https://github.com/sanic-org/sanic/issues/1691))

- Fix documentation for [get]{.title-ref} and [getlist]{.title-ref} of
  the [request.args]{.title-ref}

  Add additional example for showing the usage of
  [getlist]{.title-ref} and fix the documentation string for
  [request.args]{.title-ref} behavior
  ([#1704](https://github.com/sanic-org/sanic/issues/1704))

## 版本19.6.3

**特征**

- 启用 Towncrier 支持

  As part of this feature, [towncrier]{.title-ref} is being introduced
  as a mechanism to partially automate the process of generating and
  managing change logs as part of each of pull requests.
  ([No. 1631](https://github.com/sanic-org/sanic/issues/1631))

**改进文档**

- 文件基础设施变化
  - Enable having a single common [CHANGELOG]{.title-ref} file for
    both GitHub page and documentation
  - 修复 Sphinix 废弃警告
  - Fix documentation warnings due to invalid [rst]{.title-ref}
    indentation
  - Enable common contribution guidelines file across GitHub and
    documentation via [CONTRIBUTING.rst]{.title-ref}
    ([#1631](https://github.com/sanic-org/sanic/issues/1631))

## 版本19.6.2

**特征**

- [#1562](https://github.com/sanic-org/sanic/pull/1562) 去除
  `aiohttp` 依赖关系，并根据
  [requests-async](https://github.com/encode/requests-async) 创建新的`SanicTestClient`
- [#1475](https://github.com/sanic-org/sanic/pull/1475) 添加了ASGI
  支持(Beta)
- [#1436](https://github.com/sanic-org/sanic/pull/1436) Add
  Configure support from object string

**错误修复**

- [#1587](https://github.com/sanic-org/sanic/pull/1587) 添加缺失的
  句柄给预期头部。
- [#1560](https://github.com/sanic-org/sanic/pull/1560) Allow to
  disable Transfer-Encoding: chunked.
- [#1558](https://github.com/sanic-org/sanic/pull/1558) Fix 宽松的
  关机。
- [#1594](https://github.com/sanic-org/sanic/pull/1594) Strict
  斜线行为修复

**废弃和删除**

- [#1544](https://github.com/sanic-org/sanic/pull/1544) Drop
  依附于打分上
- [#1562](https://github.com/sanic-org/sanic/pull/1562) Drop support
  for Python 3.5
- [#1568](https://github.com/sanic-org/sanic/pull/1568) 废弃
  路由移动。

.. 警告：：警告

```
Sanic 将不支持 Python 3.5 版本的 19.6 和前进。 
然而，版本 18。 2LTS 将有其支持期延长期延时
2020年12月，因此通过 Python\'s 官方支持版本
3。 ，定于2020年9月到期。
```

## 版本19.3

**特征**

- [#1497](https://github.com/sanic-org/sanic/pull/1497) Add support
  for zero-length and RFC 5987 encoded filename for
  multipart/form-data requests.

- [#1484](https://github.com/sanic-org/sanic/pull/1484) `sanic.cookies.cookie`的
  `expires`属性的类型现在被强制执行到
  的类型是`datetime`。

- [#1482](https://github.com/sanic-org/sanic/pull/1482) 添加支持
  的`sanic.Sanic.add_route()` 的
  至`sanic.Blueprint.add_route()` 。

- [#1481](https://github.com/sanic-org/sanic/pull/1481) 接受路径参数的
  负值，类型为 `int` 或 `num` 。

- [#1476](https://github.com/sanic-org/sanic/pull/1476) 废弃了
  的使用 `sanic.request.Request.raw_args` - 它有一个基本的
  缺陷，它会丢弃重复查询字符串参数。 添加
  `sanic.request.Requery_args` 作为原始的
  use-case。

- [#1472](https://github.com/sanic-org/sanic/pull/1472) 移除请求类`repr`实现中的
  意外的`None` 检查。 此
  将请求的默认`repr` 从 `<Request>`改为
  \<Request: None />\`

- [#1470](https://github.com/sanic-org/sanic/pull/1470) 添加2个新的
  参数到 `sanic.app.Sanic.create_server`

  - `return_asyncio_server` - 是否返回
    asyncio.Server。
  - `asyncio_server_kwargs` - kwargs to pass to
    `loop.create_server` for the event loop that sanic is using.

  >

  这是一个突破性的变化。

- [#1499](https://github.com/sanic-org/sanic/pull/1499) 添加了测试和基准路由分辨率为
  的测试案例。

- [#1457](https://github.com/sanic-org/sanic/pull/1457)
  的类型在 `sanic.cookies.cookie` 中的 `max-age` 值现在是强制执行
  为整数。 非整数值替换为 \`0'。

- [#1445](https://github.com/sanic-org/sanic/pull/1445) 将
  `endpoint` 属性添加到传入的 `request` 中，包含处理器函数的
  名称。

- [#1423](https://github.com/sanic-org/sanic/pull/1423) 改进了
  请求流。 `request.stream` 现在是一个已退回的大小
  而不是一个无限制的队列。 现在呼叫者必须调用
  `request.stream.read()` 而不是一个
  `required request.stream.get()` 以阅读身体的每一部分。

  这是一个突破性的变化。

**错误修复**

- [#1502](https://github.com/sanic-org/sanic/pull/1502) Sanic was
  prefetching `time.time()` and updating it once per second to avoid
  excessive `time.time()` calls. 观察到
  在一些情况下造成内存泄漏。 预获取
  的好处似乎微不足道，因此这个好处已被删除。 修复
  [#1500](https://github.com/sanic-org/sanic/pull/1500)
- [#1501](https://github.com/sanic-org/sanic/pull/1501)修复了
  自动读取加载器中的一个错误，当过程作为模块启动时，
  "python -m init0.mod1", 在这种情况下, sanic server 开始于
  `init0/mod1.py` , 启用了 `debug` , 并在
  `init0` 中导入另一个模块.
- [#1376](https://github.com/sanic-org/sanic/pull/1376) 允许sanic
  测试客户端在构建一个 `port=None`
  时绑定到随机端口
- [#1399](https://github)。 om/sanic-org/sanic/pull/1399)增加了
  在蓝图组中指定中间件的能力。 所以从组中的蓝图中生成的所有
  路径都应用了
  中间件.
- [#1442](https://github.com/sanic-org/sanic/pull/1442) 允许
  使用 `SANIC_ACCESS_LOG` 环境变量到
  启用/禁用访问日志时未明确传递到
  `app.run()` 。 这将允许在使用枪炮运行时禁用访问日志，例如
  。

**开发者基础设施**

- [#1529](https://github.com/sanic-org/sanic/pull/1529) 更新
  项目 PyPI 凭据
- [#1515](https://github.com/sanic-org/sanic/pull/1515) fixed linter
  issue causing travis building succession(fix #1514)
- [#1490](https://github.com/sanic-org/sanic/pull/1490) 修复python
  版本在编译中
- [#1478](https://github.com/sanic-org/sanic/pull/1478) 升级
  设置工具版本并在构建过程中使用本机文档
- [#1464](https://github.com/sanic-org/sanic/pull/14644) 升级
  pytest 并修复capg 单元测试

**改进文档**

- [#1516](https://github.com/sanic-org/sanic/pull/1516) Fix typo at
  是例外文档
- [#1510](https://github.com/sanic-org/sanic/pull/1510) fixe typo in
  Asyncio example
- [#1486](https://github.com/sanic-org/sanic/pull/1486)
  文档类型
- [#1477](https://github.com/sanic-org/sanic/pull/1477) 修理文法
  in README.md
- [#1489](https://github.com/sanic-org/sanic/pull/1489) 添加
  "databases" 到扩展列表
- [#1483](https://github.com/sanic-org/sanic/pull/1483) 在扩展列表中添加
  sanic-zipkin
- [#1487](https://github.com/sanic-org/sanic/pull/1487) 删除了链接
  从扩展列表中删除 Sanic-OAuth,
- [#1460](https://github.com/sanic-org/sanic/pull/1460) 18.12
  changelog
- [#1449](https://github.com/sanic-org/sanic/pull/1449) Add example
  of amending request object
- [#1446](https://github.com/sanic-org/sanic/pull/1446) 更新
  README
- [#1444](https://github.com/sanic-org/sanic/pull/14444) 更新
  README
- [#1443](https://github.com/sanic-org/sanic/pull/1443) 更新
  README，包括新的徽标
- [#1440](https://github.com/sanic-org/sanic/pull/1440) 修复小的
  类型和 pip安装指令不匹配
- [#1424](https://github.com/sanic-org/sanic/pull/1424)
  文档改进

注： 19.3.0 被跳过用于封装目的，没有在
PyPI 上发布

## 18.12 版本

### 18.12.0

- 变更：

  - 代码片测试覆盖率从81%提高到91%。
  - 在static_file
    文档中添加串流大量文件和主机示例
  - 添加方法以在请求
    (#1379)
  - Windows ci 支持与 .appveyor.yml 集成
  - 为 AF_INET6 和 AF_UNIX 套接字使用添加文档
  - 采用黑色/isort来换代币
  - 连接丢失时取消任务
  - 简化请求 ip 和端口检索逻辑。
  - 处理负载配置文件中的配置错误。
  - CI 与 codecov 集成
  - 为配置部分添加未接文档。
  - 已弃用 Handler.log
  - 固定的 httptools 要求到版本 0.0.10 +

- 修复：

  - 修复 `remove_entity_headers` 函数(#1415)
  - 修复蓝图
    蓝图使用默认的 url_prefix时，使用 os.path。 避免无效的
    url_prefix 像api//v1 f8a6af1 那样将`http` 模块重命名为
    `helpers` 以防止与内置的 Python HTp
    库 (fixes #1323) 发生冲突
  - 修复窗口上的无功者
  - 修复清理记录器命名空间
  - 修复装饰器示例中缺少的引用
  - 使用引用参数修复重定向
  - 修复最新蓝图代码
  - 修复与 Markdown 列表相关的 latex 文档构建。
  - 修复app.py 中的循环异常处理
  - 修复窗口和其他平台中的内容长度不匹配
  - 修复静态文件的范围头处理 (#1402)
  - 修复记录器并使其工作 (#1397)
  - 修复多处理测试中的 pikcle->选取的类型
  - 修复选取蓝图更改蓝图在蓝图中的
    "name" 部分中传递的字符串，以便匹配蓝图模块属性名称的
    名称。 这使得
    蓝图能够在没有错误的情况下被选取和卸载，
    是在
    Windows中以多处理模式运行Sanic的要求。 Added a test for pickling and unpickling blueprints
    Added a test for pickling and unpickling sanic itself Added a
    test for enabling multiprocessing on an app with a blueprint
    (only useful to catch this bug if the tests are run on
    Windows).
  - 修复日志文档

## 版本 0.8

**0.8.3**

- 变更：
  - 所有权更改为 org 'sanic-org'

**0.8.0**

- 变更：
  - 添加服务器发送事件扩展 (Innokty Lebedev)
  - 优化处理 request_handler_task 取消 (Ashley
    Sommer)
  - 在重定向前Sanize URL (aveao)
  - 添加url_bytes到请求 (johndoe46)
  - py37 支持travisci(yunstanford)
  - 自动装入器支持 OSX (garyo)
  - 添加 UUID 路由支持 (Volodymyr Maksymiv)
  - 添加可用响应流 (Ashley Sommer)
  - 添加弱项到请求时段(vopankov)
  - 由于废弃
    (yunstanford) 从测试灯具中移除 ubuntu 12.04
  - 允许在add_route (kinware) 中流媒体处理程序
  - 使用 travis_retry for tox (Raphael Deem)
  - 更新测试客户端的 aiothttp 版本 (yunstanford)
  - 添加重定向导导入以提高清晰度(yingshaoxo)
  - 更新 HTTP 实体标题 (Arnulfo Solis)
  - 添加注册监听方法 (Stephan Fitzpatrick)
  - 删除 Windows 的 uvloop/ujson 依赖项 (abuckenheimer)
  - 204/304答复的内容长度标题(Arnulfo Soli)
  - 扩展 WebSocketProtocol 参数并添加文档 (Bob Olde
    Hampsink, yunstanford)
  - 更新开发状态从 alpha 到beta (Maksim
    Anisenkov)
  - KeepAlive 超时日志级别更改为调试(Arnulfo Soli)
  - 因为pest-dev/pytest#3170 (Maksim
    Aniskenov)
  - 安装 Python 3.5 和 3.6 到码头容器进行测试 (Shahin
    Azad)
  - 添加支持蓝图组和嵌套(Elias Tarhini)
  - 移除窗口设置的 uvloop(Aleksandr Kurlov)
  - Auto Reload (Yaser Amari)
  - 文档更新/修复(多个贡献者)
- 修复：
  - 修复：Linux自动重新加载(Ashley Sommer)
  - 修复：aiothttp >= 3.3.0 (Ashley Sommer)
  - 修复：在窗口上默认禁用自动重新加载 (abuckenheimer)
  - 修复 (1143)：用枪炮关闭访问日志 (hqy)
  - 修复 (1268)：文件响应的支持状态代码 (Cosmo Borsky)
  - 修复 (1266)：将 content_type 标志添加到 Sanic.statil (Cosmo Borsky)
  - 修复：从add_websocket_route
    中缺少子协议参数(ciscorn)
  - 修复 (1242)：CI 头的响应 (yunstanford)
  - 修复 (1237): 添加 websockets 的版本约束 (yunstanford)
  - 修复 (1231): 内存泄漏- 总是释放资源 (Phillip Xu)
  - 修复 (1221)：如果存在传输，请提出truthy (Raphael
    Deem)
  - 修复aiohttp>=3.1.0 (Ashley Sommer)
  - 修复所有示例(PyManiacGR, kot83)
  - 修复 (1158)：默认在调试模式下自动重新加载 (Raphael Deem)
  - 修复 (1136): ErrorHandler.response 处理器调用限制性过强的
    (Julien Castiaux)
  - 修复：原始需要类似字节的对象 (云)
  - 修复 (1120): 将列表传递到路由装饰器's host arg
    (Timothy Ebiuwe)
  - 修复：多部分/形式数据解析器中的错误(DirkGuijt)
  - 修复：值为 null
    时缺少参数的异常(NyanKiyoshi)
  - 修复：参数检查 (Howie Hu)
  - 修复 (1089): 带有命名参数和不同的
    方法的路由问题 (yunstanford)
  - 修复(1085)：以多工模式处理信号(yunstanford)
  - 修复：readme.rst中的单引号(成本)
  - 修复：方法类型 (Dmitry Dygalo)
  - 修复：Log_response 正确的IP和端口输出(Wibowo
    Arindrarto)
  - 修复(1042)：异常处理(Raphael Deem)
  - 修正：中文 URI (Howie Hu)
  - 修复 (1079)：当自己的传送无时超时 (Raphael
    Deem)
  - 修复 (1074)：在路由有斜线时修复 strit_slash(Raphael
    Deem)
  - 修复 (1050): 将 samesite cookie 添加到 cookie keys (Raphael Deem)
  - 修复 (1065)：允许在服务器启动后添加任务 (Raphael Deem)
  - 修复 (1061)：在未经授权的异常中双引号 (Raphael
    Deem)
  - 修复 (1062)：将应用程序注入到 add_task 方法 (Raphael Deem)
  - 修正: 更新 environment.yml for readthedocs (Eli Uriegas)
  - Fix: Cancel request task when response timeout is triggered
    (Jeong YunWon)
  - Fix (1052): Method not allowed response for RFC7231 compliance
    (Raphael Deem)
  - 修复：IPv6 地址和 Socket 数据格式 (Dan Palmer)

注：更新日志保持在 0.1 和 0.7之间

## 版本 0.1

**0.1.7**

- 反转静态URL和目录参数以适应spec

**0.1.6**

- 静态文件
- Lazy Cookie 加载

**0.1.5**

- Cookie
- 蓝图监听器和顺序
- 快速路由器
- 修复：在中等以上大小的帖子请求中读取不完整的文件
- 断开︰ 事后开始和之前停止现在作为他们的
  第一个参数

**0.1.4**

- 多处理

**0.1.3**

- 蓝图支持
- 快速响应处理

**0.1.1 - 0.1.2**

- 通过 CI 更新 pypi 的字符串

**0.1.0**

- 向公众发布
