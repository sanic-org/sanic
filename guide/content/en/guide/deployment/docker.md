# Docker Deployment

## Introduction

For a long time, the environment has always been a difficult problem for deployment. If there are conflicting configurations in your project, you have to spend a lot of time resolving them. Fortunately, virtualization provides us with a good solution. Docker is one of them. If you don't know Docker, you can visit [Docker official website](https://www.docker.com/) to learn more.

## Build Image

Let's start with a simple project. We will use a Sanic project as an example. Assume the project path is `/path/to/SanicDocker`.

.. column::

    The directory structure looks like this:

.. column::

    ```text
    # /path/to/SanicDocker
    SanicDocker
    ├── requirements.txt
    ├── dockerfile
    └── server.py
    ```


.. column::

    And the `server.py` code looks like this:

.. column::

    ```python
    app = Sanic("MySanicApp")

    @app.get('/')
    async def hello(request):
        return text("OK!")

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=8000)
    ```



.. note:: 

    Please note that the host cannot be 127.0.0.1 . In docker container, 127.0.0.1 is the default network interface of the container, only the container can communicate with other containers. more information please visit [Docker network](https://docs.docker.com/engine/reference/commandline/network/)



Code is ready, let's write the `Dockerfile`:

```Dockerfile

FROM sanicframework/sanic:3.8-latest

WORKDIR /sanic

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python", "server.py"]
```

Run the following command to build the image:

```shell
docker build -t my-sanic-image .
```

## Start Container

.. column::

    After the image built, we can start the container use `my-sanic-image`:

.. column::

    ```shell
    docker run --name mysanic -p 8000:8000 -d my-sanic-image
    ```


.. column::

    Now we can visit `http://localhost:8000` to see the result:

.. column::

    ```text
    OK!
    ```

## Use docker-compose

If your project consist of multiple services, you can use [docker-compose](https://docs.docker.com/compose/) to manage them.

for example, we will deploy `my-sanic-image` and `nginx`, achieve through nginx access sanic server.

.. column::

    First of all, we need prepare nginx configuration file. create a file named `mysanic.conf`:

.. column::

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


.. column::

    Then, we need to prepare `docker-compose.yml` file. The content follows:

.. column::

    ```yaml
    version: "3"

    services:
      mysanic:
        image: my-sanic-image
        ports:
          - "8000:8000"
        restart: always

      mynginx:
        image: nginx:1.13.6-alpine
        ports:
          - "80:80"
        depends_on:
          - mysanic
        volumes:
          - ./mysanic.conf:/etc/nginx/conf.d/mysanic.conf
        restart: always

    networks:
      default:
        driver: bridge
    ```


.. column::

    After that, we can start them:

.. column::

    ```shell
    docker-compose up -d
    ```


.. column::

    Now, we can visit `http://localhost:80` to see the result:

.. column::

    ```text
    OK!
    ```

