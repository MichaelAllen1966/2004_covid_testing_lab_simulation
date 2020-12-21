import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sim_utils.model import Model


class Replicator:

    def __init__(self, scenarios, replications):
        """Constructor class for Replicator
        """

        self.replications = replications
        self.scenarios = scenarios

        # Set up DataFrames for all trials results
        self.summary_output = pd.DataFrame()
        self.summary_output_by_day = pd.DataFrame()
        self.summary_queue_times = pd.DataFrame()
        self.summary_resources = pd.DataFrame()
        self.summary_tracker = pd.DataFrame()
        self.summary_max_queues = pd.DataFrame()
        self.output_pivot = pd.DataFrame()
        self.resources_pivot = pd.DataFrame()
        self.summary_time_stamps = pd.DataFrame()
        self.summary_time_stamps_by_priority_pct_50 = pd.DataFrame()
        self.summary_time_stamps_by_priority_pct_95 = pd.DataFrame()


    def pivot_results(self):
        """Summarise results across multiple scenario replicates. """

        def percentile_95(g):
            """Function for percentiles in pandas pivot table"""
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
        # Do not report dummy resources
        df.drop('dummy', inplace=True)

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
        
        # Tracker summery
        df = self.summary_tracker.copy()
        df.drop('run', inplace=True, axis=1)
        df = df.round(1)
        self.tracker_pivot = df.pivot_table(
            index = ['hour', 'name'],
            aggfunc = [np.mean],
            margins=False)
        self.tracker_pivot = self.tracker_pivot['mean']

        # Time stamps summary
        df = self.summary_time_stamps.copy()
        df.drop('run', inplace=True, axis=1)
        df = df.round(0)
        # Rename for sorting
        dict = {
                'sample_receipt_in': '01_sample_receipt_in',
                'sample_receipt_out': '01_sample_receipt_out',
                'sample_prep_auto_in': '02_sample_prep_auto_in',
                'sample_prep_auto_out': '02_sample_prep_auto_out',
                'sample_prep_manual_in': '03_sample_prep_manual_in',
                'sample_prep_manual_out': '03_sample_prep_manual_out',
                'sample_heat_in': '04_sample_heat_in',
                'sample_heat_out': '04_sample_heat_out',
                'rna_extraction_in': '05_rna_extraction_in',
                'rna_extraction_out': '05_rna_extraction_out',
                'pcr_prep_in': '06_pcr_prep_in',
                'pcr_prep_out': '06_pcr_prep_out',
                'pcr_in': '07_pcr_in',
                'pcr_out': '07_pcr_out',
                'data_analysis_in': '08_data_analysis_in',
                'data_analysis_out': '08_data_analysis_out'
                }

        df.rename(dict, axis=0, inplace=True)
        df['stage'] = list(df.index)

        self.time_stamp_pivot = df.pivot_table(
            index = ['stage', 'name'],
            aggfunc = [np.mean],
            margins=False)
        self.time_stamp_pivot = self.time_stamp_pivot['mean']
        self.time_stamp_pivot = self.time_stamp_pivot.round(0)


        # Time stamp by priority - median
        df = self.summary_time_stamps_by_priority_pct_50.copy()
        df.drop('run', inplace=True, axis=1)
        df = df.round(0)
        df.rename(dict, axis=0, inplace=True)
        df['stage'] = list(df.index)

        self.time_stamp_by_priority_pct_50_pivot = df.pivot_table(
            index = ['stage', 'name', 'priority'],
            aggfunc = [np.mean],
            margins=False)
        self.time_stamp_by_priority_pct_50_pivot = \
            self.time_stamp_by_priority_pct_50_pivot['mean']
        self.time_stamp_by_priority_pct_50_pivot = \
            self.time_stamp_by_priority_pct_50_pivot.round(0)

        # Time stamp by priority - 95th percentile
        df = self.summary_time_stamps_by_priority_pct_95.copy()
        df.drop('run', inplace=True, axis=1)
        df = df.round(0)
        df.rename(dict, axis=0, inplace=True)
        df['stage'] = list(df.index)

        self.time_stamp_by_priority_pct_95_pivot = df.pivot_table(
            index = ['stage', 'name', 'priority'],
            aggfunc = [np.mean],
            margins=False)
        self.time_stamp_by_priority_pct_95_pivot = \
            self.time_stamp_by_priority_pct_95_pivot['mean']
        self.time_stamp_by_priority_pct_95_pivot = \
            self.time_stamp_by_priority_pct_95_pivot.round(0)

    def plot_trackers(self):
        df = self.tracker_pivot.copy()
        # remove 'tracker_' from column titles
        rename_dict = {}
        for col in list(df):
            if col[0:8] == 'tracker_':
                new_col = col[8:]
            else:
                new_col = col
            rename_dict[col] = new_col
        df.rename(columns=rename_dict, inplace=True)
        
        df = df.reset_index()
        scenarios = list(set(df['name']))
        scenarios.sort()
        
        linestyles = ['-','--',':','-.']
        
        for scenario in scenarios:
            data = df[df['name'] == scenario]
            x = data['hour']
            y_data = data.drop(['hour', 'name'], axis=1)
            fig = plt.figure(figsize=(10,6))
            
            ax1 = fig.add_subplot(1,2,1)
            counter = 0
            for tracker in list(y_data):
                if tracker[-5:] == '_jobs':
                    label = tracker[0:-5]
                    ax1.plot(x, y_data[tracker], label=label, 
                        linestyle=linestyles[counter % 4])
                    counter += 1
            
            ax1.set_ylim(0)
            ax1.set_xlim(0,24)
            ax1.yaxis.set_major_locator(ticker.MultipleLocator(5))
            ax1.xaxis.set_major_locator(ticker.MultipleLocator(4))
            ax1.xaxis.set_minor_locator(ticker.MultipleLocator(1))
            ax1.set_xlabel('Hour')
            ax1.set_ylabel('Tracker count')
            ax1.set_title('Active Jobs')
            ax1.legend()
            ax1.grid(True, which='major')
            
            
            ax2 = fig.add_subplot(1,2,2)
            counter = 0
            for tracker in list(y_data):
                if tracker[-4:] == '_fte':
                    label = tracker[0:-4]
                    ax2.plot(x, y_data[tracker], label=label, 
                        linestyle=linestyles[counter % 4])
                    counter += 1
            ax2.set_ylim(0)
            ax2.set_xlim(0,24)
            ax2.yaxis.set_major_locator(ticker.MultipleLocator(5))
            ax2.xaxis.set_major_locator(ticker.MultipleLocator(4))
            ax2.xaxis.set_minor_locator(ticker.MultipleLocator(1))
            ax2.set_xlabel('Hour')
            ax2.set_ylabel('Tracker count')
            ax2.set_title('Active FTE')
            ax2.legend()
            ax2.grid(True, which='major')
            
            plt.suptitle(scenario)
            plt.tight_layout(pad=2)
            plt.savefig(f'output/tracker_{scenario}.png', dpi=600)
            plt.show()

        
   
 
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
        print('\n\n')
        print('Median time stamps throughout process')
        print('-------------------------------------')
        print(self.time_stamp_pivot)
        print('\n\n')
        print('Median time stamps throughout process, by priority')
        print('--------------------------------------------------')
        print(self.time_stamp_by_priority_pct_50_pivot.unstack())
        print('\n\n')
        print('95th percentile time stamps throughout process, by priority')
        print('-----------------------------------------------------------')
        print(self.time_stamp_by_priority_pct_95_pivot.unstack())
        print('\n\n')


    def run_scenarios(self):
        
        # Run all scenarios
        scenario_count = len(self.scenarios)
        counter = 0
        for name, scenario in self.scenarios.items():
            counter += 1
            print(
                f'\r>> Running scenario {counter} of {scenario_count}', end='')
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
        
        # Create charts
        self.plot_trackers()
        
        
    
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
        self.resources_pivot.to_csv('./output/resources.summary.csv')
    
    
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
            'queue_times': model.process.audit.queue_times,
            'tracker': model.process.audit.tracker_results,
            'time_stamps': model.process.audit.time_stamp_medians,
            'time_stamp_by_priority_pct_50':
                model.process.audit.time_stamp_by_priority_pct_50,
            'time_stamp_by_priority_pct_95':
                model.process.audit.time_stamp_by_priority_pct_95
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
            self.summary_output_by_day = \
                self.summary_output_by_day.append(result_item)
            
            # Resources summary
            result_item = results[run]['resources']
            result_item['run'] = run
            result_item['name'] = name
            self.summary_resources = self.summary_resources.append(result_item)
            
            # Max queue summary (convert from series)
            result_item = pd.DataFrame(results[run]['max_queues'])
            result_item['run'] = run
            result_item['name'] = name
            self.summary_max_queues = \
                self.summary_max_queues.append(result_item)
            
            # Queueing time summary
            result_item = pd.DataFrame(results[run]['queue_times'])
            result_item['run'] = run
            result_item['name'] = name
            self.summary_queue_times = \
                self.summary_queue_times.append(result_item)
                
            # Resource tracker
            result_item = pd.DataFrame(results[run]['tracker'])
            result_item['run'] = run
            result_item['name'] = name
            self.summary_tracker = \
                self.summary_tracker.append(result_item)

            # Time stamps summaries (medians)
            result_item = pd.DataFrame(results[run]['time_stamps'])
            result_item['run'] = run
            result_item['name'] = name
            self.summary_time_stamps = \
                self.summary_time_stamps.append(result_item)

            # Time stamps by priority
            result_item = pd.DataFrame(
                results[run]['time_stamp_by_priority_pct_50'])
            result_item['run'] = run
            result_item['name'] = name
            self.summary_time_stamps_by_priority_pct_50 = \
                self.summary_time_stamps_by_priority_pct_50.append(result_item)

            result_item = pd.DataFrame(
                results[run]['time_stamp_by_priority_pct_95'])
            result_item['run'] = run
            result_item['name'] = name
            self.summary_time_stamps_by_priority_pct_95 = \
                self.summary_time_stamps_by_priority_pct_95.append(result_item)
