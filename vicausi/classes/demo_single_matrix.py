from .data import Data
from .widget_single_matrix import Widget_Single_Matrix
from .causal_dag import Causal_DAG
from .scatter_matrix import Scatter_Matrix

css = '''
.bk.panel-widget-box {
  font-size: 14px;
  background-color: transparent;
  box-shadow: none;
  border: none;
}
'''

import panel as pn
pn.extension('katex', 'mathjax',raw_css=[css])

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
        ## Markdowns
        t_graphs = pn.pane.Markdown('''## Simulated Data of an Unidentified Causal Model''')
        t_dags = pn.pane.Markdown('''## Possible Causal Models''')
        t_interaction = pn.pane.Markdown('''Select an intervention above to see the simulated data of the intervention.''', style={'font-size': "18px",'margin-bottom': '0px'})
        ## Create Widget object
        widget = Widget_Single_Matrix(self.status, self.interventions, a_interventions, s_interventions, v_interventions)
        ##
        grid_obs = Scatter_Matrix(self.data, self.dag_id, self.var_order, self.status, self.showData)
        ##
        widget.register_callbacks_to_dags(causal_dags_obj)
        widget.register_callbacks_to_cells([grid_obs])
        ## DIAGRAMS - FIGURES 
        dags_cols = [pn.Column(pn.pane.Bokeh(causal_dags_obj[i].get_plot())) for i,_ in enumerate(causal_dags_obj)]
        if self.status not in ["static"]:
            grids_col = pn.Column(pn.Column(widget.slider, css_classes=['panel-widget-box']), grid_obs.get_grid())
        else:
            grids_col = pn.Column(grid_obs.get_grid())
        if len(self.interventions) == 1 and len(list(self.interventions.values())[0]) == 1:
            self._activate_radio_button_if_single_inter(widget)
            ## PLOT                
            self.plot = pn.Row(pn.Column(t_graphs, grids_col), pn.Column(t_dags,*dags_cols))
        else:                
            ## PLOT
            widget_boxes = widget.get_widget_box_without_slider()                
            self.plot = pn.Row(pn.Column(t_graphs,pn.Column(*widget_boxes, css_classes=['panel-widget-box']),t_interaction,grids_col), pn.Column(t_dags,*dags_cols))

    def _activate_radio_button_if_single_inter(self, widget):  
        i_type = list(self.interventions.keys())[0]
        i_var = self.interventions[i_type][0]
        if i_type == "atomic":
            widget.w_a.value = i_var
        elif i_type == "shift":
            widget.w_s.value = i_var
        elif i_type == "variance":
            widget.w_v.value = i_var

    def get_plot(self):
        return self.plot