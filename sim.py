from sim_utils.model import Model
from sim_utils.parameters import Scenario

# Temporary run model without replication


scenario = Scenario(

    process_resources={
        'sample_receipt': {
            'process_type': 'manual',
            'human_list': (['human_sample_receipt_1',
                            'human_sample_receipt_2'],
                           ['tracker_sample_receipt_fte'],
                           ['tracker_all_jobs_fte'],
                           ['tracker_sample_receipt_jobs']),
            'machine_list': ([],)},

        'sample_prep_manual': {
            'process_type': 'manual',
            'human_list': (['human_sample_prep_1',
                            'human_sample_prep_2'],
                           ['human_pcr_1',
                            'human_pcr_2',
                            'human_sample_receipt_1',
                            'human_sample_receipt_2'],
                           ['tracker_all_jobs_fte'],
                           ['tracker_sample_prep_jobs'],
                           ['tracker_sample_prep_fte']),
            'machine_list': ([],)},

        'sample_prep_auto': {
            'process_type': 'auto',
            'human_list': (['human_sample_prep_1',
                            'human_sample_prep_2'],
                           ['tracker_all_jobs_fte'],
                           ['tracker_sample_prep_jobs'],
                           ['tracker_sample_prep_fte']),
            'machine_list': (['sample_prep_automation'],
                             ['tracker_sample_prep_jobs'])},

        'sample_heat': {
            'process_type': 'auto',
            'human_list': (['human_sample_prep_1',
                            'human_sample_prep_2'],
                           ['tracker_all_jobs_fte'],
                           ['tracker_heat_fte']),
            'machine_list': (['sample_heat_incubator'],
                             ['tracker_heat_jobs'])},

        'rna_extraction': {
            'process_type': 'auto',
            'human_list': ([],),
            'machine_list': ([],)},

        'pcr_prep': {
            'process_type': 'auto',
            'human_list': (['human_pcr_1',
                            'human_pcr_2'],
                           ['tracker_all_jobs_fte'],
                           ['tracker_pcr_prep_fte']),
            'machine_list': (['pcr_plate_stamper'],
                             ['tracker_pcr_prep_jobs'])},

        'pcr': {
            'process_type': 'auto',
            'human_list': (['human_pcr_1',
                            'human_pcr_2'],
                           ['tracker_all_jobs_fte'],
                           ['tracker_pcr_fte']),
            'machine_list': (['pcr_plate_reader'],
                             ['tracker_pcr_jobs'])},
    }
)

model = Model(scenario)
model.run()
