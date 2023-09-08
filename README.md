## MiniWDL Viz

* A package for parsing and visualizing WDL files 
* Uses MiniWDL to parse a WDL file into edges, nodes, inputs, and outputs
* Creates a `mermaid.js` file to plot a flowchart of the WDL file

### Installation
To install, run 

```pip install git+https://github.com/chanzuckerberg/miniwdl-viz.git```

or 
```
git clone https://github.com/chanzuckerberg/miniwdl-viz.git
cd miniwdl-viz

python3 setup.py install
```

### Running 

To run just the parser, run 
```
miniwdl_parser /path/to/wdl
```

To run the wdl to mermaid plot run:

```
wdl_to_mermaid /path/to/wdl --plot-flowchart
```
This uses matplotlib and makes a call to the `mermaid.ink` site to generate the plot

To simply output the mermaid flowchart as a string, run

```
wdl_to_mermaid /path/to/wdl --print-flowchart
```

More options can be found using 

```
miniwdl_parser -h
```

or 

```
wdl_to_mermaid -h
```

The parser should be able to handle most WDL workflows that `miniwdl` can handle. An example of a simple vs a more complex WDL file is below:

### Simple

This was generated with the command `wdl_to_mermaid wdl/phylotree-ng/run.wdl --print-flowchart --flowchart-dir TD`
```mermaid 
flowchart LR
    classDef done fill:#f96
    call-GetSampleContigFastas{{"GetSampleContigFastas"}}
    call-GetReferenceAccessionFastas{{"GetReferenceAccessionFastas"}}
    call-RunSKA{{"RunSKA"}}
    call-ComputeClusters{{"ComputeClusters"}}
    call-GenerateClusterPhylos{{"GenerateClusterPhylos"}}
    call-AddSampleNamesToDistances{{"AddSampleNamesToDistances"}}
    call-AddSampleNamesToVariants{{"AddSampleNamesToVariants"}}
    subgraph if-L88C5["GenerateClusterPhylos.phylotree_newick != None"]
    call-AddSampleNamesToNewick{{"AddSampleNamesToNewick"}}
    end
    call-FetchNCBIMetadata{{"FetchNCBIMetadata"}}
    call-GetSampleContigFastas -->  call-RunSKA
    call-GetReferenceAccessionFastas -->  call-RunSKA
    call-RunSKA -->  call-ComputeClusters
    call-ComputeClusters -->  call-GenerateClusterPhylos
    call-RunSKA -->  call-GenerateClusterPhylos
    call-RunSKA -->  call-AddSampleNamesToDistances
    call-GenerateClusterPhylos -->  call-AddSampleNamesToVariants
    call-GenerateClusterPhylos -->  if-L88C5
    call-GenerateClusterPhylos -->  call-AddSampleNamesToNewick
```

### Complex
This was generated with the command: ```wdl_to_mermaid wdl/phylotree-ng/run.wdl --print-flowchart```
```mermaid 
flowchart TD
    classDef done fill:#f96
    call-DynamicallyCombineIntervals{{"DynamicallyCombineIntervals"}}
    decl-unpadded_intervals>"unpadded_intervals"]
    subgraph scatter-L120C3-idx["range(length(unpadded_intervals))"]
    call-ImportGVCFs{{"ImportGVCFs"}}
    call-GenotypeGVCFs{{"GenotypeGVCFs"}}
    call-HardFilterAndMakeSitesOnlyVcf{{"HardFilterAndMakeSitesOnlyVcf"}}
    end
    call-SitesOnlyGatherVcf{{"SitesOnlyGatherVcf"}}
    call-IndelsVariantRecalibrator{{"IndelsVariantRecalibrator"}}
    subgraph if-L195C3["num_gvcfs > 10000"]
    call-SNPsVariantRecalibratorCreateModel{{"SNPsVariantRecalibratorCreateModel"}}
    scatter-L219C3-idx
    call-SNPGatherTranches{{"SNPGatherTranches"}}
    end
    subgraph scatter-L219C3-idx["range(length(HardFilterAndMakeSitesOnlyVcf.sites_only_vcf))"]
    call-SNPsVariantRecalibratorScattered{{"SNPsVariantRecalibratorScattered"}}
    end
    subgraph if-L252C3["num_gvcfs <= 10000"]
    call-SNPsVariantRecalibratorClassic{{"SNPsVariantRecalibratorClassic"}}
    end
    decl-is_small_callset>"is_small_callset"]
    subgraph scatter-L279C3-idx["range(length(HardFilterAndMakeSitesOnlyVcf.variant_filtered_vcf))"]
    call-ApplyRecalibration{{"ApplyRecalibration"}}
    if-L299C5
    end
    subgraph if-L299C5["!is_small_callset"]
    call-CollectMetricsSharded{{"CollectMetricsSharded"}}
    end
    subgraph if-L317C3["is_small_callset"]
    call-FinalGatherVcf{{"FinalGatherVcf"}}
    call-CollectMetricsOnFullVcf{{"CollectMetricsOnFullVcf"}}
    end
    subgraph if-L344C3["!is_small_callset"]
    call-GatherMetrics{{"GatherMetrics"}}
    end
    call-DynamicallyCombineIntervals -->  decl-unpadded_intervals
    decl-unpadded_intervals -->  scatter-L120C3-idx
    decl-unpadded_intervals -->  call-ImportGVCFs
    scatter-L120C3-idx -->  call-ImportGVCFs
    call-ImportGVCFs -->  call-GenotypeGVCFs
    decl-unpadded_intervals -->  call-GenotypeGVCFs
    scatter-L120C3-idx -->  call-GenotypeGVCFs
    call-GenotypeGVCFs -->  call-HardFilterAndMakeSitesOnlyVcf
    scatter-L120C3-idx -->  call-HardFilterAndMakeSitesOnlyVcf
    call-HardFilterAndMakeSitesOnlyVcf -->  call-SitesOnlyGatherVcf
    call-SitesOnlyGatherVcf -->  call-IndelsVariantRecalibrator
    call-SitesOnlyGatherVcf -->  call-SNPsVariantRecalibratorCreateModel
    call-HardFilterAndMakeSitesOnlyVcf -->  scatter-L219C3-idx
    call-HardFilterAndMakeSitesOnlyVcf -->  call-SNPsVariantRecalibratorScattered
    scatter-L219C3-idx -->  call-SNPsVariantRecalibratorScattered
    call-SNPsVariantRecalibratorCreateModel -->  call-SNPsVariantRecalibratorScattered
    call-SNPsVariantRecalibratorScattered -->  call-SNPGatherTranches
    call-SitesOnlyGatherVcf -->  call-SNPsVariantRecalibratorClassic
    call-HardFilterAndMakeSitesOnlyVcf -->  scatter-L279C3-idx
    scatter-L279C3-idx -->  call-ApplyRecalibration
    call-HardFilterAndMakeSitesOnlyVcf -->  call-ApplyRecalibration
    call-IndelsVariantRecalibrator -->  call-ApplyRecalibration
    call-SNPsVariantRecalibratorScattered -->  call-ApplyRecalibration
    call-SNPsVariantRecalibratorClassic -->  call-ApplyRecalibration
    call-SNPGatherTranches -->  call-ApplyRecalibration
    decl-is_small_callset -->  if-L299C5
    call-ApplyRecalibration -->  call-CollectMetricsSharded
    scatter-L279C3-idx -->  call-CollectMetricsSharded
    decl-is_small_callset -->  if-L317C3
    call-ApplyRecalibration -->  call-FinalGatherVcf
    call-FinalGatherVcf -->  call-CollectMetricsOnFullVcf
    decl-is_small_callset -->  if-L344C3
    call-CollectMetricsSharded -->  call-GatherMetrics
```
### Contributing
This project adheres to the Contributor Covenant code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to opensource@chanzuckerberg.com.

### Reporting Security Issues
Please disclose security issues responsibly by contacting security@chanzuckerberg.com.