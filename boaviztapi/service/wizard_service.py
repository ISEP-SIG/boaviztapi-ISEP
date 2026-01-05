import glob
import os
import pandas as pd
from datetime import datetime

from boaviztapi.model.crud_models.configuration_model import CloudConfigurationModel, OnPremiseConfigurationModel, \
    CloudServerUsage

from boaviztapi.service.utils_provider import data_dir

# Data directory
cloud_dir = os.path.join(data_dir, 'archetypes/cloud')
all_files = glob.glob(os.path.join(cloud_dir, '*.csv'))
all_files.remove(os.path.join(cloud_dir, 'providers.csv'))

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

def _cloud_instance_to_cloud_config(input_onprem_config: OnPremiseConfigurationModel, cloud_instance: dict) -> CloudConfigurationModel:
    try:
        cloud_usage_model = CloudServerUsage(
            localisation=input_onprem_config.usage.localisation,
            lifespan=input_onprem_config.usage.lifespan,
            method=input_onprem_config.usage.method,
            serverLoad=input_onprem_config.usage.serverLoad,
            serverLoadAdvanced=input_onprem_config.usage.serverLoadAdvanced
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

def strategy_lift_shift(input_config: OnPremiseConfigurationModel, provider_name: str) -> CloudConfigurationModel:
    provider_name = provider_name.strip().lower()
    if provider_name not in all_cloud_configs['provider.name'].unique():
        raise ValueError(f"Provider {provider_name} not found in the cloud archetypes")

    # Gather filter parameters
    input_vcpus = input_config.cpu_core_units * input_config.cpu_quantity
    input_ram = input_config.ram_capacity * input_config.ram_quantity
    input_storage = input_config.ssd_capacity * (input_config.ssd_quantity + input_config.hdd_quantity)

    # Make a filter mask for the dataframe
    mask = (
            (all_cloud_configs['provider.name'] == provider_name) &
            (all_cloud_configs['vcpu'] >= input_vcpus) &
            (all_cloud_configs['memory'] >= input_ram) &
            (all_cloud_configs['ssd_storage'] >= input_storage)
    )
    # Filter the dataframe with the mask
    filtered_configs = all_cloud_configs[mask].copy()
    # Sort the filtered dataframe by vcpu, memory and ssd_storage
    filtered_configs = filtered_configs.sort_values(
        by=['vcpu', 'memory', 'ssd_storage'],
        ascending=[True, True, True]
    )
    if len(filtered_configs) == 0:
        raise ValueError(f"No cloud configuration found for provider {provider_name}")
    best_config = filtered_configs.iloc[0].to_dict()
    return _cloud_instance_to_cloud_config(input_config, best_config)

def strategy_right_sizing(input_config: CloudConfigurationModel) -> CloudConfigurationModel:
    return CloudConfigurationModel()

def strategy_greener_region(input_config: CloudConfigurationModel) -> CloudConfigurationModel:
    return CloudConfigurationModel()