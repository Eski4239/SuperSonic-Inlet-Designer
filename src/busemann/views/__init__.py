"""Application views; they talk to AppState only, never to the core."""
from .design_panel import DesignPanel
from .flight_panel import FlightPanel
from .results_panel import ResultsPanel

__all__ = ["DesignPanel", "FlightPanel", "ResultsPanel"]
