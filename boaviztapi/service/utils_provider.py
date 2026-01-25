import os

import pandas as pd

from boaviztapi.dto.component import CPU
from boaviztapi.model import impact
from boaviztapi.model.component import ComponentCase
from boaviztapi.model.component.cpu import attributes_from_cpu_name

data_dir = os.path.join(os.path.dirname(__file__), '../data')
_cpu_specs = pd.read_csv(os.path.join(data_dir, 'crowdsourcing/cpu_specs.csv'))
_ssd_manuf = pd.read_csv(os.path.join(data_dir, 'crowdsourcing/ssd_manufacture.csv'))
_ram_manuf = pd.read_csv(os.path.join(data_dir, 'crowdsourcing/ram_manufacture.csv'))

def get_all_cpu_family():
    df = _cpu_specs[_cpu_specs["code_name"].notna()]
    return [*df["code_name"].unique()]

def get_all_cpu_model_range():
    df = _cpu_specs[_cpu_specs["model_range"].notna()]
    return [*df["model_range"].unique()]

def get_all_cpu_name():
    df = _cpu_specs[_cpu_specs["name"].notna()]
    return [*df["name"].unique()]

def name_to_cpu(cpu_name: str) -> CPU | str:
    cpu_attributes = attributes_from_cpu_name(cpu_name)
    if cpu_attributes is not None:
        name, manufacturer, code_name, model_range, tdp, cores, threads, die_size, die_size_source, source = cpu_attributes
        return CPU(family=code_name, name=name, tdp=tdp, core_units=cores, die_size=die_size, model_range=model_range,
                   manufacturer=manufacturer)
    else:
        return f"CPU name {cpu_name} is not found in our database"

def get_all_ssd_manufacturer():
    df = _ssd_manuf[_ssd_manuf["manufacturer"].notna()]
    return [*df["manufacturer"].unique()]

def get_all_ram_manufacturer():
    df = _ram_manuf[_ram_manuf["manufacturer"].notna()]
    return [*df["manufacturer"].unique()]

def get_all_case_type():
    return ComponentCase.AVAILABLE_CASE_TYPE

def get_all_impact_criteria():
    return impact.IMPACT_CRITERIAS

def get_instance_reserve_types(provider: str, instance_id: str, reserve_type: str, localisation: str):
    instance_pricing = []
    try:
        if provider == "aws":
            from boaviztapi.service.cloud_pricing_provider import AWSPriceProvider
            instance_pricing = AWSPriceProvider().get_instance_pricing_types_for_instance(instance_id,localisation, reserve_type)
        if provider == "azure":
            from boaviztapi.service.cloud_pricing_provider import AzurePriceProvider
            instance_pricing = AzurePriceProvider().get_instance_pricing_types_for_instance(instance_id, localisation, reserve_type)
        if provider == "gcp":
            from boaviztapi.service.cloud_pricing_provider import GcpPriceProvider
            instance_pricing = GcpPriceProvider().get_instance_pricing_types_for_instance(instance_id, localisation)
    except Exception as e:
        print(e)
        return []
    return instance_pricing
