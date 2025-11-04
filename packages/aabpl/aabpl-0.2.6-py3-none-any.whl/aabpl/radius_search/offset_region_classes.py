# intersection of two circles with same r
from numpy import (linspace as _np_linspace, array as _np_array, abs as _np_abs, dot as _np_dot, roll as _np_roll)
from math import sin as _math_sin, cos as _math_cos, pi as _math_pi
from matplotlib import pyplot as plt
from aabpl.utils.general import angles_to_origin, angle_to, pt_is_left_of_vector
from aabpl.utils.rotations import transform_cell_pattern, transform_coord, transform_cell
from aabpl.utils.intersections import circle_line_segment_intersection, line_intersection, intersections_pts_arc_to_circle
from matplotlib.patches import (Rectangle as _plt_Rectangle, Polygon as _plt_Polygon, Circle as _plt_Circle)
from shapely.geometry import Polygon, LineString, Point
from geopandas import GeoSeries


# for each circle remember the meaning of the check (contains / overlaps)
# for each intersection point save what circle it comes from
# for each circle get intersection points with home cell
# for each circle-intersection point check whether its in triangle 1


class Vertex(object):
    """
    2D coordinate
    """

    def __init__(self,x,y,all_vtx):
        """
        create Vertex at coordinate
        """
        self.x = x
        self.y = y
        self.xy = (x,y)
        # self.outgoing_edges = []
        # self.incoming_edges = []
        self.regions = []
        self.all_vtx = all_vtx
        if not self.xy in all_vtx:
            all_vtx[self.xy] = self
        else:
            pass
            # self = all_vtx[self.xy]
    
    @staticmethod
    def clear(all_vtx):
        """
        clear all_vtx
        """
        all_vtx.clear()
    #

    @staticmethod
    def plot_many(vertices:dict=None, ax=None):
        """
        plot vertices at list of coordinates. if no list provided instead plots all stored in all_vtx
        """
        if ax is None:
          fig, ax = plt.subplots()

        vertices = list(vertices.values())
        if len(vertices):
            ax.scatter(x=[vtx.x for vtx in vertices], y=[vtx.y for vtx in vertices], marker='x', color='black')
        #
        return ax

    #
    
    def __repr__(self):
        props_not_to_print = ['all_vtx', 'outgoing_edges', 'incoming_edges', 'regions']
        return str(tuple([round(a,5) for a in self.xy]))
        # return str({key: val if type(val) != float else round(val,5) for key, val in self.__dict__.items() if key not in props_not_to_print})
    #

    def delete(self):
        """
        Remove vertex from all_vtx
        """
        self.all_vtx.pop(self.xy, None)
    #
#


class Edge(object):
    
    def __init__(
            self,
            vtx1:Vertex,
            vtx2:Vertex,
            all_edges:dict,
            contains:tuple=None,
            overlaps:tuple=None,
            enforce_int:bool=True
            ):
        """
        vertices are order counter clockwise
        enforce_int ensures that contains and overlaps are tuples of int() not numpy.int
        """
        self.vtx1 = vtx1
        self.vtx2 = vtx2
        self.coords = (
            vtx1.xy if (vtx1 is not None) else (None, None), 
            vtx2.xy if (vtx2 is not None) else (None, None),
            )
        self.regions = []
        self.plot_coords = None
        # vtx1.outgoing_edges.append(self)
        # vtx2.incoming_edges.append(self)
        self.all_edges = all_edges
        self.all_vtx = vtx1.all_vtx
        
        if not self.coords in all_edges:
            all_edges[self.coords] = self

        if not contains is None:
            self.contains  = tuple([int(z) for z in contains]) if enforce_int else contains
        if not overlaps is None:
            self.overlaps  = tuple([int(z) for z in overlaps]) if enforce_int else overlaps
    #

    @staticmethod
    def clear(all_edges):
        all_edges.clear()
    #

    def __repr__(self):
        props_not_to_print = ['all_edges', 'all_vtx', 'regions','coords', 'angle_min', 'angle_max', 'plot_coords']
        return str({key: val if type(val) != float else round(val,5) for key, val in self.__dict__.items() if key not in props_not_to_print})
    #
    
    def delete(self):
        self.all_edges.pop(self.coords, None)
    #
    def get_plot_coords(self, arc_steps_per_degree:float=5):
        if not self.plot_coords is None:
            return self.plot_coords
        self.plot_coords = [self.vtx1, self.vtx2]
        return self.plot_coords
    #
    @staticmethod
    def plot_many(
        edges:dict,
        ax=None,
        color_dict={'Arc':'blue', 'LineSegment':'green','Circle':'orange', 'other':'red'},
        **kwargs
        ):
        if ax is None:
          fig, ax = plt.subplots()
        #
        arc_polys = []
        for coords,edge in edges.items():
            edge.plot_single(ax=ax, color_dict=color_dict, **kwargs)
        if len(arc_polys) > 0:
            GeoSeries(arc_polys).plot(cmap='viridis', alpha=0.01, edgecolor='black', ax=ax)
        return ax
        #
    #

    def plot_single(self, ax=None, color_dict={'Arc':'blue', 'LineSegment':'green','Circle':'orange', 'other':'red'}, **kwargs):
        if ax is None:
          fig, ax = plt.subplots()
        #
        arc_polys=[]
        if self.type == 'Arc':
            # arc_polys.append(Polygon([self.center, self.coords[0], self.coords[1]]))
            plot_coords = self.get_plot_coords()
            arc_polys.append(Polygon([self.center]+self.get_plot_coords()+[self.center]))
            # ax.plot([0, self.center[0]], [0, self.center[1]], marker='.', color="black")
            rotation = angle_to((0,0), self.center)
            
            # ax.plot(
            #     [self.center[0], self.center[0]+self.r*_math_cos((rotation+self.angle_min)/360*2*_math_pi)],
            #     [self.center[1], self.center[1]+self.r*_math_sin((rotation+self.angle_min)/360*2*_math_pi)],
            #     marker='.', color='red',alpha=0.3,)
            # ax.plot(
            #     [self.center[0], self.center[0]+self.r*_math_cos((rotation+self.angle_max)/360*2*_math_pi)],
            #     [self.center[1], self.center[1]+self.r*_math_sin((rotation+self.angle_max)/360*2*_math_pi)],
            #     marker='.', color='green',alpha=0.3,)
            ax.plot(
                [self.center[0], self.center[0]+self.r*_math_cos((rotation+self.angle_vtx1)/360*2*_math_pi)],
                [self.center[1], self.center[1]+self.r*_math_sin((rotation+self.angle_vtx1)/360*2*_math_pi)],
                marker='.', color='red',alpha=0.3,)
            ax.plot(
                [self.center[0], self.center[0]+self.r*_math_cos((rotation+self.angle_vtx2)/360*2*_math_pi)],
                [self.center[1], self.center[1]+self.r*_math_sin((rotation+self.angle_vtx2)/360*2*_math_pi)],
                marker='.', color='green',alpha=0.3,)
            x_coords = [x for x,y in plot_coords]
            y_coords = [y for x,y in plot_coords]
            ax.plot(x_coords, y_coords, marker='o', color=color_dict[self.type],alpha=0.3, **kwargs)
        else:
            GeoSeries([LineString((self.vtx1.xy, self.vtx2.xy))]).plot(ax=ax, color='pink')
        return ax
    #
#

class LineSegment(Edge):
    """LineSegment between two 2D coordinates"""
    def __init__(
            self,
            vtx1:Vertex,
            vtx2:Vertex,
            all_edges:dict,
            contains:tuple=None,
            overlaps:tuple=None
        ):
        super().__init__(vtx1, vtx2, all_edges, contains=contains, overlaps=overlaps)
        self.type = 'LineSegment'
    #

    def intersection(self,edge):
        """
        
        """
        if edge.type == 'LineSegment':
            return line_intersection(self.coords, edge.coords)
        
        return circle_line_segment_intersection(
            circle_center=edge.center,
            circle_radius=edge.r,
            pt1=self.vtx1.xy,
            pt2=self.vtx2.xy,
            full_line=False,
        )
        
    def split(self, new_vtx):
        """Split at point if point is not start or end point of line segment"""
        if new_vtx.xy in self.coords:
            return [self]
        self.all_edges.pop(self.coords, None)
        line_kwargs = {'all_edges': self.all_edges, **{key: getattr(self, key) for key in ['contains', 'overlaps'] if hasattr(self, key)}}
        return [LineSegment(vtx1=self.vtx1, vtx2=new_vtx, **line_kwargs), LineSegment(vtx1=new_vtx, vtx2=self.vtx2, **line_kwargs)]
    #

    def calc_min_dist_to_pt(self, pt):
        """
        returns smallest distance between edge (a finite line segement) and pt
        """
        px = self.vtx2.x-self.vtx1.x
        py = self.vtx2.y-self.vtx1.y
        u =  ((pt[0] - self.vtx1.x) * px + (pt[1] - self.vtx1.y) * py) / float(px**2 + py**2)
        if u > 1:
            u = 1
        elif u < 0:
            u = 0
        return (((self.vtx1.x + u * px) - pt[0])**2 + ((self.vtx1.y + u * py) - pt[1])**2)**.5
    #

    def calc_max_dist_to_pt(self, pt):
        """
        returns largest distance between point and edge (=finite line segment)
        """
        return max([
            ((self.vtx1.x-pt[0])**2+(self.vtx1.y-pt[1])**2)**.5,
            ((self.vtx2.x-pt[0])**2+(self.vtx2.y-pt[1])**2)**.5
        ])
    #

    def transform_to_trgl(self, i:int):
        """
        
        """
        if i == 1: return self 
        
        new_vtx1 = Vertex(*transform_coord(self.vtx1.xy, i), all_vtx=self.all_vtx)
        new_vtx2 = Vertex(*transform_coord(self.vtx2.xy, i), all_vtx=self.all_vtx)
        
        edge_kwargs = {key: tuple(transform_cell(cell=_np_array(getattr(self, key)), i=i)) for key in ['contains', 'overlaps'] if hasattr(self, key)}
        if i%2 == 1: return LineSegment(vtx1=new_vtx1, vtx2=new_vtx2, all_edges=self.all_edges, **edge_kwargs)
        # flip order for regions 2,4,6,8
        return LineSegment(vtx1=new_vtx2, vtx2=new_vtx1, all_edges=self.all_edges, **edge_kwargs)
#


class Arc(Edge):
    """Arc around center (limited by two points on circle if supplied) """
    def __init__(
            self,
            center:tuple,
            r:float,
            all_edges:dict,
            vtx1:Vertex=None,
            vtx2:Vertex=None,
            clockwise:bool=None,
            contains:tuple=None,
            overlaps:tuple=None,
            ):
        super().__init__(vtx1, vtx2, all_edges, contains=contains, overlaps=overlaps)
        self.type = "Arc"
        self.center = center
        self.r = r
        self.vtx1 = vtx1
        self.vtx2 = vtx2
        self.angle_vtx1, self.angle_vtx2  = angles_to_origin((vtx1.xy, vtx2.xy), center) if not None in [vtx1,vtx2] else (0,360)
        self.angle_min, self.angle_max = sorted((self.angle_vtx1, self.angle_vtx2))
        # to-do. if radius/spacing is ever smaller 1/(2**.5) then angles can possibly be above 180 degrees
        self.clockwise = (self.angle_vtx2-self.angle_vtx1)%360>=180 if clockwise is None else clockwise
    #

    def intersection(self, edge):
        """
        
        """
  
        if edge.type == 'Arc':
            return intersections_pts_arc_to_circle(
                circle_center=edge.center,
                arc_center=self.center,
                arc_angle_min=self.angle_min,
                arc_angle_max=self.angle_max,
                r=self.r,
            )
        elif edge.type == 'Circle':
            return intersections_pts_arc_to_circle(
                circle_center=edge.center,
                arc_center=self.center,
                arc_angle_min=self.angle_min,
                arc_angle_max=self.angle_max,
                r=self.r,
            )
        
        return circle_line_segment_intersection(
            circle_center=self.center,
            circle_radius=self.r,
            pt1=edge.vtx1.xy,
            pt2=edge.vtx2.xy,
            full_line=False,
        )
    
    def split(self, new_vtx):
        """Split at point if point is not start or end point of arc segment"""
        if new_vtx.xy in self.coords:
            return [self]
        self.all_edges.pop(self.coords, None)
        arc_kwargs = {
            'center': self.center,
            'r': self.r,
            'all_edges': self.all_edges,
            'clockwise': self.clockwise,
            **{key: getattr(self, key) for key in ['contains', 'overlaps'] if hasattr(self, key)}
            }

        return [
            Arc(vtx1=self.vtx1, vtx2=new_vtx, **arc_kwargs), 
            Arc(vtx1=new_vtx, vtx2=self.vtx2, **arc_kwargs)
            ]
    #
    
    def calc_min_dist_to_pt(self, pt):
        """
        returns smallest distance between edge (an arc, not full circle) and pt
        """
        angle_pt = angles_to_origin([pt], self.center)[0]
        if self.angle_min < angle_pt and angle_pt < self.angle_max: # TODO double check if this condition is sufficient
            return min([
            ((self.vtx1.x-pt[0])**2+(self.vtx1.y-pt[1])**2)**.5,
            ((self.vtx2.x-pt[0])**2+(self.vtx2.y-pt[1])**2)**.5,
            ((pt[0]-self.center[0])**2 + (pt[1]-self.center[1])**2)**.5 - self.r,
        ])
        return min([
            ((self.vtx1.x-pt[0])**2+(self.vtx1.y-pt[1])**2)**.5,
            ((self.vtx2.x-pt[0])**2+(self.vtx2.y-pt[1])**2)**.5
        ])
    #

    def calc_max_dist_to_pt(self, pt):
        """
        returns largest distance between point and edge (=arc, not full circle)
        """
        angle_pt = angles_to_origin([pt], self.center)[0]
        if self.angle_min < angle_pt and angle_pt < self.angle_max: # TODO double check if this condition is sufficient
            return max([
            ((self.vtx1.x-pt[0])**2+(self.vtx1.y-pt[1])**2)**.5,
            ((self.vtx2.x-pt[0])**2+(self.vtx2.y-pt[1])**2)**.5,
            ((pt[0]-self.center[0])**2 + (pt[1]-self.center[1])**2)**.5 - self.r,
        ])
        return max([
            ((self.vtx1.x-pt[0])**2+(self.vtx1.y-pt[1])**2)**.5,
            ((self.vtx2.x-pt[0])**2+(self.vtx2.y-pt[1])**2)**.5
        ])
    #
    
    def transform_to_trgl(self, i:int):
        """
        
        """
        if i == 1: return self 
        new_center = transform_coord(self.center, i)
        new_vtx1 = Vertex(*transform_coord(self.vtx1.xy, i), all_vtx=self.all_vtx)
        new_vtx2 = Vertex(*transform_coord(self.vtx2.xy, i), all_vtx=self.all_vtx)
        # flip order for regions 2,4,6,8
        edge_kwargs = {key: tuple(transform_cell(cell=_np_array(getattr(self, key)), i=i)) for key in ['contains', 'overlaps'] if hasattr(self, key)}
        if i%2 == 1: return Arc(
            new_center,
            r=self.r,
            all_edges=self.all_edges,
            vtx1=new_vtx1,
            vtx2=new_vtx2,
            clockwise=self.clockwise,
            **edge_kwargs
            )
        return Arc(
            new_center,
            r=self.r,
            all_edges=self.all_edges,
            vtx1=new_vtx2,
            vtx2=new_vtx1,
            clockwise=not self.clockwise,
            **edge_kwargs
            )
    #
    def get_plot_coords(self, arc_steps_per_degree:float=5):
        total_angle = abs(self.angle_max - self.angle_min)
        n_steps = max(3,-int(-(total_angle * arc_steps_per_degree)))
        if not self.plot_coords is None and len(self.plot_coords)==n_steps+1:
            return self.plot_coords
        coords = []
        cx, cy = self.center
        r = self.r
        rotation = angle_to((0,0), self.center)
        total_angle = (self.angle_vtx1 - self.angle_vtx2)%360*-1 if self.clockwise else (self.angle_vtx2 - self.angle_vtx1)%360
        for angle_step in _np_linspace(0, total_angle, n_steps):
            x = cx + r * _math_cos((rotation+self.angle_vtx1+angle_step)/360*2*_math_pi)
            y = cy + r * _math_sin((rotation+self.angle_vtx1+angle_step)/360*2*_math_pi)
            coords.append((float(x),float(y)))
        self.plot_coords = coords
        # if len(coords)<2:
        #     print("coords",coords)
        return coords
    #
#

class Circle(object):
    """TODO potentially add as subclass of Edge?"""
    def __init__(self, center, r):
        self.type = "Circle"
        self.center = center
        self.r = r
        self.angle_min, self.angle_max = (0,360)
    #
    
    def plot_single(self, ax=None, facecolor="#00000011", edgecolor="green", linewidth=1, **kwargs):
        if ax is None:
          fig, ax = plt.subplots()
        #
        ax.add_patch(_plt_Circle(xy=self.center, radius=self.r, facecolor=facecolor, edgecolor=edgecolor, linewidth=linewidth, **kwargs))
        return ax
    #
#

class OffsetRegion(object):
    """OffsetRegion bounded by line segments and arcs"""

    def __init__(self, edges, checks, all_regions:dict, trgl_nr:int=1):
        self.id = -1
        self.edges = edges
        self.vertices = []
        self.trgl_nr = trgl_nr
        xs, ys = [], []
        for edge in edges:
            edge.regions.append(self)
            for vtx in (edge.vtx1, edge.vtx2):
                if vtx not in self.vertices:
                    self.vertices.append(vtx)
                    vtx.regions.append(self)
            # check if most extreme x/y values are not at the vertices but between
            if edge.type == 'Arc':
                # To-Do use clockwise information!
                if edge.clockwise:
                    if edge.angle_vtx2 < 90 and 90 < edge.angle_vtx1:
                        ys.append(edge.center[1] + edge.r)
                    if edge.angle_vtx2 < 180 and 180 < edge.angle_vtx1:
                        xs.append(edge.center[0] - edge.r)
                    if edge.angle_vtx2 < 270 and 270 < edge.angle_vtx1:
                        ys.append(edge.center[1] - edge.r)
                    if edge.angle_vtx2 > edge.angle_vtx1:
                        xs.append(edge.center[0] + edge.r)
                else:
                    if edge.angle_vtx1 < 90 and 90 < edge.angle_vtx2:
                        ys.append(edge.center[1] + edge.r)
                    if edge.angle_vtx1 < 180 and 180 < edge.angle_vtx2:
                        xs.append(edge.center[0] - edge.r)
                    if edge.angle_vtx1 < 270 and 270 < edge.angle_vtx2:
                        ys.append(edge.center[1] - edge.r)
                    if edge.angle_vtx1 > edge.angle_vtx2:
                        xs.append(edge.center[0] + edge.r)
        # if len(xs):
        #     print("xs",xs,min([vtx.x for vtx in self.vertices]),max([vtx.x for vtx in self.vertices]))
        # if len(ys):
        #     print(angles_to_origin([(1,1),(1,0),(0,-1)],(0,0)))
        #     print("ys",ys, min([vtx.y for vtx in self.vertices]),max([vtx.y for vtx in self.vertices]))
        # To-Do: For edges that have an arc it might be that a point between the vertices is 
        # the max/min x/y value. Probably only the case  
        xs = [vtx.x for vtx in self.vertices] #+ xs
        ys = [vtx.y for vtx in self.vertices] #+ ys
        self.xmin = min(xs)
        self.xmax = max(xs)
        self.ymin = min(ys)
        self.ymax = max(ys)
        self.checks = checks
        self.coords = tuple([edge.coords for edge in edges])
        self.all_regions = all_regions
        self.all_edges = edges[-1].all_edges
        self.all_vtx = edges[-1].vtx1.all_vtx

        if not self.coords in all_regions:
            all_regions[self.coords] = self
    #
    
    @staticmethod
    def delete_all(all_regions):
        all_regions.clear()
    #

    def __repr__(self):
        props_not_to_print = ['all_regions', 'all_edges', 'all_vtx', 'plot_coords']
        rnd = 5
        return str({key: {val.type:[(round(x,rnd),round(y,rnd)) for x,y in [val.vtx1,val.vtx2]]} if val in ['edges'] else (val if type(val) != float else round(val,rnd)) for key, val in self.__dict__.items() if key not in props_not_to_print})
    #

    def delete(self):
        self.all_regions.pop(self.coords, None)
    #

    def get_vertex_coords(self):
        coords = []
        for edge_start_coord, edge_end_coord in self.coords:
            if len(coords)==0 or edge_start_coord != coords[-1]:
                coords.append(edge_start_coord)
            if edge_end_coord != coords[-1]:
                coords.append(edge_end_coord)
            # if edge_start_coord not in coords:
            #     coords.append(edge_start_coord)
            # if edge_end_coord not in coords:
            #     coords.append(edge_end_coord)
        self.vertex_coords = coords
        return coords
    #

    def get_plot_coords(self, arc_steps_per_degree:float=5):
        coords = []
        for (edge_start_coord, edge_end_coord), edge in zip(self.coords, self.edges):
            if edge_start_coord not in coords:
                if edge_start_coord in coords and edge_start_coord != coords[-1]:
                    print("edges_start_repeated")
                coords.append(edge_start_coord)
            if edge.type == 'Arc':
                total_angle = abs(edge.angle_max - edge.angle_min)
                n_steps = max(3,-int(-(total_angle * arc_steps_per_degree)))
                cx, cy = edge.center
                r = edge.r
                rotation = angle_to((0,0), edge.center)
                # check distance to last coord to see whether the arc coords should be reversed or not
                reverse = int(
                    (
                    (cx + r * _math_cos((rotation+edge.angle_min)/360*2*_math_pi))**2 +
                    (cy + r * _math_sin((rotation+edge.angle_min)/360*2*_math_pi))**2
                    )**.5 > (
                    (cx + r * _math_cos((rotation+edge.angle_max)/360*2*_math_pi))**2 +
                    (cy + r * _math_sin((rotation+edge.angle_max)/360*2*_math_pi))**2
                    )**.5
                )
                
                for angle_step in _np_linspace(edge.angle_min, edge.angle_max, n_steps)[::(-1 if reverse else 1)][1:-1]:
                    x = cx + r * _math_cos((rotation+angle_step)/360*2*_math_pi)
                    y = cy + r * _math_sin((rotation+angle_step)/360*2*_math_pi)
                    if (float(x),float(y)) in coords and (float(x),float(y)) != coords[-1]:
                        print("anglestep",angle_step,edge.angle_min, edge.angle_max)
                    coords.append((float(x),float(y)))
            if edge_end_coord not in coords:
                if edge_end_coord in coords and edge_end_coord != coords[-1]:
                    print("edges_end_repeated")
                coords.append(edge_start_coord)
        self.plot_coords = coords
        return coords
    #

    def calc_area(self, arc_steps_per_degree:float=100):
        xs = []
        ys = []
        for ((x,y), edge_end_coord), edge in zip(self.coords, self.edges):
            xs.append(x)  
            ys.append(y)  
            if edge.type == 'Arc':
                total_angle = abs(edge.angle_max - edge.angle_min)
                n_steps = max(3,-int(-(total_angle * arc_steps_per_degree)))
                cx, cy = edge.center
                r = edge.r
                rotation = angle_to((0,0), edge.center)
                for angle_step in _np_linspace(edge.angle_min, edge.angle_max, n_steps):
                    xs.append(cx + r * _math_cos((rotation+angle_step)/360*2*_math_pi))
                    ys.append(cy + r * _math_sin((rotation+angle_step)/360*2*_math_pi))
        xs =_np_array(xs)
        ys =_np_array(ys)
        self.area = 0.5*_np_abs(_np_dot(xs,_np_roll(ys,1))-_np_dot(ys,_np_roll(xs,1))) 
        return self.area
    
    def plot_single(self,
                    ax=None,
                    plot_edges:bool=True,
                    plot_vertices:bool=False,
                    add_idx_edges:bool=False,
                    x_lim:tuple=(-0.02,0.52),
                    y_lim:tuple=(-0.02,0.52),
                    color='green',
                    edgecolor='black',
                    alpha=0.70, 
                    **kwargs):
        if ax is None:
            fig, ax = plt.subplots()
        kwargs = {'color': color, 'alpha': alpha, 'edgecolor': edgecolor,  **kwargs }
        GeoSeries([Polygon(self.get_plot_coords())]).plot(ax=ax, **kwargs)
        if plot_edges:
            for edge in self.edges:
                edge.plot_single(ax=ax)
        if plot_vertices:
            Vertex.plot_many(vertices=[vtx.xy for vtx in self.vertices], ax=ax)
        if add_idx_edges:
            for i, edge in enumerate(self.edges):
                ax.annotate(text=str(i), xy=edge.vtx1.xy) 
        if not x_lim is None:
            ax.set_xlim(x_lim)
        if not y_lim is None:
            ax.set_ylim(y_lim)
        return ax
    #

    @staticmethod
    def plot_many(
        regions:list, 
        plot_edges:bool=False, plot_vertices:bool=True, add_idxs:bool=True, x_lim:tuple=(-0.02,0.52), y_lim:tuple=(-0.02,0.52),
        arc_steps_per_degree:float=5,
        ax=None, cmap='tab20', alpha=0.3, title:str="", **kwargs):

        if ax is None:
            fig, ax = plt.subplots()
        
        if len(regions) > 0:
            color_keys = ['c', 'color']
            if not any([key in color_keys for key in kwargs]):
                kwargs.update({'cmap': cmap})
            
            
            try:
                # GeoSeries([Polygon(reg.get_plot_coords()) for reg in regions]).plot(ax=ax, alpha=alpha, **{'edgecolor':'black', **kwargs})
                GeoSeries([Polygon(reg.get_plot_coords(arc_steps_per_degree=arc_steps_per_degree)) for reg in regions]).plot(ax=ax, alpha=alpha, **kwargs)
            except:
                raise ValueError("kwargs", kwargs, "polys", [Polygon(reg.get_plot_coords(arc_steps_per_degree=arc_steps_per_degree)) for reg in regions],"ax", type(ax), ax, "alpha", alpha)
            if add_idxs:
                for i, region in enumerate(regions):
                    coords = region.get_vertex_coords()
                    ax.annotate(
                        text=str(i if not hasattr(region, 'id') else region.id),
                        xy=(sum([x for x,y in coords])/len(coords), sum([y for x,y in coords])/len(coords)),
                        horizontalalignment='center')
                
        if plot_edges:
            Edge.plot_many(edges=regions[-1].all_edges, ax=ax,markersize=0.2)
        if plot_vertices:
            # for reg in regions.values():
            #     Vertex.plot_many(all_vtx=[vtx.xy for vtx in reg.vertices], ax=ax)
            Vertex.plot_many(vertices=regions[-1].all_vtx, ax=ax)
        ax.set_xlim(x_lim)
        ax.set_ylim(y_lim)
        ax.set_title(title or str(len(regions)) + " regions.")
        return ax

    #

   


    def get_split_pts(self, intersection_edge):
        pts_to_split_at, vertices_intersected = [], []

        for i, edge in enumerate(self.edges):
            itx = edge.intersection(intersection_edge)
            # print(i,itx, edge)
            # check if itx is in edge
            if len(itx) == 0:
                continue 
            #

            if len(itx) == 1:
                pt = itx[0]
                # TODO check if vertex already exists: then its clear
                # new_vtx = Vertex(*itx[0])
                if not pt in vertices_intersected:
                    pts_to_split_at.append({'i': i, 'pt': pt, 'edge': edge, 'touches': pt in edge.coords, 'ids':[i]})# [edge1, itx[0], edge2], 
                else:
                    for pt_to_split_at in pts_to_split_at:
                        if pt_to_split_at['pt'] == pt:
                            pt_to_split_at['pt']['ids'].append(i)
                            print("pt_to_split_at['pt']['ids']",pt_to_split_at['pt']['ids'])
                            break
                if not pt in edge.coords:
                    vertices_intersected.append(pt)
                #
                continue
            #

            if len(itx) == 2:
                pts_to_split_at.append({'i': i, 'pts': itx, 'edge': edge, 'touches': pt in edge.coords})
                print("two intersections:", itx)
                continue
            #

            raise ValueError("TOO MANY (",len(itx),") INTERSECTIONS!", itx)
        #
        return pts_to_split_at
    #


    
    def add_check_result_no_intersection(self, intersection_edge, check):
        """
        
        """

        # mean_x = sum([c[0][0] for c in self.coords]) / len(self.coords)
        # mean_y = sum([c[0][1] for c in self.coords]) / len(self.coords)
        vtx_not_on_intersection_edge = next(
            (coord for coord in [startcoord for startcoord, endcoord in self.coords] if (
            hasattr(intersection_edge, 'vtx1') and coord != intersection_edge.vtx1.xy and coord != intersection_edge.vtx2.xy)),
            self.coords[0][0])
        if intersection_edge.type == 'LineSegment':
            # TODO this must store better on which side of the line implies check success
            result = pt_is_left_of_vector(*vtx_not_on_intersection_edge, *intersection_edge.vtx1.xy, *intersection_edge.vtx2.xy)
        else:
            x,y=vtx_not_on_intersection_edge
            # TODO as polygon is not necessarily convex centroid may lay outide, s.t this check may produce wrong results.  
            # BETTER APPROACH. Chose a point that is not on the current intersection edge. 
            # print('r', intersection_edge.r, ((mean_x-intersection_edge.center[0])**2 + (mean_y-intersection_edge.center[1])**2)**.5)
            result = intersection_edge.r**2 > ((x - intersection_edge.center[0])**2 + (y - intersection_edge.center[1])**2)
        self.checks.append({**check, 'result': result})
    #

    def split_with_circle(self, intersection_edge, check, plot_split:bool=False):
        """
        check if intersected
        split edges
        add vertices
        split region 
        TODO rework this logic. Too convoluted!
        TODO THIS FUNCTION IS WAY TOO LONG
        """
        pts_to_split_at = self.get_split_pts(intersection_edge=intersection_edge)
        # ax = self.plot_single()
        # intersection_edge.plot_single(ax=ax)
        # for pt in pts_to_split_at:
        #     print("pt",pt)
        #     ax.add_patch(_plt_Circle(xy=pt['pt'], radius=0.02, facecolor='red',alpha=0.7))
        #     ax.annotate(
        #                 text=("T" if pt['touches'] else "F") + '-' + ('L' if pt['edge'].type=='LineSegment' else 'A'), xy=pt['pt'], 
        #                 horizontalalignment='center', fontsize=10, color="black", weight="bold"
        #         )
        # ax.set_title(str(len(pts_to_split_at))+":"+str([tuple([round(c,4) for c in pt['pt']]) for pt in pts_to_split_at]))
        vertices_intersected, split_pts = [], []
        
        for split_at in pts_to_split_at:
            if 'pt' in split_at:
                if not split_at['pt'] in vertices_intersected:
                    split_pts.append(split_at)
                vertices_intersected.append(split_at['pt'])
            else:
                split_pts.append(split_at)
        
        pts_to_split_at=split_pts
        # print("Length after filter", len(pts_to_split_at), pts_to_split_at)
        if len(pts_to_split_at) == 0:
            self.add_check_result_no_intersection(intersection_edge=intersection_edge, check=check)
            return 'green' if self.checks[-1]['result'] else 'red'
        
        if len(pts_to_split_at) > 2:
            ax = self.plot_single(plot_edges=False)
            intersection_edge.plot_single(ax=ax)
            vertex_coords = self.get_vertex_coords()
            print(self)
            raise ValueError("TODO IMPLEMENT MULTIPLE INTERSECTIONS", pts_to_split_at, intersection_edge.center)
        
        line_kwargs = {
            'all_edges': self.all_edges, 
            **{key: getattr(intersection_edge, key) for key in ['contains', 'overlaps'] if hasattr(intersection_edge, key)}
            }
        arc_kwargs = {'center': intersection_edge.center, 'r': intersection_edge.r, **line_kwargs}

        if len(pts_to_split_at) == 1:
            if not 'pts' in pts_to_split_at[0]:
                self.add_check_result_no_intersection(intersection_edge=intersection_edge, check=check)
                return 'green' if self.checks[-1]['result'] else 'red'
            
            if len(pts_to_split_at[0]['pts']) != 2:
                raise ValueError("Unexpected number of itx", pts_to_split_at)
            print("OPTION A")
            start_pt, end_pt = pts_to_split_at[0]['pts']
            old_edge = pts_to_split_at[0]['edge']
            old_edge.delete()
            pos = pts_to_split_at[0]['i']
            start_vtx_existed = start_pt not in self.all_vtx
            end_vtx_existed = end_pt not in self.all_vtx

            start_new_vtx = Vertex(*start_pt, self.all_vtx) if start_vtx_existed else self.all_vtx[start_pt]
            end_new_vtx = Vertex(*end_pt, self.all_vtx) if end_vtx_existed else self.all_vtx[end_pt] 
            
            # if  type(intersection_edge) == Arc:
            if type(intersection_edge) != LineSegment:
                new_edge_start =               [Arc(vtx1=old_edge.vtx1, vtx2=start_new_vtx, clockwise=old_edge.clockwise, **arc_kwargs)] if start_vtx_existed else []
                new_edge_end =                 [Arc(vtx1=end_new_vtx,   vtx2=old_edge.vtx2, clockwise=old_edge.clockwise, **arc_kwargs)] if end_vtx_existed else []
                new_edge_middle =              [Arc(vtx1=start_new_vtx, vtx2=end_new_vtx, clockwise=old_edge.clockwise,   **arc_kwargs)]
                new_edge_intersection =         Arc(vtx1=start_new_vtx, vtx2=end_new_vtx, clockwise=None,   **arc_kwargs)#clockwise=True or False
                new_edge_intersection_reverse = Arc(vtx1=end_new_vtx,   vtx2=start_new_vtx, clockwise=not new_edge_intersection.clockwise, **arc_kwargs)
                print("new old clockwise",new_edge_intersection.clockwise, new_edge_intersection_reverse.clockwise)
            else:
                new_edge_start =               [LineSegment(vtx1=old_edge.vtx1, vtx2=start_new_vtx, **line_kwargs)] if start_vtx_existed else []
                new_edge_end =                 [LineSegment(vtx1=end_new_vtx,   vtx2=old_edge.vtx2, **line_kwargs)] if end_vtx_existed else []
                new_edge_middle =              [LineSegment(vtx1=end_new_vtx,   vtx2=old_edge.vtx2, **line_kwargs)]
                new_edge_intersection =         LineSegment(vtx1=start_new_vtx, vtx2=end_new_vtx,   **line_kwargs)
                new_edge_intersection_reverse = LineSegment(vtx1=end_new_vtx,   vtx2=start_new_vtx, **line_kwargs)
            
            # TODO MAKE THIS HANDLE LINESEGEMENTS ASWELL
            first_region_is_within_radius = pt_is_left_of_vector(*new_edge_intersection.center, *new_edge_intersection.vtx1.xy, *new_edge_intersection.vtx2.xy)
            # region without intersection_edge
            reg_without_itx = OffsetRegion(
                edges = self.edges[:pos] + new_edge_start + [new_edge_intersection] + new_edge_end + self.edges[pos+1:], 
                checks = self.checks+[{**check, 'result': first_region_is_within_radius}], all_regions = self.all_regions
            ) 
            # new intersection region 
            reg_itx = OffsetRegion(
                edges = new_edge_middle + [new_edge_intersection_reverse], 
                checks = self.checks+[{**check, 'result': not first_region_is_within_radius}], all_regions = self.all_regions
            )
            if plot_split:
                fig, ax = plt.subplots()
                self.plot_single(ax=ax, color='#caa', plot_edges=False)
                reg_without_itx.plot_single(ax=ax, color='green', alpha=0.5, hatch='/', plot_edges=False)
                reg_itx.plot_single(ax=ax, color='red', alpha=0.5, hatch='\\', plot_edges=False)
                GeoSeries([Point(intersection_edge.center).buffer(intersection_edge.r, 40)]).plot(ax=ax, edgecolor='black', facecolor='None')
                ax.set_title("1")
            self.delete()

            return 'yellow'
        
        if len(pts_to_split_at) == 2:
            start, end = pts_to_split_at
            if any(['pts' in d for d in pts_to_split_at]):
                raise ValueError("multiple double intersections", pts_to_split_at)
            start_pt, end_pt = start['pt'], end['pt'] 
            
            if start['touches'] and end['touches'] and (
                (start_pt, end_pt) in self.coords or (end_pt, start_pt) in self.coords or start_pt==end_pt
            ):
                indexes = []
                if (start_pt, end_pt) in self.coords:
                    indexes.append(self.coords.index((start_pt, end_pt)))
                if (end_pt, start_pt) in self.coords:
                    indexes.append(self.coords.index((end_pt, start_pt)))
                if any([type(edge) != type(intersection_edge) for i,edge in enumerate(self.edges) if i in indexes]):
                    print("TOOOOOOOOOOOODDDDDDDDDDOOOOOOOOOO")
                return 'pink'
            
            start_new_vtx = Vertex(*start_pt, self.all_vtx) if start_pt not in self.all_vtx else self.all_vtx[start_pt]
            end_new_vtx = Vertex(*end_pt, self.all_vtx) if end_pt not in self.all_vtx else self.all_vtx[end_pt] 
            
            if type(intersection_edge) != LineSegment:
                new_edge1 = Arc(vtx1=end_new_vtx, vtx2=start_new_vtx, clockwise=None, **arc_kwargs)
                new_edge2 = Arc(vtx1=start_new_vtx, vtx2=end_new_vtx, clockwise=not new_edge1.clockwise, **arc_kwargs)
            else:
                new_edge1 = LineSegment(vtx1=end_new_vtx, vtx2=start_new_vtx, **line_kwargs)
                new_edge2 = LineSegment(vtx1=start_new_vtx, vtx2=end_new_vtx, **line_kwargs)

            # check the type of the edge here to construct a new instance of it
            edge_start_before, edge_start_after = [[edge] for edge in start['edge'].split(start_new_vtx)] + ([] if not start['touches'] else [[]])
            edge_end_before, edge_end_after = [[edge] for edge in end['edge'].split(end_new_vtx)] + ([] if not end['touches'] else [[]])
            first_region_edge = new_edge1 if new_edge1.vtx1.xy == edge_end_before[0].vtx2.xy else new_edge2
            second_region_edge = new_edge1 if new_edge1.vtx1.xy == edge_start_before[0].vtx2.xy else new_edge2
            
            include_first_in_without_itx = (0 if start['touches'] and (start['i']+1==end['i'] or first_region_edge.vtx2.xy==self.edges[start['i']].vtx1.xy) else 1)
            # TODO MAKE THIS HANDLE LINESEGEMENTS ASWELL
            first_region_is_within_radius = pt_is_left_of_vector(*first_region_edge.center, *first_region_edge.vtx1.xy, *first_region_edge.vtx2.xy)
            
            reg_without_itx = OffsetRegion(
                edges = edge_start_after + self.edges[start['i']+include_first_in_without_itx:end['i']] + edge_end_before + [first_region_edge], 
                # checks = self.checks+[{**check, 'result': True}], all_regions = self.all_regions
                checks = self.checks+[{**check, 'result': first_region_is_within_radius}], all_regions = self.all_regions
            ) 
            # intersection
            exclude_first_in_itx = int(start['touches'] and self.edges[start['i']].vtx1.xy == first_region_edge.vtx2.xy)
            reg_itx = OffsetRegion(
                edges = edge_end_after + self.edges[end['i']+1:] +  self.edges[:start['i']] + (
                    edge_start_before if not (start['touches'] and self.edges[start['i']].vtx1.xy == first_region_edge.vtx2.xy) else []
                    ) + [second_region_edge], 
                # checks = self.checks+[{**check, 'result': True}], all_regions = self.all_regions
                checks = self.checks+[{**check, 'result': not first_region_is_within_radius}], all_regions = self.all_regions
            ) # Todo condition for when true
            
            if plot_split:
                fig, axs = plt.subplots(1,3, figsize=(12,3))
                for i in [0,1,2]:
                    ax = axs.flat[i]
                    coords = self.get_plot_coords()
                    x_coords = [x for x,y in coords]
                    y_coords = [y for x,y in coords]
                    x_min, x_max = min(x_coords), max(x_coords)
                    y_min, y_max = min(y_coords), max(y_coords)
                    x_dist, y_dist = x_max-x_min, y_max-y_min 
                    self.plot_single(
                        ax=ax, color='#ccc', plot_edges=False, x_lim=[x_min-x_dist/10, x_max+x_dist/10], y_lim=[y_min-y_dist/10, y_max+y_dist/10], plot_vertices=i==0, add_idx_edges=i==0,)
                    if i == 0:
                        first_region_edge.plot_single(ax=ax, linewidth=4)
                        ax.annotate(text='A', xy=first_region_edge.vtx1.xy)
                        ax.annotate(text='B', xy=first_region_edge.vtx2.xy)
                    if i == 1:
                        reg_without_itx.plot_single(ax=ax, color='green', alpha=0.5, hatch='/', plot_edges=False, x_lim=None, y_lim=None, plot_vertices=True)
                    if i == 2:
                        reg_itx.plot_single(ax=ax, color='red', alpha=0.5, plot_edges=False, x_lim=None, y_lim=None, plot_vertices=True)
                    GeoSeries([Point(intersection_edge.center).buffer(intersection_edge.r, 40)]).plot(ax=ax, edgecolor='black', facecolor='None')
                    if i == 0:
                        ax.set_title("T st:"+str(start['touches'])+", end:"+str(end['touches'])+ 'i st:'+str(start['i'])+' i end:'+str(end['i'])+
                                     ' nedges'+str(len(self.edges))+'+'+str(include_first_in_without_itx) + str(first_region_edge.vtx2.xy == self.edges[start['i']].vtx1.xy) )
                    elif i == 1:
                        ax.set_title("n vtcs:"+str(len(reg_without_itx.vertices)))
                    elif i == 2:
                        ax.set_title("n vtcs:"+str(len(reg_itx.vertices))+'ef'+str(exclude_first_in_itx))

            self.delete()

        # create arc
        return 'orange'
    #

    def calc_min_dist_to_pt(self, pt):
        """
        returns minimum distance of region to pt
        """
        return min([
            edge.calc_min_dist_to_pt(pt) for edge in self.edges
        ])
    #
    
    def calc_max_dist_to_pt(self, pt):
        """
        returns maximum distance of region to pt
        """
        return max([
            edge.calc_max_dist_to_pt(pt) for edge in self.edges
        ])
    #
    
    def transform_to_trgl(self, i:int):
        """
        Transform region from triangle into triangle i
        """
        if i == 1: return self 
        new_edges = []
        for edge in self.edges:
            new_edges.append(edge.transform_to_trgl(i=i))
        #
        
        if i % 2 == 1: 
            rotated_region = OffsetRegion(new_edges, checks=[], trgl_nr=i, all_regions=self.all_regions)
        else: 
            # reverse order for regions 2,4,6,8
            rotated_region = OffsetRegion(list(reversed(new_edges)), checks=[], trgl_nr=i, all_regions=self.all_regions)
        #
        
        rotated_region.contained_cells = tuple(sorted(
            [(lvl, (x,y)) for lvl, (x,y) in zip(
            [lvl for lvl,xy in self.contained_cells], 
            transform_cell_pattern([xy for lvl,xy in self.contained_cells], i))
        ]))
        
        rotated_region.overlapped_cells = tuple(sorted(
            [(lvl, (x,y)) for lvl, (x,y) in zip(
            [lvl for lvl,xy in self.overlapped_cells], 
            transform_cell_pattern([xy for lvl,xy in self.overlapped_cells], i))
        ]))
        
        return rotated_region
    #
    
    @staticmethod
    def merge_regions(regions:list, keep_old:bool=True, add_new:bool=False,):
        """
        Regions must are assumed to shared at least 1 edge, each point that is a combination of two points in regions to merged is assumed to lie within merge region 
        """

        # regions = list(all_regions.values())

        duplicated_edge_coords = set()
        all_edge_coords = set()
        all_edges = []
        for region in regions:
            for edge in region.edges:
                coords = edge.coords
                coords_rev = (coords[1], coords[0])
                
                if coords in all_edge_coords:
                    duplicated_edge_coords.update([coords, coords_rev])
                
                all_edge_coords.update([coords, coords_rev])
        
            all_edges.extend(region.edges)
            if not keep_old:
                region.delete()
        first_last_tpl_list = []
        edges_merged_region = []
        for region in regions:
            edges = region.edges
            duplicated_ids = [i for i,edge in enumerate(edges) if edge.coords in duplicated_edge_coords]
            non_duplicated_ids = [i for i,edge in enumerate(edges) if not edge.coords in duplicated_edge_coords]
            if len(non_duplicated_ids) == len(edges):
                raise ValueError("WEIRD°!")
            start = next((i for i in range(min(non_duplicated_ids), max(non_duplicated_ids)+1) if (i-1)%len(edges) not in non_duplicated_ids),None)
            end = next((i for i in range(min(non_duplicated_ids), max(non_duplicated_ids)+1) if (i+1)%len(edges) not in non_duplicated_ids), None)
            if start <= end:
                edges_merged_region.extend(edges[start:end+1])
            else:
                edges_merged_region.extend(edges[start:])
                edges_merged_region.extend(edges[:end+1])
            # check whether duplicate ids wrap around 
            
        merged_region = OffsetRegion(edges=edges_merged_region, checks=regions[0].checks, all_regions=region.all_regions, trgl_nr=min([reg.trgl_nr for reg in regions]))
        if not add_new:
            merged_region.delete()
        merged_region.contained_cells = regions[0].contained_cells
        merged_region.overlapped_cells = regions[0].overlapped_cells
        merged_region.nr = min([reg.nr for reg in regions])
        merged_region.trgl_nrs = [reg.trgl_nr for reg in regions]
        return merged_region
    #
#
