import inspect
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sim_utils.helper_functions import expand_multi_index
from sim_utils.model import Model


class Replicator:
    
    def __init__(self, scenarios, replications):
        
        self.replications = replications
        self.scenarios = scenarios
        
        # Set up DataFrames for all trials results
        self.summary_output = pd.DataFrame()
        self.summary_output_by_day = pd.DataFrame()
        self.summary_queue_times = pd.DataFrame()
        self.summary_resources = pd.DataFrame()
        self.summary_max_queues = pd.DataFrame()
        self.output_pivot = pd.DataFrame()
        self.resources_pivot = pd.DataFrame()
        
            
    def pivot_results(self):  

        def percentile_95(g):
            """Function for percentiles in pandas picot table"""
            return np.percentile(g, 95)
        
        
        # Output summary
        df = self.summary_output.copy()
        df['result_type'] = df.index
         
        pivot = df.pivot_table(
            index = ['result_type', 'name'],
            values = ['Result'],
            aggfunc = [np.min, np.mean, np.median, np.max],
            margins=False)
        
        pivot.rename(columns={'amin': 'min', 'amax': 'max'}, inplace=True)
        self.output_pivot = pivot
        
        # resource results
        df = self.summary_resources.copy()
        cols = list(df)
        cols.remove('run')
        df['resource'] = df.index
        
        # Ensure all data is is a form for aggregation
        df = df.convert_dtypes()
                
        self.resources_pivot = df.pivot_table(
            index = ['resource', 'name'],
            values = ['Used', 'Available', 'Utilisation'],
            aggfunc = [np.median],
            margins=False)
        self.resources_pivot = self.resources_pivot['median']
                
        # Queue time results
        
        df = self.summary_queue_times.copy()
         
        self.queue_times_pivot = df.pivot_table(
            index = ['queue', 'name'],
            values = ['min', '1Q', 'median', '3Q', '95_percent', 'max'],
            aggfunc = [np.median],
            margins=False)
        self.queue_times_pivot = self.queue_times_pivot['median']
        
        # Maxmium queue sizes
        
        # Max queue summary summary
        df = self.summary_max_queues.copy()
        df['queue'] = df.index
        df = df.round(0)
        self.max_queue_pivot = df.pivot_table(
            index = ['queue', 'name'],
            values = [0],
            aggfunc = [np.max, percentile_95],
            margins=False)
        self.max_queue_pivot.rename(columns={0:'Max samples'},inplace=True)
        rows_to_drop = ['q_batch_input', 'q_completed']
        self.max_queue_pivot.drop(rows_to_drop, inplace=True)
        
   
 
    def print_results(self):
                
        print('\nOutput results')
        print('--------------')
        print(self.output_pivot)
        print('\n\n')
        print('Resources used')
        print('--------------')
        print(self.resources_pivot)
        print('\n\n')
        print('Queuing times')
        print('-------------')
        print(self.queue_times_pivot[['median', 'max']])
        print('\n\n')
        print('Max samples queuing')
        print('-------------------')
        print('Results describe maximum queueing across runs')
        print(self.max_queue_pivot)
        

    def run_scenarios(self):
        
        # Run all scenarios
        scenario_count = len(self.scenarios)
        counter = 0
        for name, scenario in self.scenarios.items():
            counter += 1
            print(f'\r>> Running scenario {counter} of {scenario_count}', end='')
            scenario_output = self.run_trial(scenario)
            self.unpack_trial_results(name, scenario_output)
        
        # Clear progress output
        clear_line = '\r' + " " * 79
        print(clear_line, end = '')
        
        # Pivot results
        self.pivot_results()
        
        # Print results
        self.print_results()
        
        # save results
        self.save_results()
        
        
    
    def run_trial(self, scenario):
        trial_output = Parallel(n_jobs=-1)(delayed(self.single_run)(scenario, i) 
                for i in range(self.replications))
        
        return trial_output
        
    
    def save_results(self):
        
        self.summary_output.to_csv('./output/output.csv')
        self.summary_output_by_day.to_csv('./output/output_by_day.csv')
        self.summary_resources.to_csv('./output/resources.csv')
        self.summary_max_queues.to_csv('./output/max_queues.csv')
        self.output_pivot.to_csv('./output/output_summary.csv')
        self.resources_pivot.to_csv('./output/resouces.summary.csv')
    
    
    def single_run(self, scenario, i=0):
        print(f'{i}, ', end='' )
        model = Model(scenario)
        model.run()
        
        # Put results in a dictionary
        results = {
            'output': model.process.audit.summary_output,
            'output_by_day': model.process.audit.summary_output_by_day,
            'resources': model.process.audit.summary_resources,
            'max_queues': model.process.audit.max_queue_sizes,
            'queue_times': model.process.audit.queue_times
                   }
        
        return results
        
    



    def unpack_trial_results(self, name, results):
        

        for run in range(self.replications):
            
            # Output summary
            result_item = results[run]['output']
            result_item['run'] = run
            result_item['name'] = name
            self.summary_output = self.summary_output.append(result_item)
            
            # Output by day summary
            result_item = results[run]['output_by_day']
            result_item['run'] = run
            result_item['name'] = name
            self.summary_output_by_day = self.summary_output_by_day.append(result_item)
            
            # Resources summary
            result_item = results[run]['resources']
            result_item['run'] = run
            result_item['name'] = name
            self.summary_resources = self.summary_resources.append(result_item)
            
            # Max queue summary (convert from series)
            result_item = pd.DataFrame(results[run]['max_queues'])
            result_item['run'] = run
            result_item['name'] = name
            self.summary_max_queues = self.summary_max_queues.append(result_item)
            
            # Queueing time summary
            result_item = pd.DataFrame(results[run]['queue_times'])
            result_item['run'] = run
            result_item['name'] = name
            self.summary_queue_times = self.summary_queue_times.append(result_item)


            
        
    