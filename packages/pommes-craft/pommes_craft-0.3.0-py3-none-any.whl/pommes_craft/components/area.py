from pommes_craft.core.component import Component
import logging

# Set up a logger for this module
logger = logging.getLogger(__name__)


class Area(Component):
    """Geographical area in the energy system."""
    area_indexed = False
    link_indexed = False
    prefix = ""
    own_index = "area"

    def __init__(self, name: str):
        """Initialize an area component.

        Args:
            name: Name of the geographical area
        """
        super().__init__(name)
        self.components = {}

    def add_component(self, component: Component):
        """
        Add a component to this area.

        Args:
            component: Component object to add to this area.

        Raises:
            ValueError: If a component with the same name already exists in this area.
        """
        if component.name in self.components:
            raise ValueError(
                f"Component name '{component.name}' already exists in area '{self.name}'"
            )

        self.components[component.name] = component

    def _reassociate_components(self):
        """Re-associates components with this area after loading."""
        for comp_name, comp in self.components.items():
            if isinstance(comp, str):  # If it's just a name after loading
                # Find the actual component in the model
                found = False
                for c in self.model.components:
                    if c.name == comp:
                        self.components[comp_name] = c
                        found = True
                        break
                if not found:
                    logger.warning(f"Could not re-associate component '{comp}' with area '{self.name}'")
