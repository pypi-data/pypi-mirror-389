"""UI tool service for handling UI updates during measurements."""

import threading
from abc import ABC, abstractmethod

from bokeh.application import Application
from bokeh.server.server import Server

from quantify.visualization.plotmon.caching.in_memory_cache import InMemoryCache
from quantify.visualization.plotmon.plotmon_app import PlotmonApp
from quantify.visualization.plotmon.plotmon_server import process_message
from quantify.visualization.plotmon.utils.communication import Message


class UITool(ABC):
    """Abstract base class for UI tools."""

    _name: str | None = None

    def init(self, name: str) -> None:
        """Initialize the data source name."""
        self._name = name

    @abstractmethod
    def callback(self, msg: Message) -> None:
        """Callback function to publish messages to Plotmon."""


class QuantifyUI(UITool):
    """Quantify UI tool for handling Plotmon updates during measurements."""

    def __init__(self) -> None:
        """Initializes the QuantifyUI tool with an in-memory cache."""
        self._plotmon_cache = InMemoryCache()
        self._plotmon_app = None

    def callback(self, msg: Message) -> None:
        """
        Callback function to process incoming messages and update the Plotmon app.

        Args:
            msg: Message object containing the event to process.

        """
        if not self._plotmon_app:
            self._plotmon_app = self._create_plotmon_app()
        process_message(msg, self._plotmon_app, self._plotmon_cache)

    def init(self, name: str) -> None:
        """
        Initialize the UI tool with a name and create the Plotmon application.

        Args:
            name: str Name of the data source.

        """
        super().init(name)
        self._plotmon_app = self._create_plotmon_app()

    def _create_plotmon_app(self) -> PlotmonApp:
        if not self._name:
            raise ValueError(
                "UITool not initialized with a name. Use tool.init(name) first."
            )
        plotmon_app = PlotmonApp(
            cache=self._plotmon_cache,
            data_source_name=self._name,
        )

        application = Application(plotmon_app)
        # Port 0 will pick a free port
        self.server = Server(
            {"/": application},
            port=0,
            address="localhost",
            show=True,
            allow_websocket_origin=["*"],
        )

        # start server in a separate thread
        def _start() -> None:
            self.server.start()

        self.process = threading.Thread(target=_start)
        self.process.start()

        print(
            f"Plotmon server started at http://{self.server.address}:{self.server.port}"
        )

        return plotmon_app

    def get_server_address(self) -> str:
        """Get the address of the Plotmon server.

        Returns:
            str: The address of the Plotmon server in the format 'address:port'.

        """
        if not self.server:
            raise ValueError("Server not started yet.")
        return f"http://{self.server.address}:{self.server.port}"
