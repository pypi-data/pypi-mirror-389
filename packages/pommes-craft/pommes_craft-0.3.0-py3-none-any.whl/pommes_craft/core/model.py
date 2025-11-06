# pommes_craft/core/model.py
import logging
import copy
import shutil
import yaml
import numpy as np
import polars as pl
from pathlib import Path
import importlib
from typing import Dict, Optional, Type, Any, Sequence, List
from pommes_craft import studies_path
from pommes_craft.components.area import Area
from pommes_craft.components.link import Link
from pommes_craft.core.component import Component
from pommes_craft.core.model_context import ModelContext
from pommes.model.data_validation.dataset_check import check_inputs
from pommes.io.build_input_dataset import (
    build_input_parameters,
    read_config_file,
)
from pommes.model.build_model import build_model

# Set up a logger for this module
logger = logging.getLogger(__name__)


def _import_class_from_string(class_path: str) -> Type[Component]:
    """Dynamically import a class from a string path."""
    try:
        module_path, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError, ValueError) as e:
        logger.error(f"Failed to import class from path '{class_path}': {e}")
        raise


def _get_class_path(obj: Any) -> str:
    """Get the full import path for an object's class."""
    return f"{obj.__class__.__module__}.{obj.__class__.__name__}"


def _sanitize_for_yaml(value: Any) -> Any:
    """Recursively replace Component instances with their names in lists and dicts."""
    if isinstance(value, dict):
        return {k: _sanitize_for_yaml(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_yaml(v) for v in value]
    if isinstance(value, Component):
        return value.name
    return value


def _to_native_python_types(value: Any) -> Any:
    """Recursively convert numpy types to native Python types for YAML serialization."""
    if isinstance(value, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64,
                          np.uint8, np.uint16, np.uint32, np.uint64)):
        return int(value)
    if isinstance(value, (np.float16, np.float32, np.float64)):
        return float(value)
    if isinstance(value, np.ndarray):
        return _to_native_python_types(value.tolist())
    if isinstance(value, list):
        return [_to_native_python_types(item) for item in value]
    if isinstance(value, dict):
        return {k: _to_native_python_types(v) for k, v in value.items()}
    return value


class EnergyModel:
    """Main class for creating and solving POMMES energy system models."""


    def __init__(self,
                 name: str = "energy_model",
                 folder: Optional[Path] = None,
                 hours: Optional[Sequence[int]] = None,
                 year_ops: Optional[Sequence[int]] = None,
                 year_invs: Optional[Sequence[int]] = None,
                 year_decs: Optional[Sequence[int]] = None,
                 modes: Optional[Sequence[str]] = None,
                 resources: Optional[Sequence[str]] = None,
                 hour_types: Optional[Sequence[str]] = None,
                 add_modules: Optional[Dict[str, bool]] = None,
                 pre_process: Optional[Dict[str, Any]] = None,
                 solver_name: Optional[str] = "highs",
                 solver_options: Optional[Dict[str, str]] = None,
):
        """Initialize a new energy system model with all key attributes.

        Args:
            name: Name of the model
            hours: Operational hours for the model
            year_ops: Operational years for the model
            year_invs: Investment years for the model
            year_decs: Decommissioning years for the model
            modes: Operational modes for the model
            resources: Resource types available in the model
            add_modules: Optional dictionary to enable/disable specific modules
            pre_process: Optional dictionary containing preprocessing configurations

        """
        self.name = name
        logger.info(f"Creating new EnergyModel: '{name}' with {len(hours) if hours else 0} hours, "
                    f"{len(year_ops) if year_ops else 0} operational years, "
                    f"{len(year_invs) if year_invs else 0} investment years, "
                    f"{len(resources) if resources else 0} resources")


        if folder is None:
            self.folder = studies_path / self.name
        else:
            self.folder = folder
        self.folder.mkdir(parents=True, exist_ok=True)
        self.solver_name = solver_name
        if solver_options is None:
            self.solver_options = {}
        else:
            self.solver_options = solver_options

        # Initialize core attributes with provided values or empty lists
        self.hours = list(hours) if hours is not None else []
        self.year_ops = list(year_ops) if year_ops is not None else []
        self.year_invs = list(year_invs) if year_invs is not None else []
        self.year_decs = list(year_decs) if year_decs is not None else []
        self.modes = list(modes) if modes is not None else []
        self.resources = list(resources) if resources is not None else []
        self.hour_types = list(hour_types) if hour_types is not None else []

        # add_modules will be set when generating the POMMES model
        self.add_modules = {}
        if add_modules is not None:
            # Update the default dict with provided values
            self.add_modules.update(add_modules)

        # Default pre_process configuration
        default_pre_process = {
            'annuity_computation': {
                'combined': {
                    'combined_annuity_cost': {
                        'invest_cost': 'combined_invest_cost',
                        'finance_rate': 'combined_finance_rate',
                        'life_span': 'combined_life_span'
                    }
                },
                'conversion': {
                    'conversion_annuity_cost': {
                        'invest_cost': 'conversion_invest_cost',
                        'finance_rate': 'conversion_finance_rate',
                        'life_span': 'conversion_life_span'
                    }
                },
                'transport': {
                    'transport_annuity_cost': {
                        'invest_cost': 'transport_invest_cost',
                        'finance_rate': 'transport_finance_rate',
                        'life_span': 'transport_life_span'
                    }
                },
                'storage': {
                    'storage_annuity_cost_power': {
                        'invest_cost': 'storage_invest_cost_power',
                        'finance_rate': 'storage_finance_rate',
                        'life_span': 'storage_life_span'
                    },
                    'storage_annuity_cost_energy': {
                        'invest_cost': 'storage_invest_cost_energy',
                        'finance_rate': 'storage_finance_rate',
                        'life_span': 'storage_life_span'
                    }
                }
            },
            'discount_factor': {
                'discount_rate': 'discount_rate',
                'year_ref': 'year_ref'
            }
        }

        # Use provided pre_process or default configuration
        self.pre_process = default_pre_process
        if pre_process is not None:
            # Update with provided values
            self.pre_process.update(pre_process)

        # Component collections
        self.components = []  # Registry of all components as a list
        self.components_by_cls = {}  # Registry of all components by class
        self.areas = {}
        self.links = {}
        self._model_built = False

        # For saving/loading
        self._serializable_attributes = [
            'name', 'hours', 'year_ops', 'year_invs', 'year_decs', 'modes',
            'resources', 'hour_types', 'add_modules', 'pre_process',
            'solver_name', 'solver_options'
        ]
        # POMMES model attributes

        self.linopy_model = None
        self.config = {
            'config': {
                'solver': self.solver_name,
                'solver_options': self.solver_options,
            },
            'coords': {},
            'add_modules': None,
            'pre_process': self.pre_process,
            "input": {
                "path": None,
            }
        }
        self.parameter_tables = {}

    def context(self):
        """Return a context manager for this model."""
        return ModelContext(self)

    def copy(self, new_name: Optional[str] = None) -> 'EnergyModel':
        """
        Create a deep copy of the EnergyModel.

        This creates a new EnergyModel instance with deep copies of all
        components, allowing for independent modification.

        Args:
            new_name (Optional[str]): A new name for the copied model.
                If None, the name will be f"{self.name}_copy".

        Returns:
            EnergyModel: A new, independent copy of the energy model.
        """
        if new_name is None:
            new_name = f"{self.name}_copy"

        logger.info(f"Copying EnergyModel '{self.name}' to a new model named '{new_name}'.")

        # Create a new model instance, copying constructor arguments
        new_model = EnergyModel(
            name=new_name,
            folder=None,  # Let the new model create its own folder
            hours=copy.deepcopy(self.hours),
            year_ops=copy.deepcopy(self.year_ops),
            year_invs=copy.deepcopy(self.year_invs),
            year_decs=copy.deepcopy(self.year_decs),
            modes=copy.deepcopy(self.modes),
            resources=copy.deepcopy(self.resources),
            hour_types=copy.deepcopy(self.hour_types),
            add_modules=copy.deepcopy(self.add_modules),
            pre_process=copy.deepcopy(self.pre_process),
            solver_name=self.solver_name,
            solver_options=copy.deepcopy(self.solver_options)
        )

        # Create a mapping from old components to new components
        memo = {id(old_comp): old_comp.copy(new_model) for old_comp in self.components}

        # Deep copy components and register them with the new model
        for old_component in self.components:
            new_component = memo[id(old_component)]
            new_model.register_component(new_component)

        # Re-establish internal component relationships in the new model
        for new_component in new_model.components:
            # Re-associate components within Areas
            if isinstance(new_component, Area):
                new_component.components = {
                    name: memo[id(old_sub_comp)]
                    for name, old_sub_comp in new_component.components.items()
                }
            # Re-associate technologies within Links
            elif isinstance(new_component, Link):
                new_component.technologies = {
                    name: memo[id(old_tech)]
                    for name, old_tech in new_component.technologies.items()
                }

        logger.info(f"Successfully copied model. New model '{new_name}' has {len(new_model.components)} components.")
        return new_model

    def create_component(self, component_class: Type[Component], name: str, **kwargs) -> Component:
        """
        Factory method to create a component linked to this model.

        Args:
            component_class: Component class to instantiate
            name: Name for the new component
            **kwargs: Additional parameters to pass to the component constructor

        Returns:
            The created component instance
        """
        component = component_class(name, model=self, **kwargs)
        return self.register_component(component)

    def register_component(self, component: Component) -> Component:
        """
        Register an existing component with this model.

        Args:
            component: Component instance to register

        Returns:
            The registered component
        """

        try:
            # Set model reference if not already set 
            if component.model is None:
                component._model = self
            elif component.model != self:
                logger.error(f"Component '{component.name}' already belongs to different model")
                raise ValueError(f"Component '{component.name}' already belongs to a different model")

            self.components.append(component)

            class_name = component.__class__.__name__
            if class_name not in self.components_by_cls:
                self.components_by_cls[class_name] = []
            self.components_by_cls[class_name].append(component)

            if class_name == "Area":
                if component.name not in self.areas:
                    self.areas[component.name] = component
                else:
                    logger.error(f"Area '{component.name}' already exists in model {self.name}")
                    raise ValueError(f"Duplicate area name: {component.name}")

            elif class_name == "Link":
                if component.name not in self.links:
                    self.links[component.name] = component

            logger.debug(f"Registered component: {component.name} of type {class_name} "
                         f"(total {class_name} components: {len(self.components_by_cls[class_name])})")
            return component
        except Exception as e:
            logger.error(f"Error registering component '{component.name}': {str(e)}")
            raise

    def to_pommes_model(self, output_dir='.'):
        """
        Export the energy model to POMMES configuration files.

        This method generates the necessary configuration files (config.yaml and tables)
        based on the components registered in the energy model.

        Parameters
        ----------
        output_dir : str, optional
            Directory where the output files will be saved, by default '.'

        Returns
        -------
        dict
            Dictionary containing the paths to the generated files
        """
        try:
            self._set_add_modules()
            self._add_coords_for_indexed_components()
            self._generate_component_parameters()
            self._add_generic_coords()

        except Exception as e:
            logger.error(f"Error exporting model '{self.name}' to POMMES configuration: {str(e)}")
            raise

    def _add_generic_coords(self):
        """
        Add generic coordinates to the model configuration.

        This method adds standard coordinates like mode, resource, hour, year_op, etc.
        to the model configuration based on the model's attributes.
        """
        coords_to_add = {
            'mode': {'type': 'str', 'attr': 'modes'},
            'resource': {'type': 'str', 'attr': 'resources'},
            'hour_type': {'type': 'str', 'attr': 'hour_types'},
            'hour': {'type': 'int64', 'attr': 'hours', 'conditional': True},
            'year_op': {'type': 'int', 'attr': 'year_ops', 'conditional': True},
            'year_inv': {'type': 'int', 'attr': 'year_invs', 'conditional': True},
            'year_dec': {'type': 'int', 'attr': 'year_decs', 'conditional': True}
        }

        # Add coordinates using the dictionary and getattr
        for coord_name, config_options in coords_to_add.items():
            attr_value = getattr(self, config_options['attr'])

            # Skip if conditional and attribute is None or empty
            if config_options.get('conditional', False) and not attr_value:
                continue

            # Add to config
            self.config['coords'][coord_name] = {
                'type': config_options['type'],
                'values': attr_value
            }

    def _add_coords_for_indexed_components(self):
        """
        Add coordinates for indexed components to the model configuration.

        This method identifies components with their own indices and adds them
        as coordinates to the model configuration.
        """
        component_conversion_dict = {
            component.own_index: component.__class__.__name__ for component in self.components if
            component.own_index is not None
        }
        # Add components with index
        for k, v in component_conversion_dict.items():
            components = [c for c in self.components if c.__class__.__name__ == v]
            self.config['coords'][k] = {
                'type': 'str',
                'values': list(set([component.name for component in components]))
            }

    def _set_add_modules(self):
        """
        Activates and configures the default add_module settings.

        This method initializes and activates the default configuration for
        various modules by setting their enabled state. Each module has a
        specific functionality, and this method ensures that all are activated
        by default.

        :return: A dictionary containing the default configuration settings
            for the 'add_modules' with their activation states (True).
        :rtype: dict
        """
        # Default add_module configuration (all modules enabled)
        self.add_modules = {
            'combined': any([c.__class__.__name__ == "CombinedTechnology" for c in self.components]),
            'conversion': any([c.__class__.__name__ == "ConversionTechnology" for c in self.components]),
            'carbon': any([c.__class__.__name__ == "Carbon" for c in self.components]),
            'transport': any([c.__class__.__name__ == "TransportTechnology" for c in self.components]),
            'turpe': any([c.__class__.__name__ == "Turpe" for c in self.components]),
            'storage': any([c.__class__.__name__ == "StorageTechnology" for c in self.components]),
            'net_import': any([c.__class__.__name__ == "NetImport" for c in self.components]),
            'flexibility': any([c.__class__.__name__ == "FlexibleDemand" for c in self.components])
        }
        self.config['add_modules'] = self.add_modules

    def _generate_component_parameters(self):
        """
        Dynamically generate model parameters from component attributes by introspecting
        class definitions to determine types and default values.
        """
        logger.debug(f"Generating component parameters for {len(self.components)} components "
                     f"across {len(self.components_by_cls)} component types")


        parameters = {}
        # Track parameter groups by their index structure
        index_groups = {}

        # Track attributes by their file group
        file_attr_groups = {}  # file_name -> list of (param_name, attr_name, component_type)

        # Iterate through all components in the model
        for component_type_name, components in self.components_by_cls.items():
            if len(components) > 0:

                # Get a representative component and its class
                component_class = components[0].__class__
                params, component_index_groups = component_class.generate_class_parameters()
                parameters = parameters | params

                # Assign file names for each index group within this component type
                for index_key, attrs in component_index_groups.items():
                    # Create a descriptive file name based on prefix and index structure

                    if component_class.prefix != "":
                        file_name = f"{component_class.prefix}{index_key}.csv"
                    else:
                        file_name = f"{component_type_name.lower()}_{index_key}.csv"


                    # Store the file name for this index group
                    index_groups[(component_type_name, index_key)] = file_name

                    # Add all attributes to this file group
                    if file_name not in file_attr_groups:
                        file_attr_groups[file_name] = []

                    for attr in attrs:
                        file_attr_groups[file_name].append({
                            "param_name": f"{component_class.prefix}{attr}",
                            "attr_name": attr,
                            "component_type": component_type_name
                        })

        self.config["input"]["parameters"] = parameters

        # Assign file names to parameters
        for param_name, param_info in parameters.items():
            # Extract component type and index key
            for (component_type, index_key), file_name in index_groups.items():
                if (param_info["index_key"] == index_key) and (param_info["cls_name"] == component_type):
                    param_info["file"] = file_name
                    break

            # Clean up temporary key
            if "index_key" in param_info:
                del param_info["index_key"]

        # Now generate the tables for each group
        self._generate_tables_from_params(parameters, file_attr_groups)

    def _generate_tables_from_params(self, parameters, file_attr_groups):
        """
        Generate tables from parameters and component data.

        Args:
            parameters: Dictionary of parameter configurations
            file_attr_groups: Dictionary mapping file names to lists of attribute info
        """
        logger.debug(
            f"Generating tables from {len(parameters)} parameters across {len(file_attr_groups)} file groups")

        # Process each file group
        for file_name, attr_infos in file_attr_groups.items():

            if not attr_infos:
                continue
            comp_type = attr_infos[0]["component_type"]
            if comp_type not in self.components_by_cls:
                continue
            components = self.components_by_cls[comp_type]
            if not components:
                continue

            all_component_dfs = []
            attr_names = [attr['attr_name'] for attr in attr_infos]
            # Process each component
            for component in components:

                index_input, df = component.generate_component_table(component, attr_names, parameters)
                if df is not None:
                    all_component_dfs.append(df)

            # Combine all component dataframes and write to CSV
            if all_component_dfs:
                try:
                    combined_df = pl.concat(all_component_dfs).to_pandas()
                except Exception as e:
                    print(e)
                    for df in all_component_dfs:
                        print(df)
                if index_input:
                    combined_df = combined_df.set_index(index_input)

                self.parameter_tables[file_name] = combined_df
                logger.info(f"Generated table: {file_name} with {len(combined_df)} "
                            f"rows and {len(combined_df.columns)} columns")



    def run_pommes_model(self):
        """
        Run the POMMES optimization model using the current configuration.

        This method builds the input parameters, checks them, builds the model,
        and solves it using the specified solver and options.
        """
        logger.info(f"Running POMMES model: '{self.name}' from configuration in {self.folder}")
        p = build_input_parameters(self.config, self.parameter_tables)
        p = check_inputs(p)
        self.linopy_model = build_model(p)
        self.linopy_model.solve(solver_name=self.solver_name,
                                **self.solver_options
                                )
        logger.info(f"Model '{self.name}' solved successfully using solver: {self.solver_name}")


    def run(self):
        """
        Run the model by generating the POMMES configuration and solving the optimization problem.
        """
        self.to_pommes_model()
        self.run_pommes_model()

    def write_model(self, table_format='parquet'):
        """Save the model configuration and data tables to files.

        Args:
            table_format (str, optional): Format to save the data tables in. Defaults to 'parquet'.

        Returns:
            dict: Paths to generated files {'config': Path, 'tables': List[Path]}

        Raises:
            ValueError: If model configuration is invalid
            IOError: If there are file system related errors
            Exception: For other unexpected errors
        """
        import yaml
        generated_files = {'config_path': "", 'tables': []}

        try:
            logger.info(f"Saving model '{self.name}' to {self.folder} "
                        f"with {len(self.components)} components across {len(self.components_by_cls)} component types")

            generated_files['config_path'] = self.write_yaml()
            generated_files['tables'] = self.write_parameter_tables(table_format)

            logger.info(f"Model '{self.name}' saved successfully. Config: {generated_files['config_path']}, "
                        f"Generated {len(generated_files['tables'])} tables")

            return generated_files

        except (yaml.YAMLError, yaml.representer.RepresenterError) as e:
            logger.error(f"YAML serialization error while saving model '{self.name}': {str(e)}")
            raise ValueError(f"Failed to serialize model configuration: {str(e)}")
        except IOError as e:
            logger.error(f"I/O error while saving model '{self.name}': {str(e)}")
            raise IOError(f"Failed to write model files: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while saving model '{self.name}': {str(e)}")
            raise

    def write_yaml(self):
        """
        Write the model configuration to a YAML file.

        Returns:
            str: Path to the generated config.yaml file
        """
        import yaml
        def represent_list(dumper, data):
            """Convert Python lists to YAML sequences with flow style."""
            return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

        def represent_numpy_array(dumper, data):
            """Convert NumPy arrays to YAML sequences with flow style."""
            return dumper.represent_sequence('tag:yaml.org,2002:seq', data.tolist(), flow_style=True)

        def string_representer(dumper, data):
            """Represent strings with double quotes in YAML."""
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

        def nan_representer(dumper, _):
            """Represent NaN values as the string 'nan' in YAML."""
            return dumper.represent_scalar('tag:yaml.org,2002:str', 'nan')

        # Register the custom representers
        yaml.add_representer(list, represent_list)
        yaml.add_representer(np.ndarray, represent_numpy_array)
        yaml.add_representer(str, string_representer)
        yaml.add_representer(float('nan').__class__, nan_representer)

        # Write config.yaml
        config_path = self.folder / 'config.yaml'
        with config_path.open('w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
        return config_path.__str__()

    def write_parameter_tables(self, table_format):
        """
        Write parameter tables to files in the specified format.

        Args:
            table_format (str): Format to save the tables in ('parquet' or 'csv')

        Returns:
            list: List of paths to the generated table files
        """
        # Create data subfolder it doesn't exist
        (self.folder / 'data').mkdir(parents=True, exist_ok=True)
        # Save parameter tables
        tables = []
        for file_name, df in self.parameter_tables.items():
            file_path = self.folder / 'data' / file_name.replace('.csv', f'.{table_format}')
            if table_format == 'parquet':
                df.to_parquet(file_path)
            else:
                df.to_csv(file_path, sep=';')
            tables.append(file_path.__str__())

        return tables

    def set_all_results(self):
        """
        set results for all components in the model.

        Returns:
            dict: A dictionary mapping component names to their results
        """
        if self.linopy_model is None or not hasattr(self.linopy_model, 'solution'):
            raise ValueError("Model has not been solved yet. Run model.run() first.")

        for component in self.components:
            component.set_results()

    def get_results(self, result_type: str, result_name: str, component_classes=None):
        """
        Retrieve and concatenate results from model components.

        This method collects the specified result type and name from all components
        (or a filtered subset of components), adds area and component name information
        if applicable, and concatenates the results into a single DataFrame.

        Args:
            result_type (str): Type of result to collect ('planning' or 'operation')
            result_name (str): Name of the specific result (e.g., 'power', 'power_capacity')
            component_classes (list, optional): List of Component subclasses to filter by.
                If None, results are collected from all components.

        Returns:
            pl.DataFrame: Concatenated results from all matching components

        Raises:
            ValueError: If the model has not been solved or if invalid parameters are provided
        """
        if self.linopy_model is None or not hasattr(self.linopy_model, 'solution'):
            raise ValueError("Model has not been solved yet. Run model.run() first.")

        if result_type not in ['planning', 'operation']:
            raise ValueError("Result type must be either 'planning' or 'operation'")

        # Filter components by class if specified
        if component_classes is not None:
            components = []
            for cls in component_classes:
                class_name = cls.__name__
                if class_name in self.components_by_cls:
                    components.extend(self.components_by_cls[class_name])
        else:
            components = self.components

        # Collect results from components
        result_dfs = []

        for component in components:
            # Skip components without results
            if not hasattr(component, 'results') or not component.results:
                continue

            # Skip components without the requested result type
            if result_type not in component.results:
                continue

            # Skip components without the requested result name
            if result_name not in component.results[result_type]:
                continue

            # Get the result dataframe
            result_df = component.results[result_type][result_name]

            # Skip if no data is available
            if result_df is None or result_df.is_empty():
                continue

            # Add area information if the component is area-indexed
            if component.area_indexed:
                if 'area' not in result_df.columns:
                    result_df = result_df.with_columns(pl.lit(component.area.name).alias('area'))

            # Add link information if the component is link-indexed
            if component.link_indexed:
                if 'link' not in result_df.columns:
                    result_df = result_df.with_columns(pl.lit(component.link.name).alias('link'))

            # Add resource information if the component is resource-indexed
            if component.resource_indexed:
                if 'resource' not in result_df.columns:
                    result_df = result_df.with_columns(pl.lit(component.resource).alias('resource'))

            # Add component name if the component has own_index
            if component.own_index:
                if component.own_index not in result_df.columns:
                    result_df = result_df.with_columns(pl.lit(component.name).alias("name"))

            result_dfs.append(result_df)

        # Concatenate all dataframes if any results were found
        if result_dfs:
            return pl.concat(result_dfs, how='diagonal')
        else:
            logger.warning(f"No results found for type '{result_type}' and name '{result_name}'")
            return pl.DataFrame()

    def save(self, path: Path):
        """
        Save the EnergyModel instance and its components to a specified folder.

        This method serializes the model's configuration and components into a
        YAML file, and saves DataFrame attributes into Parquet files for
        efficiency. The target folder is cleared before saving.

        Args:
            path (Path): The path to the folder where the model will be saved.
        """
        logger.info(f"Saving model '{self.name}' to '{path}'...")

        # Prepare directory
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True)
        data_dir = path / "data"
        data_dir.mkdir()

        # Serialize model attributes
        model_spec = {
            attr: _to_native_python_types(getattr(self, attr)) for attr in self._serializable_attributes
        }

        # Serialize components
        components_spec = []
        for i, component in enumerate(self.components):
            comp_spec = {
                "class_path": _get_class_path(component),
                "name": component.name,
                "attributes": {}
            }
            for attr, value in component.__dict__.items():
                if attr.startswith('_') or attr in ['name', 'results']:
                    continue

                if isinstance(value, pl.DataFrame):
                    relative_path = Path("data") / f"component_{i}_{attr}.parquet"
                    parquet_path = path / relative_path
                    value.write_parquet(parquet_path)
                    comp_spec["attributes"][attr] = str(relative_path)
                elif isinstance(value, Component):
                    # If an attribute is another component, just save its name for re-association
                    comp_spec["attributes"][attr] = value.name
                elif isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    # Sanitize lists and dicts to replace nested components with their names
                    comp_spec["attributes"][attr] = _sanitize_for_yaml(value)

            components_spec.append(comp_spec)

        # Combine into a single structure and save to YAML
        full_spec = {
            "model": model_spec,
            "components": components_spec
        }

        yaml_path = path / "model.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(full_spec, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Model '{self.name}' saved successfully to '{path}'.")

    @classmethod
    def load(cls, path: Path) -> 'EnergyModel':
        """
        Load an EnergyModel instance and its components from a specified folder.

        This class method reconstructs a model from its serialized state,
        loading the configuration from a YAML file and data from Parquet files.

        Args:
            path (Path): The path to the folder where the model was saved.

        Returns:
            EnergyModel: The loaded EnergyModel instance.
        """
        logger.info(f"Loading model from '{path}'...")

        yaml_path = path / "model.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"Model YAML file not found at '{yaml_path}'")

        with open(yaml_path, 'r') as f:
            full_spec = yaml.safe_load(f)

        model_spec = full_spec.get("model", {})

        # Create a new model instance
        # We need to handle the 'folder' attribute separately
        init_args = {k: v for k, v in model_spec.items() if k != 'folder'}

        # The loaded model's folder should be where it's loaded from
        loaded_model = cls(folder=path, **init_args)

        # Load and register components
        components_spec = full_spec.get("components", [])

        # Use a temporary context to avoid validation errors during component creation
        with loaded_model.context():
            for comp_spec in components_spec:
                class_path = comp_spec["class_path"]
                component_class = _import_class_from_string(class_path)

                # We instantiate without calling __init__ to set attributes manually
                component = component_class.__new__(component_class)

                # Manually set attributes
                component.name = comp_spec["name"]
                component._model = loaded_model  # Set model reference

                for attr, value in comp_spec.get("attributes", {}).items():
                    if isinstance(value, str) and value.endswith('.parquet'):
                        parquet_path = path / value
                        if not parquet_path.exists():
                            logger.warning(f"Parquet file not found: {parquet_path}. Skipping attribute '{attr}'.")
                            continue
                        setattr(component, attr, pl.read_parquet(parquet_path))
                    else:
                        setattr(component, attr, value)

                # Now that the component is reconstructed, register it
                # This will populate areas, links, etc.
                loaded_model.register_component(component)

        # Re-establish component relationships that might not be serialized
        for area in loaded_model.areas.values():
            area._reassociate_components()
        for link in loaded_model.links.values():
            link._reassociate_technologies()

        logger.info(f"Model '{loaded_model.name}' loaded successfully with {len(loaded_model.components)} components.")
        return loaded_model
