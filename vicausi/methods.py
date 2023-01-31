from .classes.demo import Demo
from .classes.demo_comparative_graph import Demo_Comparative_Graph
from .classes.demo_single_matrix import Demo_Single_Matrix

def causal_visualizer(files, var_order, status = "i_value", addToggles = False, showData = False):    
    """
        Simulations of Causal Interventions using scatter matrices for the vizualization.
        Parameters:
        -----------
            files: List of npz files - one per dag
            var_order: List of vars given in order to be presented in scatter matrix
            status: String in {"static","i_value","i_density","i_range", "animated"} for static or interactive (having a slider for setting the intervention value) version of tool
    """ 
    demo = Demo(files, var_order, status = status, addToggles = addToggles, showData = showData)
    demo.get_plot().show()

def comparative_causal_visualizer(files, var_order, status = "i_value", addToggles = False, showData = False, mean_obs = False):    
    """
        Simulations of Causal Interventions using scatter matrices for the vizualization.
        Parameters:
        -----------
            files: List of npz files - one per dag
            var_order: List of vars given in order to be presented in scatter matrix
            status: String in {"static","i_value","i_density","i_range", "animated"} for static or interactive (having a slider for setting the intervention value) version of tool
    """ 
    demo = Demo_Comparative_Graph(files, var_order, status = status, addToggles = addToggles, showData = showData, mean_obs = mean_obs)
    demo.get_plot().show()

def single_matrix_visualizer(files, dag_id, var_order, status, interventions, showData = False):  #, dags_presented  
    """
        Simulations of Causal Interventions using scatter matrices for the vizualization.
        Parameters:
        -----------
            files: List of npz files - one per dag
            var_order: List of vars given in order to be presented in scatter matrix
            status: String in {"static","i_value","i_density","i_range", "animated"} for static or interactive (having a slider for setting the intervention value) version of tool
    """ 
    demo = Demo_Single_Matrix(files, dag_id, var_order, status, interventions, showData = showData)
    return demo
    # demo.get_plot().show()