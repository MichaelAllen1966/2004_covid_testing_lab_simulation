from sim_utils.model import Model
from sim_utils.parameters import Scenario

# Temporary run model without replication

scenario = Scenario(
    samples_per_day=30000,
    run_days=1,
    warm_up_days=1,
    # List of delivery times (hours from start of day)
    delivery_times=[0],  # 4,5,6,7,8,9,10,11,12
    additional_time_manual=1.33,  # 0.48, 1.33
    additional_time_auto=0.10,
    rna_extraction_batch_size=3,
    resource_numbers={
        'human_sample_receipt_1': 4,  # 4, 6
        'human_sample_receipt_2': 2,
        'human_sample_prep_1': 10,  # 22, 31, 36
        'human_sample_prep_2': 12,  # 23, 24
        'human_rna_prep_1': 4,
        'human_rna_prep_2': 4,
        'human_pcr_1': 6,
        'human_pcr_2': 6,
        'sample_heat_incubator': 4,
        'beckman_rna_extraction': 11,  # 16
        'pcr_plate_stamper': 4,
        'pcr_plate_reader': 8,
        'sample_prep_automation': 3  # 3
    },

    workstation_capacity={
        'workstation_0': 9999,
        'workstation_1a': 10,  # 9
        'workstation_1b_man': 8,  # 12
        'workstation_1b_auto': 3,  # 3
        'workstation_1c': 4,
        'workstation_2': 11,
        'workstation_3': 4,
        'workstation_4': 8
    },

    process_duration={
        'batch_input': ([0, 0, 0],),
        'sample_receipt': ([15, 0, 0],),
        'sample_prep_manual': ([15, 0, 0],),  # 15, 27
        'sample_prep_auto': ([2.5, 0, 0], [10, 0, 0], [2.5, 0, 0]),
        # [20, 0, 0], [8, 0, 0], [11, 0, 0]
        'sample_heat': ([0.5, 0, 0], [20, 0, 0], [3.5, 0, 0]),
        'pcr_prep': ([12.5, 0, 0], [5, 0, 0], [17, 0, 0]),
        'pcr': ([8, 0, 0], [90, 0, 0], [5, 0, 0]),
        'rna_extraction': ([5, 0, 0], [85, 0, 0], [2, 0, 0]),
        'data_analysis': ([0, 0, 0],)
    },

    resource_breakdown_unavailability={
        'human_sample_receipt_1': 0,
        'human_sample_receipt_2': 0,
        'human_sample_prep_1': 0,
        'human_sample_prep_2': 0,
        'human_rna_prep_1': 0,
        'human_rna_prep_2': 0,
        'human_pcr_1': 0,
        'human_pcr_2': 0,
        'sample_heat_incubator': 0,
        'beckman_rna_extraction': 0.15,
        'pcr_plate_stamper': 0.08,
        'pcr_plate_reader': 0.02,
        'sample_prep_automation': 0.04,
        'dummy': 0
    },

    resource_shift_hours={
        'human_sample_receipt_1': (1.5, 9.00),
        'human_sample_receipt_2': (9.01, 18.0),
        'human_sample_prep_1': (1.5, 9.00),
        'human_sample_prep_2': (9.01, 18.0),
        'human_rna_prep_1': (1.5, 9.00),
        'human_rna_prep_2': (9.01, 18.0),
        'human_pcr_1': (1.5, 9.00),
        'human_pcr_2': (9.01, 18.0),
        'sample_heat_incubator': (1.5, 18.0),
        'beckman_rna_extraction': (1.5, 18.0),
        'pcr_plate_stamper': (1.5, 18.0),
        'pcr_plate_reader': (1.5, 20),  # 18, 20
        'sample_prep_automation': (1.5, 18.0),
        'dummy': (1.5, 24.0)
    },

    process_start_hours={
        'sample_receipt': (1.5, 17.2),
        'sample_heat': (1.5, 17.3),
        'sample_prep': (1.5, 16.9),
        'rna_extraction': (0.25, 16.4),
        'pcr_prep': (0.25, 17.3),
        'pcr': (0.25, 20)  # 14.5, 20
    },
    
    transit_1 = {
        'interval': 20,
        'transfer_time': 3, # One way transfer time
        'max_capacity': 4}

)
model = Model(scenario)
model.run()