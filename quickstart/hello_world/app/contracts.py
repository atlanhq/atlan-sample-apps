from application_sdk.app import Input, Output

from app.generated._input import AppInputContract

# Top-level workflow input — generated from contract/app.pkl via `make generate`.
# Never edit app/generated/_input.py directly.
HelloWorldInput = AppInputContract


class HelloInput(Input):
    """Task-level input for the say_hello task."""

    name: str = "World"


class HelloOutput(Output):
    """Output from the HelloWorldApp."""

    message: str = ""
