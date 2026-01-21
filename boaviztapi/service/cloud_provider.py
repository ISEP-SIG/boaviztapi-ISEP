import os
from typing import List

import pandas as pd
import logging

from boaviztapi import data_dir
from boaviztapi.service.archetype import get_device_archetype_lst as _get_device_archetype_lst
from boaviztapi.service.cloud_pricing_provider import AzurePriceProvider, AWSPriceProvider, GcpPriceProvider

archetype_instances = pd.read_csv(os.path.join(data_dir, 'archetypes/cloud/providers.csv'))
aws_pricing_instances = AWSPriceProvider()
azure_pricing_instances = AzurePriceProvider()
gcp_pricing_instances = GcpPriceProvider()

pricing_provider_map = {
    "aws" : aws_pricing_instances,
    "azure": azure_pricing_instances,
    "gcp": gcp_pricing_instances
}

log = logging.getLogger(__name__)

def get_cloud_providers():
    return [item for item in archetype_instances['provider.name'].tolist() if item != 'scaleway']

def get_cloud_instance_types(provider: str) -> List[str]:
    if not os.path.exists(data_dir + '/archetypes/cloud/' + provider + '.csv'):
        raise ValueError(f"No available data for this cloud provider ({provider})")

    archetype_instance_ids = _get_device_archetype_lst(os.path.join(data_dir, 'archetypes/cloud/' + provider + '.csv'))
    pricing_provider = pricing_provider_map[provider]
    if pricing_provider is None:
        log.warning(f"Could not get the pricing instance ids for the provider '{provider}'")
        return archetype_instance_ids

    pricing_instance_ids = pricing_provider.instance_ids
    return list(set(archetype_instance_ids).intersection(pricing_instance_ids))

def get_cloud_instance_types_for_all_providers():
    result = dict()
    cloud_providers = get_cloud_providers()
    for provider in cloud_providers:
        if provider == "scaleway":
            continue
        result[provider] = get_cloud_instance_types(provider)
    return result