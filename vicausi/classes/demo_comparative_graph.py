from .data import Data
from .widget import Widget
from .causal_dag import Causal_DAG
from .scatter_matrix_comparative import Scatter_Matrix_Comparative

import panel as pn
pn.extension('katex', 'mathjax')

class Demo_Comparative_Graph():
    def __init__(self, files, var_order, status = "i_value", addToggles = False, showData = False, mean_obs = False):
        """
            Parameters:
            --------
                files: List of npz files - one per dag
                var_order: List of vars given in order to be presented in scatter matrix
                status: String in {"static","i_value","i_density","i_range", "animated"}
                addToggles: Boolean to add view switches
                showData: Boolean to include observations in graphs                
        """
        self.files = files
        self.var_order = var_order
        self.status = status
        self.addToggles = addToggles
        self.showData = showData     
        self.mean_obs = mean_obs  
        self.grid = None		
        ##
        self.plot = None
        self.data = None
        ##
        self.initialize_plot()

    def initialize_plot(self):
        ## Create Data object
        self.data = Data(self.files)
        a_interventions, s_interventions, v_interventions = self.data.get_interventions()
        ## Create Widget object
        widget = Widget(self.status, a_interventions, s_interventions, v_interventions, self.addToggles)
        widget_boxes = widget.get_widget_box()
        ##    
        causal_dags_ids = self.data.get_causal_dags_ids()
        causal_dags_obj = [Causal_DAG(self.data, dag_id, mean_obs = self.mean_obs) for dag_id in causal_dags_ids]
        ##
        self.grid = Scatter_Matrix_Comparative(self.data, self.var_order, self.status, self.showData, self.mean_obs)
        ##
        widget.register_callbacks_to_cells(causal_dags_obj, [self.grid])
        ## DIAGRAMS - FIGURES 
        cols = [pn.pane.Bokeh(causal_dags_obj[i].get_plot()) for i,_ in enumerate(causal_dags_obj)]
        self.plot = pn.Row(pn.Column(*widget_boxes),pn.Column(pn.Row(*cols),self.grid.get_grid()))
        
    def get_plot(self):
        return self.plot