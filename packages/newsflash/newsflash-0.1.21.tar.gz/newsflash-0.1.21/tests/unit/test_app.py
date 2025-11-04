import unittest
from typing import Type

from django.http import HttpRequest
from pydantic import BaseModel

from newsflash import App, Page
from newsflash.widgets.base import Widget


class DummyContext(BaseModel):
    key: str = "value"


class DummyWidget(Widget):

    def _build(self, request: HttpRequest) -> DummyContext:
        return DummyContext()


class TestApp(unittest.TestCase):

    def setUp(self) -> None:
        widgets: list[Type[Widget]] = [DummyWidget]

        self.page = Page(
            path="/path/to/page",
            name="test-page",
            layout="test_layout.html",
            widgets=widgets,
        )
    
    def test_init_app(self):
        app = App(pages=[self.page])
