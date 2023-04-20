# vicausi: Visualizer of Causal Assumptions and Uncertainty-Aware Simulations of Interventions

This is a visualization tool that automatically transforms the outputs of the simulation pipeline of interventions found in <url>  into uncertainty-aware visualizations.
    
The classical **scatter plot matrix** is used for the visualization of the simulated probabilistic data before and after an intervention. 
    
This is enhanced with **interaction** or **animation** to present the simulated data of interventions in slices conditioned on the intervened variable.

- **examples/insomnia.ipynb**: this notebook demonstrates how vicausi can be used to present the simulated data of interventions generated from this pipeline: https://github.com/evdoxiataka/simulated_interventions_pipeline. The insomnia-anxiety-tiredness problem that was used in the user study for evaluating visualization of probabilistic simulated interventions: https://github.com/evdoxiataka/simulated_interventions_study_analysis is used as an example. The folder contains the **npz** files of simulated data used in this user study. 
    
The following videos demonstrate the three visualization modes offered by the tool for the presentation of the simulated data after the intervention.

INTERACTIVE:

https://user-images.githubusercontent.com/37831445/233374701-3ce53253-e71a-4b8d-a21c-645cd5bcf5b6.mp4

ANIMATED:

https://user-images.githubusercontent.com/37831445/233376718-0a6c3683-1586-4457-a3b9-9c4c16622036.mp4

STATIC:

https://user-images.githubusercontent.com/37831445/233374146-c24af4cb-4335-478b-bae6-ed3a82cfba25.mp4
