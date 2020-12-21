import pandas as pd
import queue
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

        self._env = _env
        self._params = _params
        self.batch_id_count = 0
        self.parent_child = dict()
        self.id_count = 0
        self.fte_on_break = [0]
        self.count_in = []
        self.count_out = []
        self.resources = resources
        self.resources_available = resources_available
        self.resources_occupied = resources_occupied
        self.workstation_assigned_jobs = workstation_assigned_jobs

        # Queues for assignment
        self.queues = {
            'q_batch_input': queue.PriorityQueue(),
            'q_completed': queue.PriorityQueue(),
            'q_data_analysis': queue.PriorityQueue(),
            'q_heat': queue.PriorityQueue(),
            'q_heat_collation': queue.PriorityQueue(),
            'q_heat_split': queue.PriorityQueue(),
            'q_pcr': queue.PriorityQueue(),
            'q_pcr_collation': queue.PriorityQueue(),
            'q_pcr_prep': queue.PriorityQueue(),
            'q_rna_collation': queue.PriorityQueue(),
            'q_rna_extraction': queue.PriorityQueue(),
            'q_rna_extraction_split': queue.PriorityQueue(),
            'q_sample_receipt': queue.PriorityQueue(),
            'q_sample_prep': queue.PriorityQueue(),
            'q_transfer_1': queue.PriorityQueue(),
            'q_transfer_1_collation': queue.PriorityQueue(),
            'q_transfer_1_split': queue.PriorityQueue(),
        }

        # Queue monitor (lists of time/time out tuples)
        self.queue_monitors = {
            'q_data_analysis': [],
            'q_heat': [],
            'q_heat_collation': [],
            'q_heat_split': [],
            'q_pcr': [],
            'q_pcr_collation': [],
            'q_pcr_prep': [],
            'q_rna_collation': [],
            'q_rna_extraction': [],
            'q_rna_extraction_split': [],
            'q_sample_prep': [],
            'q_sample_receipt': [],
            'q_transfer_1': [],
            'q_transfer_1_collation': [],
            'q_transfer_1_split': []
        }

        # Process step counters
        self.process_step_counters = {
            'data_analysis': 0,
            'pcr': 0,
            'pcr_prep': 0,
            'rna_extraction': 0,
            'sample_heat': 0,
            'sample_prep_auto': 0,
            'sample_prep_manual': 0,
            'sample_receipt': 0,
            'transfer_1': 0
        }

        # Link from process priorities to process assign calls
        self.process_assign_calls = {
            'data_analysis': self.assign_analysis,
            'pcr': self.assign_pcr,
            'pcr_prep': self.assign_pcr_prep,
            'rna_extraction': self.assign_rna_extraction,
            'sample_heat': self.assign_sample_heat,
            'sample_prep_auto': self.assign_sample_prep,
            'sample_prep_manual': self.assign_sample_prep,
            'sample_receipt': self.assign_sample_receipt,
            'transfer_1': self.assign_transfer_1
        }

    def assign(self, queue, process):

        # Check process intervals
        interval = (self._params.process_intervals[process] if process in
                                                               self._params.process_intervals else 1)
        if int(self._env.now) % interval != 0:
            return

        process_func = self.process_steps.process_step_funcs[process]
        # Assign sample_receipts
        new_unallocated_queue = []

        while not self.queues[queue].empty():
            # Check kanban limits
            # Get job size by getting next item, inspecting and replacing
            priority, next_job = self.queues[queue].get()
            job_size = next_job.batch_size
            self.queues[queue].put((priority, next_job))
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
            job = self.queues[queue].get()[1]
            workstation = self.identify_workstation(process)
            if workstation != 'none':
                process_func(workstation, job)
                self.workstation_assigned_jobs[workstation] += 1
            else:
                # Process workstations full, replace job and stop loop
                item = (job.priority, job)
                self.queues[queue].put(item)
                break

    def assign_analysis(self, time_of_day, time_left):
        # pass any new input to process_step.batch_input
        shift = self._params.process_start_hours['data_analysis']
        if shift[0] * 60 <= time_of_day <= shift[1] * 60:
            q = 'q_data_analysis'
            process = 'data_analysis'
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
            q = 'q_heat'
            process = 'sample_heat'
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

            # Also use manual process if allowed
            if self._params.allow_manual_sample_prep:
                q = 'q_sample_prep'
                process = 'sample_prep_manual'
                self.assign(q, process)

    def assign_transfer_1(self, time_of_day, time_left):
        shift = self._params.process_start_hours['transfer_1']
        if shift[0] * 60 <= time_of_day <= shift[1] * 60:
            q = 'q_transfer_1'
            process = 'transfer_1'
            self.assign(q, process)

    def collate_for_heat(self):
        # Takes plates from sample receipt (will be split after)
        self.process_steps.collate(self._params.heat_batch_size,
                                   'q_heat_collation', 'q_heat')

    def collate_for_pcr(self):
        # Takes 4 plates from RNA extraction
        self.process_steps.collate(4, 'q_pcr_collation', 'q_pcr_prep')

    def collate_for_rna_extraction(self):
        # Process multiple plates for RNA extraction (will be split after)
        self.process_steps.collate(self._params.rna_extraction_batch_size,
                                   'q_rna_collation', 'q_rna_extraction')

    def collate_for_transfer_1(self):
        # Process multiple plates for RNA extraction (will be split after)
        self.process_steps.collate(self._params.transfer_1_batch_size,
                                   'q_transfer_1_collation', 'q_transfer_1')

    def control_process(self):
        yield self._env.timeout(5)
        while True:
            # Assign jobs from later -> earlier (enhances flow)

            time_of_day = self._env.now % self._params.day_duration
            time_left = self._params.day_duration - time_of_day

            # Model admin jobs (no resources needed)
            self.assign_batch_input()
            self.collate_for_pcr()
            self.collate_for_rna_extraction()
            self.split_after_rna_extraction()
            self.collate_for_transfer_1()
            self.split_after_transfer_1()
            self.collate_for_heat()
            self.split_after_heat()

            for key in self._params.process_priorities.keys():
                self.process_assign_calls[key](time_of_day, time_left)

            # Time before next control loop
            yield self._env.timeout(1.0)

    def display_day(self):
        while True:
            print(f'\r>> Day {int(self._env.now / self._params.day_duration)}',
                  end='')
            yield self._env.timeout(self._params.day_duration)

    def end_run_routine(self):
        self.audit.summarise_in_out()
        self.audit.summarise_resources_with_shifts()
        self.audit.summarise_queues()
        self.audit.summarise_queue_times()
        self.audit.summarise_trackers()
        self.process_completed()

    def identify_workstation(self, process):
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

    def process_completed(self):

        processed_entities = []

        keys = [
            'time_in',
            'sample_receipt_in',
            'sample_receipt_out',
            'sample_prep_auto_in',
            'sample_prep_auto_out',
            'sample_prep_manual_in',
            'sample_prep_manual_out',
            'sample_heat_in',
            'sample_heat_out',
            'rna_extraction_in',
            'rna_extraction_out',
            'pcr_prep_in',
            'pcr_prep_out',
            'pcr_in',
            'pcr_out',
            'data_analysis_in',
            'data_analysis_out'
        ]

        # Calculate time from time in
        while not self.process_steps._queues['q_completed'].empty():
            ent = self.process_steps._queues['q_completed'].get()[1]
            new_ent = dict()
            for key in keys:
                try:
                    new_ent[key] = ent.time_stamps[key] - ent.time_stamps['time_in']
                except:
                    new_ent[key] = None
            # Add back original time in
            new_ent['time_in'] = ent.time_stamps['time_in']
            new_ent['priority'] = int(ent.priority/100) + 1
            processed_entities.append(new_ent)

        keys.append('priority')
        self.time_stamp_df = pd.DataFrame(processed_entities, columns=keys)

        # Get median values for key time points
        fields = ['sample_receipt_in', 'sample_receipt_out',
                  'sample_prep_auto_in', 'sample_prep_auto_out',
                  'sample_prep_manual_in', 'sample_prep_manual_out',
                  'sample_heat_in', 'sample_heat_out',
                  'rna_extraction_in', 'rna_extraction_out',
                  'pcr_prep_in', 'pcr_prep_out',
                  'pcr_in', 'pcr_out',
                  'data_analysis_in', 'data_analysis_out']

        # Restrict time stamps to after warm up
        cutoff = self._params.day_duration * self._params.warm_up_days
        mask = self.time_stamp_df['time_in'] >= cutoff
        self.time_stamp_df = self.time_stamp_df[mask]

        # Get summary
        df_summary = self.time_stamp_df.describe().T['50%']
        df_summary = df_summary.loc[fields]
        df_summary = df_summary.round(0)
        df_summary.rename('median', inplace=True)
        self.audit.time_stamp_medians = df_summary

        # Get medians and 95 percentiles by priority
        medians = self.time_stamp_df.groupby(['priority']).median()
        medians = medians[fields].T.round(0)
        medians['process'] = medians.index
        medians = medians.melt(id_vars='process')
        medians.set_index('process', inplace=True)
        self.audit.time_stamp_by_priority_pct_50 = medians

        pct_95 = self.time_stamp_df.groupby(['priority']).quantile(0.95)
        pct_95 = pct_95[fields].T.round(0)
        pct_95['process'] = pct_95.index
        pct_95 = pct_95.melt(id_vars='process')
        pct_95.set_index('process', inplace=True)
        self.audit.time_stamp_by_priority_pct_95 = pct_95

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

    def split_after_heat(self):
        self.process_steps.split(
            self._params.heat_batch_size,
            'q_heat_split', 'q_transfer_1_collation')

    def split_after_rna_extraction(self):
        self.process_steps.split(self._params.rna_extraction_batch_size,
                                 'q_rna_extraction_split', 'q_pcr_collation')

    def split_after_transfer_1(self):
        self.process_steps.split(self._params.transfer_1_batch_size,
                                 'q_transfer_1_split', 'q_rna_collation')
