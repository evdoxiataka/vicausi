from ..utils.functions import kde, pmf, get_data_hgh_indices, retrieve_intervention_info
from ..utils.constants import DATA_SIZE, DATA_DIST_RATIO, RUG_DIST_RATIO, RUG_SIZE, BORDER_COLOR, DATA_HGH_NUM, num_i_values

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, ColorBar,LinearColorMapper
from bokeh.palettes import Oranges256, Magma256, Viridis256, Turbo256
import colorcet as cc
from bokeh.models import NumeralTickFormatter,BasicTicker

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
        self.plot_colorbar = None
        # self.colorbar_title = None
        # self.colorbar_callback = CustomJS(args=dict(title = self.colorbar_title), code='''
        #                     cb_obj.title = title;
        #                 ''')
        ## 
        self.var_type = self.data.get_var_type(self.var)
        self.pp_samples = self.data.get_var_pp_samples(self.var, self.dag_id) ## numpy array of posterior predictive samples
        if self.showData:
            self.observations = self.data.get_var_observations(self.var) ## 
        self.x_range = self.data.get_var_x_range(self.dag_id, self.var)
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
            if self.status not in ["static"]:
                self.kde_interv_cds = ColumnDataSource(data={'x':[],'y':[]})
            else:
                self.kde_interv_cds = ColumnDataSource(data={'x':[],'y':[],"group":[]})
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
        self.plot = figure(width = 420, height = 420, x_range = self.x_range, tools = [])#"wheel_zoom,reset,box_zoom"
        self.plot.xaxis.axis_label_text_font_size = "13pt"
        self.plot.xaxis.major_label_text_font_size = "11pt"
        # self.plot.axis.axis_label_text_font_style = 'bold'
        self.plot.yaxis.visible = False
        self.plot.xaxis[0].axis_label = self.var
        self.plot.border_fill_color = BORDER_COLOR
        self.plot.min_border = 15
        self.plot.toolbar.logo = None
        ## KDE
        if self.var_type == "Continuous":
            self.pp_line = self.plot.line(x='x', y='y', line_width=2, line_color = 'blue', source = self.kde_obs_cds)
            if self.status not in ['static']:
                self.i_pp_line = self.plot.line(x='x', y='y', line_width=2, line_color = 'orange', source = self.kde_interv_cds)
            else:
                mapper = LinearColorMapper(palette = cc.b_rainbow_bgyrm_35_85_c69[29:], low = 0, high = num_i_values-1)
                self.i_pp_line = self.plot.multi_line(xs='x', ys='y', line_width=2, line_color = {"field":"group", "transform":mapper}, source = self.kde_interv_cds)
                ## Dummy figure for colorbar
                self.plot_colorbar = figure(height=1260, width=120, title = "",toolbar_location=None, min_border=0, outline_line_color=None)
                self.color_bar = ColorBar(color_mapper = mapper,
                                    visible = False, 
                                    label_standoff = 8, 
                                    margin = 0,
                                    padding = 0,
                                    location = (0,0),
                                    formatter = NumeralTickFormatter(format='0.00 a'),
                                    ticker=BasicTicker(desired_num_ticks=30),
                                    bar_line_color='black',
                                    major_tick_line_color='black'
                                    )                                 
                self.plot_colorbar.add_layout(self.color_bar, 'right')
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
        if i_type == "stratify":
            samples_idx = self.data.get_var_pp_samples_idx(i_var, self.dag_id, i_value[0])
            data = self.pp_samples.flatten()[samples_idx]
        else:
            samples = self.data.get_var_i_samples(i_var, self.var, self.dag_id, i_type)
            if i_var and samples is not None:
                if self.status in ["i_value","animated"] and self.var == i_var and i_type == "atomic":
                    ## when i_value takes single value and we take a window of values around it
                    # i_idx = i_value_idx[0]
                    # i_idx_min = i_idx
                    # i_idx_max = i_idx
                    # if i_idx - 1 >= 0:
                    #     i_idx_min = i_idx - 1
                    # if i_idx + 1 < len(samples):
                    #     i_idx_max = i_idx + 2
                    # data = np.array([samples[[[*range(i_idx_min, i_idx_max, 1)]]][0][0][0]])
                    # ## when i_value is single value
                    # data = np.array([samples[i_value_idx[0]][0][0][0]])
                    ## when i_value takes values aroung a value
                    data = samples[i_value_idx]
                    if self.showData:
                        data_hgh_idx = get_data_hgh_indices(i_value[0], self.data_cds.data['x'], DATA_HGH_NUM)
                elif self.status == "static":
                    data = samples[[*range(0,len(samples),int(len(samples)/num_i_values))]]
                    if self.showData:
                        data_hgh_idx = []
                else:
                    data = samples[i_value_idx]
                    if self.showData:
                        data_hgh_idx = []
                self.x_range = self.data.get_var_i_x_range(self.dag_id, self.var, i_var, i_type)                
            else:
                data = np.array([])
                self.x_range = self.data.get_var_x_range(self.dag_id, self.var)
                if self.showData:
                    data_hgh_idx = []
            ##
            self.plot.x_range.start = self.x_range[0]
            self.plot.x_range.end = self.x_range[1]
        ## KDE CDS
        if self.var_type == "Continuous":
            if self.status not in ["static"]:
                kde_est = kde(data) 
                self.kde_interv_cds.data = {'x':kde_est['x'],'y':kde_est['y']} 
            else:
                x_list = []
                y_list = []
                group_id = []
                if len(data):
                    intev_values = [self.data.get_interventions(self.dag_id)[i_type][i_var][i] for i in [*range(0,len(samples),int(len(samples)/num_i_values))]]
                for i in range(len(data)):
                    if self.var == i_var and i_type == "atomic":
                        # kde_est = kde(np.array([data[i][0][0][0]])) 
                        kde_est = kde(data[i])
                    else:
                        kde_est = kde(data[i])
                    x_list.append(kde_est['x'])
                    y_list.append(kde_est['y'])
                    group_id.append(intev_values[i])
                self.kde_interv_cds.data = {'x':x_list,'y':y_list,'group':group_id} 
                ## COLORBAR
                if len(x_list):
                    self.plot_colorbar.title.text = i_var
                    self.color_bar.color_mapper.high = max(intev_values)
                    self.color_bar.color_mapper.low = min(intev_values)
                    self.color_bar.visible = True
                else:
                    self.plot_colorbar.title.text = ""
                    self.color_bar.visible = False
        else:
            kde_est = pmf(data) 
            self.kde_interv_cds.data = {'x':kde_est['x'], 'y':kde_est['y'], 'y0':kde_est['y0']} 
        ## OBSERVATIONS CDS
        max_v = np.concatenate((self.kde_obs_cds.data['y'], np.array(self.kde_interv_cds.data['y']).flatten()), axis=None).max()
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

    # def update_plot_stratification(self, intervention, i_type):
    #     """
    #     Parameters:
    #     -----------
    #         intervention: Dict(<i_var>: (value_idx, value))
    #         i_type: String in {"atomic", "shift","variance","stratify"}
    #     """ 
    #     i_var, _, i_value = retrieve_intervention_info(intervention)
    #     samples_idx = self.data.get_var_pp_samples_idx(i_var, self.dag_id, i_value)
    #     data = self.pp_samples.flatten()[samples_idx]
    #     # if i_var and samples is not None:
    #     #     # if self.status in ["i_value","animated"] and self.var == i_var:
    #     #     data = samples
    #             # if self.showData:
    #             #     data_hgh_idx = get_data_hgh_indices(i_value[0], self.data_cds.data['x'], DATA_HGH_NUM)
    #         # elif self.status == "static":
    #         #     data = samples
    #         #     if self.showData:
    #         #         data_hgh_idx = []
    #         # else:
    #         #     data = samples[i_value_idx]
    #         #     if self.showData:
    #         #         data_hgh_idx = []
    #         # self.x_range = self.data.get_var_i_x_range(self.var, i_var, i_type)                
    #     # else:
    #     #     data = np.array([])
    #         # if self.showData:
    #         #     data_hgh_idx = []
    #     ##
    #     # self.plot.x_range.start = self.x_range[0]
    #     # self.plot.x_range.end = self.x_range[1]
    #     ## KDE CDS
    #     if self.var_type == "Continuous":
    #         kde_est = kde(data) 
    #         self.kde_interv_cds.data = {'x':kde_est['x'],'y':kde_est['y']} 
    #     else:
    #         kde_est = pmf(data) 
    #         self.kde_interv_cds.data = {'x':kde_est['x'],'y':kde_est['y'],'y0':kde_est['y0']} 
    #     ## OBSERVATIONS CDS
    #     max_v = np.concatenate((self.kde_obs_cds.data['y'], self.kde_interv_cds.data['y']), axis=None).max()
    #     # if self.showData:
    #     #     data_obs = self.data_cds.data['x']
    #     #     if len(data_hgh_idx) == 0:
    #     #         data_idx = [i for i in range(len(data_obs))]
    #     #     else:
    #     #         data_idx = [i for i in range(len(data_obs)) if i not in data_hgh_idx]
    #     #     self.data_cds_left.data = {'x':data_obs[data_idx], 'y':np.asarray([-1*max_v/DATA_DIST_RATIO]*len(data_idx))}
    #     #     self.data_cds_hghl.data = {'x':data_obs[data_hgh_idx], 'y':np.asarray([-1*max_v/DATA_DIST_RATIO]*len(data_hgh_idx))}
    #     ## RUG CDS
    #     if self.var_type == "Continuous":
    #         self.rug_obs_cds.data = {'x':self.pp_samples.flatten(), 'y':np.asarray([-1*max_v/RUG_DIST_RATIO]*len(self.pp_samples.flatten())),'size':np.asarray([RUG_SIZE]*len(self.pp_samples.flatten()))}    

    ## CALLBACK
    def set_empy_callback(self, attr, old, new):
        pass

    ## SETTERS-GETTERS
    def get_plot(self):
        return self.plot

    def get_glyphs(self):
        return self.pp_line, self.i_pp_line, self.pp_scat, self.i_pp_scat, self.obs_left, self.obs_hghl, self.rug