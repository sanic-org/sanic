# Docker 部署

## 一. 导言

长期以来，环境一直是部署的一个困难问题。 如果您的项目中存在相互冲突的配置，您必须花费大量时间解析它们。 幸运的是，虚拟化为我们提供了一个好的解决办法。 码头就是其中之一。 如果你不知道Docker，你可以访问 [Docker官方网站](https://www.docker.com/) 了解更多信息。

## 构建图像

让我们从一个简单的项目开始。 我们将以Sanic项目为例。 假设项目路径是 `/path/to/SanicDocker` 。

.. 列:

```
目录结构看起来像这样：
```

.. 列:

````
```text
# /path/to/SanicDocker
SanicDocker
├── requirements.txt
├── dockerfile
└── server.py
```
````

.. 列:

```
`server.py`代码看起来像这样：
```

.. 列:

````
```python
app = Sanic("MySanicApp")

@app.get('/')
async def hello(request):
    return text("OK!")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```
````

.. 注：

```
请注意主机不能为127.0.0.1 。在Docker容器中，127.0.0。 是容器的默认网络接口，只有容器可以与其他容器通信。 更多信息请访问[Docker network](https://docs.docker.com/engine/reference/commandline/network/)
```

代码已经准备好，让我们写入`Dockerfile`：

```Dockerfile

FROM sanicframework/sanic:3.8-最新

WORKDIR /sanic

COPY .

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python", "server.py"]
```

运行以下命令来构建图像：

```shell
停靠构建-t my-sanic-image
```

## 启动容器

.. 列:

```
在图像生成后，我们可以启动容器使用 "my-sanic-image" ：
```

.. 列:

````
```shell
docker run --name mysanic -p 8000:8000 -d my-sanic-image
```
````

.. 列:

```
现在我们可以访问 `http://localhost:8000` 来查看结果：
```

.. 列:

````
```text
OK!
```
````

## 使用 docker-compose

如果您的项目包含多项服务，您可以使用 [docker-compose](https://docs.docker.com/compose/) 来管理它们。

例如，我们将部署`my-sanic-image`和`nginx`，通过 nginx 访问智能服务器来实现。

.. 列:

```
首先，我们需要准备 nginx 配置文件，创建一个名为 `mysanic.conf` 的文件：
```

.. 列:

````
```nginx
server {
    listen 80;
    listen [::]:80;
    location / {
      proxy_pass http://mysanic:8000/;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection upgrade;
      proxy_set_header Accept-Encoding gzip;
    }
}
```
````

.. 列:

```
然后，我们需要准备`docker-compose.yml`文件。
```

.. 列:

````
```yaml
版本: "3"

services:
  mysanic:
    image: my-sanic-image
    ports:
      - "8000:8000"
    重启

  mynginx:
    image: nginx:1.13. -alpine
    端口：
      - "80:80"
    依赖于：
      - mysanic
    卷：
      - . 神秘。 onf/etc/nginx/conf.d/mysanic.conf
    重启：总是

networks:
  default:
    driver: bridge
```
````

.. 列:

```
然后，我们可以开始：
```

.. 列:

````
```shell
docker-compose up -d
```
````

.. 列:

```
现在，我们可以访问 `http://localhost:80` 查看结果：
```

.. 列:

````
```text
OK!
```
````
