import pytest
from app.connector import HelloWorldApp
from app.contracts import HelloInput, HelloOutput


class TestHelloWorldApp:
    @pytest.fixture()
    def app(self) -> HelloWorldApp:
        return HelloWorldApp()

    @pytest.mark.asyncio
    async def test_say_hello_returns_greeting(self, app: HelloWorldApp):
        result = await app.say_hello(HelloInput(name="John Doe"))
        assert isinstance(result, HelloOutput)
        assert result.message == "Hello, John Doe!"

    @pytest.mark.asyncio
    async def test_say_hello_default_name(self, app: HelloWorldApp):
        result = await app.say_hello(HelloInput())
        assert result.message == "Hello, World!"
