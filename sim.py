from sim_utils.model import Model
from sim_utils.parameters_200421 import Scenario

# Temporary run model without replication

scenario = Scenario(
                                samples_per_day = 30000,
                                resource_numbers = {
                                'human_sample_receipt': 12,
                                'human_sample_prep': 5,
                                'human_rna_prep': 4,
                                'human_pcr': 3,
                                'beckman_rna_extraction': 16,
                                'pcr_plate_stamper': 2,
                                'pcr_plate_reader': 13,
                                'sample_prep_automation': 5
                                },
    
                                workstation_capacity = {
                                'workstation_0': 99999,
                                'workstation_1a': 6,
                                'workstation_1b_man': 7,
                                'workstation_1b_auto': 5, 
                                'workstation_2': 16,
                                'workstation_3': 2,
                                'workstation_4': 13
                                },
                                resource_shift_hours = {
                                'human_sample_receipt': (0.0, 18.0),
                                'human_sample_prep': (0.0, 18.0),
                                'human_rna_prep': (0.0, 18.0),
                                'human_pcr': (0.0, 18.0),
                                'beckman_rna_extraction': (0.0, 24.0),
                                'pcr_plate_stamper': (0.0, 24.0),
                                'pcr_plate_reader': (0.0, 24.0),
                                'sample_prep_automation': (0.0, 24.0),
                                },
                                resource_breakdown_unavailability = {
                                'human_sample_receipt': 0,
                                'human_sample_prep': 0,
                                'human_rna_prep': 0,
                                'human_pcr': 0,
                                'beckman_rna_extraction': 0.04,
                                'pcr_plate_stamper': 0.08,
                                'pcr_plate_reader': 0.02,
                                'sample_prep_automation': 0
                                },
                                process_duration = {
                                 'batch_input': ([0,0,0],),
                                 'sample_receipt': ([16, 0, 0],),
                                 'sample_prep_manual': ([37, 0, 0],),
                                 'sample_prep_auto': ([2, 0, 0], [6, 0, 0], [2, 0, 0]),
                                 'rna_extraction': ([5,0,0],[70,0,0],[2,0,0]),
                                 'pcr_prep': ([5,0,0],[10,0,0],[1,0,0]),
                                 'pcr': ([5,0,0],[117,0,0],[1,0,0]),
                                 },
                                allow_maual_sample_prep = True,
                                # Breaks for people (high prority job, but does not interupt work)
                                # Times from start of FTE day (6am)
                                tea_break_times = [2*60, 6*60, 12*60, 16*60],
                                meal_break_times = [4*60, 14*60],
                                # Spread start of break for people randomly after set start times
                                break_start_spread = 60,
                                # break duration is a uniform distribution between min and max
                                tea_break_duration = [15, 20],
                                meal_break_duration = [30, 40]
                                )

model = Model(scenario)
model.run()
