from sim_utils.model import Model
from sim_utils.parameters import Scenario

# Temporary run model without replication


scenario = Scenario(
    samples_per_day = 93 * 12,
    run_days = 2,
    warm_up_days = 2
)

model = Model(scenario)
model.run()
