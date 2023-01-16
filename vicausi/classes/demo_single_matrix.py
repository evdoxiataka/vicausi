from .data import Data
from .widget_single_matrix import Widget_Single_Matrix
from .causal_dag import Causal_DAG
from .scatter_matrix import Scatter_Matrix

import panel as pn
pn.extension('katex', 'mathjax')

class Demo_Single_Matrix():
    def __init__(self, files, dag_id, var_order, status, interventions, showData = False):
        """
            Parameters:
            --------
                files: List of npz files - one per dag
                dag_id: Int index to files list of model id whose scatter matrix will be presented
                var_order: List of vars given in order to be presented in scatter matrix
                status: String in {"static","i_value","i_density","i_range", "animated"}
                interventions: Dict {"<i_type>":"i_var"} <i_type> in {"atomic","shift","variance"}
                showData: Boolean to include observations in graphs                
        """
        self.files = files
        self.dag_id = dag_id
        self.var_order = var_order
        self.status = status
        self.interventions = interventions
        self.showData = showData        
        ##
        self.plot = None
        self.dag_plots = None
        self.data = None
        ##
        self.initialize_plot()

    def initialize_plot(self):
        ## Create Data object
        self.data = Data(self.files)
        a_interventions, s_interventions, v_interventions = self.data.get_interventions()

        ## Create Widget object
        widget = Widget_Single_Matrix(self.status, self.interventions, a_interventions, s_interventions, v_interventions)
        widget_boxes = widget.get_widget_box()
        ##    
        causal_dags_ids = self.data.get_causal_dags_ids()
        causal_dags_obj = [Causal_DAG(self.data, dag_id) for dag_id in causal_dags_ids]
        ##
        grid_obs = Scatter_Matrix(self.data, self.dag_id, self.var_order, self.status, self.showData)
        ##
        widget.register_callbacks_to_cells(causal_dags_obj, [grid_obs])
        ## DIAGRAMS - FIGURES 
        cols = [pn.Column(pn.pane.Bokeh(causal_dags_obj[i].get_plot())) for i,_ in enumerate(causal_dags_obj)]
        self.plot = pn.Row(pn.Column(*widget_boxes),pn.Column(pn.Row(grid_obs.get_grid()),pn.Row(*cols)))
        
    def get_plot(self):
        return self.plot