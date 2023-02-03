from ..utils.constants import COLS_PER_VAR
from .kde_cell import KDE_Cell
from .scatter_cell import Scatter_Cell

import panel as pn
pn.extension()

class Scatter_Matrix():
    def __init__(self, data, dag_id, var_order, status, showData = True):
        """
            Parameters:
            --------
                data           A Data obj.
                dag_id         A dag_id.
                
        """
        self.data = data
        self.dag_id = dag_id
        self.dag = data.get_dag_by_id(dag_id) ## A Dict(<var>: List of ancestor vars).
        self.var_order = var_order
        self.status = status
        self.showData = showData
        ##
        self.grid = None
        self.cells = {} ## Dict(<var>: List of cell objects (kde or scatter) corresponding to var)
        ##
        self.create_grid()

    def create_grid(self):
        ## prepare vars list ordered as wished
        vars_ordered = self._order_dag_vars()
        ##
        self.grid = pn.GridSpec(sizing_mode = 'fixed', width=600, height=600)
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
                    cell = KDE_Cell(var, self.dag_id, self.data, self.status, self.showData) 
                    if var not in self.cells:
                        self.cells[var] = []
                    self.cells[var].append(cell)
                ## SCATTER PLOT
                else:                    
                    var1 = vars_ordered[row] 
                    var2 = vars_ordered[col]
                    cell = Scatter_Cell(var1, var2, self.dag_id, self.data, self.status, self.showData)
                    if var1+"$"+var2 not in self.cells:
                        self.cells[var1+"$"+var2] = []
                    self.cells[var1+"$"+var2].append(cell)
                ##Add to grid
                self.grid[ start_point[0]:end_point[0], start_point[1]:end_point[1] ] = pn.Column(pn.pane.Bokeh(cell.get_plot()), width = 270, height = 270,sizing_mode = 'fixed')
        # if self.status == "static":
        #     start_point = ( 0, int((col+1)*COLS_PER_VAR) )
        #     end_point = ( row+1, int((col+1)*COLS_PER_VAR+1) )
        #     self.grid[ start_point[0]:end_point[0], start_point[1]:end_point[1] ] = pn.Column(pn.pane.Bokeh(cell.plot_colorbar))

    ## HELPERS    
    def _order_dag_vars(self):
        ## prepare vars list ordered as wished
        vars = list(self.dag.keys())[::-1]
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