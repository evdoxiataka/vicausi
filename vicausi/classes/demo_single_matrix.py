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
    def __init__(self, files, dag_id, var_order, status, action_vars, showData = False):#, dags_presented,
        """
            Parameters:
            --------
                files: List of npz files - one per dag
                dag_id: Int index to files list of model id whose scatter matrix will be presented
                dags_presented: List of indexes in files to defice which DAGs will be shown
                var_order: List of vars given in order to be presented in scatter matrix
                status: String in {"static","i_value","i_density","i_range", "animated"}
                action_vars: Dict {"<i_type>":List of "i_var"} <i_type> in {"atomic","shift","variance","stratify"}
                showData: Boolean to include observations in graphs                
        """
        self.files = files
        self.dag_id = dag_id
        # self.dags_presented = dags_presented
        self.var_order = var_order
        self.status = status
        self.action_vars = action_vars
        self.showData = showData   
        ##
        self.width = 550
        self.font_size = "16px"
        self.style = {'font-size': self.font_size,'margin-bottom': '0px','margin-top': '-5px','top':'0px','height':'40px'}
        ##
        if len(self.action_vars) == 1 and len(list(self.action_vars.values())[0]) == 1:
            self.single_intervention = True
        else:
            self.single_intervention = False
        ##
        self.plot = None
        self.dag_objs = None
        self.data = None
        self.widget_obj = None
        self.grid_obj = None
        self.dags_col = None
        ##
        self.initialize_plot()

    # def _set_single_intervention(self):
    #     if len(self.action_vars) == 1 and len(list(self.action_vars.values())[0]) == 1:
    #         self.single_intervention = True
    #     else:
    #         self.single_intervention = False

    def initialize_plot(self): 
        ## Create Data object
        self.data = Data(self.files)       
        ## Create DAGs   
        causal_dags_ids = self.data.get_causal_dags_ids()
        self.dag_objs = [Causal_DAG(self.data, dag_id, self.status, self.var_order) for dag_id in causal_dags_ids]
        # causal_dags_obj = [Causal_DAG(self.data, dag_id, self.var_order) for dag_id in self.dags_presented]
        ## Markdowns
        t_graphs = pn.pane.Markdown('''## Simulated Data of an Unidentified Causal Model''')
        t_dags = pn.pane.Markdown(''' *DAGs of Possible Causal Models*''', style=self.style)
        if self.single_intervention and self.status == "animated":
            t_radio = pn.pane.Markdown('''*Select the intervention to start the animation of the simulated data of the intervention.*''', style=self.style, width = self.width)
        elif self.single_intervention == False:
            t_radio = pn.pane.Markdown('''*Select an intervention to see the simulated data of the intervention.*''', style=self.style, width = self.width)
        ## Create Widget object
        interv_data = self.data.get_interventions(self.dag_id) ## Dict (<itype>: Dict(<var>:List/numpy array of samples))
        self.widget_obj = Widget_Single_Matrix(self.status, self.action_vars, {itype:interv_data[itype] for itype in self.action_vars if itype in interv_data})
        ## Create Scatter Matrix
        self.grid_obj = Scatter_Matrix(self.data, self.dag_id, self.var_order, self.status, self.showData)
        ##
        self.widget_obj.register_callbacks_to_dags(self.dag_objs)
        self.widget_obj.register_callbacks_to_cells([self.grid_obj])
        ## DIAGRAMS - FIGURES 
        ## DAGS col
        dags_cols = [pn.Column(pn.pane.Bokeh(self.dag_objs[i].get_plot())) for i,_ in enumerate(self.dag_objs)]
        self.dags_col = pn.Column(t_dags,*dags_cols)
        ## GRID col
        if self.status not in ["static"]:
            grids_col = pn.Column(pn.Column(self.widget_obj.slider, css_classes=['panel-widget-box'], width = self.width), self.grid_obj.get_grid())
        else:
            grids_col = pn.Row(self.grid_obj.get_grid(),pn.pane.Bokeh(self.grid_obj.cells[self.var_order[-1]][-1].plot_colorbar))
        ## WIDGET BOX col
        if (self.single_intervention and self.status == "animated") or (self.single_intervention == False):
            widget_boxes = self.widget_obj.get_widget_box()
            widget_col = pn.Column(t_radio,*widget_boxes, css_classes=['panel-widget-box'])
            widget_row = pn.Column(t_radio, pn.Row(*widget_boxes, css_classes=['panel-widget-box']))
        if self.single_intervention:            
            ## PLOT
            if self.status not in ["animated"]:  
                self._activate_radio_button_if_single_inter(self.widget_obj)   
                self.plot = pn.Column(t_graphs, pn.Row(pn.Column(grids_col, self.widget_obj.toggle3), self.dags_col))                           
                # self.plot = pn.Row(pn.Column(t_graphs, grids_col, self.widget.toggle3), self.dags_col)
            else:
                # widget_boxes = self.widget.get_widget_box() 
                self.plot = pn.Column(t_graphs,widget_row, pn.Row(grids_col, self.dags_col))
                # self.plot = pn.Row(pn.Column(t_graphs,widget_col, grids_col), self.dags_col)
        else:                
            ## PLOT
            # widget_boxes = self.widget.get_widget_box() 
            if self.status not in ["animated"]:       
                self.plot = pn.Column(t_graphs,widget_row,pn.Row(pn.Column(grids_col,self.widget_obj.no_i_button),self.dags_col))        
                # self.plot = pn.Row(pn.Column(t_graphs,widget_col,t_interaction,grids_col,self.widget.no_i_button), self.dags_col)
            else:        
                self.plot = pn.Column(t_graphs,widget_row,pn.Row(grids_col,self.dags_col))       
                # self.plot = pn.Row(pn.Column(t_graphs,widget_col,t_interaction,grids_col), self.dags_col)
    
    def _activate_radio_button_if_single_inter(self, widget):  
        i_type = list(self.action_vars.keys())[0]
        i_var = self.action_vars[i_type][0]
        if i_type == "atomic":
            widget.w_a.value = i_var
        elif i_type == "shift":
            widget.w_s.value = i_var
        elif i_type == "variance":
            widget.w_v.value = i_var
        elif i_type == "stratify":
            widget.w_str.value = i_var

    ## GETTERS
    def get_plot(self):
        return self.plot
	
    def get_toggle_clicks(self):
        return self.widget_obj.toggle_clicks
		
    def get_intervention_selection(self):
        return self.widget_obj.intervention_selection
		
    def get_slider_selection(self):
        return self.widget_obj.slider_selection

    def get_first_dag(self):
        return pn.pane.Bokeh(self.dag_objs[0].get_plot())

    def get_scatter_matrix(self):
        return self.grid_obj.get_grid()

    def get_scatter_matrix_causal_models(self):
        return pn.Row(self.grid_obj.get_grid(),self.dags_col)