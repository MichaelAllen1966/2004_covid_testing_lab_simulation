from sim_utils.replication import Replicator
from sim_utils.parameters import Scenario


# Name & define all scenarios (set parameters that differ from defaults in 
# sim_utils/parameters.py)

# Set up a dictionary to hold scenarios
scenarios = {}

# Name & define all scenarios 
# Set parameters that differ from defaults in sim_utils/parameters_[date].py
# Note: Resource shifts are in hours and fractions of hours. e.g. 14.5 is 2.30pm


scenarios['30k_example'] = Scenario(

    samples_per_day = 30132,

    # Basic unit of operation
    basic_batch_size = 93,

    # Batch sizing for heat stage (multiples of basic_batch_size)
    heat_batch_size = 4,

    # Equipment and workstation capacity gives 34k without FTE constraints
    # Note: sample_heat_incubator capacity is the number of number of heat
    # batches that may be run simultaneously
    resource_numbers={
        'human_sample_receipt_1': 35,
        'human_sample_receipt_2': 10,
        'human_sample_prep_1': 35,
        'human_sample_prep_2': 22,
        'human_pcr_1': 35,
        'human_pcr_2': 25,
        'sample_heat_incubator': 10,
        'pcr_plate_stamper': 9,
        'pcr_plate_reader': 15,
        'sample_prep_automation': 5
    },

    # Workstation capacity was set to give 37.5k per workstation, 35 overall
    workstation_capacity={
        'workstation_0': 9999,
        'workstation_1a': 21,
        'workstation_1b_man': 25,
        'workstation_1b_auto': 5,
        'workstation_2': 10,
        'workstation_3': 9,
        'workstation_4': 15
    },

    # Resource available hours (use hours)
    resource_shift_hours={
        'human_sample_receipt_1': (0.30, 9.00),
        'human_sample_receipt_2': (9.01, 17.75),
        'human_sample_prep_1': (0.30, 9.00),
        'human_sample_prep_2': (9.01, 17.75),
        'human_pcr_1': (0.30, 9.00),
        'human_pcr_2': (9.01, 17.75),
        'sample_heat_incubator': (0.0, 24.0),
        'pcr_plate_stamper': (0.0, 24.0),
        'pcr_plate_reader': (0.0, 24.0),
        'sample_prep_automation': (0.0, 24.0)
    },

    # FTE should always be present for start times
    process_start_hours={
        'sample_receipt': (0.3, 17.2),
        'sample_prep': (0.3, 16.9),
        'sample_heat': (0.3, 17.3),
        'pcr_prep': (0.3, 16.8),
        'pcr': (0.3, 24)
    },

    # Process duration. Tuple of fixed time, time per entity, and time per item
    # in entity. Multi-step automated processes have three sets of times 
    # (set up, automated, clean down)
    process_duration={
        'batch_input': ([0, 0, 0],),
        'sample_receipt': ([33, 0, 0],),
        'sample_prep_manual': ([51, 0, 0],),
        'sample_prep_auto': ([25, 0, 0], [6, 0, 0], [6, 0, 0]),
        'sample_heat': ([2, 0, 0], [30, 0, 0], [2, 0, 0]),
        'pcr_prep': ([45, 0, 0], [5, 0, 0], [4, 0, 0]),
        'pcr': ([5, 0, 0], [90, 0, 0], [5, 0, 0]),
        'data_analysis': ([0, 0, 0],)
    },

    # Resource unavailability on any whole day due to breakdown
    resource_breakdown_unavailability={
        'human_sample_receipt_1': 0,
        'human_sample_receipt_2': 0,
        'human_sample_prep_1': 0,
        'human_sample_prep_2': 0,
        'human_pcr_1': 0,
        'human_pcr_2': 0,
        'sample_heat_incubator': 0,
        'pcr_plate_stamper': 0.08,
        'pcr_plate_reader': 0.02,
        'sample_prep_automation': 0,
    },

    allow_maual_sample_prep=True,
    tea_break_times=[2 * 60, 7 * 60, 12 * 60, 16 * 60],
    meal_break_times=[4 * 60, 14 * 60],
    break_start_spread=60,
    tea_break_duration=[25, 35],
    meal_break_duration=[40, 50]
    )

# Set up and call replicator
replications = 30
replications = Replicator(scenarios, replications)
replications.run_scenarios()
