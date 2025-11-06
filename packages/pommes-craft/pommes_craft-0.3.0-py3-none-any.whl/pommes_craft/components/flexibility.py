from typing import Dict, Optional, Union

import numpy as np
import polars as pl

from pommes_craft.core.component import Component


class FlexibleDemand(Component):
    """Component representing net import/export of resources to/from the system."""
    area_indexed = True
    link_indexed = False
    resource_indexed = True
    prefix = "flexibility_"
    own_index = None

    attr_index_dict = {
        "demand": ["hour", "year_op"],
        "conservation_hrs": ["year_op"],
        "ramp_up": ["year_op"],
        "ramp_down": ["year_op"],
        "max_demand": ["hour", "year_op"],
        "min_demand": ["hour", "year_op"],
        "variable_cost": ["hour", "year_op"],
    }
    # Class-level type annotations for all attributes that will be set dynamically
    demand: pl.DataFrame
    conservation_hrs: pl.DataFrame
    ramp_up: pl.DataFrame
    ramp_down: pl.DataFrame
    max_demand: pl.DataFrame
    min_demand: pl.DataFrame
    variable_cost: pl.DataFrame

    def __init__(
            self,
            name: str,
            resource: str,
            demand: Optional[Union[float, Dict[int, float], Dict[int, Dict[int, float]], pl.DataFrame]] = 0.,
            conservation_hrs: Optional[Union[int, Dict[int, int], pl.DataFrame]] = 0,
            ramp_up: Optional[Union[float, Dict[int, float], pl.DataFrame]] = np.nan,
            ramp_down: Optional[Union[float, Dict[int, float], pl.DataFrame]] = np.nan,
            max_demand: Optional[Union[float, Dict[int, float], Dict[int, Dict[int, float]], pl.DataFrame]] = 1.,
            min_demand: Optional[Union[float, Dict[int, float], Dict[int, Dict[int, float]], pl.DataFrame]] = 1.,
            variable_cost: Optional[Union[float, Dict[int, float], Dict[int, Dict[int, float]], pl.DataFrame]] = 0.,
    ):
        """Initialize a net import component.

        Args:
            name: Name of the net import component
            resource: Resource with flexible demand
            demand: Default demand
            conservation_hrs: Number of hours during which the total demand is conserved
            ramp_up: Maximum ramp up rate
            ramp_down: Maximum ramp down rate
            max_demand: Max demand after flexibility used
            min_demand: Min demand after flexibility used
            variable_cost: Cost incurred for shifting the demand
        """
        super().__init__(name)
        self.resource = resource

        # Get all parameters from locals() without 'self' and 'name'
        params = {
            k: v
            for k, v in locals().items()
            if k not in ("self", "name") and k in self.attr_index_dict
        }
        # Process each attribute using the generic method
        for attr_name, attr_value in params.items():
            other_columns = self.attr_index_dict.get(attr_name, [])
            attr_df = self.process_attribute_input(attr_name, attr_value, other_columns)
            # add the resource column
            attr_df = attr_df.with_columns(resource=pl.lit(self.resource))
            setattr(
                self,
                attr_name,
                attr_df,
            )
