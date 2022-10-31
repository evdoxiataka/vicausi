from .classes.demo import Demo

def causal_visualizer(files, var_order, status = "i_value",addToggles = False, showData = False):    
    """
        Simulations of Causal Interventions using scatter matrices for the vizualization.
        Parameters:
        -----------
            files: List of npz files - one per dag
            var_order: List of vars given in order to be presented in scatter matrix
            status: String in {"static","i_value","i_density","i_range", "animated"} for static or interactive (having a slider for setting the intervention value) version of tool
    """ 
    demo = Demo(files, var_order, status = "i_value",addToggles = False, showData = False)
    demo.get_plot().show()