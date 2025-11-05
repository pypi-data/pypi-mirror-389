import asyncio
from http import HTTPStatus

from asgikit.requests import Request
from tests.utils.asgi import HttpSendInspector


async def test_respond_plain_text():
    inspector = HttpSendInspector()
    scope = {"type": "http", "headers": []}
    request = Request(scope, None, inspector)

    await request.respond_text("Hello, World!")

    assert inspector.body == "Hello, World!"


async def test_stream():
    async def stream_data():
        yield "Hello, "
        yield "World!"

    inspector = HttpSendInspector()
    scope = {"type": "http", "http_version": "1.1", "headers": []}
    request = Request(scope, None, inspector)
    await request.respond_stream(stream_data())

    assert inspector.body == "Hello, World!"


async def test_stream_context_manager():
    inspector = HttpSendInspector()
    scope = {"type": "http", "http_version": "1.1", "headers": []}
    request = Request(scope, None, inspector)

    async with request.response_writer() as write:
        await write("Hello, ")
        await write("World!")

    assert inspector.body == "Hello, World!"


async def test_respond_file(tmp_path):
    tmp_file = tmp_path / "tmp_file.txt"
    tmp_file.write_text("Hello, World!")

    inspector = HttpSendInspector()
    scope = {"type": "http", "http_version": "1.1", "headers": []}

    async def sleep_receive():
        while True:
            await asyncio.sleep(1000)

    request = Request(scope, sleep_receive, inspector)
    await request.respond_file(tmp_file)

    assert inspector.body == "Hello, World!"


async def test_respond_status():
    inspector = HttpSendInspector()
    scope = {"type": "http", "headers": []}
    request = Request(scope, None, inspector)
    await request.respond_status(HTTPStatus.IM_A_TEAPOT)

    assert inspector.status == HTTPStatus.IM_A_TEAPOT
    assert inspector.body == ""


async def test_respond_empty():
    inspector = HttpSendInspector()
    scope = {"type": "http", "headers": []}
    request = Request(scope, None, inspector)

    await request.respond_status(HTTPStatus.OK)
    assert inspector.status == HTTPStatus.OK
    assert inspector.body == ""


async def test_respond_temporary_redirect():
    inspector = HttpSendInspector()
    scope = {"type": "http", "headers": []}
    request = Request(scope, None, inspector)
    await request.respond_redirect("/redirect")

    assert inspector.status == HTTPStatus.TEMPORARY_REDIRECT
    assert (b"location", b"/redirect") in inspector.headers


async def test_respond_permanent_redirect():
    inspector = HttpSendInspector()
    scope = {"type": "http", "headers": []}
    request = Request(scope, None, inspector)
    await request.respond_redirect("/redirect", permanent=True)

    assert inspector.status == HTTPStatus.PERMANENT_REDIRECT
    assert (b"location", b"/redirect") in inspector.headers


async def test_respond_post_get_redirect():
    inspector = HttpSendInspector()
    scope = {"type": "http", "headers": []}
    request = Request(scope, None, inspector)
    await request.respond_redirect_post_get("/redirect")

    assert inspector.status == HTTPStatus.SEE_OTHER
    assert (b"location", b"/redirect") in inspector.headers


async def test_respond_set_header():
    inspector = HttpSendInspector()
    scope = {"type": "http", "headers": []}
    request = Request(scope, None, inspector)
    request.response.headers.set("name", "value")
    await request.respond_status(HTTPStatus.OK)

    assert inspector.status == HTTPStatus.OK
    assert (b"name", b"value") in inspector.headers


async def test_respond_add_header():
    inspector = HttpSendInspector()
    scope = {"type": "http", "headers": []}
    request = Request(scope, None, inspector)
    request.response.headers.add("name", "value1")
    request.response.headers.add("name", "value2")
    await request.respond_status(HTTPStatus.OK)

    assert inspector.status == HTTPStatus.OK
    assert (b"name", b"value1, value2") in inspector.headers


async def test_respond_set_cookie():
    inspector = HttpSendInspector()
    scope = {"type": "http", "headers": []}
    request = Request(scope, None, inspector)
    request.response.cookies.set("name", "value")
    await request.respond_status(HTTPStatus.OK)

    assert inspector.status == HTTPStatus.OK
    assert (b"Set-Cookie", b"name=value; HttpOnly; SameSite=lax") in inspector.headers