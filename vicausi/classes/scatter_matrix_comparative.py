from ..utils.constants import COLS_PER_VAR
from .kde_cell_comparative import KDE_Cell_Comparative
from .scatter_cell_comparative import Scatter_Cell_Comparative

import panel as pn
pn.extension()

class Scatter_Matrix_Comparative():
    def __init__(self, data, var_order, status, showData = True, mean_obs = False):
        """
            Parameters:
            --------
                data           A Data obj.
                dag_id         A dag_id.
                
        """
        self.data = data
        self.dags = data.get_dags() ## A List of dags 
        self.var_order = var_order
        self.status = status
        self.showData = showData
        self.mean_obs = mean_obs
        ##
        self.grid = None
        self.cells = {} ## Dict(<var>: List of cell objects (kde or scatter) corresponding to var)
        ##
        self.create_grid()

    def create_grid(self):
        ## prepare vars list ordered as wished
        vars_ordered = self._order_dag_vars()
        ##
        self.grid = pn.GridSpec(sizing_mode = 'fixed')
        for row in range(len(vars_ordered)):
            for col in range(len(vars_ordered)):
                if col > row:
                    break
                start_point = ( row, int(col*COLS_PER_VAR) )
                end_point = ( row+1, int((col+1)*COLS_PER_VAR) )
                cell = None
                ## KDE PLOT
                if col == row: 
                    var = vars_ordered[col]
                    cell = KDE_Cell_Comparative(var, self.data, self.status, self.showData, self.mean_obs ) 
                    if var not in self.cells:
                        self.cells[var] = []
                    self.cells[var].append(cell)
                ## SCATTER PLOT
                else:                    
                    var1 = vars_ordered[row] 
                    var2 = vars_ordered[col]
                    cell = Scatter_Cell_Comparative(var1, var2, self.data, self.status, self.showData, self.mean_obs )
                    if var1+"$"+var2 not in self.cells:
                        self.cells[var1+"$"+var2] = []
                    self.cells[var1+"$"+var2].append(cell)
                ##Add to grid
                self.grid[ start_point[0]:end_point[0], start_point[1]:end_point[1] ] = pn.Column(pn.pane.Bokeh(cell.get_plot()), width = 220, height = 220)

    ## HELPERS    
    def _order_dag_vars(self):
        ## prepare vars list ordered as wished
        vars = list(set([var for dag in self.dags for var in dag ]))
        vars_ordered = []
        for var in self.var_order:
            if var in vars:
                vars_ordered.append(var)
                vars.remove(var)
        for var in vars:
            vars_ordered.append(var)
        return vars_ordered
    
    ## SETTERS-GETTERS
    def get_grid(self):
        return self.grid