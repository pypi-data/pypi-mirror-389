import pytest
from pathlib import Path
import polars as pl
import shutil
from polars.testing import assert_frame_equal

from pommes_craft.core.model import EnergyModel
from pommes_craft.components.area import Area
from pommes_craft.components.demand import Demand
from pommes_craft.components.link import Link
from pommes_craft.components.transport_technology import TransportTechnology
from pommes_craft.components.conversion_technology import ConversionTechnology


@pytest.fixture
def simple_model():
    """Fixture for a simple EnergyModel with no components."""
    return EnergyModel(
        name="test_simple_model",
        hours=list(range(3)),
        year_ops=[2030, 2040],
        resources=['electricity']
    )


@pytest.fixture
def model_with_data():
    """Fixture for an EnergyModel with components and a DataFrame."""
    model = EnergyModel(
        name="test_data_model",
        hours=list(range(2)),
        year_ops=[2030],
        resources=['electricity']
    )
    with model.context():
        area = Area(name="Area1")
        demand_data = pl.DataFrame({
            "hour": [0, 1, 0, 1],
            "year_op": [2030, 2030, 2030, 2030],
            "demand": [100.5, 101.5, 102.5, 103.5],
        })
        demand = Demand(name="ElectricityDemand", demand=demand_data, resource="electricity")
        area.add_component(demand)
    return model


def test_save_and_load_simple_model(simple_model, tmp_path: Path):
    """Test saving and loading a simple model without components."""
    save_path = tmp_path / "simple_model_save"

    # 1. Save the model
    simple_model.save(save_path)

    # 2. Assert that files were created
    assert (save_path / "model.yaml").exists()
    assert (save_path / "data").is_dir()

    # 3. Load the model
    loaded_model = EnergyModel.load(save_path)

    # 4. Assertions
    assert loaded_model.name == simple_model.name
    assert loaded_model.hours == simple_model.hours
    assert loaded_model.year_ops == simple_model.year_ops
    assert loaded_model.resources == simple_model.resources
    assert len(loaded_model.components) == 0
    assert loaded_model.folder == save_path


def test_save_and_load_model_with_data(model_with_data, tmp_path: Path):
    """Test saving and loading a model with components and DataFrame attributes."""
    save_path = tmp_path / "data_model_save"

    # 1. Save the model
    model_with_data.save(save_path)

    # 2. Assert that files were created
    assert (save_path / "model.yaml").exists()
    data_dir = save_path / "data"
    assert data_dir.is_dir()
    # Check for the parquet file of the demand component's 'value' attribute
    assert len(list(data_dir.glob("*.parquet"))) == 1

    # 3. Load the model
    loaded_model = EnergyModel.load(save_path)

    # 4. Assertions for the model
    assert loaded_model.name == model_with_data.name
    assert len(loaded_model.components) == len(model_with_data.components)

    # 5. Get original and loaded components for comparison
    original_area = next(c for c in model_with_data.components if isinstance(c, Area))
    original_demand = next(c for c in model_with_data.components if isinstance(c, Demand))

    loaded_area = next(c for c in loaded_model.components if isinstance(c, Area))
    loaded_demand = next(c for c in loaded_model.components if isinstance(c, Demand))

    # 6. Assert component attributes
    assert loaded_area.name == original_area.name
    assert loaded_demand.name == original_demand.name

    # 7. Assert DataFrame equality
    assert_frame_equal(loaded_demand.demand, original_demand.demand)

    # 8. Assert re-association of components
    assert len(loaded_area.components) == 1
    assert loaded_area.components['ElectricityDemand'] == loaded_demand


def test_save_and_load_retains_relative_paths(model_with_data, tmp_path: Path):
    """
    Test that moving the saved folder doesn't break loading,
    proving that paths are relative.
    """
    original_save_path = tmp_path / "original_location"
    new_save_path = tmp_path / "new_location"

    model_with_data.save(original_save_path)

    # 2. Move the entire folder to a new location
    shutil.move(str(original_save_path), str(new_save_path))

    # 3. Load the model from the new path
    # This should work if paths inside model.yaml are relative
    try:
        loaded_model = EnergyModel.load(new_save_path)
    except FileNotFoundError as e:
        pytest.fail(f"Loading from moved directory failed. Paths are likely not relative. Error: {e}")

    # 4. Assert that the model loaded correctly
    assert loaded_model.name == model_with_data.name
    assert len(loaded_model.components) == 2
    loaded_demand = next(c for c in loaded_model.components if isinstance(c, Demand))
    original_demand = next(c for c in model_with_data.components if isinstance(c, Demand))
    assert_frame_equal(loaded_demand.demand, original_demand.demand)


def test_save_and_load_with_links_and_technologies(tmp_path: Path):
    """Test saving and loading a model with links and associated technologies."""
    # 1. Create a model with a more complex structure
    model = EnergyModel(
        name="test_link_model",
        hours=list(range(2)),
        year_ops=[2030],
        resources=['electricity', 'hydrogen']
    )
    with model.context():
        area1 = Area(name="Area1")
        area2 = Area(name="Area2")
        link = Link(name="L1", area_from=area1, area_to=area2)
        tech = ConversionTechnology(name="Electrolyzer",
                                    factor={"electricity": -1.0, "hydrogen": 0.7},
                                    invest_cost=500, life_span=20
                                    )
        area1.add_component(tech)
        transport_technology = TransportTechnology(name="ElectricLine", resource="electricity", invest_cost=10.)
        link.add_transport_technology(transport_technology)

    save_path = tmp_path / "link_model_save"
    model.save(save_path)

    # 2. Load the model
    loaded_model = EnergyModel.load(save_path)

    # 3. Assertions
    assert len(loaded_model.components) == 5
    loaded_link = next(c for c in loaded_model.components if isinstance(c, Link))
    loaded_transport_tech = next(c for c in loaded_model.components if isinstance(c, TransportTechnology))
    loaded_tech = next(c for c in loaded_model.components if isinstance(c, ConversionTechnology))

    assert loaded_link.name == "L1"
    assert loaded_tech.name == "Electrolyzer"
    assert loaded_link.technologies['ElectricLine'] == loaded_transport_tech
    assert loaded_transport_tech.link.name == "L1"


def test_copy_simple_model(simple_model):
    """Test copying a simple model without components."""
    # 1. Copy the model
    copied_model = simple_model.copy(new_name="copied_simple_model")

    # 2. Assert basic properties
    assert copied_model is not simple_model
    assert copied_model.name == "copied_simple_model"
    assert copied_model.hours == simple_model.hours
    assert copied_model.year_ops == simple_model.year_ops
    assert len(copied_model.components) == 0

    # 3. Assert that modifying the copy does not affect the original
    copied_model.hours.append(99)
    assert copied_model.hours != simple_model.hours
    assert 99 not in simple_model.hours


def test_copy_model_with_data(model_with_data):
    """Test copying a model with components and data."""
    # 1. Copy the model
    copied_model = model_with_data.copy()

    # 2. Assert model properties
    assert copied_model.name == f"{model_with_data.name}_copy"
    assert len(copied_model.components) == len(model_with_data.components)
    assert copied_model.components is not model_with_data.components

    # 3. Get original and copied components
    original_area = next(c for c in model_with_data.components if isinstance(c, Area))
    original_demand = next(c for c in model_with_data.components if isinstance(c, Demand))

    copied_area = next(c for c in copied_model.components if isinstance(c, Area))
    copied_demand = next(c for c in copied_model.components if isinstance(c, Demand))

    # 4. Assert components are new instances and belong to the new model
    assert copied_area is not original_area
    assert copied_demand is not original_demand
    assert copied_area.model is copied_model
    assert copied_demand.model is copied_model

    # 5. Assert component data is copied correctly
    assert copied_area.name == original_area.name
    assert_frame_equal(copied_demand.demand, original_demand.demand)

    # 6. Assert that component relationships are preserved in the new model
    assert len(copied_area.components) == 1
    assert copied_area.components['ElectricityDemand'] is copied_demand


def test_copy_is_deep(model_with_data):
    """Test that the copy is a deep copy and modifications are isolated."""
    # 1. Copy the model
    copied_model = model_with_data.copy()

    # 2. Get a component from the copied model
    copied_demand = next(c for c in copied_model.components if isinstance(c, Demand))
    original_demand = next(c for c in model_with_data.components if isinstance(c, Demand))

    # 3. Modify a DataFrame in the copied component
    modified_df = copied_demand.demand.with_columns(
        pl.col("demand") * 2
    )
    copied_demand.demand = modified_df

    # 4. Assert that the original component's DataFrame is unchanged
    assert not copied_demand.demand.equals(original_demand.demand)
    assert_frame_equal(original_demand.demand, pl.DataFrame({
        "hour": [0, 1, 0, 1],
        "year_op": [2030, 2030, 2030, 2030],
        "demand": [100.5, 101.5, 102.5, 103.5],
        "resource": ["electricity"] * 4,
    }))

    # 5. Add a new component to the copied model and check counts
    with copied_model.context():
        new_area = Area(name="Area2")
    assert len(copied_model.components) == 3
    assert len(model_with_data.components) == 2
