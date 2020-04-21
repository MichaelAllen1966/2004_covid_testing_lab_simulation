import numpy as np

class Scenario(object):
    '''
    Model scenario parameters
         
    '''
    
    def __init__(self, *initial_data, **kwargs):
        
        # Set default values
        # 16/4/2020 Adjust paramters so that day starts with FTE arrival


        # Work arrival
        self.samples_per_day = 30000
        self.deliveries_per_day = 1

        # Day and run parameters
        # 16/4/2020 Model is designed to run primarily in single days
        self.day_duration = 1440
        self.fte_start = 0
        self.fte_end = 17.75 * 60
        self.run_days = 1
        self.warm_up_days = 0
        
        # Breaks for people (high prority job, but does not interupt work)
        # Times from start of FTE day (6am)
        self.tea_break_times = [2*60, 6*60, 12*60, 16*60]
        self.meal_break_times = [4*60, 14*60]
        # Spread start of break for people randomly after set start times
        self.break_start_spread = 60
                
        # break duration is a uniform distribution between min and max
        self.tea_break_duration = [15, 20]
        self.meal_break_duration = [30, 40]
        
        # Audit parameters
        self.audit_interval = 15

        # Resource numbers        
        self.resource_numbers = {
            'human_sample_receipt': 12,
            'human_sample_prep': 5,
            'human_rna_prep': 4,
            'human_pcr': 3,
            'biomek': 16,
            'pcr_plate_stamper': 2,
            'pcr_plate_reader': 13,
            'sample_prep_automation': 5
            }

        # Resource available hours (use hours)
        self.resource_shift_hours = {
            'human_sample_receipt': (0.0, 18.0),
            'human_sample_prep': (0.0, 18.0),
            'human_rna_prep': (0.0, 18.0),
            'human_pcr': (0.0, 18.0),
            'biomek': (0.0, 24.0),
            'pcr_plate_stamper': (0.0, 24.0),
            'pcr_plate_reader': (0.0, 24.0),
            'sample_prep_automation': (0.0, 24.0),
            }
        
        # FTE resources (these will take breaks!)
        self.fte_resources = ['human_sample_receipt', 'human_sample_prep','human_rna_prep',
                              'human_pcr']
        
        # Process duration. Tuple of fixed time, time per entity, and time per item in entity.
        # Multi-step automated processes have three sets of times (set up, automated, clean down)
        self.process_duration = {
             'batch_input': ([0,0,0],),
             'sample_receipt': ([16, 0, 0],),
             'sample_prep_manual': ([37, 0, 0],),
             'sample_prep_auto': ([2, 0, 0], [6, 0, 0], [2, 0, 0]),
             'rna_extraction': ([5,0,0],[70,0,0],[2,0,0]),
             'pcr_prep': ([5,0,0],[10,0,0],[1,0,0]),
             'pcr': ([5,0,0],[117,0,0],[1,0,0]),
             }
        
        self.allow_maual_sample_prep = False
        
        # Add a triangular distribution of extra time per prcoess
        # Average extra time with be 1/4 of this (e.g. 0.25 = 6.25% added length on average)       
        self.additional_time_manual = 0.25
        self.additional_time_auto = 0.10
                
        # Last process start (minutes before day end)
        # Adjust for length of FTE day (as model set up to start with FTE arrival)
        self.process_last_start = {
            'sample_receipt': 60,
            'sample_prep': 150,
            'rna_extraction': 0,
            'pcr_prep': 0,
            'pcr': 0,
            }

        # rna pcr kanban group limit
        # Limit of PCR read capapcity multiple allowed from sample prep onwards
        self.pcr_kanban_limit = 3.0
    
        # Process priories (lower number - higher prioirity)
        self.process_priorites = {
            'sample_receipt': 45,
            'sample_prep_manual': 50,
            'sample_prep_auto': 43,
            'rna_extraction': 40,
            'pcr_prep': 35,
            'pcr': 30
            }
        
        # Process resources = tuple of different resources needed and lists of alternatives
        # Remember to put , after a single list to miantain tuple format!
        # A tuple of two or more elemnts will require resources from each tuple element
        self.process_resources = {
            'sample_receipt': {
                'process_type': 'manual',
                'human_list': (['human_sample_receipt'],),
                'machine_list': ([],)},
            'sample_prep_manual': {
                'process_type': 'manual',
                'human_list': (['human_sample_receipt']),
                'machine_list': ([],)},
            'sample_prep_auto': {
                'process_type': 'auto',
                'human_list': (['human_sample_prep'],),
                'machine_list': (['sample_prep_automation'],)},
            'rna_extraction':{
                'process_type': 'auto',
                'human_list': (['human_rna_prep'],),
                'machine_list': (['biomek'],)},
            'pcr_prep':{
                'process_type': 'auto',
                'human_list': (['human_pcr'],),
                'machine_list': (['pcr_plate_stamper'],)},
            'pcr':{
                'process_type': 'auto',
                'human_list': (['human_pcr'],),
                'machine_list': (['pcr_plate_reader'],)},
            }
        
        # Workstation (used to limit work in progress)
        
        self.process_workstations = {
            'data_analysis': ['workstation_0'],
            'batch_input': ['workstation_0'],
            'sample_receipt': ['workstation_1_man'],
            'sample_prep_manual' : ['workstation_1_man'],
            'sample_prep_auto' : ['workstation_1_auto'],
            'rna_extraction': ['workstation_2'],
            'pcr_prep': ['workstation_3'],
            'pcr': ['workstation_4']
            }


        self.workstation_capacity = {
            'workstation_0': 99999,
            'workstation_1_man': 12,
            'workstation_1_auto': 5, 
            'workstation_2': 16,
            'workstation_3': 2,
            'workstation_4': 13
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

        # Sort priority dictionary by value
        self.process_priorites = {key: value for key, value in sorted(
            self.process_priorites.items(), key=lambda item: item[1])}
        
        # Convert resource shifts to minutes, and place in new dictionary
        self.resource_shifts = dict()
        
        for resource, shift_hours in self.resource_shift_hours.items():
            start = shift_hours[0] * 60
            end = shift_hours[1] * 60
            self.resource_shifts[resource] = (start, end)
            