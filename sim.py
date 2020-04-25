from sim_utils.model import Model
from sim_utils.parameters import Scenario

# Temporary run model without replication


scenario = Scenario(

    samples_per_day = 30132,
    
    basic_batch_size = 93,

    resource_numbers = {
            'human_sample_receipt': 99,
            'human_sample_prep': 99,
            'human_rna_prep': 99,
            'human_pcr': 99,
            'sample_heat_block': 99,
            'beckman_rna_extraction': 99,
            'pcr_plate_stamper': 99,
            'pcr_plate_reader': 99,
            'sample_prep_automation': 99
            },
    
    # Workstations represent the physical capacity (max jobs)
    # 7 auto sample prep or 16 manual
    workstation_capacity =  {
            'workstation_0': 99999,
            'workstation_1a': 8,
            'workstation_1b_man': 9,
            'workstation_1b_auto': 3, 
            'workstation_1c': 99, 
            'workstation_2': 16,
            'workstation_3': 4,
            'workstation_4': 13
            },

    # Resource available hours (use hours)
    resource_shift_hours =  {
            'human_sample_receipt': (0.3, 17.75),
            'human_sample_prep': (0.3, 17.75),
            'human_rna_prep': (0.3, 17.75),
            'human_pcr': (0.3, 17.75),
            'sample_heat_block': (0.0, 24.0),
            'beckman_rna_extraction': (0.0, 24.0),
            'pcr_plate_stamper': (0.0, 24.0),
            'pcr_plate_reader': (0.0, 24.0),
            'sample_prep_automation': (0.0, 24.0),
            },
    
    # FTE should always be present for start times
    process_start_hours = {
            'sample_receipt': (0., 15.5),
            'sample_prep': (0., 15.5),
            'sample_heat': (0., 15.5),
            'rna_extraction': (0., 24),
            'pcr_prep': (0., 24),
            'pcr': (0.3, 24)
            },
    
    # Process duration. Tuple of fixed time, time per entity, and time per item in entity.
    # Multi-step automated processes have three sets of times (set up, automated, clean down)
    process_duration = {
             'batch_input': ([0,0,0],),
             'sample_receipt': ([16, 0, 0],),
             'sample_prep_manual': ([37, 0, 0],),
             'sample_prep_auto': ([2, 0, 0], [6, 0, 0], [8, 0, 0]),
             'sample_heat':  ([1, 0, 0], [20, 0, 0], [2, 0, 0]),
             'rna_extraction': ([15,0,0],[77,0,0],[5,0,0]),
             'pcr_prep': ([31,0,0],[10,0,0],[1,0,0]),
             'pcr': ([5,0,0],[117,0,0],[1,0,0]),
             'data_analysis': ([0,0,0],)
             },
    
    # Resource unavailability on any whole day due to breakdown
    resource_breakdown_unavailability = {
            'human_sample_receipt': 0,
            'human_sample_prep': 0,
            'human_rna_prep': 0,
            'human_pcr': 0,
            'sample_heat_block': 0,
            'beckman_rna_extraction': 0.0,
            'pcr_plate_stamper': 0.0,
            'pcr_plate_reader': 0.0,
            'sample_prep_automation': 0
            },
    
              
    allow_maual_sample_prep = True,
    tea_break_times = [2*60, 7*60, 12*60, 16*60],
    meal_break_times = [4*60, 14*60],
    break_start_spread = 60,
    tea_break_duration = [1,1] ,#[25, 35],
    meal_break_duration = [1,1] #[40, 50]
    )
  

model = Model(scenario)
model.run()
