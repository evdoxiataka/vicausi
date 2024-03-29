import numpy as np
import json
from ..utils.constants import x_range_mag, stratification_window_magn
from ..utils.functions import kde

class Data():

    def __init__(self, files):
        """
            Parameters:
            --------
                name            A String within the set {"<variableName>"}.
                control         A Control object
        """
        self.files = files
        ##
        self.causal_inference = {}
        self.observations = {}
        self.atomic_interventions = {}
        self.shift_interventions = {}
        self.variance_interventions = {} 
        ##
        self.kdes = {}
        #
        self.graph = None
        ##
        self._retrieve_causal_inference_from_files()
        self._estimate_kdes()

    def _estimate_kdes(self):        
        for dag_id in self.causal_inference['dags']:
            self.kdes[dag_id] = {}
            for samples_type in self.causal_inference['dags'][dag_id]:                
                if samples_type in ["ia_samples","is_samples","iv_samples"]:
                    self.kdes[dag_id][samples_type] = {}
                    for i_var in self.causal_inference['dags'][dag_id][samples_type]:
                        self.kdes[dag_id][samples_type][i_var] = {}
                        for var in self.causal_inference['dags'][dag_id][samples_type][i_var]: 
                            self.kdes[dag_id][samples_type][i_var][var] = []
                            for i_data in self.causal_inference['dags'][dag_id][samples_type][i_var][var]:
                                self.kdes[dag_id][samples_type][i_var][var].append(kde(i_data))
                                                                                        
    def _retrieve_causal_inference_from_files(self):
        """
        Parameters:
        -----------
            files: List of file paths
        """
        self.causal_inference['dags'] = {}
        self.causal_inference["vars"] = {}
        for i,file in enumerate(self.files):
            inf_data = np.load(file)
            header_js = json.loads(inf_data['header.json'])
            graph = self.get_graph(header_js)
            dag = self.get_causal_dag(graph)
            ##
            self.causal_inference['dags'][i] = {}
            self.causal_inference['dags'][i]['dag'] = dag
            ## PP SAMPLES        
            self.causal_inference['dags'][i]['pp_samples'] = {} ## Dict <i_var>: numpy array of shape (chain, draw, obs_id) of posterior predictive samples
            ## INTERVENTIONS       
            self.causal_inference['dags'][i]['ia_samples'] = {}## Dict <i_var>: Dict <var>: numpy array of samples after intervention of shape (i_value, chain, draw, obs_id)
            self.causal_inference['dags'][i]['is_samples'] = {}
            self.causal_inference['dags'][i]['iv_samples'] = {}
            for i_var in dag:
                if i_var not in self.atomic_interventions:
                    self.causal_inference["vars"][i_var] = {}
                    self.causal_inference["vars"][i_var]["type"] = self.get_var_dist_type(graph, i_var+"_")
                    self.atomic_interventions[i_var] = inf_data[header_js["inference_data"]["observed_data"]['vars']["ai_"+i_var]["array_name"]].tolist()
                    self.causal_inference["vars"][i_var]["dist"] = self.get_var_dist(graph, i_var+"_")
                    if self.causal_inference["vars"][i_var]["dist"] == "Normal":
                        self.shift_interventions[i_var] = inf_data[header_js["inference_data"]["observed_data"]['vars']["si_"+i_var]["array_name"]].tolist()
                        self.variance_interventions[i_var] = inf_data[header_js["inference_data"]["observed_data"]['vars']["vi_"+i_var]["array_name"]].tolist()
                ## pp_samples
                self.causal_inference['dags'][i]['pp_samples'][i_var] = inf_data[header_js["inference_data"]["posterior_predictive"]['vars'][i_var]["array_name"]]
                ## atomic
                self.causal_inference['dags'][i]['ia_samples'][i_var] = {}
                for coord_idx,var in enumerate(header_js["inference_data"]["atomic_intervention"]["coords"]["var"]):
                    self.causal_inference['dags'][i]['ia_samples'][i_var][var] = inf_data[header_js["inference_data"]["atomic_intervention"]['vars'][i_var]["array_name"]][coord_idx]
                ## shift-variance
                if i_var in self.shift_interventions:
                    self.causal_inference['dags'][i]['is_samples'][i_var] = {}
                    self.causal_inference['dags'][i]['iv_samples'][i_var] = {}
                    for coord_idx, var in enumerate(header_js["inference_data"]["shift_intervention"]["coords"]["var"]):
                        self.causal_inference['dags'][i]['is_samples'][i_var][var] = inf_data[header_js["inference_data"]["shift_intervention"]['vars'][i_var]["array_name"]][coord_idx]
                    for coord_idx, var in enumerate(header_js["inference_data"]["variance_intervention"]["coords"]["var"]):
                        self.causal_inference['dags'][i]['iv_samples'][i_var][var] = inf_data[header_js["inference_data"]["variance_intervention"]['vars'][i_var]["array_name"]][coord_idx]
                ##
                if i_var not in self.observations:
                    self.observations[i_var] = inf_data[header_js["inference_data"]["constant_data"]['vars'][i_var.upper()]["array_name"]]
        ## estimate var x_range across models
        # self._estimate_x_range_across_models()
        self._estimate_x_range()
        
    def get_graph(self, header_js):
        graph = header_js["inference_data"]["sample_stats"]["attrs"]["graph"]
        return json.loads(graph.replace("'", "\""))
    
    def get_causal_dag(self, graph):    
        deterministic = [i for i,v in graph.items() if v['type'] == 'deterministic']
        obs_vars = [i[:-1] for i,v in graph.items() if v['type'] == 'observed' and i[:-1] in deterministic]
        dag = {}
        indep_vars = [var for var in obs_vars if len(graph[var+"_"]['parents']) == 0]
        for var in obs_vars:
            dag[var] = [p for p in graph[var+"_"]['parents'] if p in obs_vars]
        return dag
        
    def get_var_dist_type(self, graph, var_name):
        """"
            Return any in {"Continuous","Discrete"}
        """
        if "type" in graph[var_name]["distribution"]:
            return graph[var_name]["distribution"]["type"]
        else:
            return ""
    
    def get_var_dist(self, graph, var_name):
        if "dist" in graph[var_name]["distribution"]:
            return graph[var_name]["distribution"]["dist"]
        else:
            return graph[var_name]["type"]

    def _estimate_x_range(self):
        self.causal_inference['x_range'] = {}
        self.causal_inference['x_range']['pp_samples'] = {}
        self.causal_inference['x_range']['ia_samples'] = {}
        self.causal_inference['x_range']['is_samples'] = {}
        self.causal_inference['x_range']['iv_samples'] = {}
        for var in self.observations:
            x_range_min = None
            x_range_max = None
            x_range_ia_var_min = {}
            x_range_ia_var_max = {}
            x_range_is_var_min = {}
            x_range_is_var_max = {}
            x_range_iv_var_min = {}
            x_range_iv_var_max = {}
            for i in self.causal_inference['dags']:
                if i not in self.causal_inference['x_range']['pp_samples']:
                    self.causal_inference['x_range']['pp_samples'][i] = {}
                    self.causal_inference['x_range']['ia_samples'][i] = {}
                    self.causal_inference['x_range']['is_samples'][i] = {}
                    self.causal_inference['x_range']['iv_samples'][i] = {}
                ## pp_samples
                if var in self.causal_inference['dags'][i]['pp_samples']:
                    x_range_min = self.causal_inference['dags'][i]['pp_samples'][var].min()
                    x_range_max = self.causal_inference['dags'][i]['pp_samples'][var].max()
                ## atomic intervention
                for i_var in self.causal_inference['dags'][i]['ia_samples']:
                    if var in self.causal_inference['dags'][i]['ia_samples'][i_var]:
                        x_range_ia_var_min[i_var] = min([x_range_min,np.array(self.causal_inference['dags'][i]['ia_samples'][i_var][var]).min()]).tolist()
                        x_range_ia_var_max[i_var]= max([x_range_max,np.array(self.causal_inference['dags'][i]['ia_samples'][i_var][var]).max()]).tolist()
                ## shift
                for i_var in self.causal_inference['dags'][i]['is_samples']:
                    if var in self.causal_inference['dags'][i]['is_samples'][i_var]:
                        x_range_is_var_min[i_var] = min([x_range_min, np.array(self.causal_inference['dags'][i]['is_samples'][i_var][var]).min()]).tolist()
                        x_range_is_var_max[i_var] = max([x_range_max, np.array(self.causal_inference['dags'][i]['is_samples'][i_var][var]).max()]).tolist()
                        x_range_iv_var_min[i_var] = min([x_range_min,np.array(self.causal_inference['dags'][i]['iv_samples'][i_var][var]).min()]).tolist()
                        x_range_iv_var_max[i_var] = max([x_range_max,np.array(self.causal_inference['dags'][i]['iv_samples'][i_var][var]).max()]).tolist()
                ## var x_range of pp_samples
                self.causal_inference['x_range']['pp_samples'][i][var] = (x_range_min-x_range_mag*abs(x_range_max-x_range_min),x_range_max+x_range_mag*abs(x_range_max-x_range_min))
                ## var x_range of ia_samples
                for i_var in x_range_ia_var_min:
                    var_min = x_range_ia_var_min[i_var]
                    var_max = x_range_ia_var_max[i_var]
                    if i_var not in self.causal_inference['x_range']['ia_samples'][i]:
                        self.causal_inference['x_range']['ia_samples'][i][i_var] = {}
                    self.causal_inference['x_range']['ia_samples'][i][i_var][var] = (var_min-x_range_mag*abs(var_max-var_min),var_max+x_range_mag*abs(var_max-var_min))
                ## var x_range of is_samples
                for i_var in x_range_is_var_min:
                    ## shift
                    var_min = x_range_is_var_min[i_var]
                    var_max = x_range_is_var_max[i_var]
                    if i_var not in self.causal_inference['x_range']['is_samples'][i]:
                        self.causal_inference['x_range']['is_samples'][i][i_var] = {}
                    self.causal_inference['x_range']['is_samples'][i][i_var][var] = (var_min-x_range_mag*abs(var_max-var_min),var_max+x_range_mag*abs(var_max-var_min))
                    ## variance
                    var_min = x_range_iv_var_min[i_var]
                    var_max = x_range_iv_var_max[i_var]
                    if i_var not in self.causal_inference['x_range']['iv_samples'][i]:
                        self.causal_inference['x_range']['iv_samples'][i][i_var] = {}
                    self.causal_inference['x_range']['iv_samples'][i][i_var][var] = (var_min-x_range_mag*abs(var_max-var_min),var_max+x_range_mag*abs(var_max-var_min))


    def _estimate_x_range_across_models(self):
        self.causal_inference['x_range'] = {}
        self.causal_inference['x_range']['pp_samples'] = {}
        self.causal_inference['x_range']['ia_samples'] = {}
        self.causal_inference['x_range']['is_samples'] = {}
        self.causal_inference['x_range']['iv_samples'] = {}
        for var in self.observations:
            x_range_min = []
            x_range_max = []
            x_range_ia_var_min = {}
            x_range_ia_var_max = {}
            x_range_is_var_min = {}
            x_range_is_var_max = {}
            x_range_iv_var_min = {}
            x_range_iv_var_max = {}
            for i in self.causal_inference['dags']:
                ## pp_samples
                if var in self.causal_inference['dags'][i]['pp_samples']:
                    x_range_min.append(self.causal_inference['dags'][i]['pp_samples'][var].min())
                    x_range_max.append(self.causal_inference['dags'][i]['pp_samples'][var].max())
                ## atomic intervention
                for i_var in self.causal_inference['dags'][i]['ia_samples']:
                    if var in self.causal_inference['dags'][i]['ia_samples'][i_var]:
                        if i_var not in x_range_ia_var_min:
                            x_range_ia_var_min[i_var] = []
                            x_range_ia_var_max[i_var] = []
                        x_range_ia_var_min[i_var].append(np.array(self.causal_inference['dags'][i]['ia_samples'][i_var][var]).min())
                        x_range_ia_var_max[i_var].append(np.array(self.causal_inference['dags'][i]['ia_samples'][i_var][var]).max())
                ## shift
                for i_var in self.causal_inference['dags'][i]['is_samples']:
                    if var in self.causal_inference['dags'][i]['is_samples'][i_var]:
                        if i_var not in x_range_is_var_min:
                            x_range_is_var_min[i_var] = []
                            x_range_is_var_max[i_var] = []
                            x_range_iv_var_min[i_var] = []
                            x_range_iv_var_max[i_var] = []
                        x_range_is_var_min[i_var].append(np.array(self.causal_inference['dags'][i]['is_samples'][i_var][var]).min())
                        x_range_is_var_max[i_var].append(np.array(self.causal_inference['dags'][i]['is_samples'][i_var][var]).max())
                        x_range_iv_var_min[i_var].append(np.array(self.causal_inference['dags'][i]['iv_samples'][i_var][var]).min())
                        x_range_iv_var_max[i_var].append(np.array(self.causal_inference['dags'][i]['iv_samples'][i_var][var]).max())
            ## var x_range of pp_samples
            if len(x_range_min):
                var_min = min(x_range_min)
                var_max = max(x_range_max)
                self.causal_inference['x_range']['pp_samples'][var] = (var_min-x_range_mag*abs(var_max-var_min),var_max+x_range_mag*abs(var_max-var_min))
            ## var x_range of ia_samples
            for i_var in x_range_ia_var_min:
                var_min = min(x_range_ia_var_min[i_var])
                var_max = max(x_range_ia_var_max[i_var])
                if i_var not in self.causal_inference['x_range']['ia_samples']:
                    self.causal_inference['x_range']['ia_samples'][i_var] = {}
                self.causal_inference['x_range']['ia_samples'][i_var][var] = (var_min-x_range_mag*abs(var_max-var_min),var_max+x_range_mag*abs(var_max-var_min))
            ## var x_range of is_samples
            for i_var in x_range_is_var_min:
                ## shift
                var_min = min(x_range_is_var_min[i_var])
                var_max = max(x_range_is_var_max[i_var])
                if i_var not in self.causal_inference['x_range']['is_samples']:
                    self.causal_inference['x_range']['is_samples'][i_var] = {}
                self.causal_inference['x_range']['is_samples'][i_var][var] = (var_min-x_range_mag*abs(var_max-var_min),var_max+x_range_mag*abs(var_max-var_min))
                ## variance
                ## shift
                var_min = min(x_range_iv_var_min[i_var])
                var_max = max(x_range_iv_var_max[i_var])
                if i_var not in self.causal_inference['x_range']['iv_samples']:
                    self.causal_inference['x_range']['iv_samples'][i_var] = {}
                self.causal_inference['x_range']['iv_samples'][i_var][var] = (var_min-x_range_mag*abs(var_max-var_min),var_max+x_range_mag*abs(var_max-var_min))

    ## GETTERS-SETTERS
    def get_interventions(self, dag_id):
        pp_samples = self.causal_inference['dags'][dag_id]['pp_samples']
        str_inter_data = {var: np.arange(min(pp_samples[var].flatten()),max(pp_samples[var].flatten()),(max(pp_samples[var].flatten())-min(pp_samples[var].flatten())+1)/len(self.atomic_interventions[var])).tolist() for var in pp_samples}
        return {"atomic":self.atomic_interventions, "shift":self.shift_interventions, "variance":self.variance_interventions,"stratify":str_inter_data}
    
    def get_causal_dags_ids(self):
         return [i for i in self.causal_inference['dags']]
        
    def get_dag_by_id(self, dag_id):
        return self.causal_inference['dags'][dag_id]['dag']
    
    def get_dags(self):
        return [self.causal_inference['dags'][i]['dag'] for i in self.causal_inference['dags']]

    def get_var_type(self, var):
        if var in self.causal_inference["vars"]:
            return self.causal_inference["vars"][var]["type"]
        else:
            return None
        
    def get_var_observations(self, var):
        if var in self.observations:
            return self.observations[var]
        else:
            return None
        
    def get_var_pp_samples(self, var, dag_id): 
        if var in self.causal_inference['dags'][dag_id]['pp_samples']:
            return self.causal_inference['dags'][dag_id]['pp_samples'][var]
        else:
            return None

    def get_var_pp_samples_idx(self, var, dag_id, window_median): 
        if var in self.causal_inference['dags'][dag_id]['pp_samples']:
            pp_samples = self.causal_inference['dags'][dag_id]['pp_samples'][var].flatten()
            offset = stratification_window_magn*(max(pp_samples) - min(pp_samples))/2
            window_min = window_median - abs(offset)
            window_max = window_median + abs(offset)
            return np.where((pp_samples > window_min) & (pp_samples < window_max))
        else:
            return None
        
    def get_var_x_range(self, dag_id, var):
        if dag_id in self.causal_inference['x_range']['pp_samples'] and var in self.causal_inference['x_range']['pp_samples'][dag_id]:
            return self.causal_inference['x_range']['pp_samples'][dag_id][var]
        else:
            return None
        
    def get_var_i_x_range(self, dag_id, var, i_var, i_type):
        """
        Parameters:
        -----------
        i_type: String in {"atomic", "shift","variance"}
        """
        samples_type = ""
        if i_type == "atomic":
            samples_type = "ia_samples"
        elif i_type == "shift":
            samples_type = "is_samples"
        elif i_type == "variance":
            samples_type = "iv_samples"
        if samples_type!="" and dag_id in self.causal_inference['x_range'][samples_type] and i_var in self.causal_inference['x_range'][samples_type][dag_id] and var in self.causal_inference['x_range'][samples_type][dag_id][i_var]:
            return self.causal_inference['x_range'][samples_type][dag_id][i_var][var]
        else:
            return None
        
    def get_var_i_samples(self, i_var, var, dag_id, i_type):
        """
        Parameters:
        -----------
        i_type: String in {"atomic", "shift","variance"}
        """
        samples_type = ""
        if i_type == "atomic":
            samples_type = "ia_samples"
        elif i_type == "shift":
            samples_type = "is_samples"
        elif i_type == "variance":
            samples_type = "iv_samples"
        if samples_type!="" and i_var in self.causal_inference['dags'][dag_id][samples_type] and var in self.causal_inference['dags'][dag_id][samples_type][i_var]:
            return self.causal_inference['dags'][dag_id][samples_type][i_var][var]
        else:
            return None

    def get_kde_y_range(self, i_var, var, dag_id, i_type, pp_samples_kde_y_max):
        samples_type = ""
        if i_type == "atomic":
            samples_type = "ia_samples"
        elif i_type == "shift":
            samples_type = "is_samples"
        elif i_type == "variance":
            samples_type = "iv_samples"
        if samples_type!="" and i_var in self.kdes[dag_id][samples_type] and var in self.kdes[dag_id][samples_type][i_var]:
            y_max = [pp_samples_kde_y_max]
            for i in range(len(self.kdes[dag_id][samples_type][i_var][var])):
                y_max.append(self.kdes[dag_id][samples_type][i_var][var][i]['y'].max())
            return np.array(y_max).max().item()
        else:
         return pp_samples_kde_y_max
            

    

            
        