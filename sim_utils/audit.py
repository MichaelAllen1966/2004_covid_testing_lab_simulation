import numpy as np
import pandas as pd


class Audit:

    def __init__(self, _process):

        self._env = _process._env
        self._params = _process._params
        self._queues = _process.queues
        self._queue_monitors = _process.queue_monitors
        self._recources = _process.resources
        self._count_in = _process.count_in
        self._count_out = _process.count_out
        self._fte_on_break = _process.fte_on_break

        # Set up queue audit
        self.queue_names = ['day'] + [
            key for key, _ in self._queues.items()]
        self.queue_audit = pd.DataFrame(columns=self.queue_names)

        # Set up resources audit
        self.resource_names = ['day'] + [
            key for key, _ in self._recources.items()]
        self.resource_audit = pd.DataFrame(columns=self.resource_names +
                                                   ['tracker_break_fte'])

    def audit_queue(self):
        day = self._env.now
        audit_counts = {key: len(value) for key, value in self._queues.items()}
        audit_counts['day'] = day / self._params.day_duration
        self.queue_audit = self.queue_audit.append(
            audit_counts, ignore_index=True)

    def audit_resources(self):
        time = self._env.now
        resource_counts = {key: value.count for key, value in
                           self._recources.items()}
        resource_counts['tracker_break_fte'] = self._fte_on_break[0]
        resource_counts['day'] = time / self._params.day_duration
        for resource, shift in self._params.resource_shifts.items():
            label = resource + '_shift'
            if shift[0] < time < shift[1]:
                resource_counts[label] = 1
            else:
                resource_counts[label] = 0
        self.resource_audit = self.resource_audit.append(resource_counts,
                                                         ignore_index=True)

    def summarise_in_out(self):
        incount = self._count_in
        outcount = self._count_out
        df_in = pd.DataFrame(incount,
                             columns=['batch_id', 'time_mins', 'count'])
        day = (df_in['time_mins'] / self._params.day_duration).astype(int)
        df_in['day'] = day
        df_out = pd.DataFrame(outcount,
                              columns=['batch_id', 'time_mins', 'count',
                                       'time_in',
                                       'time_out'])
        day = (df_out['time_mins'] / self._params.day_duration).astype(int)
        df_out['day'] = day

        # Remove valaues before warm up
        df_in = df_in.loc[df_in['time_mins'] >= self._params.audit_warm_up]
        df_out = df_out.loc[df_out['time_mins'] >= self._params.audit_warm_up]

        df_in_pivot = df_in.pivot_table(
            index='day',
            values='count',
            aggfunc=[np.sum],
            margins=False)

        df_out_pivot = df_out.pivot_table(
            index='day',
            values='count',
            aggfunc=[np.sum],
            margins=False)

        df_summary = pd.DataFrame()
        df_summary['input'] = df_in_pivot['sum']['count'].astype('int')
        if df_out_pivot.shape[0] > 0:
            df_summary['output'] = df_out_pivot['sum']['count']
        else:
            df_summary['output'] = 0
        df_summary['demand_met'] = np.round(
            df_summary['output'] / df_summary['input'], 2)

        # Get batch_in_out times
        batch_process_time = pd.DataFrame(index=df_in['batch_id'])
        batch_process_time['day_in'] = df_in['day']
        batch_process_time['time_in'] = df_in['time_mins']
        batch_process_time['size_in'] = df_in['count']
        batch_process_time.dropna(inplace=True)

        if df_out_pivot.shape[0] > 0:
            batch_time_pivot = df_out.pivot_table(
                index='batch_id',
                values=['day', 'time_in', 'time_out'],
                aggfunc=[np.min, np.max],
                margins=False)

            batch_times = np.round(
                ((batch_time_pivot['amax']['time_out'] -
                  batch_time_pivot['amin']['time_in']) / 60), 2)

            # Add day to batch times
            batch_day_in = df_in[['batch_id', 'day']]
            batch_day_in.set_index('batch_id', inplace=True)

            batch_times = pd.concat([batch_times, batch_day_in], axis=1,
                                    sort=False)
            batch_times.dropna(inplace=True)
            df_summary['median_process_time_hours'] = np.median(batch_times[0])
            df_summary['max_process_time_hours'] = np.max(batch_times[0])
        else:
            df_summary['median_process_time_hours'] = np.nan
            df_summary['max_process_time_hours'] = np.nan

        # Reindex starting at day 1 
        df_summary.index = range(1, df_summary.shape[0] + 1)

        # Store in object
        self.summary_output_by_day = df_summary

        self.summary_output = df_summary = self.summary_output_by_day.mean()
        self.summary_output = pd.DataFrame(self.summary_output)
        self.summary_output.rename(columns={0: 'Result'}, inplace=True)
        self.summary_output = self.summary_output.round(2)

    def summarise_queues(self):

        queue_units = {
            'q_batch_input': 0,
            'q_sample_receipt': self._params.basic_batch_size,
            'q_sample_prep': self._params.basic_batch_size,
            'q_rna_extraction': self._params.basic_batch_size,
            'q_sample_heat': self._params.basic_batch_size,
            'q_pcr_collation': self._params.basic_batch_size,
            'q_pcr_prep': self._params.basic_batch_size * 2,
            'q_pcr': self._params.basic_batch_size * 4,
            'q_data_analysis': self._params.basic_batch_size * 4,
            'q_completed': self._params.basic_batch_size * 4
        }

        queued_units = pd.DataFrame()
        for key, value in queue_units.items():
            queue_samples = self.queue_audit[key] * value
            queued_units[key] = queue_samples

        self.max_queue_sizes = queued_units.max()

    def summarise_queue_times(self):

        self.queue_times = pd.DataFrame()
        keys = []

        for key, value in self._queue_monitors.items():

            if len(value) > 0:
                keys.append(key)
                results = dict()
                array = np.array(value)
                times = array[:, 1] - array[:, 0]
                results['min'] = np.min(times)
                results['1Q'] = np.quantile(times, 0.25)
                results['median'] = np.median(times)
                results['3Q'] = np.quantile(times, 0.75)
                results['95_percent'] = np.quantile(times, 0.95)
                results['max'] = np.max(times)
                self.queue_times = self.queue_times.append(pd.Series(results),
                                                           ignore_index=True)

        self.queue_times['queue'] = keys
        cols = ['queue', 'min', '1Q', 'median', '3Q', '95_percent', 'max']
        self.queue_times = self.queue_times[cols]
        self.queue_times = self.queue_times.round(1)

    def summarise_resources_with_shifts(self):
        index = [key for key, value in self._params.resource_numbers.items() if
                 value > 0]

        # Remove trackers from utilisation summary
        index = [item for item in index if item[0:7] != 'tracker']

        columns = ['Available', 'Used', 'Utilisation']


        self.summary_resources = pd.DataFrame(index=index, columns=columns)
        for resource in index:
            # Get number available on-shift
            available = self._params.resource_numbers[resource]
            # Get resource use only when resources are on-shift
            resource_shift = resource + '_shift'
            mask = self.resource_audit[resource_shift] == 1
            mean_resources_use = self.resource_audit[resource][mask].mean()
            mean_utilisation = mean_resources_use / available
            # Put results in dictionary
            result = {'Available': available,
                      'Used': mean_resources_use,
                      'Utilisation': mean_utilisation}
            # Add to DataFrame
            self.summary_resources.loc[resource] = result
            

    def summarise_trackers(self):
        """Aggregate trackers by hour"""
        self.tracker_results = pd.DataFrame()
        df = self.resource_audit.copy()
        index = list(df)
        # Get tracker columns (remove whether on shift or not for trackers
        index = [item for item in index if item[0:7] == 'tracker' and
                 item[-6:] != '_shift']
        if len(index) == 0:
            # No trackers active
            return
        day_fraction = df['day'] % 1.0
        hour = day_fraction.values * 24
        df['hour'] = hour.astype(int)
        self.tracker_results = df.pivot_table(
            index='hour',
            aggfunc=[np.mean],
            margins=False)
        # Limit table
        self.tracker_results = self.tracker_results['mean'][index]


    def run_audit(self):
        yield self._env.timeout(self._params.audit_warm_up)

        while True:
            self.audit_queue()
            self.audit_resources()
            yield self._env.timeout(self._params.audit_interval)
