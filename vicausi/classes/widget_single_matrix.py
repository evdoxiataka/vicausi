from functools import partial
from bokeh.models import Slider, Toggle
import asyncio
import panel as pn
pn.extension()

class Widget_Single_Matrix():
    
    def __init__(self, status, interventions, a_interventions, s_interventions, v_interventions, is_single_intervention, addToggles = True):
        """
            Parameters:
            --------
                status           A String within the set {"i_value","static","animated","i_density","i_range"}.
                a_interventions  A Dict(<var>: List of intervention values)
                interventions    A Dict(<i_type>: List of <i_var>). Interventions to be included in widgets.
                is_single_intervention Boolean determines if interventions contain a single intervention
        """
        ##
        self.status = status
        self.a_interventions = a_interventions
        self.s_interventions = s_interventions
        self.v_interventions = v_interventions
        self.interventions = interventions
        self.single_intervention = is_single_intervention
        self.addToggles = addToggles
        ##
        self.w_a = None ## Radio button widget for atomic intervention
        self.w_s = None
        self.w_v = None
        self.slider = None
        self.no_i_button = None
        if self.addToggles:
            # self.toggle1 = None ## toggle button for observations
            # self.toggle2 = None ## toggle button for posterior predictive samples
            self.toggle3 = None ## toggle button for after intervention samples
        self.widget_box = []
        # if self.status == "animated":
        #     self.widget_box.append(pn.Spacer(height=16))
        ##
        if self.status == "i_value":
            self.slider_titles_map = {"atomic":"Set the value of *","shift":"Set the shift (x) of *'s mean (mean+x)","variance":"Set the divisor (x) of *'s variance (variance/x)"}
        else:
            self.slider_titles_map = {"atomic":"The value of * is","shift":"The shift (x) of *'s mean (mean+x) is","variance":"The divisor (x) of *'s variance (variance/x) is"}
        ##
        self.create_widgets()
        self.register_callbacks()
    
    def create_widgets(self):   
        ## Atomic
        if "atomic" in self.interventions:       
            self.w_a = pn.widgets.RadioBoxGroup(name ='varsRadios', options = self.interventions["atomic"], inline=True, value = "")     
            if self.single_intervention and self.status == "animated":
                title = pn.pane.Markdown(''' Click to start the animation ''', style={'font-size': "18px",'margin-bottom': '0px'})
            else:                
                title = pn.pane.Markdown(''' Atomic Intervention ''', style={'font-size': "18px",'margin-bottom': '0px'})
            self.widget_box.append(pn.WidgetBox(title, self.w_a))
        ## Shift
        if "shift" in self.interventions:
            self.w_s = pn.widgets.RadioBoxGroup(name ='varsRadios', options = self.interventions["shift"], inline=True, value = "")
            if self.single_intervention and self.status == "animated":
                title = pn.pane.Markdown(''' Click to start the animation ''', style={'font-size': "18px",'margin-bottom': '0px'})
            else:                
                title = pn.pane.Markdown(''' Shift Intervention ''', style={'font-size': "18px",'margin-bottom': '0px'})
            self.widget_box.append(pn.WidgetBox(title, self.w_s))
        ## Variance
        if "variance" in self.interventions:
            self.w_v = pn.widgets.RadioBoxGroup(name ='varsRadios', options = self.interventions["variance"], inline=True, value = "")
            if self.single_intervention and self.status == "animated":
                title = pn.pane.Markdown(''' Click to start the animation ''', style={'font-size': "18px",'margin-bottom': '0px'})
            else:                
                title = pn.pane.Markdown(''' Variance Intervention ''', style={'font-size': "18px",'margin-bottom': '0px'})
            self.widget_box.append(pn.WidgetBox(title, self.w_v))
        ## SLIDER 
        if self.status in ["i_value", "animated"]:
            self.slider = Slider(start=0., end=5., value=0., step=1., title = self.slider_titles_map[list(self.interventions.keys())[0]], show_value = False, tooltips = False, disabled = True)                
        if self.slider is not None:# and self.status != "animated"
            self.widget_box.append(self.slider)
        ## VIEW BUTTONS
        ## Toggle buttons
        if self.addToggles:
            # self.toggle1 = Toggle(label="Observations", button_type="primary", active=True, background= "green")
            # self.toggle2 = Toggle(label="PP Samples", button_type="primary", active=True, background= "blue")
            self.toggle3 = Toggle(label="Post-Intervention PP Samples", button_type="primary", active=True, background= "orange")
        ## No intervention
        self.no_i_button = pn.widgets.Button(name='Clear Intervention', button_type='primary')
        if self.status not in ["animated"]:
            self.widget_box = [self.no_i_button]+self.widget_box

    def register_callbacks_to_dags(self, dags):
        """
        Parameters:
        -----------
            dags: list of Causal_DAGS objects
        """
        for dag in dags:
            self.no_i_button.on_click(partial(self.no_interv_update_dag, dag))
            if self.w_a:
                self.w_a.param.watch(partial(self.sel_var_update_dag, "atomic", dag), ['value'], onlychanged=False)
            if self.w_s:
                self.w_s.param.watch(partial(self.sel_var_update_dag, "shift", dag), ['value'], onlychanged=False)
            if self.w_v:
                self.w_v.param.watch(partial(self.sel_var_update_dag, "variance", dag), ['value'], onlychanged=False)

    def register_callbacks_to_cells(self, grids):
        """
        Parameters:
        -----------
            grids: List of Scatter_Matrix objects
        """
        for grid in grids:
            for var in grid.cells:
                for cell in grid.cells[var]:
                    if self.addToggles:
                        self._link_buttons_with_glyphs(var, cell)  
                    self.no_i_button.on_click(partial(self.no_interv_update_cell,cell))
                    if self.w_a:
                        self.w_a.param.watch(partial(self.sel_var_update_cell, "atomic", cell), ['value'], onlychanged=False) 
                    if self.w_s:
                        self.w_s.param.watch(partial(self.sel_var_update_cell, "shift", cell), ['value'], onlychanged=False)
                    if self.w_v:
                        self.w_v.param.watch(partial(self.sel_var_update_cell, "variance", cell), ['value'], onlychanged=False) 
                    if self.status in ["i_value", "animated"]:
                        if self.w_a:
                            self.slider.on_change("value", partial(self.sel_value_update_cell, "atomic", cell))
                        if self.w_s:
                            self.slider.on_change("value", partial(self.sel_value_update_cell, "shift", cell))
                        if self.w_v:
                            self.slider.on_change("value", partial(self.sel_value_update_cell, "variance", cell))
                 
    def register_callbacks(self):        
        ## No Intervention button
        self.no_i_button.on_click(self.no_interv_update_slider)
        ## ATOMIC
        if self.w_a:
            self.w_a.param.watch(partial(self.sel_var_update_slider, "atomic"), ['value'], onlychanged=False) 
            if self.status == "animated":
                self.w_a.param.watch(self.sel_var_animation, ['value']) 
        ## SHIFT
        if self.w_s:            
            self.w_s.param.watch(partial(self.sel_var_update_slider, "shift"), ['value'], onlychanged=False)
            if self.status == "animated":
                self.w_s.param.watch(self.sel_var_animation, ['value'])
        ## VARIANCE
        if self.w_v: 
            self.w_v.param.watch(partial(self.sel_var_update_slider, "variance"), ['value'], onlychanged=False) 
            if self.status == "animated":
                self.w_v.param.watch(self.sel_var_animation, ['value']) 
        ## slider
        if self.status in ["i_value", "animated"]:
            self.slider.on_change("title", self.set_title)
            if self.w_a:
                self.slider.on_change("value", partial(self.sel_value_update_slider, "atomic"))            
            if self.w_s:
                self.slider.on_change("value", partial(self.sel_value_update_slider, "shift"))
            if self.w_v:
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
            intervention_arg = self._retrieve_intervention_argument(event.new, interventions)   
            cell.update_plot(intervention_arg, i_type)
    
    async def locked_update(self, i, var, i_type, interventions):
        if i < len(interventions[var]):
            self.slider.title = self.slider_titles_map[i_type].replace("*",var)+":"+"{:.2f}".format(interventions[var][i])
            self.slider.value = i
        else:##animation finished
            self.no_i_button.clicks = self.no_i_button.clicks+1
            if self.w_a:
                self.w_a.disabled = False
            if self.w_s:
                self.w_s.disabled = False
            if self.w_v:
                self.w_v.disabled = False
        
    async def sel_var_animation(self, event):
        if event.new:
            var = event.new
            i_type = ""
            if self.w_a and self.w_a.value is not None:
                i_type = "atomic"
            elif self.w_s and self.w_s.value is not None:
                i_type = "shift"
            elif self.w_v and self.w_v.value is not None:
                i_type = "variance"    
            ##disable all widgets
            if self.w_a:
                self.w_a.disabled = True
            if self.w_s:
                self.w_s.disabled = True
            if self.w_v:
                self.w_v.disabled = True
            ##
            interventions = self._retrieve_intervention_values(i_type)
            for i,_ in enumerate(interventions[var]):                
                pn.state.curdoc.add_next_tick_callback(partial(self.locked_update, i, var, i_type, interventions))
                await asyncio.sleep(0.5)
            pn.state.curdoc.add_next_tick_callback(partial(self.locked_update, i+1, var, i_type, interventions))
        
    def sel_var_update_slider(self, i_type, event):
        """
            i_type: String in {"atomic","shift","variance"}
        """
        if event.new:
            ##
            self._reset_i_radio_buttons(itype = i_type)
            interventions = self._retrieve_intervention_values(i_type)
            ##
            self._update_slider(event.new, i_type, interventions)

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
                    self.slider.title = self.slider_titles_map[i_type].replace("*",var)+":"+"{:.2f}".format(interv_values[new])
                
    def sel_value_update_cell(self, i_type, cell, attr, old, new):
        ##
        var = self._retrieve_radio_button_selection(i_type)
        if var:
            interventions = self._retrieve_intervention_values(i_type)
            ##
            intervention_arg = self._retrieve_intervention_argument(var, interventions, [new,None])
            cell.update_plot(intervention_arg, i_type)
        
    # ## CALLBACKs called when no intervention button is clicked
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
            # self.slider.title = "x"
            # i_type = list(self.interventions.keys())[0]
            self.slider.title = self.slider_titles_map[list(self.interventions.keys())[0]]
            self.slider.value = 0.
            
    def _reset_i_radio_buttons(self, itype = None):
        if itype is None:
            if self.w_a:
                self.w_a.value = ""
            if self.w_s:
                self.w_s.value = ""
            if self.w_v:
                self.w_v.value = ""
        elif itype == "atomic":
            if self.w_s:
                self.w_s.value = ""
            if self.w_v:
                self.w_v.value = ""
        elif itype == "shift":
            if self.w_a:
                self.w_a.value = ""
            if self.w_v:
                self.w_v.value = ""
        elif itype == "variance":
            if self.w_a:
                self.w_a.value = ""
            if self.w_s:
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
    
    def _update_slider(self, var, i_type, interventions):
        if self.status not in ["animated", "static"] and self.slider.disabled:
            self.slider.disabled = False
        if self.status == "i_value":
            interv_values = interventions[var]
            self.slider.start = 0
            self.slider.end = len(interv_values)-1
            self.slider.step = 1
            self.slider.title = self.slider_titles_map[i_type].replace("*",var)+":"+"{:.2f}".format(interv_values[0])
            self.slider.value = 0  
        elif self.status == "animated":
            interv_values = interventions[var]
            self.slider.start = 0
            self.slider.end = len(interv_values)-1
            self.slider.step = 1
            self.slider.title = self.slider_titles_map[i_type].replace("*",var)+":"+"{:.2f}".format(interv_values[0])
            self.slider.value = 0
    
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
        return intervention_arg
    
    def _link_buttons_with_glyphs(self, var, cell):
        if "$" in var:##scatter plot
            pp_circle, obs_circle, i_pp_circle = cell.get_glyphs()
            # if obs_circle is not None:
            #     self.toggle1.js_link('active', obs_circle, 'visible')
            # if pp_circle is not None:
            #     self.toggle2.js_link('active', pp_circle, 'visible')
            if i_pp_circle is not None:
                self.toggle3.js_link('active', i_pp_circle, 'visible')
        else:## kde plot
            pp_line, i_pp_line, pp_scat, i_pp_scat, obs_left, obs_hghl, rug = cell.get_glyphs()
            # if pp_line is not None:
            #     self.toggle2.js_link('active', pp_line, 'visible')
            if i_pp_line is not None:
                self.toggle3.js_link('active', i_pp_line, 'visible')
            # if pp_scat is not None:
            #     self.toggle2.js_link('active', pp_scat, 'visible')
            if i_pp_scat is not None:
                self.toggle3.js_link('active', i_pp_scat, 'visible')
            # if obs_left is not None:
            #     self.toggle1.js_link('active', obs_left, 'visible')
            # if obs_hghl is not None:
            #     self.toggle1.js_link('active', obs_hghl, 'visible')
            # if rug is not None:
            #     self.toggle2.js_link('active', rug, 'visible')

    ## SETTERS - GETTERS
    def set_slider_value(self, i_value_idx):
        self.slider.disabled = False
        self.slider.value = i_value_idx
        self.slider.disabled = True

    def get_widget_box(self):
        return self.widget_box

    def get_widget_box_without_slider(self):
        if self.slider:
            return self.widget_box[:-1]
        else:
            return self.widget_box