from ..utils.functions import kde, pmf, get_data_hgh_indices, retrieve_intervention_info
from ..utils.constants import DATA_SIZE, DATA_DIST_RATIO, RUG_DIST_RATIO, RUG_SIZE, BORDER_COLOR, DATA_HGH_NUM

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

import numpy as np

class KDE_Cell():
    def __init__(self, var, dag_id, data, status, showData = True):
        """
            Parameters:
            --------
                data            A Data obj.
        """
        self.var = var
        self.dag_id = dag_id
        self.data = data        
        self.status = status   
        self.showData = showData
        ##
        self.plot = None
        ## 
        self.var_type = self.data.get_var_type(self.var)
        self.pp_samples = self.data.get_var_pp_samples(self.var, self.dag_id) ## numpy array of posterior predictive samples
        if self.showData:
            self.observations = self.data.get_var_observations(self.var) ## 
        self.x_range = self.data.get_var_x_range(self.var)
        ## 
        self.kde_obs_cds = None
        self.kde_interv_cds = None
        if self.showData:
            self.data_cds = None
            self.data_cds_hghl = None
            self.data_cds_left = None
        self.rug_obs_cds = None
        ## Bokeh glyphs of plot
        self.pp_line = None ## kde line glyph
        self.i_pp_line = None
        self.pp_scat = None ## pmf dot glyph
        self.i_pp_scat = None
        self.obs_left = None
        self.obs_hghl = None
        self.rug = None
        ##
        self.initialize_plot()

    def initialize_plot(self):
        ## KDE cds
        if self.var_type == "Continuous":
            kde_est = kde(self.pp_samples)   
            self.kde_obs_cds = ColumnDataSource(data={'x':kde_est['x'],'y':kde_est['y']})
            self.kde_interv_cds = ColumnDataSource(data={'x':[],'y':[]})
        else:
            kde_est = pmf(self.pp_samples)
            self.kde_obs_cds = ColumnDataSource(data={'x':kde_est['x'],'y':kde_est['y'],'y0':kde_est['y0']})
            self.kde_interv_cds = ColumnDataSource(data={'x':[],'y':[],'y0':[]})                    
        ## Observvations cds
        max_v = self.kde_obs_cds.data['y'].max()
        if self.showData:
            self.data_cds = ColumnDataSource(data={'x':self.observations,'y':np.asarray([-1*max_v/DATA_DIST_RATIO]*len(self.observations))})
            self.data_cds_hghl = ColumnDataSource(data = {'x':np.asarray([]),'y':np.asarray([])})
            self.data_cds_left = ColumnDataSource(data = {'x':self.observations,'y':np.asarray([-1*max_v/DATA_DIST_RATIO]*len(self.observations))})
        ## Rug plot cds
        if self.var_type == "Continuous":
            r_data = self.pp_samples.flatten()
            self.rug_obs_cds = ColumnDataSource(data = {'x':r_data,'y':np.asarray([-1*max_v/RUG_DIST_RATIO]*len(r_data)),'size':np.asarray([RUG_SIZE]*len(r_data))})
        ## FIGURE and glyphs
        self.plot = figure(width = 400, height = 400, x_range = self.x_range, tools = "wheel_zoom,reset,box_zoom")
        self.plot.yaxis.visible = False
        self.plot.xaxis[0].axis_label = self.var
        self.plot.border_fill_color = BORDER_COLOR
        self.plot.min_border = 15
        self.plot.toolbar.logo = None
        ## KDE
        if self.var_type == "Continuous":
            self.pp_line = self.plot.line(x='x', y='y', line_width=2, line_color = 'blue', source = self.kde_obs_cds)
            self.i_pp_line = self.plot.line(x='x', y='y', line_width=2, line_color = 'orange', source = self.kde_interv_cds)
        else:
            self.pp_line = self.plot.segment(x0 = 'x', y0 ='y0', x1 = 'x', y1 = 'y', source = self.kde_obs_cds, line_alpha = 1.0, color = "blue", line_width = 1)
            self.pp_scat = self.plot.scatter('x', 'y', source = self.kde_obs_cds, size = 4, fill_color = "blue", fill_alpha = 1.0, line_color = "blue")
            self.i_pp_line = self.plot.segment(x0 = 'x', y0 ='y0', x1 = 'x', y1 = 'y', source = self.kde_interv_cds, line_alpha = 0.5, color = "orange", line_width = 1)
            self.i_pp_scat = self.plot.scatter('x', 'y', source = self.kde_interv_cds, size = 4, fill_color = "orange", fill_alpha = 0.5, line_color = "orange")
        ## DATA     
        if self.showData:
            self.obs_left = self.plot.asterisk('x', 'y', size = DATA_SIZE, line_color = '#00CCFF', source = self.data_cds_left)
            self.obs_hghl = self.plot.asterisk('x', 'y', size = DATA_SIZE, line_color = 'orange', source = self.data_cds_hghl)
        ## RUG PLOT
        if self.var_type == "Continuous":
            self.rug = self.plot.dash('x', 'y', size='size', angle = 90.0, angle_units = 'deg', line_color = 'blue', source = self.rug_obs_cds)   
        
    def update_plot(self, intervention, i_type):
        """
        Parameters:
        -----------
            intervention: Dict(<i_var>: (value_idx, value))
            i_type: String in {"atomic", "shift","variance"}
        """ 
        i_var, i_value_idx, i_value = retrieve_intervention_info(intervention)
        samples = self.data.get_var_i_samples(i_var, self.var, self.dag_id, i_type)
        if i_var and samples is not None:
            if self.status in ["i_value","animated"] and self.var == i_var and i_type == "atomic":
                data = np.array([samples[i_value_idx[0]][0][0][0]])
                if self.showData:
                    data_hgh_idx = get_data_hgh_indices(i_value[0], self.data_cds.data['x'], DATA_HGH_NUM)
            elif self.status == "static":
                data = samples
                if self.showData:
                    data_hgh_idx = []
            else:
                data = samples[i_value_idx]
                if self.showData:
                    data_hgh_idx = []
            self.x_range = self.data.get_var_i_x_range(self.var, i_var, i_type)                
        else:
            data = np.array([])
            self.x_range = self.data.get_var_x_range(self.var)
            if self.showData:
                data_hgh_idx = []
        ##
        self.plot.x_range.start = self.x_range[0]
        self.plot.x_range.end = self.x_range[1]
        ## KDE CDS
        if self.var_type == "Continuous":
            kde_est = kde(data) 
            self.kde_interv_cds.data = {'x':kde_est['x'],'y':kde_est['y']} 
        else:
            kde_est = pmf(data) 
            self.kde_interv_cds.data = {'x':kde_est['x'],'y':kde_est['y'],'y0':kde_est['y0']} 
        ## OBSERVATIONS CDS
        max_v = np.concatenate((self.kde_obs_cds.data['y'], self.kde_interv_cds.data['y']), axis=None).max()
        if self.showData:
            data_obs = self.data_cds.data['x']
            if len(data_hgh_idx) == 0:
                data_idx = [i for i in range(len(data_obs))]
            else:
                data_idx = [i for i in range(len(data_obs)) if i not in data_hgh_idx]
            self.data_cds_left.data = {'x':data_obs[data_idx], 'y':np.asarray([-1*max_v/DATA_DIST_RATIO]*len(data_idx))}
            self.data_cds_hghl.data = {'x':data_obs[data_hgh_idx], 'y':np.asarray([-1*max_v/DATA_DIST_RATIO]*len(data_hgh_idx))}
        ## RUG CDS
        if self.var_type == "Continuous":
            self.rug_obs_cds.data = {'x':self.pp_samples.flatten(), 'y':np.asarray([-1*max_v/RUG_DIST_RATIO]*len(self.pp_samples.flatten())),'size':np.asarray([RUG_SIZE]*len(self.pp_samples.flatten()))}    

    ## SETTERS-GETTERS
    def get_plot(self):
        return self.plot

    def get_glyphs(self):
        return self.pp_line, self.i_pp_line, self.pp_scat, self.i_pp_scat, self.obs_left, self.obs_hghl, self.rug