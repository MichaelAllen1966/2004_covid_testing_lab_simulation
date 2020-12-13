from sim_utils.replication import Replicator
from sim_utils.parameters import Scenario


# Name & define all scenarios (set parameters that differ from defaults in 
# sim_utils/parameters.py)

# Set up a dictionary to hold scenarios
scenarios = {}

# Name & define all scenarios 
# Set parameters that differ from defaults in sim_utils/parameters_[date].py
# Note: Resource shifts are in hours and fractions of hours. e.g. 14.5 is 2.30pm

# Baseline scenario (model defaults)
# Deliveries may be Singl, Even, or Dist

scenarios['test'] = Scenario(
    delivery_schedule_name='Custom'
)

# Set up and call replicator
replications = 30
replications = Replicator(scenarios, replications)
replications.run_scenarios()
