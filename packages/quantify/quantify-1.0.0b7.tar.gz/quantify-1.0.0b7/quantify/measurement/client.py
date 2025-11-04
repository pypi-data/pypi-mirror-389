"""Measurement client module for handling experiment communication and data updates."""

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from quantify.measurement.services.experiments import (
    start_experiment,
    stop_experiment,
    update_experiment,
)
from quantify.measurement.services.plot_config import (
    get_config_from_dataset,
)
from quantify.measurement.services.ui_tool import QuantifyUI, UITool
from quantify.visualization.plotmon.utils.communication import (
    Message,
)

if TYPE_CHECKING:
    from quantify.measurement.control import MeasurementControl


class MeasurementClient:
    """Measurement client for handling experiment communication and data updates."""

    def __init__(
        self, mc: "MeasurementControl", ui_tool: UITool = QuantifyUI()
    ) -> None:
        """Initialize the measurement client.

        Args:
            mc: The measurement control instance.
            ui_tool: The UI tool instance to use for communication.
            Can initialize and sends it to the server.

        """
        self.mc = mc
        self._last_experiment_name: str | None = None
        self._ui_tool = ui_tool
        self._ui_tool.init(mc._short_name)

        # Keep reference to original methods
        self._mc_init = mc._init
        self._mc_finish = mc._finish
        self._mc_update = mc._update

    def _init(self, name: str) -> None:
        self._mc_init(name)
        if self.mc._dataset is None:
            logging.warning(
                "Failed to initialize experiment '%s': Dataset not found.", name
            )
            return

        if self._last_experiment_name != name:
            # Reconfigure graphs on new experiment
            graph_config_message = Message(
                event=get_config_from_dataset(self.mc._dataset, self.mc.name),
                timestamp=datetime.now().isoformat(),
            )
            self._send_message(graph_config_message)
            self._last_experiment_name = name

        message = Message(
            event=start_experiment(self.mc._dataset, self.mc.name),
            timestamp=datetime.now().isoformat(),
        )
        self._send_message(message)

    def _finish(self) -> None:
        self._mc_finish()
        if self.mc._dataset is None:
            logging.warning(
                "Failed to end experiment '%s': Dataset not found.",
                self._last_experiment_name,
            )
            return
        message = Message(
            event=stop_experiment(self.mc._dataset, self.mc.name),
            timestamp=datetime.now().isoformat(),
        )

        self._send_message(message)

    def _send_message(self, message: Message) -> None:
        """Send a message to the plot monitoring server."""
        self._ui_tool.callback(message)

    def _update(self, print_message: str | None = None) -> None:
        """Call the parent class update method, send a message with recent data."""
        self._mc_update(print_message)
        if self.mc._dataset is not None:
            updates = update_experiment(
                self.mc._dataset,
                self.mc.name,
                self.mc._nr_acquired_values,
                int(self.mc._batch_size_last) if self.mc._batch_size_last else 1,
            )
            for update in updates:
                message = Message(
                    event=update,
                    timestamp=datetime.now().isoformat(),
                )
                self._send_message(message)
