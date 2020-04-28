import numpy as np

from sim_utils.entity import Entity


class ProcessSteps:
    """
 
    Methods
    -------

    batch_input:
        Create job batches of samples for model (not a physcial step; 
        does not need resources).
    
    collate:
        Combines multiple entities into a single (e.g. combine plates)
        Admin step that requires no time or resources.
    
    data_analysis:
        Data analysis process step. No resources currently used.
    
    fte_break:
        FTE break process step. Used for tea and coffee breaks. Breaks are
        highest priority process, but do not interupt other work.

    generate_meal_breaks:
        Generates a meal break for all human resources.
    
    generate_tea_breaks:
        Generates a tea break for all human resources.

    generate_input:
        Continuous loop of work arrival. Adds new work to batch input.

    occupy_resources_automated_subprocess:
        Obtains and occupied resources for a automated process step. Includes
        set-up and clean-down steps that also require human.

    occupy_resources_single_subprocess:
        Obtains and occupied resources for a single process step.

    
    """

    def __init__(self, _process):

        self._env = _process._env
        self._batch_id_count = _process.batch_id_count = 0
        self._count_in = _process.count_in
        self._count_out = _process.count_out
        self._id_count = _process.id_count
        self._params = _process._params
        self.queue_monitors = _process.queue_monitors
        self._queues = _process.queues
        self._resources = _process.resources
        self._resources_available = _process.resources_available
        self._resources_occupied = _process.resources_occupied
        self._workstation_assigned_jobs = _process.workstation_assigned_jobs

        self.process_step_counters = _process.process_step_counters

        self.process_step_funcs = {
            'batch_input': self.batch_input,
            'sample_receipt': self.sample_receipt,
            'sample_prep_auto': self.sample_prep_auto,
            'sample_prep_manual': self.sample_prep_manual,
            'sample_heat': self.sample_heat,
            'rna_extraction': self.rna_extraction,
            'pcr_prep': self.pcr_prep,
            'pcr': self.pcr,
            'data_analysis': self.data_analysis
        }

    def batch_input(self, workstation, job):
        """Create job batches of samples for model (not a physcial step; 
        does not need resources)."""

        orginal_batch_size = job.batch_size
        # Round batches up to complete  batches
        new_batches = int(
            np.ceil(orginal_batch_size / self._params.basic_batch_size))

        if new_batches > 1:
            for _batch in range(new_batches):
                self._id_count += 1
                entity = Entity(_env=self._env,
                                _params=self._params,
                                batch_id=job.batch_id,
                                batch_size=self._params.basic_batch_size,
                                entity_id=self._id_count,
                                entity_type='registered sample tubes',
                                last_queue='q_sample_receipt',
                                last_queue_time_in=self._env.now,
                                parent_ids=[job.entity_id],
                                time_in=job.time_in)

                # Add to sample_accesion queue
                self._queues['q_sample_receipt'].append(entity)

        self._workstation_assigned_jobs[workstation] -= 1

    def breakdown(self, resource, breakdown_time):
        """Resource breakdown. Treated like normal work."""
        with self._resources[resource].request(priority=0) as req:
            # Get resource as soon as free
            yield req
            self._resources_available[resource] -= 1
            self._resources_occupied[resource] += 1
            # Breakdown time
            yield self._env.timeout(breakdown_time)
            # Breakdown complete (repaired)
            self._resources_available[resource] += 1
            self._resources_occupied[resource] -= 1

    def check_resourse_availability(self, resources_required):
        time_of_day = self._env.now % self._params.day_duration
        number_of_recources_required = len(resources_required)
        number_of_recources_found = 0
        resources_selected = []  # names of selected resources
        # Look through all resources required
        for resource_list in resources_required:
            # Check availability of alternative resources
            for resource in resource_list:
                # Check whether time is within shift operating times
                shift = self._params.resource_shifts[resource]
                shift_available = shift[0] <= time_of_day < shift[1]
                # Check number of resources available
                if shift_available and self._resources_available[resource] > 0:
                    number_of_recources_found += 1
                    resources_selected.append(resource)
                    break

        all_resources_found = (True if number_of_recources_required ==
                                       number_of_recources_found else False)

        return (all_resources_found, resources_selected)

    def collate(self, batch_size, from_queue, to_queue):
        """ Admin step that requires no time or resources.
        Use the first entitiy form each batch for the batch id and time in."""
        while len(self._queues[from_queue]) >= batch_size:
            parent_ids = []
            new_batch_size = 0
            # Get entities to combine
            for i in range(batch_size):
                ent = self._queues[from_queue].pop()
                new_batch_size += ent.batch_size
                parent_ids.append(ent.entity_id)

                # Record queuing time
                self.record_queuing_time(
                    ent.last_queue, ent.last_queue_time_in, self._env.now)

                # Use inital batch id and time in from first entity
                if i == 0:
                    batch_id = ent.batch_id
                    time_in = ent.time_in

            # Generate new entity    
            self._id_count += 1
            new_ent = Entity(_env=self._env,
                             _params=self._params,
                             batch_id=batch_id,
                             batch_size=new_batch_size,
                             entity_id=self._id_count,
                             entity_type='collated',
                             last_queue=to_queue,
                             last_queue_time_in=self._env.now,
                             parent_ids=parent_ids,
                             time_in=time_in)
            # Add to queue
            self._queues[to_queue].append(new_ent)

    def data_analysis(self, workstation, job):
        """Data analysis process step. No resources currently used."""

        time_for_data_analysis = 0
        output_log = [job.batch_id, self._env.now, job.batch_size, job.time_in,
                      self._env.now + time_for_data_analysis]
        self._count_out.append(output_log)
        self._queues['q_completed'].append(job)
        self._workstation_assigned_jobs[workstation] -= 1

        self.record_queuing_time(
            'q_data_analysis', job.last_queue_time_in, self._env.now)

    def fte_break(self, resource, break_time):
        """FTE break process step. Used for tea and coffee breaks. Breaks are
        highest priority process, but do not interupt other work. Break is
        triggered after a random time (to spread breaks) which is set in the 
        model paramters file."""

        # Spread break starts by adding random delay over set period
        delay = np.random.uniform(0, self._params.break_start_spread)
        yield self._env.timeout(delay)

        # Get resources for break  (does not interupt work)
        with self._resources[resource].request(priority=0) as req:
            # Get resource as soon as free
            yield req
            # Break time
            self._resources_available[resource] -= 1
            self._resources_occupied[resource] += 1
            yield self._env.timeout(break_time)
            # End break
            self._resources_available[resource] += 1
            self._resources_occupied[resource] -= 1

    def generate_breakdowns(self):
        while True:
            # Loop through resources
            for resource, unavailability in \
                    self._params.resource_breakdown_unavailability.items():
                if unavailability > 0:
                    number_of_resources = self._params.resource_numbers[
                        resource]
                    number_unavailable = np.random.binomial(number_of_resources,
                                                            unavailability)
                    if number_unavailable > 0:
                        # Resources are unavailable for a day
                        time_unavailable = self._params.day_duration
                        for _i in range(number_unavailable):
                            self._env.process(
                                self.breakdown(resource, time_unavailable))

            # 1 day delay before next call        
            yield self._env.timeout(self._params.day_duration)

    def generate_meal_breaks(self, delay):
        """Generates a meal break for all human resources."""
        # Delay sets time of break in day
        yield self._env.timeout(delay)
        while True:
            # Get current time
            time_of_day = self._env.now % self._params.day_duration
            # Loop through resources
            for resource in self._params.fte_resources:
                # Only call for a break if shift activate at the time
                # Check whether time is within shift operating times
                shift = self._params.resource_shifts[resource]
                shift_available = shift[0] <= time_of_day < shift[1]
                if shift_available:
                    # Loop through numbers in each resource pool
                    for _i in range(self._params.resource_numbers[resource]):
                        # Set break duration
                        min_duration = self._params.meal_break_duration[0]
                        max_duration = self._params.meal_break_duration[1]
                        break_time = np.random.uniform(min_duration,
                                                       max_duration)
                        # Call break 
                        self._env.process(self.fte_break(resource, break_time))
                        # 1 day delay before next call
            yield self._env.timeout(self._params.day_duration)

    def generate_tea_breaks(self, delay):
        """Generates a tea break for all human resources."""

        # Delay sets time of break in day
        yield self._env.timeout(delay)
        while True:
            # Get current time
            time_of_day = self._env.now % self._params.day_duration
            # Loop through resources
            for resource in self._params.fte_resources:
                # Only call for a break if shift activate at the time
                # Check whether time is within shift operating times
                shift = self._params.resource_shifts[resource]
                shift_available = shift[0] <= time_of_day < shift[1]
                if shift_available:
                    # Loop through numbers in each resource pool
                    for _i in range(self._params.resource_numbers[resource]):
                        # Set break duration
                        min_duration = self._params.tea_break_duration[0]
                        max_duration = self._params.tea_break_duration[1]
                        break_time = np.random.uniform(min_duration,
                                                       max_duration)
                        # Call break 
                        self._env.process(self.fte_break(resource, break_time))
            # 1 day delay before next call        
            yield self._env.timeout(self._params.day_duration)

    def generate_input(self):
        """Continuous loop of work arrival. Adds new work to batch input."""
        # First delivery at start of day
        # While loop continues generating new patients throughout model run
        while True:
            # generate new entity and add to list of current entities
            self._id_count += 1
            self._batch_id_count += 1
            arrival_ent = Entity(_env=self._env,
                                 _params=self._params,
                                 batch_id=self._batch_id_count,
                                 batch_size=self._params.arrival_batch_size,
                                 entity_id=self._id_count,
                                 entity_type='arrival batch',
                                 parent_ids=[],
                                 last_queue='q_batch_input',
                                 last_queue_time_in=self._env.now,
                                 time_in=self._env.now)

            # Add to queue for batching input
            self._queues['q_batch_input'].append(arrival_ent)

            # Log input
            input_log = [self._batch_id_count, self._env.now,
                         self._params.arrival_batch_size]
            self._count_in.append(input_log)

            # Schedule next admission
            yield self._env.timeout(self._params.interarrival_time)

    def occupy_resources_automated_subprocess(self, workstation,
                                              human_resources,
                                              machine_resources,
                                              stage_process_times, priority,
                                              entity_to_create,
                                              queue_to_add_new_entity,
                                              process_step):

        """Obtains and occupied resources for a process step involving 3 steps:
            1) Machine set up (requires machine + human)
            2) Automated step (machine only)        
            3) Machine clean down (requires machine + human)
        We assume that the clean down can be done by a different human to the
        set up."""

        search_for_resources = True

        # continue looking for resources until all available
        while search_for_resources:

            # Search for macine and human resoucres
            machine_resources_found, machine_resources_selected = \
                self.check_resourse_availability(machine_resources)

            human_resources_found, human_resources_selected = \
                self.check_resourse_availability(human_resources)
            # Check both resources found
            if human_resources_found and machine_resources_found:
                # All resources are available
                search_for_resources = False
                break
            else:
                # Not all resources found wait for 1 min continue loop
                yield self._env.timeout(1)

        # Steps to take after finding all resoucres

        self.process_step_counters[process_step] += 1

        # Request resources from environment
        human_resource_requests = []
        machine_resource_requests = []

        # Adjust resource counts

        for resource in machine_resources_selected:
            self._resources_available[resource] -= 1
            self._resources_occupied[resource] += 1

        for resource in human_resources_selected:
            self._resources_available[resource] -= 1
            self._resources_occupied[resource] += 1

        # Request resources

        for resource in machine_resources_selected:
            req = self._resources[resource].request(priority=priority)
            machine_resource_requests.append((self._resources[resource], req))
            yield req

        for resource in human_resources_selected:
            req = self._resources[resource].request(priority=priority)
            human_resource_requests.append((self._resources[resource], req))
            yield req

        # Resources co-opted

        self.process_step_counters[process_step] += 1

        # Add NumPy triangular additional time
        process_time = stage_process_times[0]
        process_time *= np.random.triangular(
            1.0, 1.0, 1 + self._params.additional_time_manual)

        # All resources commited: run process
        yield self._env.timeout(process_time)

        # release human resources
        for resource, req in human_resource_requests:
            resource.release(req)

        # Release human resource counts
        for chosen_resource in human_resources_selected:
            self._resources_available[chosen_resource] += 1
            self._resources_occupied[chosen_resource] -= 1

        ########################################################################

        # Automated process time

        # Add NumPy triangular additional time
        process_time = stage_process_times[1]
        process_time *= np.random.triangular(
            1.0, 1.0, 1 + self._params.additional_time_auto)

        # All resources commited: run process
        yield self._env.timeout(process_time)

        ########################################################################

        # Clean down - require human resources again

        search_for_resources = True

        # continue looking for resources until all available
        while search_for_resources:
            # Search for humand and machien resoucres
            human_resources_found, human_resources_selected = \
                self.check_resourse_availability(human_resources)
            # Check resources found
            if human_resources_found:
                # All resources are available
                search_for_resources = False
                break
            else:
                # Not all resources found wait for 1 min continue loop
                yield self._env.timeout(1)

        # Request human resources from environment (adjust counts then request)

        human_resource_requests = []
        for resource in human_resources_selected:
            self._resources_available[resource] += 1
            self._resources_occupied[resource] -= 1

        for resource in human_resources_selected:
            req = self._resources[resource].request(priority=priority - 1)
            human_resource_requests.append((self._resources[resource], req))
            yield req

        # Add NumPy triangular additional time
        process_time = stage_process_times[2]
        process_time *= np.random.triangular(
            1.0, 1.0, 1 + self._params.additional_time_manual)

        # All resources commited: run process
        yield self._env.timeout(process_time)

        ########################################################################

        # All stages finished - release all resources

        # release human resources
        for resource, req in human_resource_requests:
            resource.release(req)

        # Release human resource counts
        for chosen_resource in human_resources_selected:
            self._resources_available[chosen_resource] += 1
            self._resources_occupied[chosen_resource] -= 1

        # release machine resources
        for resource, req in machine_resource_requests:
            resource.release(req)

        # Release machine resource counts
        for chosen_resource in machine_resources_selected:
            self._resources_available[chosen_resource] += 1
            self._resources_occupied[chosen_resource] -= 1

        # Add entitiy to queue
        entity_to_create.last_queue_time_in = self._env.now
        self._queues[queue_to_add_new_entity].append(entity_to_create)

        # Free workstation
        self._workstation_assigned_jobs[workstation] -= 1
        self.process_step_counters[process_step] -= 1

        # Reduce kanban counts as necessary
        self.reduce_kanban_counts(process_step, entity_to_create.batch_size)

    def occupy_resources_single_subprocess(self, workstation,
                                           resources_required, process_time,
                                           priority, entity_to_create,
                                           queue_to_add_new_entity,
                                           process_step):

        """Obtains and occupied resources for a single process step (e.g manual
        or semi-automated process). c.f. Multi-step process which has machine
        set up, automation, and machine clean-down. """

        search_for_resources = True

        # continue looking for resources until all available
        while search_for_resources:
            all_resources_found, resources_selected = \
                self.check_resourse_availability(resources_required)
            if all_resources_found:
                # All resources are available
                search_for_resources = False
                break
            else:
                # Not all resources found wait for 1 min continue loop
                yield self._env.timeout(1)

        # Steps to take after finding all resources

        self.process_step_counters[process_step] += 1

        # Adjust resource counts

        resource_requests = []  # resource request obejects
        for resource in resources_selected:
            self._resources_available[resource] -= 1
            self._resources_occupied[resource] += 1

        # Request resources from environment

        for resource in resources_selected:
            req = self._resources[resource].request(priority=priority)
            resource_requests.append((self._resources[resource], req))
            yield req

        # Add NumPy triangular additional time
        process_time *= np.random.triangular(
            1.0, 1.0, 1 + self._params.additional_time_manual)

        # All resources commited: run process
        yield self._env.timeout(process_time)

        # release resources
        for resource, req in resource_requests:
            resource.release(req)

        # Release resource counts
        for chosen_resource in resources_selected:
            self._resources_available[chosen_resource] += 1
            self._resources_occupied[chosen_resource] -= 1

        # Add entitiy to queue
        entity_to_create.last_queue_time_in = self._env.now
        self._queues[queue_to_add_new_entity].append(entity_to_create)

        # Free workstation
        self._workstation_assigned_jobs[workstation] -= 1
        self.process_step_counters[process_step] -= 1

        # Reduce kanban counts as necessary
        self.reduce_kanban_counts(process_step, entity_to_create.batch_size)

    def pcr(self, workstation, job):

        num_entities = 1

        # Get resources required (a tuple of lists of required alternative
        # resources)
        human_resources = self._params.process_resources['pcr']['human_list']
        machine_resources = self._params.process_resources['pcr'][
            'machine_list']

        # Process time
        process_times = self._params.process_duration['pcr']

        stage_process_times = []
        for stage in process_times:
            process_time = (stage[0] +
                            stage[1] * num_entities +
                            stage[2] * num_entities * job.batch_size)
            stage_process_times.append(process_time)

        process_priority = self._params.process_priorites['pcr']

        # Generate new entity (one output entity per job)
        self._id_count += 1

        entity = Entity(_env=self._env,
                        _params=self._params,
                        batch_id=job.batch_id,
                        batch_size=self._params.basic_batch_size * 4,
                        entity_id=self._id_count,
                        entity_type='pcr output',
                        last_queue='q_data_analysis',
                        last_queue_time_in=self._env.now,
                        parent_ids=[job.entity_id],
                        time_in=job.time_in)

        self._env.process(self.occupy_resources_automated_subprocess(
            workstation=workstation, human_resources=human_resources,
            machine_resources=machine_resources,
            stage_process_times=stage_process_times,
            priority=process_priority, entity_to_create=entity,
            queue_to_add_new_entity='q_data_analysis', process_step='pcr'))

        self.record_queuing_time(
            'q_pcr', job.last_queue_time_in, self._env.now)

    def pcr_prep(self, workstation, job):
        """Plate stamping for PCR + add reagents."""

        num_entities = 1

        # Get resources required (a tuple of list of required alternative
        # resources)
        human_resources = self._params.process_resources['pcr_prep'][
            'human_list']
        machine_resources = self._params.process_resources['pcr_prep'][
            'machine_list']

        # Process time
        process_times = self._params.process_duration['pcr_prep']

        stage_process_times = []
        for stage in process_times:
            process_time = (stage[0] +
                            stage[1] * num_entities +
                            stage[2] * num_entities * job.batch_size)
            stage_process_times.append(process_time)

        process_priority = self._params.process_priorites['pcr_prep']

        # Generate new entity (one output entity per job)
        self._id_count += 1

        entity = Entity(_env=self._env,
                        _params=self._params,
                        batch_id=job.batch_id,
                        batch_size=self._params.basic_batch_size * 4,
                        entity_id=self._id_count,
                        entity_type='plate for pcr read',
                        last_queue='q_pcr',
                        last_queue_time_in=self._env.now,
                        parent_ids=[job.entity_id],
                        time_in=job.time_in)

        self._env.process(self.occupy_resources_automated_subprocess(
            workstation=workstation, human_resources=human_resources,
            machine_resources=machine_resources,
            stage_process_times=stage_process_times,
            priority=process_priority, entity_to_create=entity,
            queue_to_add_new_entity='q_pcr', process_step='pcr_prep'))

        self.record_queuing_time(
            'q_pcr_prep', job.last_queue_time_in, self._env.now)

    def record_queuing_time(self, queue, time_in, time_out):

        """Add time entered/left queue to process queue monitors"""

        self.queue_monitors[queue].append((time_in, time_out))

    def reduce_kanban_counts(self, process, quantity):
        """Reduce quantity in kanban group if process is at end of a kanban 
        group"""
        relevant_kanban_groups = self._params.kanban_end[process]
        if len(relevant_kanban_groups) > 0:
            for kanban_group in relevant_kanban_groups:
                self._params.kanban_group_counts[kanban_group] -= quantity

    def rna_extraction(self, workstation, job):

        num_entities = 1

        # Get resources required (a tuple of list of required alternative
        # resources)
        human_resources = self._params.process_resources['rna_extraction'][
            'human_list']
        machine_resources = self._params.process_resources['rna_extraction'][
            'machine_list']

        # Process time
        process_times = self._params.process_duration['rna_extraction']

        stage_process_times = []
        for stage in process_times:
            process_time = (stage[0] +
                            stage[1] * num_entities +
                            stage[2] * num_entities * job.batch_size)
            stage_process_times.append(process_time)

        process_priority = self._params.process_priorites['rna_extraction']

        # Generate new entity (one output entity per job)
        self._id_count += 1

        entity = Entity(_env=self._env,
                        _params=self._params,
                        batch_id=job.batch_id,
                        batch_size=self._params.basic_batch_size,
                        entity_id=self._id_count,
                        entity_type='plate for pcr',
                        last_queue='q_pcr_collation',
                        last_queue_time_in=self._env.now,
                        parent_ids=[job.entity_id],
                        time_in=job.time_in)

        self._env.process(self.occupy_resources_automated_subprocess(
            workstation=workstation, human_resources=human_resources,
            machine_resources=machine_resources,
            stage_process_times=stage_process_times,
            priority=process_priority, entity_to_create=entity,
            queue_to_add_new_entity='q_pcr_collation',
            process_step='rna_extraction'))

        self.record_queuing_time(
            'q_rna_extraction', job.last_queue_time_in, self._env.now)

    def sample_heat(self, workstation, job):
        # Job is a single input entity

        num_entities = 1

        # Get resources required (a tuple of list of required alternative
        # resources)
        human_resources = self._params.process_resources['sample_heat'][
            'human_list']
        machine_resources = self._params.process_resources['sample_heat'][
            'machine_list']

        # Process time
        process_times = self._params.process_duration['sample_heat']

        stage_process_times = []
        for stage in process_times:
            process_time = (stage[0] +
                            stage[1] * num_entities +
                            stage[2] * num_entities * job.batch_size)
            stage_process_times.append(process_time)

        process_priority = self._params.process_priorites['sample_heat']

        # Generate new entity (one output entity per job)
        self._id_count += 1

        # Define entity to create
        entity = Entity(_env=self._env,
                        _params=self._params,
                        batch_id=job.batch_id,
                        batch_size=self._params.basic_batch_size,
                        entity_id=self._id_count,
                        entity_type='samples in plate for rna extraction',
                        last_queue='q_rna_collation',
                        last_queue_time_in=self._env.now,
                        parent_ids=[job.entity_id],
                        time_in=job.time_in)

        # Define queue to add new entitiy to
        self._env.process(self.occupy_resources_automated_subprocess(
            workstation=workstation, human_resources=human_resources,
            machine_resources=machine_resources,
            stage_process_times=stage_process_times,
            priority=process_priority, entity_to_create=entity,
            queue_to_add_new_entity='q_rna_collation',
            process_step='sample_heat'))

        self.record_queuing_time(
            'q_sample_heat', job.last_queue_time_in, self._env.now)

    def sample_prep_auto(self, workstation, job):
        """
        """
        # Job is a single input entity

        num_entities = 1

        # Get resources required (a tuple of list of required alternative
        # resources)
        human_resources = self._params.process_resources['sample_prep_auto'][
            'human_list']
        machine_resources = self._params.process_resources['sample_prep_auto'][
            'machine_list']

        # Process time
        process_times = self._params.process_duration['sample_prep_auto']

        stage_process_times = []
        for stage in process_times:
            process_time = (stage[0] +
                            stage[1] * num_entities +
                            stage[2] * num_entities * job.batch_size)
            stage_process_times.append(process_time)

        process_priority = self._params.process_priorites['sample_prep_auto']

        # Generate new entity (one output entity per job)
        self._id_count += 1

        # Define entity to create
        entity = Entity(_env=self._env,
                        _params=self._params,
                        batch_id=job.batch_id,
                        batch_size=self._params.basic_batch_size,
                        entity_id=self._id_count,
                        entity_type='samples in plate for rna extraction',
                        last_queue='q_sample_heat',
                        last_queue_time_in=self._env.now,
                        parent_ids=[job.entity_id],
                        time_in=job.time_in)

        # Define queue to add new entitiy to
        self._env.process(self.occupy_resources_automated_subprocess(
            workstation=workstation, human_resources=human_resources,
            machine_resources=machine_resources,
            stage_process_times=stage_process_times,
            priority=process_priority, entity_to_create=entity,
            queue_to_add_new_entity='q_sample_heat',
            process_step='sample_prep_auto'))

        self.record_queuing_time(
            'q_sample_prep', job.last_queue_time_in, self._env.now)

    def sample_prep_manual(self, workstation, job):
        """
        """

        # Job is a single input entity

        num_entities = 1

        # Get resources required (a tuple of list of required alternative
        # resources)

        resources_required = \
            self._params.process_resources['sample_prep_manual']['human_list']

        # Process time
        process_times = self._params.process_duration['sample_prep_manual'][0]

        process_time = (process_times[0] +
                        process_times[1] * num_entities +
                        process_times[2] * num_entities * job.batch_size)

        process_priority = self._params.process_priorites['sample_prep_manual']

        # Generate new entity (one output entity per job)
        self._id_count += 1

        # Define entity to create
        entity = Entity(_env=self._env,
                        _params=self._params,
                        batch_id=job.batch_id,
                        batch_size=self._params.basic_batch_size,
                        entity_id=self._id_count,
                        entity_type='samples in plate for rna extraction',
                        last_queue='q_sample_heat',
                        last_queue_time_in=self._env.now,
                        parent_ids=[job.entity_id],
                        time_in=job.time_in)

        # Define queue to add new entitiy to
        self._env.process(self.occupy_resources_single_subprocess(
            workstation=workstation, resources_required=resources_required,
            process_time=process_time, priority=process_priority,
            entity_to_create=entity, queue_to_add_new_entity='q_sample_heat',
            process_step='sample_prep_manual'))

        self.record_queuing_time(
            'q_sample_prep', job.last_queue_time_in, self._env.now)

    def sample_receipt(self, workstation, job):
        """
        Process as described:
            Takes batches of 250 samples. Log and rack into racks of samples.
            Time taken = 133 min         

        """

        # Job is a single input entity

        num_entities = 1

        # Get resources required (a tuple of list of required alternative
        # resources)
        resources_required = self._params.process_resources['sample_receipt'][
            'human_list']

        # Process time
        process_times = self._params.process_duration['sample_receipt'][0]

        process_time = (process_times[0] +
                        process_times[1] * num_entities +
                        process_times[2] * num_entities * job.batch_size)

        process_priority = self._params.process_priorites['sample_receipt']

        # Generate new entity (one output entity per job)
        self._id_count += 1

        entity = Entity(_env=self._env,
                        _params=self._params,
                        batch_id=job.batch_id,
                        batch_size=self._params.basic_batch_size,
                        entity_id=self._id_count,
                        entity_type='rack of tubes for sample prep',
                        last_queue='q_sample_prep',
                        last_queue_time_in=self._env.now,
                        parent_ids=[job.entity_id],
                        time_in=job.time_in)

        self._env.process(self.occupy_resources_single_subprocess(
            workstation=workstation, resources_required=resources_required,
            process_time=process_time, priority=process_priority,
            entity_to_create=entity, queue_to_add_new_entity='q_sample_prep',
            process_step='sample_receipt'))

        self.record_queuing_time(
            'q_sample_receipt', job.last_queue_time_in, self._env.now)
