from utils.utils.constants import COLS_PER_VAR
from utils.classes.kde_cell import KDE_Cell
from utils.classes.scatter_cell import Scatter_Cell

import networkx as nx
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Arrow, VeeHead, LabelSet

import numpy as np
import panel as pn
pn.extension()

class Causal_DAG():
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
        self.plot = None
        self.grid = None
        self.cells = {} ## Dict(<var>: List of cell objects (kde or scatter) corresponding to var)
        ##
        self.nodes_cds = None
        self.edges_cds = None
        self.labels_cds = None
        ##
        self.initialize_plot()
        self.create_grid()

    def initialize_plot(self):
        self.plot = figure(width = 600, height = 350, x_range=(-1.2, 1.2), y_range=(-1.2, 1.2),
                  x_axis_location = None, y_axis_location = None, toolbar_location = None,
                  title="")##background_fill_color="#efefef"
        self.plot.grid.grid_line_color = None
        ##
        graph = self._create_digraph()
        pos = nx.planar_layout(graph)
        x, y = zip(*pos.values())
        nodes = [node for node in graph.nodes]
        xs = []
        ys = []
        start_n = []
        stop_n = []
        for edge in graph.edges:
            xs.append([pos[edge[0]][0],pos[edge[1]][0]])
            ys.append([pos[edge[0]][1],pos[edge[1]][1]])
            start_n.append(edge[0])
            stop_n.append(edge[1])
        ## COLOR of EDGES
        color = ['blue' for e in graph.edges]
        line_dash = ['solid' for e in graph.edges]
        ## ARROWS
        for i in range(len(graph.edges)):
            # self.plot.add_layout( Arrow(end = VeeHead(size=15), x_start = xs[i][0]+0.49*(xs[i][1]-xs[i][0]), y_start = ys[i][0]+0.49*(ys[i][1]-ys[i][0]), x_end = (xs[i][0]+xs[i][1])/2, y_end = (ys[i][0]+ys[i][1])/2))
            self.plot.add_layout( Arrow(end = VeeHead(size=16,line_color="blue",fill_color="blue"), x_start = xs[i][1]-0.03*(xs[i][1]-xs[i][0]), y_start = ys[i][1]-0.03*(ys[i][1]-ys[i][0]), x_end = xs[i][1]-0.02*(xs[i][1]-xs[i][0]), y_end = ys[i][1]-0.02*(ys[i][1]-ys[i][0]), tags = [stop_n[i]] ))
        ## EDGES
        self.edges_cds = ColumnDataSource(data = {'xs':xs,'ys':ys,'start_n':start_n,'stop_n':stop_n,'color':color,"line_dash":line_dash})
        self.plot.multi_line(xs = 'xs', ys = 'ys', source = self.edges_cds, line_color='color', line_alpha=0.8, line_width=1.5, line_join = 'miter', line_dash = "line_dash", name = 'edge')
        ## NODES
        self.nodes_cds = ColumnDataSource(data = {'x':x,'y':y,'name':nodes,'color':["blue"]*len(nodes)})
        self.plot.circle(x='x', y='y', source = self.nodes_cds, size=18., fill_color='color', alpha=1., name = 'node')
        # LABELS
        self.labels_cds = ColumnDataSource({'x': x, 'y': y,'name': [i for i in pos]})
        self.plot.add_layout(LabelSet(x='x', y='y', text='name', source = self.labels_cds, x_offset=-20,y_offset=10))

    def update_plot(self, i_vars, i_type = None):
        """
            Parameters
            ----------                
                i_vars:           List of intervention variables
                i_type:           String in {"atomic","shift","intervention"}
        """        
        new_edge_data = {}
        new_edge_data['xs'] = self.edges_cds.data['xs']
        new_edge_data['ys'] = self.edges_cds.data['ys']
        new_edge_data['start_n'] = self.edges_cds.data['start_n']
        new_edge_data['stop_n'] = self.edges_cds.data['stop_n']
        ##
        new_node_data = {}
        new_node_data['x'] = self.nodes_cds.data['x']
        new_node_data['y'] = self.nodes_cds.data['y']
        new_node_data['name'] = self.nodes_cds.data['name']
        if len(i_vars) == 0:
            new_edge_data['color'] = ['blue' for e in self.edges_cds.data['start_n']]
            new_edge_data['line_dash'] = ['solid' for e in self.edges_cds.data['start_n']]
            self.edges_cds.data =  new_edge_data
            ##
            new_node_data['color'] = ['blue']*len(self.nodes_cds.data['name'])
            self.nodes_cds.data =  new_node_data
        else:
            if i_type == "atomic":
                new_edge_data['color'] = ['orange' if i_var in i_vars else 'blue' for i_var in self.edges_cds.data['stop_n']]
                new_edge_data['line_dash'] = ['dashed' if i_var in i_vars else 'solid' for i_var in self.edges_cds.data['stop_n']]
                for i_var in self.edges_cds.data['stop_n']:
                    if i_var in i_vars:
                        self.plot.select(tags=[i_var]).end.line_color = "orange"
                        self.plot.select(tags=[i_var]).end.fill_color = "orange"
                        # print(self.dag_id,i_var,self.plot.select(tags=[i_var]).end.line_color)
                    else:
                        self.plot.select(tags=[i_var]).end.line_color = "blue"
                        self.plot.select(tags=[i_var]).end.fill_color = "blue"
            else:
                new_edge_data['color'] = ['blue' for e in self.edges_cds.data['start_n']]
                new_edge_data['line_dash'] = ['solid' for e in self.edges_cds.data['start_n']]
                for i_var in self.edges_cds.data['stop_n']:
                    self.plot.select(tags=[i_var]).end.line_color = "blue"
                    self.plot.select(tags=[i_var]).end.fill_color = "blue"
            self.edges_cds.data = new_edge_data
            ##
            new_node_data['color'] = ['orange' if n in i_vars else 'blue' for n in self.nodes_cds.data['name']]
            self.nodes_cds.data =  new_node_data

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
                self.grid[ start_point[0]:end_point[0], start_point[1]:end_point[1] ] = pn.Column(pn.pane.Bokeh(cell.get_plot()), width = 220, height = 220)

    ## HELPERS
    def _create_digraph(self):
        """
        Parameters:
        -----------
            dag   A Dict(<var>: List of ancestor vars).
        """
        graph = nx.DiGraph()
        graph.add_edges_from([(j,i) for i in self.dag for j in self.dag[i]])
        return graph
    
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
    def get_plot(self):
        return self.plot

    def get_dag_col(self):
        return pn.Column(pn.pane.Bokeh(self.plot), self.grid)