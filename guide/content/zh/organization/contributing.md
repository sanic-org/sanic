# 贡献中

感谢您的兴趣！ Sanic总是在寻找贡献者。 如果你觉得不舒服的贡献代码，请将文档添加到源文件中，或帮助[Sanic User Guide](https://github)。 请提供文件或执行实例，以此表示欢迎！

我们致力于为所有人提供一个友好、安全和受欢迎的环境，不论其性别、性取向、残疾、族裔、宗教或类似的个人特征。 我们的[行为守则](https://github.com/sanic-org/sanic/blob/master/CONDUCT.md)规定了行为标准。

## 安装

要在 Sanic 上开发(主要是运行测试)，强烈建议从源头安装。

所以假定你已经克隆了仓库，并且在工作目录中已经设置了虚拟环境，然后运行：

```sh
pip install -e ".[dev]"
```

## 依赖关系变化

`Sanic` 不使用 `requirements*.txt` 文件来管理与此相关的任何依赖关系，以简化管理依赖关系所需的努力。 请确保您已经阅读并理解文档的下面一节，其中解释了`sanic` 如何管理`setup.py`文件中的依赖关系。

| 依赖类型                                                                                                                                 | 用法                     | 安装                                                                                              |
| ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------- | ----------------------------------------------------------------------------------------------- |
| 所需经费                                                                                                                                 | 智能正常运行所需的最低依赖关系        | `pip3 install -e .`                                                                             |
| tests_request / extras_require['test'] | 运行 `sanic` 设备测试所需的依赖关系 | \`pip3 install -e '.[test]' |
| extras_require['dev']                                       | 增加捐款的额外发展要求            | \`pip3 install -e '.[dev]'  |
| extras_require['docs']                                      | 建立和加强卫生文档所需的依赖关系       | \`pip3 install -e '.[docs]' |

## 正在运行所有测试

要运行 Sanic 测试，建议像这样使用tox：

```sh
tox
```

看看这么简单！

`tox.ini`含有不同的环境。 Running `tox` without any arguments will
run all unittests, perform lint and other checks.

## 不需要时运行

`tox` 环境 -> `[testenv]`

只能执行空闲的玩家就能运行类似于环境的\`毒性'：

```sh

tox -e py37 -v -- tests/test_config.py
# 或
tox -e py310 -v -- tests/test_config.py
```

## 运行行检查

`tox` 环境 -> `[testenv:lin]`

执行 `flake8` 、 `black` 和 `isort` 检查。

```sh
tox -e lint
```

## 运行类型批注检查

`tox` 环境 -> `[testenv:type-checking]`

执行`mypy`检查。

```sh
tox -e 类型检查
```

## 运行其他检查

`tox` 环境 -> `[testenv:check]`

执行其他检查。

```sh
tox -e 检查
```

## 运行静态分析

`tox` 环境 -> `[testenv:security]`

执行静态分析安全扫描

```sh
tox -e 安全
```

## 运行文档智能检查

`tox` 环境 -> `[testenv:docs]`

对文档进行智能检查

```sh
tox -e 文档
```

## 代码样式

为了保持代码的一致性，Sanic使用以下工具：

1. [isort](https://github.com/timothycrosley/isort)
2. [black](https://github.com/python/black)
3. [flake8](https://github.com/PyCQA/flake8)
4. [slotscheck](https://github.com/ariebovenberg/slotscheck)

### isort

`isort` 排序的 Python 导入。 它将进口分为三类，按字母顺序排列：

1. 内置的
2. 第三方
3. 特定项目

### 黑色

`black` 是一个 Python 代码格式。

### 火焰8

`flake8` 是一个 Python 风格指南，将以下工具包装成一个工具：

1. PyFlakes
2. pycodestyle
3. Ned Batchid's McCabe 脚本

### slotscheck

`slotscheck` ensures that there are no problems with `__slots__` (e.g., overlaps, or missing slots in base classes).

`isort`, `black`, `flake8`, `slotscheck` 检查是在 `tox` 链接检查期间进行的。

**最简单** 使您的代码符合要求的方法是在提交之前运行以下内容：

```bash
做得很好
```

欲了解更多详情，请参阅[tox documentation](https://tox.readthedocs.io/en/ index.html)。

## 拉取请求

所以拉取请求批准规则非常简单：

1. 所有合并请求必须通过单元测试。
2. 所有合并请求必须经过核心开发团队中至少一个当前成员的审查和批准。
3. 所有合并请求都必须通过 flake8 检查。
4. 所有合并请求必须匹配 `isort` 和 `black` 要求。
5. 所有合并请求必须为 **PROPERLY** 类型，除非给予豁免。
6. 所有合并请求必须与现有代码一致。
7. 如果您决定从任何通用接口中移除/更改任何内容，则应根据我们的[废弃政策](https://sanicframework.org/en/guide/project/policies.html#disposition)随附一个废弃的消息。
8. 如果你实现了一个新功能，你应该至少有一个单元测试来伴随它。
9. 一个例子必须是：
   - 如何使用 Sanic 的例子
   - 如何使用 Sanic 扩展
   - 如何使用 Sanic 和异步库的例子

## 文件

回车. 我们正在重新编写我们的文件，以便改变这种情况。
