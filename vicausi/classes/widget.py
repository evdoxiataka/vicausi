from functools import partial
from bokeh.models import Toggle, Slider, RangeSlider
import asyncio
import numpy as np
import panel as pn
pn.extension()

class Widget():
    
    def __init__(self, status, a_interventions, s_interventions, v_interventions, addToggles = True):
        """
            Parameters:
            --------
                status           A String within the set {"i_value","static","animated","i_density","i_range"}.
                a_interventions  A Dict(<var>: List of intervention values)
        """
        ##
        self. status = status
        self.addToggles = addToggles
        self.a_interventions = a_interventions
        self.s_interventions = s_interventions
        self.v_interventions = v_interventions
        # self.dags = None ## List of Causal_DAGS objects
        ##
        self.w_a = None ## Radio button widget for atomic intervention
        self.w_s = None
        self.w_v = None
        self.slider = None
        self.no_i_button = None
        if self.addToggles:
            self.toggle1 = None ## toggle button for observations
            self.toggle2 = None ## toggle button for posterior predictive samples
            self.toggle3 = None ## toggle button for after intervention samples
        self.widget_box = []
        if self.status == "animated":
            self.widget_box.append(pn.Spacer(height=16))
        ##
        self.create_widgets()
        self.register_callbacks()
    
    def create_widgets(self):   
        ## Atomic
        self.w_a = pn.widgets.RadioBoxGroup(name ='varsRadios', options = list(self.a_interventions.keys()), inline=True, value = "")
        ti_a = pn.pane.Markdown('''
                                ### Atomic Intervention
                                $$var = x$$

                                $$var$$:
                                ''')
        self.widget_box.append(pn.WidgetBox(ti_a, self.w_a))
        ## Shift - Variance
        if self.s_interventions:
            ## Shift
            self.w_s = pn.widgets.RadioBoxGroup(name ='varsRadios', options = list(self.s_interventions.keys()), inline=True, value = "")
            ti_s = pn.pane.Markdown('''
                                ### Shift Intervention
                                $$var \sim Normal(\mu+x, \sigma)$$

                                $$var$$:
                                ''')
            self.widget_box.append(pn.WidgetBox(ti_s, self.w_s))
            ## Variance
            self.w_v = pn.widgets.RadioBoxGroup(name ='varsRadios', options = list(self.v_interventions.keys()), inline=True, value = "")
            ti_v = pn.pane.Markdown('''
                                ### Variance Intervention
                                $$var \sim Normal(\mu, \sigma/x)$$

                                $$var$$:
                                ''')
            self.widget_box.append(pn.WidgetBox(ti_v, self.w_v))
        ## SLIDER 
        if self.status in ["i_value", "animated"]:
            self.slider = Slider(start=0., end=5., value=0., step=1., title="x", show_value = False, tooltips = False, disabled = True)                
        elif self.status == "i_density":
            self.slider = Slider(start=1., end=5., value=1., step=1., title="Number of values in range of x", disabled = True)
        elif self.status == "i_range":  
            self.slider = RangeSlider(start=0., end=5., value=(0.,5.), step=.1, title="x", show_value = False, tooltips = False, disabled = True)
        if self.slider is not None:# and self.status != "animated"
            self.widget_box.append(self.slider)
        ## VIEW BUTTONS
        ## No intervention
        self.no_i_button = pn.widgets.Button(name='Clear Intervention', button_type='primary')
        ## Toggle buttons
        if self.addToggles:
            self.toggle1 = Toggle(label="Observations", button_type="primary", active=True, background= "green")
            self.toggle2 = Toggle(label="PP Samples", button_type="primary", active=True, background= "blue")
            self.toggle3 = Toggle(label="Post-Intervention PP Samples", button_type="primary", active=True, background= "orange")
            self.widget_box.append(pn.WidgetBox('### View', self.no_i_button, self.toggle1, self.toggle2, self.toggle3))
        elif self.status not in ["animated"]:
            self.widget_box = [self.no_i_button]+self.widget_box
            
    def register_callbacks_to_cells(self, dags, grids):
        """
        Parameters:
        -----------
            dags: list of Causal_DAGS objects
            grids: List of Scatter_Matrix objects
        """
        # self.dags = dags
        for dag in dags:
            self.no_i_button.on_click(partial(self.no_interv_update_dag, dag))
            self.w_a.param.watch(partial(self.sel_var_update_dag, "atomic", dag), ['value'], onlychanged=False)
            if self.w_s:
                self.w_s.param.watch(partial(self.sel_var_update_dag, "shift", dag), ['value'], onlychanged=False)
                self.w_v.param.watch(partial(self.sel_var_update_dag, "variance", dag), ['value'], onlychanged=False)
        ##
        for grid in grids:
            for var in grid.cells:
                for cell in grid.cells[var]:
                    if self.addToggles:
                        self._link_buttons_with_glyphs(var, cell)  
                    ##
                    self.no_i_button.on_click(partial(self.no_interv_update_cell,cell))
                    self.w_a.param.watch(partial(self.sel_var_update_cell, "atomic", cell), ['value'], onlychanged=False) 
                    if self.w_s:
                        self.w_s.param.watch(partial(self.sel_var_update_cell, "shift", cell), ['value'], onlychanged=False)
                        self.w_v.param.watch(partial(self.sel_var_update_cell, "variance", cell), ['value'], onlychanged=False) 
                    if self.status in ["i_value", "i_density", "i_range", "animated"]:
                        self.slider.on_change("value", partial(self.sel_value_update_cell, "atomic", cell))
                        if self.w_s:
                            self.slider.on_change("value", partial(self.sel_value_update_cell, "shift", cell))
                            self.slider.on_change("value", partial(self.sel_value_update_cell, "variance", cell))
                 
    def register_callbacks(self):        
        ## No Intervention button
        self.no_i_button.on_click(self.no_interv_update_slider)
        ## Atomic
        self.w_a.param.watch(partial(self.sel_var_update_slider, "atomic"), ['value'], onlychanged=False) 
        if self.status == "animated":
            self.w_a.param.watch(self.sel_var_animation, ['value']) 
        ##
        if self.w_s:
            ## SHIFT
            self.w_s.param.watch(partial(self.sel_var_update_slider, "shift"), ['value'], onlychanged=False)
            if self.status == "animated":
                self.w_s.param.watch(self.sel_var_animation, ['value'])
            ## VARIANCE
            self.w_v.param.watch(partial(self.sel_var_update_slider, "variance"), ['value'], onlychanged=False) 
            if self.status == "animated":
                self.w_v.param.watch(self.sel_var_animation, ['value']) 
        ## slider
        if self.status in ["i_value", "i_density", "i_range", "animated"]:
            self.slider.on_change("value", partial(self.sel_value_update_slider, "atomic"))
            self.slider.on_change("title", self.set_title)
            if self.w_s:
                self.slider.on_change("value", partial(self.sel_value_update_slider, "shift"))
                self.slider.on_change("value", partial(self.sel_value_update_slider, "variance"))   
            
    ## CALlBACKS called when a radio button is clicked
    def sel_var_update_dag(self, i_type, dag, event):
        """
        Parameters:
        ----------
        dag: A Causal_DAG object
        """
        if event.new:
            dag.update_plot([event.new], i_type = i_type)
            
    def sel_var_update_cell(self, i_type, cell, event):
        """
            i_type: String in {"atomic","shift","variance"}
            cell: A KDE_plot or Scatter_plot object
        """
        if event.new:
            ##
            interventions = self._retrieve_intervention_values(i_type)
            ##
            if self.status == "i_density":
                intervention_arg = self._retrieve_intervention_argument(event.new, interventions, [1,None])
            else:
                intervention_arg = self._retrieve_intervention_argument(event.new, interventions)   
            cell.update_plot(intervention_arg, i_type)
    
    async def locked_update(self, i, var, interventions):
        if i < len(interventions[var]):
            self.slider.title = "x:"+"{:.3f}".format(interventions[var][i])
            self.slider.value = i
        else:
            self.no_i_button.clicks = self.no_i_button.clicks+1
            self.w_a.disabled = False
            self.w_s.disabled = False
            self.w_v.disabled = False
        
    async def sel_var_animation(self, event):
        if event.new:
            var = event.new
            i_type = ""
            if self.w_a.value is not None:
                i_type = "atomic"
            elif self.w_s.value is not None:
                i_type = "shift"
            elif self.w_v.value is not None:
                i_type = "variance"    
            ##disable all widgets
            self.w_a.disabled = True
            self.w_s.disabled = True
            self.w_v.disabled = True
            ##
            interventions = self._retrieve_intervention_values(i_type)
            for i,_ in enumerate(interventions[var]):                
                pn.state.curdoc.add_next_tick_callback(partial(self.locked_update, i,var,interventions))
                await asyncio.sleep(0.5)
            pn.state.curdoc.add_next_tick_callback(partial(self.locked_update, i+1,var,interventions))
        
    def sel_var_update_slider(self, i_type, event):
        """
            i_type: String in {"atomic","shift","variance"}
        """
        if event.new:
            ##
            self._reset_i_radio_buttons(itype = i_type)
            interventions = self._retrieve_intervention_values(i_type)
            ##
            self._update_slider(event.new, interventions)

    ## CALLBACKs called when a new value is set on slider
    def sel_value_update_slider(self, i_type, attr, old, new):
        """
            i_type: String in {"atomic","shift","variance"}
        """
        ##
        var = self._retrieve_radio_button_selection(i_type)
        if var:
            interventions = self._retrieve_intervention_values(i_type)
            ##
            if var:
                if self.status in ["i_value", "animated"]:
                    interv_values = interventions[var]
                    self.slider.title = "x:"+"{:.4f}".format(interv_values[new])
                elif self.status == "i_range":
                    x_start = new[0]
                    x_end = new[1]
                    interv_values = []
                    i_value_idx = []
                    for i,val in enumerate(interventions[var]):
                        if i>=x_start and i<=x_end:
                            interv_values.append(val)
                            i_value_idx.append(i)
                    self.slider.title = "x:"+"{:.3f}".format(interv_values[0])+"..."+"{:.3f}".format(interv_values[-1])
    
    def sel_value_update_cell(self, i_type, cell, attr, old, new):
        ##
        var = self._retrieve_radio_button_selection(i_type)
        if var:
            interventions = self._retrieve_intervention_values(i_type)
            ##
            if self.status == "i_range":
                intervention_arg = self._retrieve_intervention_argument(var, interventions, [new[0],new[1]])
            else:
                intervention_arg = self._retrieve_intervention_argument(var, interventions, [new,None])
            cell.update_plot(intervention_arg, i_type)
        
    ## CALLBACKs called when no intervention button is clicked
    def no_interv_update_slider(self, event):
        self._reset_i_radio_buttons()
        self._reset_slider()
        
    def no_interv_update_cell(self, cell, event):
        cell.update_plot({},None)
        
    def no_interv_update_dag(self, dag, event):
        dag.update_plot([])
    
    ## CALLBACK called when slider's title is changed
    def set_title(self, attr, old, new):
        pass
    
    ## HELPERs
    def _retrieve_intervention_values(self, itype):
        if itype == "atomic":
            return self.a_interventions
        elif itype == "shift":
            return self.s_interventions
        elif itype == "variance":
            return self.v_interventions
        else:
            return None
    
    def _reset_slider(self):
        if self.status not in ["static"]:
            self.slider.disabled = True
        if self.status in ["i_value","animated"]:
            self.slider.start = 0.
            self.slider.end = 5.
            self.slider.step = 1.
            self.slider.title = "x"
            self.slider.value = 0.
        elif self.status == "i_density":
            self.slider.start = 1.
            self.slider.end = 5.
            self.slider.step = 1.
            self.slider.value = 1.
        elif self.status == "i_range":
            self.slider.start = 0.
            self.slider.end = 5.
            self.slider.step = 1.
            self.slider.title = "x"
            self.slider.value = (0.,5.)
            
    def _reset_i_radio_buttons(self, itype = None):
        if itype is None:
            self.w_a.value = ""
            self.w_s.value = ""
            self.w_v.value = ""
        elif itype == "atomic":
            self.w_s.value = ""
            self.w_v.value = ""
        elif itype == "shift":
            self.w_a.value = ""
            self.w_v.value = ""
        elif itype == "variance":
            self.w_a.value = ""
            self.w_s.value = ""
            
    def _retrieve_radio_button_selection(self, itype):
        if itype == "atomic":
            return self.w_a.value
        elif itype == "shift":
            return self.w_s.value
        elif itype == "variance":
            return self.w_v.value
        else:
            return None
    
    def _update_slider(self, var, interventions):
        if self.status not in ["animated", "static"] and self.slider.disabled:
            self.slider.disabled = False
        if self.status == "i_value":
            interv_values = interventions[var]
            self.slider.start = 0
            self.slider.end = len(interv_values)-1
            self.slider.step = 1
            self.slider.title = "x:"+"{:.3f}".format(interv_values[0])
            self.slider.value = 0  
        elif self.status == "animated":
            interv_values = interventions[var]
            self.slider.start = 0
            self.slider.end = len(interv_values)-1
            self.slider.step = 1
            self.slider.title = "x:"+"{:.3f}".format(interv_values[0])
            self.slider.value = 0
        elif self.status == "i_density":
            interv_values = interventions[var]
            self.slider.start = 1
            self.slider.end = len(interv_values)+1
            self.slider.step = 1
            self.slider.value = 1
        elif self.status == "i_range":
            interv_values = interventions[var]
            self.slider.start = 0
            self.slider.end = len(interv_values)-1
            self.slider.step = 1
            self.slider.title = "x:"+"{:.3f}".format(interv_values[0])+"..."+"{:.3f}".format(interv_values[-1])
            self.slider.value = (0,len(interv_values)-1)
    
    def _retrieve_intervention_argument(self, var, interventions, value_idx = [0,None]):
        intervention_arg = None
        if value_idx[1] is None:
            value_idx[1] = len(interventions)
        if self.status == "i_value":
            interv_values = interventions[var] 
            intervention_arg = {var:{"i_value_idx":[value_idx[0]],"i_value":[interv_values[value_idx[0]]]}}
        elif self.status == "animated":
            interv_values = interventions[var]
            intervention_arg = {var:{"i_value_idx":[value_idx[0]],"i_value":[interv_values[value_idx[0]]]}}
        elif self.status == "static":
            intervention_arg = {var:{}}
        elif self.status == "i_density":
            interv_values = interventions[var]
            i_value_idx = list(np.arange(0,len(interv_values),value_idx[0]))
            intervention_arg = {var:{"i_value_idx":i_value_idx,"i_value":[interv_values[i] for i in i_value_idx]}}
        elif self.status == "i_range":
            interv_values = interventions[var]
            interv_values = []
            i_value_idx = []
            for i,val in enumerate(interventions[var]):
                if i>=value_idx[0] and i<=value_idx[1]:
                    interv_values.append(val)
                    i_value_idx.append(i)
            intervention_arg = {var:{"i_value_idx":i_value_idx,"i_value":interv_values}}
        return intervention_arg
    
    def _link_buttons_with_glyphs(self, var, cell):
        if "$" in var:##scatter plot
            pp_circle, obs_circle, i_pp_circle = cell.get_glyphs()
            if obs_circle is not None:
                self.toggle1.js_link('active', obs_circle, 'visible')
            if pp_circle is not None:
                self.toggle2.js_link('active', pp_circle, 'visible')
            if i_pp_circle is not None:
                self.toggle3.js_link('active', i_pp_circle, 'visible')
        else:## kde plot
            pp_line, i_pp_line, pp_scat, i_pp_scat, obs_left, obs_hghl, rug = cell.get_glyphs()
            if pp_line is not None:
                self.toggle2.js_link('active', pp_line, 'visible')
            if i_pp_line is not None:
                self.toggle3.js_link('active', i_pp_line, 'visible')
            if pp_scat is not None:
                self.toggle2.js_link('active', pp_scat, 'visible')
            if i_pp_scat is not None:
                self.toggle3.js_link('active', i_pp_scat, 'visible')
            if obs_left is not None:
                self.toggle1.js_link('active', obs_left, 'visible')
            if obs_hghl is not None:
                self.toggle1.js_link('active', obs_hghl, 'visible')
            if rug is not None:
                self.toggle2.js_link('active', rug, 'visible')
            
    ## SETTERS - GETTERS
    def get_widget_box(self):
        return self.widget_box