import numpy as np
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

from ..utils.constants import BORDER_COLOR, COLORs, COLORs_sim, BASE_COLOR
from ..utils.functions import retrieve_intervention_info


class Scatter_Cell_Comparative():

    def __init__(self, var1, var2, data, status, showData = True, mean_obs = False):
        """
            Parameters:
            --------
                name            A String within the set {"<variableName>"}.
                control         A Control object
        """
        self.var1 = var1
        self.var2 = var2
        self.data = data
        self.dags = data.get_dags()
        self.status = status
        self.showData = showData
        self.mean_obs = mean_obs
        ##
        self.plot = None
        ## 
        self.var_type1 = self.data.get_var_type(self.var1)
        self.var_type2 = self.data.get_var_type(self.var2)
        self.x_range_var1 = self.data.get_var_x_range(self.var1)
        self.x_range_var2 = self.data.get_var_x_range(self.var2)
        self.pp_samples1 = {}
        self.pp_samples2 = {}
        # self.pp_samples1 = self.data.get_var_pp_samples(self.var1, self.dag_id).flatten() ## numpy array of posterior predictive samples
        # self.pp_samples2 = self.data.get_var_pp_samples(self.var2, self.dag_id).flatten()
        self.observations1 = self.data.get_var_observations(self.var1) ## 
        self.observations2 = self.data.get_var_observations(self.var2)
        ## 
        self.scatter_obs_cds = {}
        self.scatter_interv_cds = {}
        self.data_pairs_cds = None
        ## Bokeh glyphs of plot
        self.pp_circle = {}
        self.obs_circle = None
        self.i_pp_circle = {}
        ##
        self.initialize_plot()

    def initialize_plot(self): 
        ## FIGURE and glyphs
        self.plot = figure(width = 400, height = 400, x_range = self.x_range_var1, y_range = self.x_range_var2, tools = [])
        self.plot.xaxis[0].axis_label = self.var1
        self.plot.yaxis[0].axis_label = self.var2
        self.plot.border_fill_color = BORDER_COLOR
        self.plot.min_border = 15
        self.plot.toolbar.logo = None
        ## 
        if self.mean_obs:            
            self.pp_samples1 = np.mean( np.array([self.data.get_var_pp_samples(self.var1, dag_id).flatten() for dag_id,_ in enumerate(self.dags)]), axis=0 )
            self.pp_samples2 = np.mean( np.array([self.data.get_var_pp_samples(self.var2, dag_id).flatten() for dag_id,_ in enumerate(self.dags)]), axis=0 )
            ## scatter plot cds
            self.scatter_obs_cds = ColumnDataSource(data = {'x':self.pp_samples1,'y':self.pp_samples2})
            ## SCATTER PLOT
            self.pp_circle = self.plot.circle('x', 'y', size = 4, color = BASE_COLOR, source = self.scatter_obs_cds, fill_alpha = 0.2)
        else:
            for dag_id,_ in enumerate(self.dags):
                self.pp_samples1[dag_id] = self.data.get_var_pp_samples(self.var1, dag_id).flatten() ## numpy array of posterior predictive samples
                self.pp_samples2[dag_id] = self.data.get_var_pp_samples(self.var2, dag_id).flatten()
                ## scatter plot cds
                self.scatter_obs_cds[dag_id] = ColumnDataSource(data = {'x':self.pp_samples1[dag_id],'y':self.pp_samples2[dag_id]})
                ## SCATTER PLOT
                self.pp_circle[dag_id] = self.plot.circle('x', 'y', size = 4, color = COLORs[dag_id], source = self.scatter_obs_cds[dag_id], fill_alpha = 0.2)
        for dag_id,_ in enumerate(self.dags):
            self.scatter_interv_cds[dag_id] = ColumnDataSource(data = {'x':[],'y':[]})
            self.i_pp_circle[dag_id] = self.plot.circle('x', 'y', size = 4, color = COLORs_sim[dag_id], source = self.scatter_interv_cds[dag_id], fill_alpha = 0.2)
        ## pairs of observations
        if self.showData:
            self.data_pairs_cds = ColumnDataSource(data = {'x':self.observations1,'y':self.observations2})
            self.obs_circle = self.plot.circle('x', 'y', size = 5, color = '#00CCFF', source = self.data_pairs_cds, fill_alpha = 0.5)
        
    def update_plot(self, intervention, i_type):
        """
        Parameters:
        -----------
            samples1: numpy array of samples after intervention
            x_range1: tupple (xmin,xmax) of range of x-axis estimated for var across all dags
        """        
        ##
        i_var, i_value_idx, _ = retrieve_intervention_info(intervention)
        iscellupdated =  0
        for dag_id,_ in enumerate(self.dags):
            samples1 = self.data.get_var_i_samples(i_var, self.var1, dag_id, i_type)
            samples2 = self.data.get_var_i_samples(i_var, self.var2, dag_id, i_type)
            if i_var and samples1 is not None:
                iscellupdated = 1
                if self.status == "static":
                    data1 = samples1
                    data2 = samples2
                else:
                    data1 = samples1[i_value_idx]
                    data2 = samples2[i_value_idx]
            else:
                data1 = np.array([])
                data2 = np.array([])
            ## SCATTER CDS
            self.scatter_interv_cds[dag_id].data = {'x':np.array(data1).flatten(),"y":np.array(data2).flatten()}##remove np.array
        ##
        if iscellupdated:
            x_range = self.data.get_var_i_x_range(self.var1, i_var, i_type)
            y_range = self.data.get_var_i_x_range(self.var2, i_var, i_type)
        else:
            x_range = self.data.get_var_x_range(self.var1)
            y_range = self.data.get_var_x_range(self.var2)
        self.plot.x_range.start = x_range[0]
        self.plot.x_range.end = x_range[1]
        self.plot.y_range.start = y_range[0]
        self.plot.y_range.end = y_range[1]
         

    ## SETTERS-GETTERS
    def get_plot(self):
        return self.plot
    
    def get_glyphs(self):
        return self.pp_circle, self.obs_circle, self.i_pp_circle