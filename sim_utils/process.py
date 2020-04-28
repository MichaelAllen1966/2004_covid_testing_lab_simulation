from sim_utils.process_steps import ProcessSteps
from sim_utils.audit import Audit

class Process:
    """
    A collection of process steps.
    
    Parameters
    ----------
    batch_id_count: count of unique delivery batch ids (integer)
    id_count: count of unique ids (integer)
    parent_child = child ids for each parent id (dictionary)
 
    """
    
    def __init__(self, _env, _params, resources, resources_available,
                 resources_occupied, workstation_assigned_jobs):
        
        # Question: do we need a dictionary of all enitites in model?
        self._env = _env
        self._params = _params
        self.batch_id_count = 0
        self.parent_child = dict()
        self.id_count = 0
        self.count_in = []
        self.count_out = []
        self.resources = resources
        self.resources_available = resources_available
        self.resources_occupied = resources_occupied
        self.workstation_assigned_jobs = workstation_assigned_jobs
        
        # Queues for assignment
        self.queues = {
            'q_batch_input': [],
            'q_sample_receipt': [],
            'q_sample_prep': [],
            'q_sample_heat': [],
            'q_rna_collation': [],
            'q_rna_extraction': [],
            'q_pcr_collation': [],
            'q_pcr_prep': [],
            'q_pcr': [],
            'q_data_analysis': [],
            'q_completed': []          
            }
            
        # Queue monitor (lists of time/time out tuples)
        self.queue_monitors = {
            'q_sample_receipt': [],
            'q_sample_prep': [],
            'q_sample_heat': [],
            'q_rna_collation': [],
            'q_rna_extraction': [],
            'q_pcr_collation': [],
            'q_pcr_prep': [],
            'q_pcr': [],
            'q_data_analysis': []      
            }
 
        # Process step counters
        self.process_step_counters = {
            'sample_receipt': 0,
            'sample_prep_manual': 0,
            'sample_prep_auto': 0,
            'sample_heat': 0,
            'rna_extraction': 0,
            'pcr_prep': 0,
            'pcr': 0,
            'data_analysis': 0
            }

        # Link from process priorities to process assign calls
        self.process_assign_calls = {
            'pcr': self.assign_pcr,
            'pcr_prep': self.assign_pcr_prep,
            'rna_extraction': self.assign_rna_extraction,
            'sample_heat': self.assign_sample_heat,
            'sample_prep_auto': self.assign_sample_prep,
            'sample_prep_manual': self.assign_sample_prep,
            'sample_receipt': self.assign_sample_receipt
            }
                 
        
    def assign(self, queue, process):
        
        process_func = self.process_steps.process_step_funcs[process]
        # Assign sample_receipts
        new_unallocated_queue = []
       
        while (len(self.queues[queue]) > 0):
            # Check kanban limits 
            job_size = self.queues[queue][-1].batch_size
            relevant_kanban_groups = self._params.kanban_start[process]
            if len(relevant_kanban_groups) > 0:
                # Check any relavant kanban group limits are OK
                all_kanban_limts_ok = True
                for kanban_group in relevant_kanban_groups:
                    current_kanban_count = \
                        self._params.kanban_group_counts[kanban_group]
                    kanban_capacity = \
                        self._params.kanban_group_max[kanban_group]
                    spare_kanban_capacity = \
                        kanban_capacity - current_kanban_count
                    if spare_kanban_capacity < job_size:
                        all_kanban_limts_ok = False
                # if at least one kanban limit breached break loop
                if all_kanban_limts_ok == False:
                    # End assign loop
                    break
                else:
                    # Adjust kanban group counts
                    for kanban_group in relevant_kanban_groups:
                        self._params.kanban_group_counts[kanban_group] += \
                            job_size
            
            # All relevant kanban limits OK -  proceed to assign job
            job = self.queues[queue].pop()
            workstation = self.indentify_workstation(process)
            if workstation != 'none':
                # Allocate job to sample_receipt process
                process_func(workstation, job)
                self.workstation_assigned_jobs[workstation] += 1
            else: 
                # Process workstations full, move all remaining jobs to
                # unallocated job queue
                new_unallocated_queue = [job] + self.queues[queue]
                self.queues[queue] = []
                
        self.queues[queue] = new_unallocated_queue
        
    def assign_analysis(self):
        # pass any new input to process_step.batch_input
        q = 'q_data_analysis'; process = 'data_analysis'
        self.assign(q, process)    
    
    def assign_batch_input(self):
        # pass any new input to process_step.batch_input
        q = 'q_batch_input'
        process = 'batch_input'
        self.assign(q, process)
        
    def assign_pcr_prep(self, time_of_day, time_left):
        shift = self._params.process_start_hours['pcr_prep']
        if shift[0] * 60 <= time_of_day <= shift[1] * 60:
            q = 'q_pcr_prep'
            process = 'pcr_prep'
            self.assign(q, process)
        
    def assign_pcr(self, time_of_day, time_left):
        shift = self._params.process_start_hours['pcr']
        if shift[0] * 60 <= time_of_day <= shift[1] * 60:
            q = 'q_pcr'
            process = 'pcr'
            self.assign(q, process)
        
    def assign_rna_extraction(self, time_of_day, time_left):
        shift = self._params.process_start_hours['rna_extraction']
        if shift[0] * 60 <= time_of_day <= shift[1] * 60:
            # Assign sample_receipts
            q = 'q_rna_extraction'
            process = 'rna_extraction'
            self.assign(q, process)
            
    def assign_sample_heat(self, time_of_day, time_left):
        shift = self._params.process_start_hours['sample_heat']
        if shift[0] * 60 <= time_of_day <= shift[1] * 60:
            # Assign sample_receipts
            q = 'q_sample_heat'; process = 'sample_heat'
            self.assign(q, process)
        

    def assign_sample_receipt(self, time_of_day, time_left):
        shift = self._params.process_start_hours['sample_receipt']
        if shift[0] * 60 <= time_of_day <= shift[1] * 60:
                # Assign sample_receipts
                q = 'q_sample_receipt'
                process = 'sample_receipt'
                self.assign(q, process)
        
    def assign_sample_prep(self, time_of_day, time_left):
        shift = self._params.process_start_hours['sample_prep']
        if shift[0] * 60 <= time_of_day <= shift[1] * 60:            
            q = 'q_sample_prep'
            process = 'sample_prep_auto'
            self.assign(q, process)
            
            #Also use manual process if allowed
            if self._params.allow_maual_sample_prep:
                q = 'q_sample_prep'
                process = 'sample_prep_manual'
                self.assign(q, process)
            

    def collate_for_pcr(self):
        # Takes 2 plates from RNA extraction and combines to one for PCR
        self.process_steps.collate(2, 'q_pcr_collation', 'q_pcr_prep')
        
    def collate_for_rna_extraction(self):
        # Process two plates for RNA extraction
        self.process_steps.collate(2, 'q_rna_collation', 'q_rna_extraction')

    def control_process(self):
        yield self._env.timeout(5)
        while True:
            # Assign jobs from later -> earlier (enhances flow)

            time_of_day = self._env.now % self._params.day_duration
            time_left = self._params.day_duration - time_of_day
            
            # Model admin jobs (no resources needed)
            self.assign_batch_input()
            self.assign_analysis()
            self.collate_for_rna_extraction()
            self.collate_for_pcr()
            
            for key, _ in self._params.process_priorites.items():
                self.process_assign_calls[key](time_of_day, time_left)
                    
            # Time before next control loop
            yield self._env.timeout(1.0)
           
    
    def display_day(self):
        while True:
            print (f'\r>> Day {int(self._env.now/self._params.day_duration)}',
                   end='')
            yield self._env.timeout(self._params.day_duration)
            
    def end_run_routine(self):
        self.audit.summarise_in_out()
        self.audit.summarise_resources_with_shifts()
        self.audit.summarise_queues()
        self.audit.summarise_queue_times()
        self.audit.summarise_trackers()
        
       
            
    def indentify_workstation(self, process):
        """
        Loops through workstations that can perform a process. Looks for 
        workstation with greatest remaining capacity. If no workstation has
        capapcity, returns 'none'
        """
        
        selected_workstation = 'none'
        best_remaining_capacity = 0
        
        workstations = self._params.process_workstations[process]
        for workstation in workstations:
            workstation_capacity = \
                self._params.workstation_capacity[workstation]
            workstation_assigned = self.workstation_assigned_jobs[workstation]
            remaining_capacity = workstation_capacity - workstation_assigned
            if remaining_capacity > best_remaining_capacity:
                best_remaining_capacity = remaining_capacity
                selected_workstation = workstation
        
        return selected_workstation
    

    def set_up_audit(self):
        self.audit = Audit(self)
     
        
    def set_up_breaks(self):
        if len(self._params.meal_break_times) > 0:
            for meal_break in self._params.meal_break_times:
                self._env.process(
                    self.process_steps.generate_meal_breaks(meal_break))
        if len(self._params.tea_break_times) > 0:
            for tea_break in self._params.tea_break_times:
                self._env.process(
                    self.process_steps.generate_tea_breaks(tea_break))
            
    def set_up_process_steps(self):
        self.process_steps = ProcessSteps(self)