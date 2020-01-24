import io

from sanic.response import text


data = "abc" * 10_000_000


def test_request_buffer_queue_size(app):
    default_buf_qsz = app.config.get("REQUEST_BUFFER_QUEUE_SIZE")
    qsz = 1
    while qsz == default_buf_qsz:
        qsz += 1
    app.config.REQUEST_BUFFER_QUEUE_SIZE = qsz

    @app.post("/post", stream=True)
    async def post(request):
        assert request.stream.buffer_size == qsz
        print("request.stream.buffer_size =", request.stream.buffer_size)

        bio = io.BytesIO()
        while True:
            bdata = await request.stream.read()
            if not bdata:
                break
            bio.write(bdata)

            head = bdata[:3].decode("utf-8")
            tail = bdata[3:][-3:].decode("utf-8")
            print(head, "...", tail)

        bio.seek(0)
        return text(bio.read().decode("utf-8"))

    request, response = app.test_client.post("/post", data=data)
    assert response.status == 200
    assert response.text == data
