from sim_utils.replication import Replicator
from sim_utils.parameters_200421 import Scenario


# Set up a dictionary to hold scenarios
scenarios = {}

# Name & define all scenarios (set parameters that differ from defaults in sim_utils/parameters.py)

scenarios['30k_recommended'] = Scenario(samples_per_day = 30000,
                                resource_numbers = {
                                'human_sample_receipt': 12,
                                'human_sample_prep': 5,
                                'human_rna_prep': 4,
                                'human_pcr': 3,
                                'biomek': 16,
                                'pcr_plate_stamper': 2,
                                'pcr_plate_reader': 13,
                                'sample_prep_automation': 5
                                },
                                resource_shift_hours = {
                                'human_sample_receipt': (0.0, 18.0),
                                'human_sample_prep': (0.0, 18.0),
                                'human_rna_prep': (0.0, 18.0),
                                'human_pcr': (0.0, 18.0),
                                'biomek': (0.0, 24.0),
                                'pcr_plate_stamper': (0.0, 24.0),
                                'pcr_plate_reader': (0.0, 24.0),
                                'sample_prep_automation': (0.0, 24.0),
                                },
                                workstation_capacity = {
                                'workstation_0': 99999,
                                'workstation_1_man': 12,
                                'workstation_1_auto': 5, 
                                'workstation_2': 16,
                                'workstation_3': 2,
                                'workstation_4': 13
                                },
                                resource_breakdown_unavailability = {
                                'human_sample_receipt': 0,
                                'human_sample_prep': 0,
                                'human_rna_prep': 0,
                                'human_pcr': 0,
                                'biomek': 0.1,
                                'pcr_plate_stamper': 0,
                                'pcr_plate_reader': 0,
                                'sample_prep_automation': 0
                                })


# Set up and call replicator
replications = 30
replications = Replicator(scenarios, replications)
replications.run_scenarios()
