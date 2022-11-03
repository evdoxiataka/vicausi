from .data import Data
from .widget import Widget
from .causal_dag import Causal_DAG

import panel as pn
pn.extension('katex', 'mathjax')

class Demo():
    def __init__(self, files, var_order, status = "i_value", addToggles = False, showData = False):
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
        causal_dags_obj = [Causal_DAG(self.data, dag_id, self.var_order, self.status, self.showData) for dag_id in causal_dags_ids]
        ##
        widget.register_callbacks_to_cells(causal_dags_obj)
        ## DIAGRAMS - FIGURES 
        cols = [dag.get_dag_col() for dag in causal_dags_obj]
        self.plot = pn.Row(pn.Column(*widget_boxes),pn.Row(*cols))
        
    def get_plot(self):
        return self.plot