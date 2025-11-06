#!/usr/bin/env python
# coding: utf-8

# # Flexible Demand with Solar and Storage (24-hour example)
#
# This notebook demonstrates a simple 24-hour optimization using pommes_craft with:
#  - One area and one resource: electricity.
#  - Solar generation (as a conversion technology with an availability profile).
#  - A battery storage system.
#  - Flexible demand that can shift within the day subject to conservation and bounds.
#
#  It sets up the model programmatically, runs the optimization, and visualizes the results.
#

# In[41]:


import numpy as np
import polars as pl
import pandas as pd

from pommes_craft import (
    EnergyModel,
    data_path,
    Area,
    Demand,
    EconomicHypothesis,
    ConversionTechnology,
    StorageTechnology,
    NetImport,
    TimeStepManager,
    FlexibleDemand,
    Spillage,
    LoadShedding
)


# ## 1. Define model horizon and basic sets
# We model 24 hours for year 2025.

# In[36]:

def test_flexible_demand_solar_storage():
    hours = list(range(24))
    year = 2025
    energy_model = EnergyModel(
        name="flex_demand_solar_storage",
        hours=hours,
        year_ops=[year],
        year_invs=[year],
        year_decs=[2050],
        modes=["base"],
        resources=["electricity"],
    )

    # ## 2. Build components: economics, time step, area
    #

    # In[37]:

    with energy_model.context():
        EconomicHypothesis("eco", discount_rate=0.0, year_ref=year, planning_step=25)
        TimeStepManager("ts", time_step_duration=1.0, operation_year_duration=24.0)
        area = Area("area1")

    # ## 3. Create a solar generator
    # We use ConversionTechnology with an availability profile (0 to 1).

    # In[38]:

    # Simple bell-shaped availability curve for solar
    avail = np.clip(np.sin((np.array(hours) - 6) * np.pi / 12), 0, 1)  # sunrise ~6h, sunset ~18h
    availability_df = pl.DataFrame({
        "hour": hours,
        "year_op": [year] * len(hours),
        "availability": avail.astype(float),
    })

    with energy_model.context():
        pv = ConversionTechnology(
            name="pv",
            factor={"electricity": 1.0},  # produces electricity
            availability=availability_df,
            must_run=1.,
            variable_cost=0.0,
            invest_cost=12.0,
            life_span=25.,
        )
        area.add_component(pv)

    # ## 4. Add a battery storage system
    # We set round-trip efficiency roughly 90% (0.95 in/out).
    # We allow up to 30 MW charge/discharge and 120 MWh energy capacity (investment bounds).
    #

    # In[39]:

    with energy_model.context():
        battery = StorageTechnology(
            name="battery",
            factor_in={"electricity": -1.},
            factor_out={"electricity": 0.9},  # 90% discharge efficiency
            factor_keep={"electricity": 0.},
            invest_cost_power=0.,
            invest_cost_energy=0.,
            life_span=10.,
        )
        area.add_component(battery)

    # ## 5. Define flexible and inflexible demand
    # We use the `project_load_curve` from the `demandforge` package to obtain a load curve for France with a long term projection of electric vehicle load and select one summer day. We define the flexible load as the electric vehicle load and the rest as the inflexible load.

    # In[48]:

    demand_projection = pd.read_parquet(data_path / "demand" / "demand_FR_2025.parquet")
    mask = demand_projection.index.dayofyear == 150
    inflex_cols = ["baseload_projected", "winter_thermosensitive_projected", "summer_thermosensitive_projected"]
    inflexible_demand = demand_projection.loc[mask, inflex_cols].sum(axis=1)
    flexible_demand = demand_projection.loc[mask, "ev_projected"]

    flexible_demand_pl = (
        pl.DataFrame(data=flexible_demand.values, schema=["demand"])
        .with_columns(
            hour=pl.Series(hours),
            year_op=year
        )
    )
    inflexible_demand_pl = (
        pl.DataFrame(data=inflexible_demand.values, schema=["demand"])
        .with_columns(
            hour=pl.Series(hours),
            year_op=year
        )
    )

    # In[49]:

    with energy_model.context():
        flex = FlexibleDemand(
            name="flexible_load",
            resource="electricity",
            demand=flexible_demand_pl,
            conservation_hrs=24,
            max_demand=flexible_demand_pl['demand'].max(),
            min_demand=0.,
            variable_cost=10.
        )
        area.add_component(flex)

        demand = Demand(
            name="inflexible_load",
            resource="electricity",
            demand=inflexible_demand_pl,
        )
        area.add_component(demand)

        spillage = Spillage(
            name="electricity_spillage",
            resource="electricity",
            max_capacity=1000.,
            cost=0.
        )
        area.add_component(spillage)

        load_shedding = LoadShedding(
            name="electricity_load_shedding",
            resource="electricity",
            max_capacity=0.,
            cost=0.
        )
        area.add_component(load_shedding)

    with energy_model.context():
        grid = NetImport(
            name="grid",
            resource="electricity",
            import_price=10000.,
            max_yearly_energy_export=0.
        )
        area.add_component(grid)

    energy_model.run()
    energy_model.set_all_results()
    print('Solved. Objective:', getattr(energy_model.linopy_model, 'objective', None))

    for comp in energy_model.components:
        if hasattr(comp, 'results') and comp.results:
            print(f'Component: {comp.name} ({comp.__class__.__name__})')
            for k in comp.results.keys():
                print('  -', k, list(comp.results[k].keys()))

    pv_power = energy_model.get_results('operation', 'power', component_classes=[ConversionTechnology])
    bat_in = energy_model.get_results('operation', 'power_in', component_classes=[StorageTechnology])
    bat_out = energy_model.get_results('operation', 'power_out', component_classes=[StorageTechnology])
    grid_power = energy_model.get_results('operation', 'import', component_classes=[NetImport])
    flex_df = energy_model.get_results('operation', 'demand', component_classes=[FlexibleDemand])
