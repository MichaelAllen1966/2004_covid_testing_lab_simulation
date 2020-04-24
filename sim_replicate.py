from sim_utils.replication import Replicator
from sim_utils.parameters import Scenario


# Name & define all scenarios (set parameters that differ from defaults in sim_utils/parameters.py)

# Set up a dictionary to hold scenarios
scenarios = {}

# Name & define all scenarios 
# Set parameters that differ from defaults in sim_utils/parameters_[date].py
# Note: Resource shifts are in hours and fractions of hours. e.g. 14.5 is 2.30pm

scenarios['30k_recommended'] = Scenario(
    samples_per_day = 30000,

    basic_batch_size = 93,

    resource_numbers = {
        'human_sample_receipt_shift_1': 12,
        'human_sample_receipt_shift_2': 12,
        'human_sample_prep_shift_1': 5,
        'human_sample_prep_shift_2': 5,
        'human_rna_prep_shift_1': 4,
        'human_rna_prep_shift_2': 4,
        'human_pcr_shift_1': 3,
        'human_pcr_shift_2': 3,
        'beckman_rna_extraction': 16,
        'pcr_plate_stamper': 2,
        'pcr_plate_reader': 13,
        'sample_prep_automation': 5
        },
    
    # Workstations represent the physical capacity  
    workstation_capacity = {
        'workstation_0': 99999,
        'workstation_1a': 6,
        'workstation_1b_man': 7,
        'workstation_1b_auto': 5, 
        'workstation_2': 16,
        'workstation_3': 2,
        'workstation_4': 13
        },

    # Resource available hours (use hours)
    resource_shift_hours = {
        'human_sample_receipt_shift_1': (0.3, 9.0),
        'human_sample_receipt_shift_2': (9.0, 17.75),
        'human_sample_prep_shift_1': (0.3, 9.0),
        'human_sample_prep_shift_2': (9.0, 17.75),
        'human_rna_prep_shift_1': (0.3, 9.0),
        'human_rna_prep_shift_2': (9.0, 17.75),
        'human_pcr_shift_1': (0.3, 9.0),
        'human_pcr_shift_2': (9.0, 17.75),
        'beckman_rna_extraction': (0.0, 24.0),
        'pcr_plate_stamper': (0.0, 24.0),
        'pcr_plate_reader': (0.0, 24.0),
        'sample_prep_automation': (0.0, 24.0),
        },
    
    # Range of times new jobs may start
    process_start_hours = {
        'sample_receipt': (0, 17),
        'sample_prep': (0, 15.5),
        'rna_extraction': (0, 24),
        'pcr_prep': (0, 24),
        'pcr': (0, 24)
        },

     # Resource unavailability on any whole day due to breakdown
    resource_breakdown_unavailability = {
        'human_sample_receipt_shift_1': 0,
        'human_sample_receipt_shift_2': 0,
        'human_sample_prep_shift_1': 0,
        'human_sample_prep_shift_2': 0,
        'human_rna_prep_shift_1': 0,
        'human_rna_prep_shift_2': 0,
        'human_pcr_shift_1': 0,
        'human_pcr_shift_2': 0,
        'beckman_rna_extraction': 0.04,
        'pcr_plate_stamper': 0.08,
        'pcr_plate_reader': 0.02,
        'sample_prep_automation': 0
        },
    
    # Process duration. Tuple of fixed time, time per entity, and time per item in entity.
    # Multi-step automated processes have three sets of times (set up, automated, clean down)
    process_duration = {
         'batch_input': ([0,0,0],),
         'sample_receipt': ([16, 0, 0],),
         'sample_prep_manual': ([37, 0, 0],),
         'sample_prep_auto': ([2, 0, 0], [6, 0, 0], [2, 0, 0]),
         'rna_extraction': ([5,0,0],[70,0,0],[2,0,0]),
         'pcr_prep': ([5,0,0],[10,0,0],[1,0,0]),
         'pcr': ([5,0,0],[117,0,0],[1,0,0]),
         },
             
    allow_maual_sample_prep = False,
    tea_break_times = [2*60, 6*60, 12*60, 16*60],
    meal_break_times = [4*60, 14*60],
    break_start_spread = 60,
    tea_break_duration = [15, 20],
    meal_break_duration = [30, 40],
    
    # rna pcr kanban group limit
    # Limit of PCR read capapcity multiple allowed from sample prep onwards
    pcr_kanban_limit = 3
    )


# Set up and call replicator
replications = 30
replications = Replicator(scenarios, replications)
replications.run_scenarios()
