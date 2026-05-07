from application_sdk.contracts.base import Input, Output


class HelloInput(Input):
    name: str = "World"


class HelloOutput(Output):
    message: str = ""
