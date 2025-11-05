from lifesimmc.core.base_module import BaseModule
from lifesimmc.core.context import Context


class CovarianceCalculationModule(BaseModule):
    """Class representation of the base module."""

    def __init__(self, name: str, config_from: str):
        """Constructor method."""
        self.name = name
        self.config_from = config_from

    def apply(self, context: Context) -> Context:
        """Apply the module.

        :param context: The context object of the pipelines
        :return: The (updated) context object
        """
        pass
