class Entity(object):
    """
    Entities (widgets, people, etc) handled by the simulation
    
    Attributes
    ----------
    _env: Refernce to SimPy environment object
    _params: Reference to model paraemters
    batch_size: Quantitity of items in entitiy (float)
    entity_id: Entity ID number (int)
    entity_type: Description of entity (string)
    parent_ids: IDs of parent entity (list)
    process_step: Used to track process (int)
    
    Methods
    -------
    __init__
        Constructor method
    
    
    """
    
 
    
    def __init__(self,
                 _env,
                 _params,
                 batch_id = 0,
                 batch_size = 1,
                 entity_id = 0,
                 entity_type = 'generic',
                 last_queue = '',
                 last_queue_time_in = 0,
                 parent_ids = [],
                 process_step = 0,
                 time_in = 0,
                 time_out = 0
                 ):
        
        """
        Constructor method for entitiy

        Paramters
        ---------
        _env : SimPy environment object
            Reference tp SimPy environment object
        _params: Model parameters object
            Reference to model paraemters
        batch_id : int
            id of delivery batch
        batch_size : float
            Batch size (may be units or continuous variable, e.g. weight).
        entity_id : integer
            Entity ID
        entity_type: string 
            Description of entity
        last_queue: string
            Name of last queue entered
        last_queue_time_in: float
            Time entered last queue
        parent_ids : list
            List of any parent entities
        process_step : int
            Used to track process

        Returns
        -------
        None.

        """
        
        self._env = _env
        self._params = _params
        self.batch_id = batch_id
        self.batch_size = batch_size
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.last_queue = last_queue
        self.last_queue_time_in = last_queue_time_in
        self.parent_ids = parent_ids
        self.time_in = time_in
        self.time_out = time_out