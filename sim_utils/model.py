import simpy
from sim_utils.process import Process


class Model(object):
    """
    Model class for SimPy model. Initiates and runs a single instance of a
    model.
    
    Attributes
    ----------
    _env: SimPy environment (object)
    _params: Model parameters (object)
    entities: List of all entities currently in model
    resources: Dictionary of resource objects, and numbers in model (dictionary)
    resources_available: Current resources available (dictionary)
    resources_occupied: Current resources occupied (dictionary)
    workstation_assigned_jobs: Count of assigned jobs (dictionary)
    workstation_queued_jobs: Count of queued jobs (dictionary)
    
    Methods
    -------
    __init__
        Constructor method (sets up SimPy environment)
    

    """
    
    
    def __init__(self, _params):
        """
         Constructor method for SimPy model obejct.
        """
        
        self._env = simpy.Environment()
        self._params = _params
        self.entities = []
        self.resources = dict()
        self.resources_available = dict()
        self.resources_occupied = dict()
        self.workstation_assigned_jobs = dict()
        
   
    def run(self):
        """
        Initiate model:
            
            * Set up resources
            * Set up workstations
            * Set up starting processes
            * Run model        
        """
        
        # Set up resources and workstations        
        self.set_up_resources()
        self.set_up_workstations()
    
        # Set up processes and audit
        self.set_up_process()
        self.process.set_up_process_steps()
        self.process.set_up_audit()
        
            
        # Initialise processes that will run on model run
        self._env.process(self.process.process_steps.generate_breakdowns())
        self._env.process(self.process.control_process())
        self._env.process(self.process.display_day())
        self._env.process(self.process.audit.run_audit())
        self.process.set_up_breaks()
        for delivery_time in self._params.delivery_times:
            self._env.process(self.process.process_steps.generate_input(
                delivery_time))

        # Run
        self._env.run(self._params.run_length)
        
        # End of run
        self.process.end_run_routine()        
        
        
    def set_up_process(self):
        self.process = Process(self._env, 
                               self._params, 
                               self.resources,
                               self.resources_available,
                               self.resources_occupied, 
                               self.workstation_assigned_jobs)

    
    def set_up_resources(self):
        """
        Set up:
        self.resources: A dictionary of resource objects
        self.resources_available: A dictionary of count of resources available
        self.resources_occupied: A dictionary of count of resources occupied
        """
        # Set up resources
        for key, value in self._params.resource_numbers.items():
            # Store resource objects in a dictionary
            # Set up dictionaries of available and occupied
            self.resources_available[key] = value
            self.resources_occupied[key] = 0
            if value > 0:
                self.resources[key] = simpy.PriorityResource(
                    self._env, capacity=value)

            
            
    def set_up_workstations(self):
        """
        Set up dictionaries for counts of assigned jobs and queued jobs for each
        workstation. """
        for key, _ in self._params.workstation_capacity.items():
            self.workstation_assigned_jobs[key] = 0