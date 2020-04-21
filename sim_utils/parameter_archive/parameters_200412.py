import numpy as np

class Scenario(object):
    '''
    Model scenario parameters
         
    '''
    
    def __init__(self, *initial_data, **kwargs):
        
        # Set default values
        
        # Work arrival
        self.samples_per_day = 30000
        self.deliveries_per_day = 4

        # Day and run parameters
        self.day_duration = 1440
        self.fte_start = 6 * 60
        self.fte_end = 24 * 60
        self.run_days = 1
        self.warm_up_days = 0
        
        # Breaks for people (high prority job, but does not interupt work)
        self.tea_break_times = [8*60, 13*60, 17*60, 19*60]
        self.meal_break_times = [11*60, 19*60]
        # Spread start of break for people randomly after set start times
        self.break_start_spread = 60
                
        # break duration is a uniform distribution between min and max
        self.tea_break_duration = [15, 20]
        self.meal_break_duration = [30, 40]
        
        # Audit parameters
        self.audit_interval = 15

        
        # Resource numbers        
        self.resource_numbers = {
            'human_sample_process': 30,
            'human_rna_prep': 10,
            'human_pcr': 2,
            'biomek': 10,
            'pcr_plate_reader': 6
            }
        
        # FTE resources (these will take breaks!)
        self.fte_resources = ['human_sample_process', 'human_rna_prep', 'human_pcr']
        
        # Process duration. Tuple of fixed time, time per entity, and time per item in entity.
        # Multi-step automated processes have three sets of times (set up, automated, clean down)
        self.process_duration = {
             'batch_input': ([0,0,0],),
             'sample_accession': ([50, 0, 0],),
             'sample_preparation': ([40, 0, 0],),
             'rna_extraction': ([10,0,0],[30,0,0],[2,0,0]),
             'pcr_prep': ([25, 0, 0],),
             'pcr': ([5,0,0],[117,0,0],[5,0,0]),
             }
        
        # Add a triangular distribution of extra time per prcoess
        # Average extra time with be 1/4 of this (e.g. 0.25 = 6.25% added length on average)       
        self.additional_time_manual = 0.25
        self.additional_time_auto = 0.10
                
        # Last process start (minutes before day end)
        self.process_last_start = {
            'analysis': 0,
            'pcr': 0,
            'pcr_prep': 0,
            'rna_extraction': 100,
            'collate_for_pcr': 0,
            'sample_preparation': 60,
            'sample_accession': 60,
            }

    
        # Process priories (lower number - higher prioirity)
        self.process_priorites = {
            'batch_input': 50,
            'sample_accession': 50,
            'sample_preparation': 45,
            'rna_extraction': 40,
            'pcr_prep': 35,
            'pcr': 30,
            'data-analysis': 25
            }
        
        # Process resources = tuple of different resources needed and lists of alternatives
        # Remember to put , after a single list to miantain tuple format!
        # A tuple of two or more elemnts will require resources from each tuple element
        self.process_resources = {
            'sample_accession': {
                'process_type': 'manual',
                'human_list': (['human_sample_process'],),
                'machine_list': ([],)},
            'sample_preparation': {
                'process_type': 'manual',
                'human_list': (['human_sample_process'],),
                'machine_list': ([],)},
            'rna_extraction':{
                'process_type': 'auto',
                'human_list': (['human_rna_prep'],),
                'machine_list': (['biomek'],)},
            'pcr_prep':{
                'process_type': 'manual',
                'human_list': (['human_pcr'],),
                'machine_list': ([],)},
            'pcr':{
                'process_type': 'auto',
                'human_list': (['human_pcr'],),
                'machine_list': (['pcr_plate_reader'],)},
            }
        
        # Workstation (used to limit work in progress)
        
        self.process_workstations = {
            'data_analysis': ['workstation_0'],
            'batch_input': ['workstation_0'],
            'sample_accession': ['workstation_1'],
            'sample_preparation' : ['workstation_1'],
            'rna_extraction': ['workstation_2'],
            'pcr_prep': ['workstation_3'],
            'pcr': ['workstation_4']
            }


        self.workstation_capacity = {
            'workstation_0': 99999,
            'workstation_1': 30,
            'workstation_2': 10,
            'workstation_3': 2,
            'workstation_4': 6
            }
        

        # Overwrite default values
        
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        
        for key in kwargs:
            setattr(self, key, kwargs[key])
            
        # Calculations
        
        # Set arrival batch size and round (down) oto nearest 92
        self.arrival_batch_size = self.samples_per_day / self.deliveries_per_day
        self.arrival_batch_size = np.floor(self.arrival_batch_size / 92) * 92
        
        # Set interarrival time
        self.interarrival_time = self.day_duration / self.deliveries_per_day
        
        # Set warm up and run length
        self.audit_warm_up = self.day_duration * self.warm_up_days
        self.run_length = self.run_days * self.day_duration + self.audit_warm_up