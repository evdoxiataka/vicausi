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
        NUM_STATIC_INSTANCES = 3
        ## Create Data object
        self.data = Data(self.files)
        a_interventions, s_interventions, v_interventions = self.data.get_interventions()
        ##    
        causal_dags_ids = self.data.get_causal_dags_ids()
        causal_dags_obj = [Causal_DAG(self.data, dag_id) for dag_id in causal_dags_ids]
        if self.status not in ["static"]:
            ## Create Widget object
            widget = Widget_Single_Matrix(self.status, self.interventions, a_interventions, s_interventions, v_interventions)
            widget_boxes = widget.get_widget_box()
            ##
            grid_obs = Scatter_Matrix(self.data, self.dag_id, self.var_order, self.status, self.showData)
            ##
            widget.register_callbacks_to_dags(causal_dags_obj)
            widget.register_callbacks_to_cells([grid_obs])
            ## DIAGRAMS - FIGURES 
            cols = [pn.Column(pn.pane.Bokeh(causal_dags_obj[i].get_plot())) for i,_ in enumerate(causal_dags_obj)]
            self.plot = pn.Row(pn.Column(*widget_boxes),pn.Column(pn.Row(grid_obs.get_grid()),pn.Row(*cols)))
        else:
            widgets = []
            grid_obs = []
            for i_type, i_vars in self.interventions.items():
                for i_var in i_vars:
                    for i in range(NUM_STATIC_INSTANCES):
                        ## Create Widget object
                        widgets.append(Widget_Single_Matrix("i_value", {i_type:[i_var]}, a_interventions, s_interventions, v_interventions))
                        ##
                        grid_obs.append(Scatter_Matrix(self.data, self.dag_id, self.var_order, "i_value", self.showData))
                        ##
                        # if i == 0:
                        #     widgets[-1].register_callbacks_to_dags(causal_dags_obj)
                        widgets[-1].register_callbacks_to_cells([grid_obs[-1]])
                        ## set slider to ith i_value
                        slider_value_idx = 0
                        interventions = None
                        if i_type == "atomic":                            
                            interventions = a_interventions[i_var]
                        elif i_type == "shift":
                            interventions = s_interventions[i_var]
                        elif i_type == "variance":
                            interventions = v_interventions[i_var]
                        slider_value_idx = len(interventions)
                        slider_value_idx = i*int(slider_value_idx / NUM_STATIC_INSTANCES)
                        widgets[-1].set_slider_value(i_type, i_var, slider_value_idx)
                    ## DIAGRAMS - FIGURES 
                    dags_cols = [pn.Column(pn.pane.Bokeh(causal_dags_obj[i].get_plot())) for i,_ in enumerate(causal_dags_obj)]
                    grids_cols = [pn.Column(grid_obs[i].get_grid()) for i,_ in enumerate(grid_obs)]
                    self.plot = pn.Column(pn.Row(*grids_cols),pn.Row(*dags_cols))
        
    def get_plot(self):
        return self.plot