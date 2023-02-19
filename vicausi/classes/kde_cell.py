from ..utils.functions import kde, pmf, get_data_hgh_indices, retrieve_intervention_info
from ..utils.constants import DATA_SIZE, DATA_DIST_RATIO, RUG_DIST_RATIO, RUG_SIZE, BORDER_COLOR, DATA_HGH_NUM, num_i_values, BASE_COLOR, SECONDARY_COLOR, STATIC_BASE_COLOR

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, ColorBar, LinearColorMapper, Legend, Line
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
        self.base_color = BASE_COLOR
        self.second_color = SECONDARY_COLOR
        if self.status == "static":
            self.base_color = STATIC_BASE_COLOR
        ##
        self.y_max = None
        self.y_min = None
        ##
        self.plot = None
        self.plot_colorbar = None
        self.plot_legend = None
        self.legend = None
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
        ## CDS
        ## KDE
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
        ## OBSERVATIONS
        max_v = self.kde_obs_cds.data['y'].max()
        if self.showData:
            self.data_cds = ColumnDataSource(data={'x':self.observations,'y':np.asarray([-1*max_v/DATA_DIST_RATIO]*len(self.observations))})
            self.data_cds_hghl = ColumnDataSource(data = {'x':np.asarray([]),'y':np.asarray([])})
            self.data_cds_left = ColumnDataSource(data = {'x':self.observations,'y':np.asarray([-1*max_v/DATA_DIST_RATIO]*len(self.observations))})
        ## RUG PLOT
        if self.var_type == "Continuous":
            r_data = self.pp_samples.flatten()
            self.rug_obs_cds = ColumnDataSource(data = {'x':r_data,'y':np.asarray([-1*max_v/RUG_DIST_RATIO]*len(r_data)),'size':np.asarray([RUG_SIZE]*len(r_data))})
        ## FIGURE
        y_min = -1*max_v/RUG_DIST_RATIO - 0.6*(max_v/RUG_DIST_RATIO)
        self.plot = figure(width = 420, height = 420, tools = [], x_range = self.x_range,y_range = (y_min,max_v+0.1*max_v))#"wheel_zoom,reset,box_zoom" 
        self.plot.xaxis.axis_label_text_font_size = "13pt"
        self.plot.xaxis.major_label_text_font_size = "11pt"
        # self.plot.ygrid.grid_line_color = None
        # self.plot.axis.axis_label_text_font_style = 'bold'        
        self.plot.yaxis.visible = False
        self.plot.xaxis[0].axis_label = self.var
        self.plot.xaxis[0].ticker.desired_num_ticks = 4
        self.plot.border_fill_color = BORDER_COLOR
        self.plot.min_border = 14
        self.plot.toolbar.logo = None
        ## KDE GLYPHS
        if self.var_type == "Continuous":
            self.pp_line = self.plot.line(x='x', y='y', line_width=2, line_color = self.base_color, source = self.kde_obs_cds)
            if self.status not in ['static']:
                self.i_pp_line = self.plot.line(x='x', y='y', line_width=2, line_color = self.second_color, source = self.kde_interv_cds)
            else:
                mapper = LinearColorMapper(palette = cc.b_linear_bmy_10_95_c71, low = 0, high = num_i_values-1)
                # mapper = LinearColorMapper(palette = cc.b_rainbow_bgyrm_35_85_c69[29:], low = 0, high = num_i_values-1)
                self.i_pp_line = self.plot.multi_line(xs='x', ys='y', line_width=2, line_color = {"field":"group", "transform":mapper}, source = self.kde_interv_cds)
                ## Dummy figure for colorbar
                self.plot_colorbar = figure(height=600, width=0, title = "",title_location = "left",toolbar_location=None, min_border=0, outline_line_color=None)
                self.plot_colorbar.title.align = "right"
                self.plot_colorbar.title.text_font_size = "16px"
                self.plot_colorbar.title.text_font_style = "normal"
                self.plot_colorbar.margin = 0
                self.plot_colorbar.min_border = 0
                self.plot_colorbar.frame_width=0
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
            self.pp_line = self.plot.segment(x0 = 'x', y0 ='y0', x1 = 'x', y1 = 'y', source = self.kde_obs_cds, line_alpha = 1.0, color = self.base_color, line_width = 1)
            self.pp_scat = self.plot.scatter('x', 'y', source = self.kde_obs_cds, size = 4, fill_color = self.base_color, fill_alpha = 1.0, line_color = self.base_color)
            self.i_pp_line = self.plot.segment(x0 = 'x', y0 ='y0', x1 = 'x', y1 = 'y', source = self.kde_interv_cds, line_alpha = 0.5, color = self.second_color, line_width = 1)
            self.i_pp_scat = self.plot.scatter('x', 'y', source = self.kde_interv_cds, size = 4, fill_color = self.second_color, fill_alpha = 0.5, line_color = self.second_color)
        ## LEGEND   
        self.plot_legend = figure(width=140, height=140,min_border=0,toolbar_location=None, outline_line_color=None)
        self.plot_legend.yaxis.visible = False
        self.plot_legend.xaxis.visible = False
        self.plot_legend.xgrid.grid_line_color = None
        self.plot_legend.ygrid.grid_line_color = None

        source = ColumnDataSource(data=dict(x=[0,1], y=[1,1]))
        line_glyph1 = Line(x="x", y="y", line_color=self.base_color, line_width=2)
        line1 = self.plot_legend.add_glyph(source, line_glyph1)
        line1.visible = False
        if self.status not in ['static']:
            line_glyph2 = Line(x="x", y="y", line_color=self.second_color, line_width=2)
            line2 = self.plot_legend.add_glyph(source, line_glyph2)
            line2.visible = False   
            self.legend = Legend(items=[("before interv.", [line1]), ("after interv.", [line2])], location="center", orientation="vertical",
                        border_line_color="white", title='', title_text_font_size = '12pt', title_text_font_style = 'normal', label_text_font_size = '12pt')
        else:
            self.legend = Legend(items=[("before interv.", [line1])], location="center", orientation="vertical",
                        border_line_color="white", title='', title_text_font_size = '12pt', title_text_font_style = 'normal', label_text_font_size = '12pt')
        self.plot_legend.add_layout(self.legend, "center")    
        ## DATA     
        if self.showData:
            self.obs_left = self.plot.asterisk('x', 'y', size = DATA_SIZE, line_color = '#00CCFF', source = self.data_cds_left)
            self.obs_hghl = self.plot.asterisk('x', 'y', size = DATA_SIZE, line_color = self.second_color, source = self.data_cds_hghl)
        ## RUG PLOT
        if self.var_type == "Continuous":
            self.rug = self.plot.dash('x', 'y', size='size', angle = 90.0, angle_units = 'deg', line_color = self.base_color, source = self.rug_obs_cds)   

    def update_plot(self, intervention, i_type):
        """
        Parameters:
        -----------
            intervention: Dict(<i_var>: (value_idx, value))
            i_type: String in {"atomic", "shift","variance"}
        """ 
        ##
        i_var, i_value_idx, i_value = retrieve_intervention_info(intervention)
        ##
        if i_type == "stratify":
            samples_idx = self.data.get_var_pp_samples_idx(i_var, self.dag_id, i_value[0])
            data = self.pp_samples.flatten()[samples_idx]
        else:
            samples = self.data.get_var_i_samples(i_var, self.var, self.dag_id, i_type)
            if i_var and samples is not None:
                if self.status in ["i_value","animated"] and self.var == i_var and i_type == "atomic":
                    data = samples[i_value_idx]
                    if self.showData:
                        data_hgh_idx = get_data_hgh_indices(i_value[0], self.data_cds.data['x'], DATA_HGH_NUM)
                elif self.status == "static":
                    data = samples
                    # data = samples[[*range(0,len(samples),int(len(samples)/num_i_values))]]
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
                ## fix limits of y axis
                y_max = self.data.get_kde_y_range(i_var, self.var, self.dag_id, i_type, self.kde_obs_cds.data['y'].max())
                self.y_max = y_max + 0.05*y_max
                self.y_min = -1*self.y_max/RUG_DIST_RATIO - 0.6*(self.y_max/RUG_DIST_RATIO)
                self.plot.y_range.end = self.y_max
                self.plot.y_range.start = self.y_min
                ##
                kde_est = kde(data) 
                self.kde_interv_cds.data = {'x':kde_est['x'],'y':kde_est['y']}             
            else:
                x_list = []
                y_list = []
                group_id = []                
                if len(data):
                    i_values_edges = [*range(0,len(data),int(len(data)/num_i_values))]
                    i_values = self.data.get_interventions(self.dag_id)
                    mean_group_intev_values = [(i_values[i_type][i_var][i]+i_values[i_type][i_var][i+1])/2. for i in i_values_edges]
                    for idx,_ in enumerate(i_values_edges):
                        if idx == len(i_values_edges)-1:
                            break
                        idx1 = i_values_edges[idx]
                        idx2 = i_values_edges[idx+1]
                        kde_est = kde(data[[*range(idx1,idx2)]].flatten())
                        x_list.append(kde_est['x'])
                        y_list.append(kde_est['y'])                        
                        group_id.append(mean_group_intev_values[idx])
                        ##
                        if i_type == "shift":
                            self.plot_colorbar.title.text = "after interv.: "+i_var+" shift x"
                        elif i_type == "variance":
                            self.plot_colorbar.title.text = "after interv.: "+i_var+" variance x"
                        else:
                            self.plot_colorbar.title.text = "after interv.: "+i_var
                        self.color_bar.color_mapper.high = max(mean_group_intev_values)
                        self.color_bar.color_mapper.low = min(mean_group_intev_values)
                        self.color_bar.visible = True
                self.kde_interv_cds.data = {'x':x_list,'y':y_list,'group':group_id} 
                ## COLORBAR
                if len(x_list) == 0:
                    self.plot_colorbar.title.text = ""
                    self.color_bar.visible = False
        else:
            kde_est = pmf(data) 
            self.kde_interv_cds.data = {'x':kde_est['x'], 'y':kde_est['y'], 'y0':kde_est['y0']} 
        ## OBSERVATIONS CDS
        if self.y_max:
            max_v = self.y_max
        else:
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

    ## CALLBACK
    def set_empy_callback(self, attr, old, new):
        pass

    ## SETTERS-GETTERS
    def get_plot(self):
        return self.plot

    def get_glyphs(self):
        return self.pp_line, self.i_pp_line, self.pp_scat, self.i_pp_scat, self.obs_left, self.obs_hghl, self.rug