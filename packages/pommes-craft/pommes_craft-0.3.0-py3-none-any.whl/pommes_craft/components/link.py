from pommes_craft.core.component import Component
from pommes_craft.components.area import Area
from pommes_craft.components.transport_technology import TransportTechnology
import logging

# Set up a logger for this module
logger = logging.getLogger(__name__)

class Link(Component):
    """Connection between areas using a transport technology."""
    area_indexed = False
    link_indexed = False
    resource_indexed = True
    prefix = ""
    own_index = "link"

    def __init__(
        self,
        name: str,
        area_from: Area,
        area_to: Area,
    ):
        """Initialize a link component.

        Args:
            name: Name of the link
            area_from: Source area for the link
            area_to: Destination area for the link
        """
        super().__init__(name)
        self.area_from = area_from
        self.area_to = area_to
        self.technologies = {}


    def add_transport_technology(self, transport_technology: TransportTechnology):
        """
        Add transport technology to a link.

        Args:
            transport_technology: TransportTechnology object containing resource and other transport parameters.

        Raises:
            ValueError: If a transport technology with the same name already exists in this link.
        """
        if transport_technology.name in self.technologies:
            raise ValueError(
                f"TransportTechnology named '{transport_technology.name}' already exists in link '{self.name}'"
            )

        self.technologies[transport_technology.name] = transport_technology
        transport_technology.register_link(self)

    def _reassociate_technologies(self):
        """Re-associates technologies with this link after loading."""
        for tech_name, tech in self.technologies.items():
            if isinstance(tech, str):  # If it's just a name after loading
                # Find the actual component in the model
                found = False
                for c in self.model.components:
                    if c.name == tech:
                        self.technologies[tech_name] = c
                        found = True
                        break
                if not found:
                    logger.warning(f"Could not re-associate technology '{tech}' with link '{self.name}'")
