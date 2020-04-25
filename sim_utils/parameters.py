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
        self.basic_batch_size = 93

        # Day and run parameters
        # 16/4/2020 Model is designed to run primarily in single days
        self.day_duration = 1440
        self.run_days = 1
        self.warm_up_days = 0
        
        # Breaks for people (high prority job, but does not interupt work)
        # Times from start of FTE day (6am)
        self.tea_break_times = [2*60, 7*60, 12*60, 16*60]
        self.meal_break_times = [4*60, 14*60]
        # Spread start of break for people randomly after set start times
        self.break_start_spread = 60
                
        # break duration is a uniform distribution between min and max
        self.tea_break_duration = [25, 35]
        self.meal_break_duration = [40, 50]
        
        # Audit parameters
        self.audit_interval = 15

        # Resource numbers        
        self.resource_numbers = {
            'human_sample_receipt_1': 30,
            'human_sample_receipt_2': 10,
            'human_sample_prep_1': 35,
            'human_sample_prep_2': 22,
            'human_rna_prep_1': 10,
            'human_rna_prep_2': 10,
            'human_pcr_1': 35,
            'human_pcr_2': 25,
            'sample_heat_block': 15,
            'beckman_rna_extraction': 28,
            'pcr_plate_stamper': 9,
            'pcr_plate_reader': 15,
            'sample_prep_automation': 5
            }
        
        self.workstation_capacity =  {
            'workstation_0': 9999,
            'workstation_1a': 21,
            'workstation_1b_man': 25,
            'workstation_1b_auto': 5, 
            'workstation_1c': 15, 
            'workstation_2': 26,
            'workstation_3': 9,
            'workstation_4': 15
            }

        # Resource available hours (use hours)
        self.resource_shift_hours = {
            'human_sample_receipt_1': (0.30, 9.00),
            'human_sample_receipt_2': (9.01, 17.75),
            'human_sample_prep_1': (0.30, 9.00),
            'human_sample_prep_2': (9.01, 17.75),
            'human_rna_prep_1': (0.30, 9.00),
            'human_rna_prep_2': (9.01, 17.75),
            'human_pcr_1': (0.30, 9.00),
            'human_pcr_2': (9.01, 17.75),
            'sample_heat_block': (0.0, 24.0),
            'beckman_rna_extraction': (0.0, 24.0),
            'pcr_plate_stamper': (0.0, 24.0),
            'pcr_plate_reader': (0.0, 24.0),
            'sample_prep_automation': (0.0, 24.0)
            }

        
        # Resource unavailability on any whole day due to breakdown
        self.resource_breakdown_unavailability = {
            'human_sample_receipt_1': 0,
            'human_sample_receipt_2': 0,
            'human_sample_prep_1': 0,
            'human_sample_prep_2': 0,
            'human_rna_prep_1': 0,
            'human_rna_prep_2': 0,
            'human_pcr_1': 0,
            'human_pcr_2': 0,
            'sample_heat_block': 0,
            'beckman_rna_extraction': 0.04,
            'pcr_plate_stamper': 0.08,
            'pcr_plate_reader': 0.02,
            'sample_prep_automation': 0
            }
        
        # FTE resources (these will take breaks!)
        self.fte_resources = [
            'human_sample_receipt_1',
            'human_sample_receipt_2',
            'human_rna_prep_1',
            'human_rna_prep_2',
            'human_pcr_1',
            'human_pcr_2',
            ]

        
        # Process duration. Tuple of fixed time, time per entity, and time per item in entity.
        # Multi-step automated processes have three sets of times (set up, automated, clean down)
        self.process_duration = {
             'batch_input': ([0,0,0],),
             'sample_receipt': ([33, 0, 0],),
             'sample_prep_manual': ([51, 0, 0],),
             'sample_prep_auto': ([25, 0, 0], [6, 0, 0], [6, 0, 0]),
             'sample_heat':  ([2, 0, 0], [20, 0, 0], [2, 0, 0]),
             'rna_extraction': ([12.5,0,0],[77,0,0],[2,0,0]),
             'pcr_prep': ([45,0,0],[5,0,0],[4,0,0]),
             'pcr': ([5,0,0],[90,0,0],[5,0,0]),
             'data_analysis': ([0,0,0],)
             }
        
        self.allow_maual_sample_prep = False
        
        # Add a triangular distribution of extra time per prcoess
        # Average extra time with be 1/4 of this (e.g. 0.25 = 6.25% added length on average)       
        self.additional_time_manual = 0.25
        self.additional_time_auto = 0.10
                
        # Range of times new jobs may start
        self.process_start_hours = {
            'sample_receipt': (0.3, 15.5),
            'sample_prep': (0.3, 15.5),
            'sample_heat': (0.3, 15.5),
            'rna_extraction': (0.3, 24),
            'pcr_prep': (0.3, 24),
            'pcr': (0.3, 24)
            }

        # Process priories (lower number - higher prioirity)
        self.process_priorites = {
            'sample_receipt': 100,
            'sample_prep_manual': 80,
            'sample_prep_auto': 70,
            'sample_heat': 60,
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
                'human_list': (['human_sample_receipt_1',
                                'human_sample_receipt_2'],),
                'machine_list': ([],)},
            
            'sample_prep_manual': {
                'process_type': 'manual',
                'human_list': (['human_sample_prep_1',
                                'human_sample_prep_2'],
                               ['human_pcr_1',
                                'human_pcr_2',
                                'human_rna_prep_1',
                                'human_rna_prep_2',
                                'human_sample_receipt_1', 
                                'human_sample_receipt_2']),
                'machine_list': ([],)},
            
            'sample_prep_auto': {
                'process_type': 'auto',
                'human_list': (['human_sample_prep_1',
                                'human_sample_prep_2'],),
                'machine_list': (['sample_prep_automation'],)},
            
            'sample_heat': {
                'process_type': 'auto',
                'human_list': (['human_sample_prep_1',
                                'human_sample_prep_2'],),
                'machine_list': (['sample_heat_block'],)},
            
            'rna_extraction':{
                'process_type': 'auto',
                'human_list': (['human_rna_prep_1',
                                'human_rna_prep_2'],),
                'machine_list': (['beckman_rna_extraction'],)},
          
            'pcr_prep':{
                'process_type': 'auto',
                'human_list': (['human_pcr_1',
                                'human_pcr_2'],),
                'machine_list': (['pcr_plate_stamper'],)},
          
            'pcr':{
                'process_type': 'auto',
                'human_list': (['human_pcr_1',
                                'human_pcr_2'],),
                'machine_list': (['pcr_plate_reader'],)},
            }
        
        # Workstation (used to limit work in progress)
        
        self.process_workstations = {
            'data_analysis': ['workstation_0'],
            'batch_input': ['workstation_0'],
            'sample_receipt': ['workstation_1a'],
            'sample_prep_manual' : ['workstation_1b_man'],
            'sample_prep_auto' : ['workstation_1b_auto'],
            'sample_heat': ['workstation_1c'],
            'rna_extraction': ['workstation_2'],
            'pcr_prep': ['workstation_3'],
            'pcr': ['workstation_4']
            }


        # kanban groups have start process, end process, max samples, current samples
        self.kanban_groups = {
            0: ['rna_extraction', 
                'pcr', 
                self.resource_numbers['pcr_plate_reader'] * 372 * 999]
                }
        
        #self.kanban_groups = {}


        # Overwrite default values
        
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        
        for key in kwargs:
            setattr(self, key, kwargs[key])
            
        # Calculations
        
        # Set arrival batch size and round (down) to nearest basic batch size
        self.arrival_batch_size = self.samples_per_day / self.deliveries_per_day
        self.arrival_batch_size = np.floor(
            self.arrival_batch_size / self.basic_batch_size) * self.basic_batch_size
        
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

        # Set up kanban group counts and dictionaries for start.end
        self.kanban_group_counts = dict()
        self.kanban_group_max = dict()
        self.kanban_start = dict()
        self.kanban_end = dict()
        
        # Set up dictionaries based on process
        for key in self.process_duration.keys():
            self.kanban_start[key] = []
            self.kanban_end[key] = []

        # Update dictionaries if kanban groups exist        
        if len(self.kanban_groups) > 0:
            
            # Add process start and ends to dictionaries
            for key, value in self.kanban_groups.items():
                self.kanban_start[value[0]].append(key)
                self.kanban_end[value[1]].append(key)
            
            # Set up kanban group counts
            for key, value in self.kanban_groups.items():
                self.kanban_group_counts[key] = 0
                self.kanban_group_max[key] = value[2]