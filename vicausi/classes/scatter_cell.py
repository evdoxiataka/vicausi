from ..utils.constants import BORDER_COLOR
from ..utils.functions import retrieve_intervention_info

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

import numpy as np

class Scatter_Cell():

    def __init__(self, var1, var2, dag_id, data, status, showData = True):
        """
            Parameters:
            --------
                name            A String within the set {"<variableName>"}.
                control         A Control object
        """
        self.var1 = var1
        self.var2 = var2
        self.data = data
        self.dag_id = dag_id
        self.status = status
        self.showData = showData
        ##
        self.plot = None
        ## 
        self.var_type1 = self.data.get_var_type(self.var1)
        self.var_type2 = self.data.get_var_type(self.var2)
        self.x_range_var1 = self.data.get_var_x_range(self.var1)
        self.x_range_var2 = self.data.get_var_x_range(self.var2)
        self.pp_samples1 = self.data.get_var_pp_samples(self.var1, self.dag_id).flatten() ## numpy array of posterior predictive samples
        self.pp_samples2 = self.data.get_var_pp_samples(self.var2, self.dag_id).flatten()
        self.observations1 = self.data.get_var_observations(self.var1) ## 
        self.observations2 = self.data.get_var_observations(self.var2)
        ## 
        self.scatter_obs_cds = None
        self.scatter_interv_cds = None
        self.data_pairs_cds = None
        ## Bokeh glyphs of plot
        self.pp_circle = None
        self.obs_circle = None
        self.i_pp_circle = None
        ##
        self.initialize_plot()

    def initialize_plot(self):
        ## scatter plot cds
        self.scatter_obs_cds = ColumnDataSource(data = {'x':self.pp_samples1,'y':self.pp_samples2})
        self.scatter_interv_cds = ColumnDataSource(data = {'x':[],'y':[]})
        ## pairs of observations
        if self.showData:
            self.data_pairs_cds = ColumnDataSource(data = {'x':self.observations1,'y':self.observations2}) 
        ## FIGURE and glyphs
        self.plot = figure(width = 400, height = 400, x_range = self.x_range_var1, y_range = self.x_range_var2, tools = [])
        self.plot.xaxis[0].axis_label = self.var1
        self.plot.yaxis[0].axis_label = self.var2
    #     p.border_fill_color = BORDER_COLOR
        self.plot.min_border = 15
        self.plot.toolbar.logo = None
        ## SCATTER PLOT
        self.pp_circle = self.plot.circle('x', 'y', size = 4, color = 'blue', source = self.scatter_obs_cds, fill_alpha = 0.2)
        if self.showData:
            self.obs_circle = self.plot.circle('x', 'y', size = 5, color = '#00CCFF', source = self.data_pairs_cds, fill_alpha = 0.5)
        self.i_pp_circle = self.plot.circle('x', 'y', size = 4, color = 'orange', source = self.scatter_interv_cds, fill_alpha = 0.2)
        
    def update_plot(self, intervention, i_type):
        """
        Parameters:
        -----------
            samples1: numpy array of samples after intervention
            x_range1: tupple (xmin,xmax) of range of x-axis estimated for var across all dags
        """        
        ##
        i_var, i_value_idx, i_value = retrieve_intervention_info(intervention)
        samples1 = self.data.get_var_i_samples(i_var, self.var1, self.dag_id, i_type)
        samples2 = self.data.get_var_i_samples(i_var, self.var2, self.dag_id, i_type)
        if i_var and samples1 is not None:
            if self.status == "static":
                data1 = samples1
                data2 = samples2
            else:
                data1 = samples1[i_value_idx]
                data2 = samples2[i_value_idx]
            x_range = self.data.get_var_i_x_range(self.var1, i_var, i_type)
            y_range = self.data.get_var_i_x_range(self.var2, i_var, i_type)
        else:
            data1 = np.array([])
            data2 = np.array([])
            x_range = self.data.get_var_x_range(self.var1)
            y_range = self.data.get_var_x_range(self.var2)
        ##
        self.plot.x_range.start = x_range[0]
        self.plot.x_range.end = x_range[1]
        self.plot.y_range.start = y_range[0]
        self.plot.y_range.end = y_range[1]
        ## SCATTER CDS
        self.scatter_interv_cds.data = {'x':np.array(data1).flatten(),"y":np.array(data2).flatten()}##remove np.array 

    ## SETTERS-GETTERS
    def get_plot(self):
        return self.plot
    
    def get_glyphs(self):
        return self.pp_circle, self.obs_circle, self.i_pp_circle