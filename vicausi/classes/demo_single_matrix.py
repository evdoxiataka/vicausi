from .data import Data
from .widget_single_matrix import Widget_Single_Matrix
from .causal_dag import Causal_DAG
from .scatter_matrix import Scatter_Matrix
from ..utils.constants import NUM_STATIC_INSTANCES

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
                interventions: Dict {"<i_type>":List of "i_var"} <i_type> in {"atomic","shift","variance"}
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
        ##    
        causal_dags_ids = self.data.get_causal_dags_ids()
        causal_dags_obj = [Causal_DAG(self.data, dag_id) for dag_id in causal_dags_ids]
        ## markdowns
        t_graphs = pn.pane.Markdown('''
                                ### Simulated Data of an Unidentified Causal Model
                                ''')
        t_dags = pn.pane.Markdown('''
                                ### Which of the following models (if any) corresponds to the data presented above?
                                ''')
        if self.status not in ["static"]:
            ## Create Widget object
            widget = Widget_Single_Matrix(self.status, self.interventions, a_interventions, s_interventions, v_interventions)
            widget_boxes = widget.get_widget_box_without_slider()
            ##
            grid_obs = Scatter_Matrix(self.data, self.dag_id, self.var_order, self.status, self.showData)
            ##
            widget.register_callbacks_to_dags(causal_dags_obj)
            widget.register_callbacks_to_cells([grid_obs])
            ## DIAGRAMS - FIGURES 
            cols = [pn.Column(pn.pane.Bokeh(causal_dags_obj[i].get_plot())) for i,_ in enumerate(causal_dags_obj)]
            self.plot = pn.Column(pn.Column(*widget_boxes),pn.Column(pn.Column(t_graphs, widget.slider, grid_obs.get_grid()),pn.Column(t_dags, pn.Row(*cols))))
        else:
            widgets = []
            grid_obs = []
            for i in range(NUM_STATIC_INSTANCES):
                ## Create Widget object
                widgets.append(Widget_Single_Matrix("i_value", self.interventions, a_interventions, s_interventions, v_interventions))
                ##
                grid_obs.append(Scatter_Matrix(self.data, self.dag_id, self.var_order, "i_value", self.showData))
                ##
                if i == 0:
                    widgets[i].register_callbacks_to_dags(causal_dags_obj)
                widgets[i].register_callbacks_to_cells([grid_obs[-1]])
            ## register callback in case of more than one intervention to link widgets and update slider
            if len(widgets)>1:
                widgets[0].register_callbacks_in_static(widgets[1:])
            ## DIAGRAMS - FIGURES 
                dags_cols = [pn.Column(pn.pane.Bokeh(causal_dags_obj[i].get_plot())) for i,_ in enumerate(causal_dags_obj)]
                grids_cols = [pn.Column(widgets[i].slider,grid_obs[i].get_grid()) for i,_ in enumerate(grid_obs)]                
            ## if single intervention is given, click the radiobutton through code
            if len(self.interventions) == 1 and len(list(self.interventions.values())[0]) == 1:
                i_type = list(self.interventions.keys())[0]
                i_var = self.interventions[i_type][0]
                if i_type == "atomic":
                    widgets[0].w_a.value = i_var
                elif i_type == "shift":
                    widgets[0].w_s.value = i_var
                elif i_type == "variance":
                    widgets[0].w_v.value = i_var
                    [widget.slider.value for widget in widgets]
                ## PLOT                
                self.plot = pn.Column(pn.Column(t_graphs, pn.Row(*grids_cols)), pn.Column(t_dags,pn.Row(*dags_cols)))
            else:                
                ## PLOT
                widget_boxes = widgets[0].get_widget_box_without_slider()                
                self.plot = pn.Column(pn.Column(*widget_boxes), pn.Column(t_graphs,pn.Row(*grids_cols)), pn.Column(t_dags,pn.Row(*dags_cols)))
        
    def get_plot(self):
        return self.plot