from ..utils.functions import kde, pmf, get_data_hgh_indices, retrieve_intervention_info
from ..utils.constants import DATA_SIZE, DATA_DIST_RATIO, RUG_DIST_RATIO, RUG_SIZE, BORDER_COLOR, DATA_HGH_NUM, COLORs, COLORs_sim, BASE_COLOR

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

import numpy as np

class KDE_Cell_Comparative():
    def __init__(self, var, data, status, showData = True, mean_obs = False):
        """
            Parameters:
            --------
                data            A Data obj.
        """
        self.var = var        
        self.data = data  
        self.dags = data.get_dags()     
        self.status = status   
        self.showData = showData
        self.mean_obs = mean_obs
        ##
        self.plot = None
        ## 
        self.var_type = self.data.get_var_type(self.var)
        self.pp_samples = {} # Dict <dag_id>: numpy array
        if self.showData:
            self.observations = self.data.get_var_observations(self.var) ## 
        self.x_range = self.data.get_var_x_range(self.var)
        ## 
        self.kde_obs_cds = {}
        self.kde_interv_cds = {}
        if self.showData:
            self.data_cds = None
            self.data_cds_hghl = None
            self.data_cds_left = None
        # self.rug_obs_cds = None
        ## Bokeh glyphs of plot
        self.pp_line = {} ## kde line glyph
        self.i_pp_line = {}
        self.pp_scat = {} ## pmf dot glyph
        self.i_pp_scat = {}
        self.obs_left = None
        self.obs_hghl = None
        self.rug = None
        ##
        self.initialize_plot()

    def initialize_plot(self):                
        ## Rug plot cds
        # if self.var_type == "Continuous":
        #     r_data = self.pp_samples.flatten()
        #     self.rug_obs_cds = ColumnDataSource(data = {'x':r_data,'y':np.asarray([-1*max_v/RUG_DIST_RATIO]*len(r_data)),'size':np.asarray([RUG_SIZE]*len(r_data))})
        ## FIGURE and glyphs
        self.plot = figure(width = 400, height = 400, x_range = self.x_range, tools = "wheel_zoom,reset,box_zoom")
        self.plot.yaxis.visible = False
        self.plot.xaxis[0].axis_label = self.var
        self.plot.border_fill_color = BORDER_COLOR
        self.plot.min_border = 15
        self.plot.toolbar.logo = None
        ## 
        if self.mean_obs:
            self.pp_samples = np.mean( np.array([ self.data.get_var_pp_samples(self.var, dag_id) for dag_id,_ in enumerate(self.dags) ]), axis=0 )
            ## KDE cds
            if self.var_type == "Continuous":
                kde_est = kde(self.pp_samples)   
                self.kde_obs_cds = ColumnDataSource(data={'x':kde_est['x'],'y':kde_est['y']})
                self.pp_line = self.plot.line(x='x', y='y', line_width=2, line_color = BASE_COLOR, source = self.kde_obs_cds)
            else:
                kde_est = pmf(self.pp_samples)
                self.kde_obs_cds = ColumnDataSource(data={'x':kde_est['x'],'y':kde_est['y'],'y0':kde_est['y0']}) 
                self.pp_line = self.plot.segment(x0 = 'x', y0 ='y0', x1 = 'x', y1 = 'y', source = self.kde_obs_cds, line_alpha = 1.0, color = BASE_COLOR, line_width = 1)
                self.pp_scat= self.plot.scatter('x', 'y', source = self.kde_obs_cds, size = 4, fill_color = BASE_COLOR, fill_alpha = 1.0, line_color = BASE_COLOR)
            max_v = self.kde_obs_cds.data['y'].max()
        else:
            for dag_id,_ in enumerate(self.dags):
                self.pp_samples[dag_id] = self.data.get_var_pp_samples(self.var, dag_id) ## numpy array of posterior predictive samples
                ## KDE cds
                if self.var_type == "Continuous":
                    kde_est = kde(self.pp_samples[dag_id] )   
                    self.kde_obs_cds[dag_id] = ColumnDataSource(data={'x':kde_est['x'],'y':kde_est['y']})
                    self.pp_line[dag_id] = self.plot.line(x='x', y='y', line_width=2, line_color = COLORs[dag_id], source = self.kde_obs_cds[dag_id])
                else:
                    kde_est = pmf(self.pp_samples[dag_id] )
                    self.kde_obs_cds[dag_id]  = ColumnDataSource(data={'x':kde_est['x'],'y':kde_est['y'],'y0':kde_est['y0']}) 
                    self.pp_line[dag_id] = self.plot.segment(x0 = 'x', y0 ='y0', x1 = 'x', y1 = 'y', source = self.kde_obs_cds[dag_id] , line_alpha = 1.0, color = COLORs[dag_id], line_width = 1)
                    self.pp_scat[dag_id] = self.plot.scatter('x', 'y', source = self.kde_obs_cds[dag_id] , size = 4, fill_color = COLORs[dag_id], fill_alpha = 1.0, line_color = COLORs[dag_id])
            max_v = max([cds.data['y'].max() for _,cds in self.kde_obs_cds.items()])
        for dag_id,_ in enumerate(self.dags):
            ## KDE
            if self.var_type == "Continuous":
                self.kde_interv_cds[dag_id] = ColumnDataSource(data={'x':[],'y':[]})
                self.i_pp_line[dag_id] = self.plot.line(x='x', y='y', line_width=2, line_color = COLORs_sim[dag_id], source = self.kde_interv_cds[dag_id] )
            else:
                self.kde_interv_cds[dag_id]  = ColumnDataSource(data={'x':[],'y':[],'y0':[]})
                self.i_pp_line[dag_id] = self.plot.segment(x0 = 'x', y0 ='y0', x1 = 'x', y1 = 'y', source = self.kde_interv_cds[dag_id] , line_alpha = 0.5, color = COLORs_sim[dag_id], line_width = 1)
                self.i_pp_scat[dag_id] = self.plot.scatter('x', 'y', source = self.kde_interv_cds[dag_id] , size = 4, fill_color = COLORs_sim[dag_id], fill_alpha = 0.5, line_color = COLORs_sim[dag_id])
        ## DATA     
        ## Observvations cds        
        if self.showData:
            self.data_cds = ColumnDataSource(data={'x':self.observations,'y':np.asarray([-1*max_v/DATA_DIST_RATIO]*len(self.observations))})
            self.data_cds_hghl = ColumnDataSource(data = {'x':np.asarray([]),'y':np.asarray([])})
            self.data_cds_left = ColumnDataSource(data = {'x':self.observations,'y':np.asarray([-1*max_v/DATA_DIST_RATIO]*len(self.observations))})
            self.obs_left = self.plot.asterisk('x', 'y', size = DATA_SIZE, line_color = '#00CCFF', source = self.data_cds_left)
            self.obs_hghl = self.plot.asterisk('x', 'y', size = DATA_SIZE, line_color = 'orange', source = self.data_cds_hghl)
        # ## RUG PLOT
        # if self.var_type == "Continuous":
        #     self.rug = self.plot.dash('x', 'y', size='size', angle = 90.0, angle_units = 'deg', line_color = 'blue', source = self.rug_obs_cds)   
        
    def update_plot(self, intervention, i_type):
        """
        Parameters:
        -----------
            intervention: Dict(<i_var>: (value_idx, value))
            i_type: String in {"atomic", "shift","variance"}
        """ 
        i_var, i_value_idx, i_value = retrieve_intervention_info(intervention)
        iscellupdated =  0
        for dag_id,_ in enumerate(self.dags):
            samples = self.data.get_var_i_samples(i_var, self.var, dag_id, i_type)
            if i_var and samples is not None:
                iscellupdated = 1
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
            else:
                data = np.array([])
                if self.showData:
                    data_hgh_idx = []
            ## KDE CDS
            if self.var_type == "Continuous":
                kde_est = kde(data) 
                self.kde_interv_cds[dag_id].data = {'x':kde_est['x'],'y':kde_est['y']} 
            else:
                kde_est = pmf(data) 
                self.kde_interv_cds[dag_id].data = {'x':kde_est['x'],'y':kde_est['y'],'y0':kde_est['y0']} 
        ## OBSERVATIONS CDS
        if self.mean_obs:
            maxes = [self.kde_obs_cds.data['y'].max()]
        else:
            maxes = [cds.data['y'].max() for _,cds in self.kde_obs_cds.items()]
        maxes_i = [cds.data['y'].max() for _,cds in self.kde_interv_cds.items() if len(cds.data['y'])]
        if len(maxes_i):
            maxes.extend(maxes_i)
        max_v = max(maxes)
        if self.showData:
            data_obs = self.data_cds.data['x']
            if len(data_hgh_idx) == 0:
                data_idx = [i for i in range(len(data_obs))]
            else:
                data_idx = [i for i in range(len(data_obs)) if i not in data_hgh_idx]
            self.data_cds_left.data = {'x':data_obs[data_idx], 'y':np.asarray([-1*max_v/DATA_DIST_RATIO]*len(data_idx))}
            self.data_cds_hghl.data = {'x':data_obs[data_hgh_idx], 'y':np.asarray([-1*max_v/DATA_DIST_RATIO]*len(data_hgh_idx))}
            # ## RUG CDS
            # if self.var_type == "Continuous":
            #     self.rug_obs_cds.data = {'x':self.pp_samples.flatten(), 'y':np.asarray([-1*max_v/RUG_DIST_RATIO]*len(self.pp_samples.flatten())),'size':np.asarray([RUG_SIZE]*len(self.pp_samples.flatten()))}    
        ##
        if iscellupdated:
            self.x_range = self.data.get_var_i_x_range(self.var, i_var, i_type)  
        else:
            self.x_range = self.data.get_var_x_range(self.var)
        self.plot.x_range.start = self.x_range[0]
        self.plot.x_range.end = self.x_range[1]
        

    ## SETTERS-GETTERS
    def get_plot(self):
        return self.plot

    def get_glyphs(self):
        return self.pp_line, self.i_pp_line, self.pp_scat, self.i_pp_scat, self.obs_left, self.obs_hghl, self.rug