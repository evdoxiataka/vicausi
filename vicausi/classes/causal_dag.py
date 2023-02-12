from ..utils.constants import BASE_COLOR, SECONDARY_COLOR, STATIC_BASE_COLOR

import networkx as nx
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Arrow, VeeHead, LabelSet

import panel as pn
pn.extension()

class Causal_DAG():
    def __init__(self, data, dag_id, status, var_order): # status, showData = True , mean_obs = False
        """
            Parameters:
            --------
                data           A Data obj.
                dag_id         A dag_id.
                
        """
        self.dag_id = dag_id
        self.dag = data.get_dag_by_id(dag_id) ## A Dict(<var>: List of ancestor vars).
        self.var_order = var_order
        self.status = status
        ##
        self.title_font_size = "16px"
        self.labels_font_size = "14px"
        ##
        self.base_color = BASE_COLOR
        self.second_color = SECONDARY_COLOR
        if self.status == "static":
            self.base_color = STATIC_BASE_COLOR
        # self.mean_obs = mean_obs
        # if self.mean_obs:
        #     self.base_color = BASE_COLOR
        # else:
        #     self.base_color = BASE_COLOR
        ##
        self.plot = None
        ##
        self.nodes_cds = None
        self.edges_cds = None
        self.labels_cds = None
        ##
        self.initialize_plot()

    def initialize_plot(self):
        ## FIGURE
        self.plot = figure(width = 260, height = 210, x_range = (-1.25, 1.6), y_range = (-1.1, 1.2),
                  x_axis_location = None, y_axis_location = None, toolbar_location = None, background_fill_color = None, outline_line_color = None,
                  title="Causal Model"+" "+str(self.dag_id + 1))##BORDER_COLOR
        self.plot.grid.grid_line_color = None
        self.plot.title.align = "center"
        self.plot.title.text_font_size = self.title_font_size
        # self.plot.title.text_font_style = "normal"
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
        color = [self.base_color for e in graph.edges]
        line_dash = ['solid' for e in graph.edges]
        ## ARROWS
        for i in range(len(graph.edges)):
            # self.plot.add_layout( Arrow(end = VeeHead(size=15), x_start = xs[i][0]+0.49*(xs[i][1]-xs[i][0]), y_start = ys[i][0]+0.49*(ys[i][1]-ys[i][0]), x_end = (xs[i][0]+xs[i][1])/2, y_end = (ys[i][0]+ys[i][1])/2))
            self.plot.add_layout( Arrow(end = VeeHead(size = 16, line_color = self.base_color, fill_color=self.base_color), x_start = xs[i][1]-0.03*(xs[i][1]-xs[i][0]), y_start = ys[i][1]-0.03*(ys[i][1]-ys[i][0]), x_end = xs[i][1]-0.02*(xs[i][1]-xs[i][0]), y_end = ys[i][1]-0.02*(ys[i][1]-ys[i][0]), tags = [stop_n[i]] ))
        ## EDGES
        self.edges_cds = ColumnDataSource(data = {'xs':xs,'ys':ys,'start_n':start_n,'stop_n':stop_n,'color':color,"line_dash":line_dash})
        self.plot.multi_line(xs = 'xs', ys = 'ys', source = self.edges_cds, line_color='color', line_alpha = 0.8, line_width = 1.5, line_join = 'miter', line_dash = "line_dash", name = 'edge')
        ## NODES
        self.nodes_cds = ColumnDataSource(data = {'x':x,'y':y,'name':nodes,'color':[self.base_color]*len(nodes)})
        self.plot.circle(x='x', y='y', source = self.nodes_cds, size=18., fill_color='color', line_color='color', alpha=1., name = 'node')
        # LABELS
        self.labels_cds = ColumnDataSource({'x': x, 'y': y,'name': [i for i in pos]})
        self.plot.add_layout(LabelSet(x='x', y='y', text='name', source = self.labels_cds, x_offset=-20, y_offset=10, text_font_size=self.labels_font_size))

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
            new_edge_data['color'] = [self.base_color for e in self.edges_cds.data['start_n']]
            new_edge_data['line_dash'] = ['solid' for e in self.edges_cds.data['start_n']]
            self.edges_cds.data =  new_edge_data
            ##
            new_node_data['color'] = [self.base_color]*len(self.nodes_cds.data['name'])
            self.nodes_cds.data =  new_node_data
        else:
            if i_type == "atomic":
                new_edge_data['color'] = [self.second_color if i_var in i_vars else self.base_color for i_var in self.edges_cds.data['stop_n']]
                new_edge_data['line_dash'] = ['dashed' if i_var in i_vars else 'solid' for i_var in self.edges_cds.data['stop_n']]
                for i_var in self.edges_cds.data['stop_n']:
                    if i_var in i_vars:
                        self.plot.select(tags=[i_var]).end.line_color = self.second_color#COLORs_sim[self.dag_id] 
                        self.plot.select(tags=[i_var]).end.fill_color = self.second_color#COLORs_sim[self.dag_id] 
                    else:
                        self.plot.select(tags=[i_var]).end.line_color = self.base_color
                        self.plot.select(tags=[i_var]).end.fill_color =self.base_color
            else:
                new_edge_data['color'] = [self.base_color for e in self.edges_cds.data['start_n']]
                new_edge_data['line_dash'] = ['solid' for e in self.edges_cds.data['start_n']]
                for i_var in self.edges_cds.data['stop_n']:
                    self.plot.select(tags=[i_var]).end.line_color = self.base_color
                    self.plot.select(tags=[i_var]).end.fill_color = self.base_color
            self.edges_cds.data = new_edge_data
            ##
            new_node_data['color'] = [self.second_color  if n in i_vars else self.base_color for n in self.nodes_cds.data['name']]
            self.nodes_cds.data =  new_node_data

    ## HELPERS
    def _create_digraph(self):
        """
        Parameters:
        -----------
            dag   A Dict(<var>: List of ancestor vars).
        """
        graph = nx.DiGraph()
        n_from_keys = list(self.dag.keys())
        n_from_keys.extend([v for l in self.dag.values() for v in l])
        graph_nodes = set(n_from_keys)
        for var in self.var_order:
            if var in graph_nodes:
                graph.add_node(var)
        for n in graph.nodes:
            if n in self.dag:
                for n_start in self.dag[n]:
                    graph.add_edges_from([(n_start, n)])
                    # graph.add_edges_from([(j,i) for i in self.dag for j in self.dag[i]])
        return graph
    
    ## SETTERS-GETTERS
    def get_plot(self):
        return self.plot