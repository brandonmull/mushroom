"""Shared utility functions for mushroom dataset analysis."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from IPython.display import HTML, display

class Analyzer:
    """Class for analyzing mushroom dataset."""

    def __init__(self, dataset):
        self.dataset = dataset
        self.edibility_count = self.dataset.data.original.groupby('poisonous').size()
        self.feature_names = self.dataset.data.features.columns.values
        self.feature_count = len(self.feature_names)
        self.feature_pairs = list()
        self.feature_values = dict()

        for i, feature in enumerate(self.feature_names):
            self.feature_values[feature] = self.dataset.data.features[feature].unique()

        for i in range(0, self.feature_count - 1):
            feature1 = self.feature_names[i]
            for j in range(i + 1, self.feature_count):
                feature2 = self.feature_names[j]
                self.feature_pairs.append([feature1, feature2])

    def count_exclusive_feature_pairs(self, data):
        """Count edible and poisonous occurrences for each feature-value pair combination.

        A feature pair is exclusive when all mushrooms sharing that pair of values
        have the same edibility (either all edible or all poisonous).
        """
        result = list()

        def count_of(tally, value1, value2, edibility):
            return (tally[value1][value2][edibility]
                    if value1 in tally
                    and value2 in tally[value1]
                    and edibility in tally[value1][value2]
                    else 0)

        for i, feature_pair in enumerate(self.feature_pairs):
            feature1 = feature_pair[0]
            feature2 = feature_pair[1]
            tally = data.groupby([feature1, feature2, 'poisonous']).size()

            for v1, value1 in enumerate(self.feature_values[feature1]):
                for v2, value2 in enumerate(self.feature_values[feature2]):
                    result.append({
                        'feature1_name': feature1,
                        'feature1_value': value1,
                        'feature2_name': feature2,
                        'feature2_value': value2,
                        'edible_count': count_of(tally, value1, value2, 'e'),
                        'poisonous_count': count_of(tally, value1, value2, 'p')
                    })

        return pd.DataFrame(result)


    def find_minimal_set_of_exclusive_feature_pairs(self, edibility):
        """Find the minimal set of exclusive feature pairs that identify edible/poisonous mushrooms.

        An exclusive feature pair for a given class is a pair of feature values that appears
        only on mushrooms of that class and never on the other class.
        """

        if edibility not in ('e', 'p'):
            raise ValueError("edibility must be 'e' or 'p'")

        data = self.dataset.data.original
        desired_count = 'edible_count' if edibility == 'e' else 'poisonous_count'
        undesired_count = 'poisonous_count' if edibility == 'e' else 'edible_count'
        minimal_set = pd.DataFrame(columns=[
            'feature1_name',
            'feature1_value',
            'feature2_name',
            'feature2_value',
            'edible_count',
            'poisonous_count',
        ])

        total_accounted_for = 0
        while total_accounted_for < self.edibility_count[edibility]:
            matching = (self
                .count_exclusive_feature_pairs(data)
                .query(f'{desired_count} > 0 and {undesired_count} == 0')
                .sort_values(by=[desired_count], ascending=False)
            )
            if matching.empty:
                break
            top_feature_pair = matching.iloc[0]
            minimal_set.loc[len(minimal_set.index)] = top_feature_pair
            total_accounted_for += top_feature_pair[desired_count]
            already_considered_1 = data[top_feature_pair['feature1_name']] == top_feature_pair['feature1_value']
            already_considered_2 = data[top_feature_pair['feature2_name']] == top_feature_pair['feature2_value']
            data = data.drop(data[already_considered_1 & already_considered_2].index)

        return minimal_set


class Visualizer:
    """Class for visualizing mushroom dataset features."""

    def __init__(self, dataset):
        self.dataset = dataset
        self.feature_map = self.parse_feature_value_map(dataset.metadata['additional_info']['variable_info'])

    def build_feature_crosstab(self, feature1_name, feature2_name, edibility_values=('e', 'p')):
        """Build a cross-tabulation xarray for two features, split by edibility."""
        data = self.dataset.data.original
        feature1_values = sorted(data[feature1_name].dropna().unique().tolist())
        feature2_values = sorted(data[feature2_name].dropna().unique().tolist())

        expected_index = pd.MultiIndex.from_product([
            feature1_values,
            feature2_values,
            edibility_values,
        ], names=[feature1_name, feature2_name, 'poisonous'])

        counts = (
            data.groupby([feature1_name, feature2_name, 'poisonous'])
            .size()
            .reindex(expected_index, fill_value=0)
        )

        cross_tab = counts.to_xarray()
        cross_tab = cross_tab.transpose(feature1_name, feature2_name, 'poisonous')
        return cross_tab


    def parse_feature_value_map(self, variable_info_text):
        """Parse the variable_info text into a mapping of feature names to value maps."""
        feature_map = {}
        for line in variable_info_text.splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.match(r'^\d+\.\s*([^:]+):\s*(.+)$', line)
            if not match:
                continue

            feature_name = match.group(1).strip()
            pairs = [pair.strip() for pair in match.group(2).split(',') if pair.strip()]
            value_map = {}
            for pair in pairs:
                if '=' not in pair:
                    continue
                long_name, code = pair.split('=', 1)
                value_map[code.strip()] = long_name.strip()

            feature_map[feature_name] = value_map

        return feature_map


    def plot_feature_crosstab(self, cross_tab, title=None, figsize=(14, 10), show_value_legend=False):
        """Plot a 3D bar chart of feature crosstab split by edibility."""
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='3d')
        fig.subplots_adjust(left=0.03, right=0.99, top=0.94, bottom=0.06)

        feature1_name = cross_tab.dims[0]
        feature2_name = cross_tab.dims[1]

        x_labels = list(cross_tab.coords[feature1_name].values)
        y_labels = list(cross_tab.coords[feature2_name].values)
        x_positions = range(len(x_labels))
        y_positions = range(len(y_labels))

        x_coords = []
        y_coords = []
        z_edible = []
        z_poisonous = []
        for x_idx, x_label in enumerate(x_labels):
            for y_idx, y_label in enumerate(y_labels):
                x_coords.append(x_idx)
                y_coords.append(y_idx)
                z_edible.append(int(cross_tab.sel({feature1_name: x_label, feature2_name: y_label, 'poisonous': 'e'}).item()))
                z_poisonous.append(int(cross_tab.sel({feature1_name: x_label, feature2_name: y_label, 'poisonous': 'p'}).item()))

        x_coords = np.array(x_coords)
        y_coords = np.array(y_coords)
        z_edible = np.array(z_edible)
        z_poisonous = np.array(z_poisonous)

        dx = 0.35
        dy = 0.35

        ax.bar3d(x_coords - dx / 2, y_coords - dy / 2, np.zeros_like(z_edible),
                dx, dy, z_edible, color='#39ff14', shade=True, label='edible')
        ax.bar3d(x_coords + dx / 2, y_coords - dy / 2, np.zeros_like(z_poisonous),
                dx, dy, z_poisonous, color='#a020f0', shade=True, label='poisonous')

        ax.set_xticks([i for i in x_positions])
        ax.set_xticklabels(x_labels, rotation=45, ha='right')
        ax.set_yticks([i for i in y_positions])
        ax.set_yticklabels(y_labels)

        ax.set_xlabel(feature1_name)
        ax.set_ylabel(feature2_name)
        ax.set_zlabel('Count')
        ax.set_title(title or f'3D histogram of {feature1_name} x {feature2_name} split by poisonous')
        ax.legend()

        if show_value_legend:
            legend_text_blocks = []
            for feature_name in (feature1_name, feature2_name):
                if feature_name in self.feature_map:
                    value_map = self.feature_map[feature_name]
                    legend_lines = [f'{feature_name} values:']
                    legend_lines += [f'{code} = {label}' for code, label in sorted(value_map.items())]
                    legend_text_blocks.append('\n'.join(legend_lines))

            if legend_text_blocks:
                legend_text = '\n\n'.join(legend_text_blocks)
                ax.text2D(
                    0.02,
                    0.98,
                    legend_text,
                    transform=ax.transAxes,
                    fontsize=9,
                    va='top',
                    ha='left',
                    family='monospace',
                    bbox=dict(facecolor='white', alpha=0.90, edgecolor='none'),
                )

        plt.show()


    def print_feature_crosstab(self, cross_tab, show_value_legend=False):
        """Display an HTML table of feature crosstab split by edibility."""
        feature1_name = cross_tab.dims[0]
        feature2_name = cross_tab.dims[1]

        edible_df = cross_tab.sel(poisonous='e').to_pandas()
        poisonous_df = cross_tab.sel(poisonous='p').to_pandas()

        edible_df = edible_df.rename_axis(index=feature1_name, columns=feature2_name)
        poisonous_df = poisonous_df.rename_axis(index=feature1_name, columns=feature2_name)

        legend_html = ''
        if show_value_legend:
            legend_cells = []
            for feature_name in (feature1_name, feature2_name):
                if feature_name in self.feature_map:
                    value_map = self.feature_map[feature_name]
                    rows = ''.join(
                        f'<tr><td style="padding:4px 8px;">{code}</td><td style="padding:4px 8px;">{label}</td></tr>'
                        for code, label in sorted(value_map.items())
                    )
                    legend_cells.append(f'''
                        <div style="flex:1; min-width:0;">
                            <h4 style="margin:0 0 0.5rem 0;">{feature_name} legend</h4>
                            <table style="border-collapse:collapse; width:100%; border:1px solid #ccc; font-size:90%;">
                                <thead><tr><th style="padding:6px 10px; text-align:left; border-bottom:1px solid #ccc;">Code</th><th style="padding:6px 10px; text-align:left; border-bottom:1px solid #ccc;">Meaning</th></tr></thead>
                                <tbody>{rows}</tbody>
                            </table>
                        </div>
                    ''' )
            legend_html = f'''
            <div style="display:flex; gap:1rem; align-items:flex-start; margin-bottom:1rem;">
                {''.join(legend_cells)}
            </div>
            '''

        html = f'''
        <div style="display:flex; gap:2rem; align-items:flex-start; margin-bottom:1rem;">
            <div style="flex:1; min-width:0;">
                <h3 style="margin:0 0 0.5rem 0;">Edible counts</h3>
                {edible_df.to_html(border=1, classes='dataframe', justify='center')}
            </div>
            <div style="flex:1; min-width:0;">
                <h3 style="margin:0 0 0.5rem 0;">Poisonous counts</h3>
                {poisonous_df.to_html(border=1, classes='dataframe', justify='center')}
            </div>
        </div>
        {legend_html}
        '''
        display(HTML(html))

        return {'edible': edible_df, 'poisonous': poisonous_df}