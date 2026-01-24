import glob
import os

import numpy as np
import pandas as pd
import logging
import json
from datetime import datetime

from boaviztapi import config
from boaviztapi.model.crud_models.configuration_model import CloudConfigurationModel, OnPremiseConfigurationModel, \
    CloudServerUsage
from boaviztapi.service.archetype import get_cloud_instance_archetype
from boaviztapi.service.cloud_provider import get_cloud_instance_types
from boaviztapi.service.electricity_maps.carbon_intensity_provider import CarbonIntensityProvider
from boaviztapi.service.cloud_pricing_provider import _estimate_localisation, AWSPriceProvider, AzurePriceProvider, \
    GcpPriceProvider
from boaviztapi.service.sustainability_provider import get_cloud_impact

from boaviztapi.service.utils_provider import data_dir
from boaviztapi.utils.costs_calculator import CostCalculator, CurrencyConvertedCostBreakdown

# Initialise logger
log = logging.getLogger(__name__)

# Data directory
cloud_dir = os.path.join(data_dir, 'archetypes/cloud')
all_files = glob.glob(os.path.join(cloud_dir, '*.csv'))
try:
    all_files.remove(os.path.join(cloud_dir, 'providers.csv'))
except ValueError:
    pass

# Dataframe of all the cloud configurations in the archetype folder
df_list = []
for filename in all_files:
    df = pd.read_csv(filename)

    file_label = os.path.splitext(os.path.basename(filename))[0]
    # Add the provider name (from filename) as a column
    df['provider.name'] = file_label.strip().lower()
    # Convert memory to float due to some rogue string values in there
    df['memory'] = pd.to_numeric(df['memory'], errors='coerce')
    # Convert the values used for filtering to float64
    df = df.astype({'vcpu': 'float64', 'memory': 'float64', 'ssd_storage': 'float64'})
    df_list.append(df)

# The parsed dataframe with all the cloud configurations
all_cloud_configs: pd.DataFrame = pd.concat(df_list, join="outer", axis=0, ignore_index=True, sort=False)

# Dataframe with pricing availability
pricing_availability = pd.read_csv(os.path.join(data_dir, 'electricity/electricitymaps_zones.csv'),
                                   header=0)

def _get_pricing_type(provider: str, instance_type: str):
    if provider == 'aws':
        return 'OnDemand', 'yrTerm1Standard.allUpfront'
    elif provider == 'azure':
        return 'LinuxOnDemand', 'yrTerm1Standard.allUpfront'
    elif provider == 'gcp':
        return 'Linux On Demand cost', None
    else:
        raise ValueError(f"Unknown cloud provider: {provider}")

def _cloud_instance_to_cloud_config(input_onprem_config: OnPremiseConfigurationModel, cloud_instance: dict) -> CloudConfigurationModel:
    try:
        cloud_usage_model = CloudServerUsage(
            localisation=input_onprem_config.usage.localisation,
            lifespan=input_onprem_config.usage.lifespan,
            method=input_onprem_config.usage.method if input_onprem_config.usage.method.lower() != 'electricity' else 'load',
            serverLoad=input_onprem_config.usage.serverLoad,
            serverLoadAdvanced=input_onprem_config.usage.serverLoadAdvanced,
            instancePricingType=_get_pricing_type(cloud_instance['provider.name'], cloud_instance['id'])[0],
            reservedPlan=_get_pricing_type(cloud_instance['provider.name'], cloud_instance['id'])[1]
        )
        model = CloudConfigurationModel(
            type='cloud',
            name=input_onprem_config.name + '-lift&shift',
            created=datetime.now(),
            cloud_provider=cloud_instance['provider.name'],
            instance_type=cloud_instance['id'],
            usage=cloud_usage_model,
            user_id=input_onprem_config.user_id,
        )
    except Exception as e:
        raise ValueError(f"Error while converting cloud instance to cloud configuration: {e}") from e
    return model

def _provider_factory(provider: str):
    if provider == 'aws':
        return AWSPriceProvider()
    elif provider == 'azure':
        return AzurePriceProvider()
    elif provider == 'gcp':
        return GcpPriceProvider()
    else:
        raise ValueError(f"Unknown cloud provider: {provider}")


def strategy_lift_shift(input_config: OnPremiseConfigurationModel, provider_name: str) -> CloudConfigurationModel:
    provider_name = provider_name.strip().lower()
    if provider_name not in all_cloud_configs['provider.name'].unique():
        raise ValueError(f"Provider {provider_name} not found in the cloud archetypes")

    # Gather filter parameters
    input_vcpus = input_config.cpu_core_units * input_config.cpu_quantity
    input_ram = input_config.ram_capacity * input_config.ram_quantity

    # Limit the filter parameters to the maximum values available in the cloud archetypes
    provider_configs = all_cloud_configs[all_cloud_configs['provider.name'] == provider_name]
    if input_vcpus > provider_configs['vcpu'].max():
        log.warning(f"input_vcpus[{input_vcpus}] > provider_configs['vcpu'].max()[{provider_configs['vcpu'].max()}]."
                    f"Given on-premise virtual CPU cores requirements exceed the biggest vcpu size available at {provider_name}. "
                    f"Limiting input_vcpus to the maximum provided by the cloud provider!")
        input_vcpus = min(input_vcpus, provider_configs['vcpu'].max())
    if input_ram > provider_configs['memory'].max():
        log.warning(f"input_ram[{input_ram}] > provider_configs['memory'].max()[{provider_configs['memory'].max()}]. "
                    f"Given on-premise memory requirements exceed the biggest memory size available at {provider_name}. "
                    f"Limiting input_ram to the maximum provided by the cloud provider!")
        input_ram = min(input_ram, provider_configs['memory'].max())

    valid_instance_types = get_cloud_instance_types(provider_name)
    # Make a filter mask for the dataframe
    mask = (
            (all_cloud_configs['provider.name'] == provider_name) &
            (all_cloud_configs['vcpu'] >= input_vcpus) &
            (all_cloud_configs['memory'] >= input_ram) &
            (all_cloud_configs['id'].isin(valid_instance_types))
    )
    # Filter the dataframe with the mask
    filtered_configs = all_cloud_configs[mask].copy()
    # Sort the filtered dataframe by vcpu, memory and ssd_storage
    filtered_configs = filtered_configs.sort_values(
        by=['vcpu', 'memory'],
        ascending=[True, True]
    )
    if len(filtered_configs) == 0:
        raise ValueError(f"No cloud configuration found for provider {provider_name} that fits the given requirements!")
    best_config = filtered_configs.iloc[0].to_dict()
    return _cloud_instance_to_cloud_config(input_config, best_config)


async def _get_cloud_costs_for_instance(input_config: CloudConfigurationModel) -> CurrencyConvertedCostBreakdown:
    calculator = CostCalculator(duration=getattr(input_config.usage, "lifespan", 1))
    cost_results = await calculator.configuration_costs(input_config)
    cost_results = cost_results.model_dump(exclude_none=True)
    return cost_results

def _try_impact_extraction(impacts: dict, key: str):
    if impacts is None:
        return 0.0
    try:
        if key in impacts:
            impact = impacts[key]
            return impact['use']['value']
    except KeyError:
        return 0.0

async def strategy_right_sizing(input_config: CloudConfigurationModel, provider_name: str) -> CloudConfigurationModel:
    provider_name = provider_name.strip().lower()
    if provider_name not in all_cloud_configs['provider.name'].unique():
        raise ValueError(f"Provider {provider_name} not found in the cloud archetypes")

    if not input_config.usage.serverLoad and not input_config.usage.serverLoadAdvanced:
        raise ValueError("Basic/Advanced server load must be specified in the input configuration")

    cloud_archetype = get_cloud_instance_archetype(input_config.instance_type, input_config.cloud_provider)
    if not cloud_archetype:
        raise ValueError(f"{input_config.instance_type} at {input_config.cloud_provider} not found")

    # Get the current usage load
    if input_config.usage.serverLoadAdvanced:
        load_obj = input_config.usage.serverLoadAdvanced
        current_load = np.average([load_obj.slot1.load, load_obj.slot2.load, load_obj.slot3.load])
    else:
        current_load = input_config.usage.serverLoad

    # If the current usage load is >= 85%, then the configuration is already optimal
    if current_load >= 85:
        return input_config

    # The target load for a reasonable configuration is 85%
    target_load = 85

    valid_instance_types = get_cloud_instance_types(provider_name)
    mask = (
            (all_cloud_configs['provider.name'] == provider_name) &
            (all_cloud_configs['vcpu'] <= cloud_archetype['vcpu']['default']) &
            (all_cloud_configs['memory'] >= cloud_archetype['memory']['default']) &
            (all_cloud_configs['id'].isin(valid_instance_types))
    )
    filtered_configs = all_cloud_configs[mask].copy()

    if len(filtered_configs) == 0:
        raise ValueError(f"No cloud configuration found for provider {provider_name} that matches the given criteria!")
    if not cloud_archetype['vcpu']['default'] or cloud_archetype['vcpu']['default'] == 0:
        raise ValueError(
            f"No default vCPU value found for the instance {input_config.instance_type} and cloud provider {input_config.cloud_provider}!")

    # Compute the estimated load for each configuration
    filtered_configs['estimated_load'] = (cloud_archetype['vcpu']['default'] * current_load) / filtered_configs['vcpu']

    # Sort the configurations based on the estimated loads
    filtered_configs = filtered_configs.sort_values(
        by=['estimated_load'],
        ascending=[True]
    )

    # Limit the number of configurations to have a better load than the current one, but to be under or equal to the target load to allow headroom
    filtered_configs = filtered_configs[(filtered_configs['estimated_load'] >= current_load) & (
                filtered_configs['estimated_load'] <= target_load)].copy()

    if len(filtered_configs) == 0:
        raise ValueError(f"No cloud configuration found for provider {provider_name} that matches the given criteria!")

    # There are more configs, use pricing and impacts as a tiebreaker
    final_duration = getattr(input_config.usage, "lifespan", 1) # Final duration for the lifespan
    for index, row in filtered_configs.iterrows():
        try:
            temp_config = input_config.model_copy(deep=True)
            if input_config.cloud_provider != provider_name:
                # If the resulting config is from another provider, switch back to default pricing types for compatibility
                temp_config.usage.instancePricingType = _get_pricing_type(provider_name, temp_config.instance_type)[0]
                temp_config.usage.reservedPlan = _get_pricing_type(provider_name, temp_config.instance_type)[1]
            temp_config.cloud_provider = provider_name
            temp_config.instance_type = row['id']
            impacts = await get_cloud_impact(temp_config, False, final_duration, config["default_criteria"])
            impacts = getattr(impacts, "impacts", None)
            gwp = _try_impact_extraction(impacts, "gwp")
            pe = _try_impact_extraction(impacts, "pe")
            adp = _try_impact_extraction(impacts, "adp")
            filtered_configs.at[index, 'gwp'] = gwp
            filtered_configs.at[index, 'pe'] = pe
            filtered_configs.at[index, 'adp'] = adp

            costs = await _get_cloud_costs_for_instance(temp_config)
            filtered_configs.at[index, 'estimated_cost'] = costs['eur']['total_cost']
            filtered_configs.at[index, 'energy_cost'] = costs['eur']['breakdown']['energy_costs']
            filtered_configs.at[index, 'operating_cost'] = costs['eur']['breakdown']['operating_costs']


        except Exception as e:
            log.error(e)
            filtered_configs.at[index, 'estimated_cost'] = 0.0
            filtered_configs.at[index, 'gwp'] = 0.0
            filtered_configs.at[index, 'pe'] = 0.0
            filtered_configs.at[index, 'adp'] = 0.0
            filtered_configs.at[index, 'energy_cost'] = 0.0
            filtered_configs.at[index, 'operating_cost'] = 0.0


    # Exclude configs which don't have the same cost types as the input config
    input_config_costs = await _get_cloud_costs_for_instance(input_config)

    input_breakdown = input_config_costs.get('eur', {}).get('breakdown', {})
    input_energy = input_breakdown.get('energy_costs')
    input_operating = input_breakdown.get('operating_costs')

    input_has_energy = input_energy is not None and not np.isnan(input_energy) and input_energy != 0.0
    input_has_operating = input_operating is not None and not np.isnan(input_operating) and input_operating != 0.0

    if input_has_energy:
        energy_mask = (filtered_configs['energy_cost'].notna()) & (filtered_configs['energy_cost'] != 0.0)
    else:
        energy_mask = (filtered_configs['energy_cost'].isna()) | (filtered_configs['energy_cost'] == 0.0)

    if input_has_operating:
        operating_mask = (filtered_configs['operating_cost'].notna()) & (filtered_configs['operating_cost'] != 0.0)
    else:
        operating_mask = (filtered_configs['operating_cost'].isna()) | (filtered_configs['operating_cost'] == 0.0)

    mask = energy_mask & operating_mask
    filtered_configs = filtered_configs[mask]

    if len(filtered_configs) == 0:
        raise RuntimeError("No configuration matches the given criteria!")

    # Sort the final results based on the 5 attributes in the 'by' parameter
    if 'estimated_cost' in filtered_configs.columns:
        filtered_configs = filtered_configs.sort_values(by=['estimated_cost', 'estimated_load', "gwp", "pe", "adp"], ascending=[True, False, True, True, True])

    best_match = filtered_configs.iloc[0]
    result_config = input_config.model_copy(deep=True)

    result_config.cloud_provider = provider_name
    if result_config.usage.serverLoad:
        result_config.usage.serverLoad = best_match['estimated_load']
    if result_config.usage.serverLoadAdvanced:
        load_obj = result_config.usage.serverLoadAdvanced
        for slot in [load_obj.slot1, load_obj.slot2, load_obj.slot3]:
            slot.load = best_match['estimated_load']

    result_config.instance_type = best_match['id']
    if input_config.cloud_provider != provider_name:
        # If the resulting config is from another provider, switch back to default pricing types for compatibility
        result_config.usage.instancePricingType = _get_pricing_type(provider_name, result_config.instance_type)[0]
        result_config.usage.reservedPlan = _get_pricing_type(provider_name, result_config.instance_type)[1]

    return result_config

async def strategy_greener_region(input_config: CloudConfigurationModel) -> CloudConfigurationModel:
    if not input_config.usage.localisation:
        raise ValueError("A localisation is required to compute the greener cloud strategy")
    # Gather all the regions for the given provider and instance type

    provider_data = _provider_factory(input_config.cloud_provider)
    regions = provider_data.get_regions_for_instance(input_config.instance_type)

    if len(regions) == 1:
        log.info(
            f"No better configuration option was found for {input_config.cloud_provider}/{input_config.instance_type}")
        return input_config
    # Check the carbon footprint of each region
    locations = []
    for region in regions:
        try:
            locations.append(_estimate_localisation(region, input_config.cloud_provider))
        except Exception as e:
            log.warning(f"Error while computing carbon intensity for {region}: {e}")
            continue
    locations = np.unique(locations)
    intensities = {}
    carbon_intensity_cache = await CarbonIntensityProvider.get_cache_scheduler('monthly').get_results()
    carbon_intensity_cache = {key: (json.loads(value) if isinstance(value, str) else value) 
                                  for key, value in carbon_intensity_cache.items()}
    for location in locations:
        try:
            for carbon_intensity in carbon_intensity_cache.values():
                if carbon_intensity['zone'] == location:
                    intensities[location] = carbon_intensity['carbonIntensity']
        except Exception as e:
            log.warning(f"Error while computing carbon intensity for {location}: {e}")
            continue
    if intensities == {}:
        raise ValueError('Could not compute the carbon intensity for any of the regions of the given cloud configuration!')
    greenest_location = min(intensities, key=intensities.get)
    if not greenest_location:
        raise ValueError('Could not compute the greenest location for the given cloud configuration!')

    # If the greenest location is the current one, return the same config
    if greenest_location == input_config.usage.localisation:
        log.info(
            f"No better configuration option was found for {input_config.cloud_provider}/{input_config.instance_type}")
        return input_config

    # Set the new location to the cloud configuration and send it back
    input_config.usage.localisation = greenest_location
    return input_config