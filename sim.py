from sim_utils.model import Model
from sim_utils.parameters import Scenario

# Temporary run model without replication


scenario = Scenario(run_days = 10)

model = Model(scenario)
model.run()
