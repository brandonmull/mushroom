"""Shared utility functions for mushroom dataset analysis."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from IPython.display import HTML, display

class Analysis:
    """Class for analyzing mushroom dataset."""

    def __init__(self, dataset):
        self.dataset = dataset
        self.edibilityCount = self.dataset.data.original.groupby('poisonous').size()
        self.featureNames = self.dataset.data.features.columns.values
        self.featureCount = len(self.featureNames)
        self.featurePairs = list()
        self.featureValues = dict()

        for i, feature in enumerate(self.featureNames):
            self.featureValues[feature] = self.dataset.data.features[feature].unique()

        for i in range(0, self.featureCount - 1):
            feature1 = self.featureNames[i]
            for j in range(i + 1, self.featureCount):
                feature2 = self.featureNames[j]
                self.featurePairs.append([feature1, feature2])

    def countFeaturePairs(self, data):
        """Count edible and poisonous occurrences for each feature-value pair combination."""
        result = list()

        def countOf(tally, value1, value2, edibility):
            return (tally[value1][value2][edibility]
                    if value1 in tally
                    and value2 in tally[value1]
                    and edibility in tally[value1][value2]
                    else 0)

        for i, featurePair in enumerate(self.featurePairs):
            feature1 = featurePair[0]
            feature2 = featurePair[1]
            tally = data.groupby([feature1, feature2, 'poisonous']).size()

            for v1, value1 in enumerate(self.featureValues[feature1]):
                for v2, value2 in enumerate(self.featureValues[feature2]):
                    result.append({
                        'feature1Name': feature1,
                        'feature1Value': value1,
                        'feature2Name': feature2,
                        'feature2Value': value2,
                        'edibleCount': countOf(tally, value1, value2, 'e'),
                        'poisonousCount': countOf(tally, value1, value2, 'p')
                    })

        return pd.DataFrame(result)


    def findMinimalSetOfIdentifyingFeaturePairs(self, edibility):
        """Find the minimal set of feature pairs that identify edible/poisonous mushrooms."""

        if edibility not in ('e', 'p'):
            raise ValueError("edibility must be 'e' or 'p'")

        data = self.dataset.data.original
        desiredCount = 'edibleCount' if edibility == 'e' else 'poisonousCount'
        undesiredCount = 'poisonousCount' if edibility == 'e' else 'edibleCount'
        minimalSet = pd.DataFrame(columns=[
            'feature1Name',
            'feature1Value',
            'feature2Name',
            'feature2Value',
            'edibleCount',
            'poisonousCount',
        ])

        while True:
            topFeaturePair = (self
                .countFeaturePairs(data)
                .query(f'{desiredCount} > 0 and {undesiredCount} == 0')
                .sort_values(by=[desiredCount], ascending=False)
                .iloc[0]
            )
            minimalSet.loc[len(minimalSet.index)] = topFeaturePair
            totalAccountedFor = minimalSet[desiredCount].sum()
            alreadyConsidered1 = data[topFeaturePair['feature1Name']] == topFeaturePair['feature1Value']
            alreadyConsidered2 = data[topFeaturePair['feature2Name']] == topFeaturePair['feature2Value']
            data = data.drop(data[alreadyConsidered1 & alreadyConsidered2].index)
            if totalAccountedFor >= self.edibilityCount[edibility]:
                break

        return minimalSet


    def buildFeatureCrosstab(self, feature1Name, feature2Name, edibilityValues=('e', 'p')):
        """Build a cross-tabulation xarray for two features, split by edibility."""
        data = self.dataset.data.original
        feature1Values = sorted(data[feature1Name].dropna().unique().tolist())
        feature2Values = sorted(data[feature2Name].dropna().unique().tolist())

        expectedIndex = pd.MultiIndex.from_product([
            feature1Values,
            feature2Values,
            edibilityValues,
        ], names=[feature1Name, feature2Name, 'poisonous'])

        counts = (
            data.groupby([feature1Name, feature2Name, 'poisonous'])
            .size()
            .reindex(expectedIndex, fill_value=0)
        )

        crossTab = counts.to_xarray()
        crossTab = crossTab.transpose(feature1Name, feature2Name, 'poisonous')
        return crossTab


    def parseFeatureValueMap(self, variableInfoText):
        """Parse the variable_info text into a mapping of feature names to value maps."""
        featureMap = {}
        for line in variableInfoText.splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.match(r'^\d+\.\s*([^:]+):\s*(.+)$', line)
            if not match:
                continue

            featureName = match.group(1).strip()
            pairs = [pair.strip() for pair in match.group(2).split(',') if pair.strip()]
            valueMap = {}
            for pair in pairs:
                if '=' not in pair:
                    continue
                longName, code = pair.split('=', 1)
                valueMap[code.strip()] = longName.strip()

            featureMap[featureName] = valueMap

        return featureMap


    def plotFeatureCrosstab(self, crossTab, title=None, figsize=(14, 10), showValueLegend=False):
        """Plot a 3D bar chart of feature crosstab split by edibility."""
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='3d')
        fig.subplots_adjust(left=0.03, right=0.99, top=0.94, bottom=0.06)

        feature1Name = crossTab.dims[0]
        feature2Name = crossTab.dims[1]

        xLabels = list(crossTab.coords[feature1Name].values)
        yLabels = list(crossTab.coords[feature2Name].values)
        xPositions = range(len(xLabels))
        yPositions = range(len(yLabels))

        xCoords = []
        yCoords = []
        zEdible = []
        zPoisonous = []
        for xIdx, xLabel in enumerate(xLabels):
            for yIdx, yLabel in enumerate(yLabels):
                xCoords.append(xIdx)
                yCoords.append(yIdx)
                zEdible.append(int(crossTab.sel({feature1Name: xLabel, feature2Name: yLabel, 'poisonous': 'e'}).item()))
                zPoisonous.append(int(crossTab.sel({feature1Name: xLabel, feature2Name: yLabel, 'poisonous': 'p'}).item()))

        xCoords = np.array(xCoords)
        yCoords = np.array(yCoords)
        zEdible = np.array(zEdible)
        zPoisonous = np.array(zPoisonous)

        dx = 0.35
        dy = 0.35

        ax.bar3d(xCoords - dx / 2, yCoords - dy / 2, np.zeros_like(zEdible),
                dx, dy, zEdible, color='#39ff14', shade=True, label='edible')
        ax.bar3d(xCoords + dx / 2, yCoords - dy / 2, np.zeros_like(zPoisonous),
                dx, dy, zPoisonous, color='#a020f0', shade=True, label='poisonous')

        ax.set_xticks([i for i in xPositions])
        ax.set_xticklabels(xLabels, rotation=45, ha='right')
        ax.set_yticks([i for i in yPositions])
        ax.set_yticklabels(yLabels)

        ax.set_xlabel(feature1Name)
        ax.set_ylabel(feature2Name)
        ax.set_zlabel('Count')
        ax.set_title(title or f'3D histogram of {feature1Name} x {feature2Name} split by poisonous')
        ax.legend()

        if showValueLegend:
            featureMap = self.parseFeatureValueMap(self.dataset.metadata['additional_info']['variable_info'])
            legendTextBlocks = []
            for featureName in (feature1Name, feature2Name):
                if featureName in featureMap:
                    valueMap = featureMap[featureName]
                    legendLines = [f'{featureName} values:']
                    legendLines += [f'{code} = {label}' for code, label in sorted(valueMap.items())]
                    legendTextBlocks.append('\n'.join(legendLines))

            if legendTextBlocks:
                legendText = '\n\n'.join(legendTextBlocks)
                ax.text2D(
                    0.02,
                    0.98,
                    legendText,
                    transform=ax.transAxes,
                    fontsize=9,
                    va='top',
                    ha='left',
                    family='monospace',
                    bbox=dict(facecolor='white', alpha=0.90, edgecolor='none'),
                )

        plt.show()


    def printFeatureCrosstab(self, crossTab, showValueLegend=False):
        """Display an HTML table of feature crosstab split by edibility."""
        feature1Name = crossTab.dims[0]
        feature2Name = crossTab.dims[1]

        edibleDf = crossTab.sel(poisonous='e').to_pandas()
        poisonousDf = crossTab.sel(poisonous='p').to_pandas()

        edibleDf = edibleDf.rename_axis(index=feature1Name, columns=feature2Name)
        poisonousDf = poisonousDf.rename_axis(index=feature1Name, columns=feature2Name)

        legendHtml = ''
        if showValueLegend:
            featureMap = self.parseFeatureValueMap(self.dataset.metadata['additional_info']['variable_info'])
            legendCells = []
            for featureName in (feature1Name, feature2Name):
                if featureName in featureMap:
                    valueMap = featureMap[featureName]
                    rows = ''.join(
                        f'<tr><td style="padding:4px 8px;">{code}</td><td style="padding:4px 8px;">{label}</td></tr>'
                        for code, label in sorted(valueMap.items())
                    )
                    legendCells.append(f'''
                        <div style="flex:1; min-width:0;">
                            <h4 style="margin:0 0 0.5rem 0;">{featureName} legend</h4>
                            <table style="border-collapse:collapse; width:100%; border:1px solid #ccc; font-size:90%;">
                                <thead><tr><th style="padding:6px 10px; text-align:left; border-bottom:1px solid #ccc;">Code</th><th style="padding:6px 10px; text-align:left; border-bottom:1px solid #ccc;">Meaning</th></tr></thead>
                                <tbody>{rows}</tbody>
                            </table>
                        </div>
                    ''' )
            legendHtml = f'''
            <div style="display:flex; gap:1rem; align-items:flex-start; margin-bottom:1rem;">
                {''.join(legendCells)}
            </div>
            '''

        html = f'''
        <div style="display:flex; gap:2rem; align-items:flex-start; margin-bottom:1rem;">
            <div style="flex:1; min-width:0;">
                <h3 style="margin:0 0 0.5rem 0;">Edible counts</h3>
                {edibleDf.to_html(border=1, classes='dataframe', justify='center')}
            </div>
            <div style="flex:1; min-width:0;">
                <h3 style="margin:0 0 0.5rem 0;">Poisonous counts</h3>
                {poisonousDf.to_html(border=1, classes='dataframe', justify='center')}
            </div>
        </div>
        {legendHtml}
        '''
        display(HTML(html))

        return {'edible': edibleDf, 'poisonous': poisonousDf}