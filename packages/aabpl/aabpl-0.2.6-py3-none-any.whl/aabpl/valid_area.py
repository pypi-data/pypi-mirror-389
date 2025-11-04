from numpy import (
    array as _np_array, 
    exp as _np_exp,
    unique, linspace, invert, flip, transpose, concatenate, sign, zeros, 
    min as _np_min, max as _np_max, equal, where, logical_or, logical_and, all, newaxis)
from math import inf as _math_inf, pi as _math_pi, acos as _math_acos, sin as _math_sin
from shapely.geometry import Polygon as _shapely_Polygon, MultiPoint as _shapely_MultiPoint, MultiPolygon as _shapely_MultiPolygon
from pandas import DataFrame as _pd_DataFrame
from concave_hull import concave_hull
from matplotlib import pyplot as plt
from matplotlib.patches import (Rectangle as _plt_Rectangle, Polygon as _plt_Polygon, Circle as _plt_Circle)
from .illustrations.plot_utils import plot_polygon
from .utils.general import count_polygon_interiors
from .utils.intersections import circle_line_segment_intersection

def infer_sample_area_from_pts(
        pts:_pd_DataFrame=None,
        grid=None,
        hull_type:str=['buffered_cells', 'concave','convex','bounding_box','grid', 'buffer'][0],
        concavity:float=1,
        buffer:float=None,
        tolerance:float=None,
        x:str='lon',
        y:str='lat',
        plot_sample_area:dict=None,
) -> _shapely_Polygon:
    """Creates and returns a polygon containing all points which can be used to draw random points within

    Args:
    -------
    pts (pandas.DataFrame):
        DataFrame of points for which a search for other points within the specified radius shall be performed
    hull_type (str):
        Must be one of ['concave','convex','bounding_box','grid']. 
            - 'buffered_cells': each non-empty cell plus buffer around them
            - 'concave': a concave hull will be drawn around points. 
            - 'convex': a convex hull will be drawn around points.
            - 'bounding_box': a bounding box around points will be drawn
            - 'grid': a box covering full grid will be drawn
    concavity (float):
        will only be used when hull_type=='concave'. Value must be in (0,Inf]. Small values results in "very concave"(=fuzzy) hull. Inf results in convex hull (default=1)
    buffer (float):
        Size of the buffer that shall be applied on the hull. If None then it will be set equal to radius (r) (default=None)
    tolerance (float):
        Tolerance>=0 used to simplify geometry using Douglas-Peucker specifying maximum allowed geometry displacement. Chosing a parameter that is too small might result in performance issues. (default=None)
    x (str):
        column name of x-coordinate (=longtitude) in pts_source (default='lon')
    y (str):
        column name of y-coordinate (=lattitude) in pts_source (default='lat')
    
    Returns:
    -------
    sample_poly (shapely.geometry.Polygon):
        a grid covering all points (custom class containing 
    """
    # To-Do maybe add minumum observations per cell to be kept
    if tolerance is None:
        tolerance = buffer

    area_missing_from_hull = 1

    if hull_type == 'bounding_box':
    
        min_x, min_y = pts[[x,y]].values.min(axis=0)
        max_x, max_y = pts[[x,y]].values.max(axis=0)
        hull_coordinates = [
            (min_x,min_y),
            (max_x,min_y),
            (max_x,max_y),
            (min_x,max_y),
            ]
        
    elif hull_type == 'grid':
        if grid is None:
            raise ValueError('In order to use the grid bounds as valid area, a grid needs to be supplied as function input: infer_sample_area_from_pts(grid=...)')
        hull_coordinates = [
            (grid.total_bounds.xmin,grid.total_bounds.ymin),
            (grid.total_bounds.xmax,grid.total_bounds.ymin),
            (grid.total_bounds.xmax,grid.total_bounds.ymax),
            (grid.total_bounds.xmin,grid.total_bounds.ymax),
            ]
    
    elif hull_type in ['concave', 'convex']:
    
        hull_coordinates = concave_hull(
            points=pts[[x,y]].values,
            concavity=concavity if hull_type=='concave' else _math_inf,
        )
    elif hull_type == 'buffered_points' or hull_type == 'buffer':
        if hull_type == 'buffer':
            print("sample_area hull_type 'buffer' deprectated. Use 'buffered_points' instead.")
        if len(pts)>10000:
            print("WARNING: creating a buffer around each point might cause long computation times for "+str(len(pts))+" points. Consider using hull_type='concave' as more efficient method.")
        
        q=max(1,-(-2*buffer/tolerance)//1)
        sample_poly = _shapely_MultiPoint(pts[[x,y]].values).buffer(distance=buffer, quad_segs=q).simplify(tolerance)
        # don't simplify this shape
        area_missing_from_hull = 0

    elif hull_type=='buffered_cells':
        id_to_pt_ids = grid.id_to_pt_ids
        row_col_to_bounds = grid.row_col_to_bounds
        polygons = [[[(xmin,ymin),(xmax,ymin),(xmax,ymax),(xmin,ymax)]] for (xmin,ymin),(xmax,ymax) in [row_col_to_bounds[id] for id in id_to_pt_ids]]
        # maybe create one np array arround with coords of buffered cell around (0,0) and then add centroids to it 
        sample_poly = _shapely_MultiPolygon(polygons).buffer(buffer, quadsegs=3)
        # don't simplify this shape
        area_missing_from_hull = 0
           
    else:
        raise ValueError("hull_type to infere sample area for random points must be in ['buffered_cells', 'concave','convex','buffered_points', 'bounding_box', 'grid']. Value provided:",hull_type)
    #
    if area_missing_from_hull > 0:
        hull_poly = _shapely_Polygon(hull_coordinates).buffer(distance=0,quad_segs=1)
        # plot_polygon(poly=hull_poly)
        while area_missing_from_hull > 0:
            sample_poly = hull_poly
            q=max(1,-(-2*buffer/tolerance)//1)
            sample_poly = sample_poly.buffer(distance=buffer, quad_segs=q)
            
            sample_poly = sample_poly.simplify(tolerance)

            area_missing_from_hull = hull_poly.difference(
                sample_poly.intersection(hull_poly)
            ).area
            tolerance = tolerance*0.8
        #

    # plot_polygon(poly=sample_poly)
    if not plot_sample_area is None:
        fig,ax = plt.subplots(nrows=1,ncols=1,figsize=(8,8))
        ax.scatter(x=pts[x], y=pts[y], color="#51da58", s=0.3)
        plot_polygon(ax=ax, poly=sample_poly, facecolor="#06047640", edgecolor='red')
    # shoot warning if polygon is getting comple

    return sample_poly
#

def remove_invalid_area_from_sample_poly(
        sample_poly:_shapely_Polygon,
        invalid_areas:_shapely_Polygon,
):
    valid_area_poly = sample_poly.difference(invalid_areas)

    return valid_area_poly
#

def apply_invalid_area_on_grid(
        
):
    return
#

def disk_cell_intersection_area(
    disk_center_pt:_np_array,      
    cell_bounds:tuple=((0,0),(1,1)),
    grid_spacing:float=0.0075,
    r:float=0.0075,
    silent = False,
    return_n_itx=False,
) -> float:
    """
    note this does not handle the case where the point lies within cell bounds

    Calculates intersection area of cell and search-circle (0,grid_spacing**2)
    Case for no intersection will be handled before (fully included or fully excluded).
    Case 1: two intersection points (more than half of square are within radius) - 3 vertices are within circle 
    Case 2: two intersection points (more than half of square are within radius) - 1 vertex is within circle
    Case 3: two intersection points (less than half of square within radius) - 0 vertices within circle (same row or col)
    Case 4: two intersection points (unclear wheter more or less than half) - 2 vertices within circle (same row or col)
    Case 5: four intersection points (more than half of circle is included) - 2 vertices within circle (same row or col)
    
    TODO: if grid_spacing/2 is greater than radius there will be weird instances 

    This can also be done already as a function of the point offset
    and is also symmetrical towards the triangle
    the intersection area only needs to be computed for those cases where excluded cells are intersected 

    """
    
    (xmin,ymin),(xmax,ymax) = cell_bounds
    if grid_spacing is None:
        rectangle_area = (abs(xmax-xmin)*abs(ymax-ymin))
    else:
        rectangle_area = grid_spacing**2
    calculated_area = 0
    precision = 13
    if not silent:
        fig,ax=plt.subplots()
        ax.add_patch(_plt_Circle(xy=disk_center_pt, radius=r, alpha=0.4))
        ax.add_patch(_plt_Rectangle(xy=(xmin,ymin),width=(xmax-xmin),height=(ymax-ymin), alpha=0.4))
        ax.autoscale_view()
    
    vtx_coords = (
        (xmin,ymin),
        (xmax,ymin),
        (xmax,ymax),
        (xmin,ymax),
        )
    vtx_dis_to_c = (
        ((disk_center_pt[0]-vtx_coords[0][0])**2+(disk_center_pt[1]-vtx_coords[0][1])**2)**.5,
        ((disk_center_pt[0]-vtx_coords[1][0])**2+(disk_center_pt[1]-vtx_coords[1][1])**2)**.5,
        ((disk_center_pt[0]-vtx_coords[2][0])**2+(disk_center_pt[1]-vtx_coords[2][1])**2)**.5,
        ((disk_center_pt[0]-vtx_coords[3][0])**2+(disk_center_pt[1]-vtx_coords[3][1])**2)**.5
    )
    vtx_in_r = [dis<=r for dis in vtx_dis_to_c]
    
    if sum(vtx_in_r)==4:
        if return_n_itx:
            return (rectangle_area, sum(vtx_in_r)) 
        else:
            return rectangle_area
    #
    if sum(vtx_in_r)==0:
        # circular segment 
        # say vertices B and C are closest to circle center. Then circle intersects BC 
        # (twice unless only touching or not intersecting at all)
        v_closest1, v_secondclosest1 = [i for d,i in sorted([(d,i) for i,d in enumerate(vtx_dis_to_c)])][:2]
        segment1 = (vtx_coords[v_closest1], vtx_coords[v_secondclosest1])
        itx_pts = circle_line_segment_intersection(
            circle_center=disk_center_pt,
            circle_radius=r,
            pt1=segment1[0],
            pt2=segment1[1],
            full_line=False,
            precision=precision,
        )
        if len(itx_pts)<2:
            if return_n_itx:
                return (0., sum(vtx_in_r))
            else:
                return 0.
        
        itx_pt1, itx_pt2 = itx_pts
        #             
    elif sum(vtx_in_r)==1:
        # circular segment + triangle
        # say vertex B is closest to circle center then circle intersect AB and BC
        v_closest1 = vtx_dis_to_c.index(min(vtx_dis_to_c))
        segment1 = (vtx_coords[(v_closest1-1)%4], vtx_coords[v_closest1])
        segment2 = (vtx_coords[v_closest1], vtx_coords[(v_closest1+1)%4])
        itx_pt1 = circle_line_segment_intersection(
            circle_center=disk_center_pt,
            circle_radius=r,
            pt1=segment1[0],
            pt2=segment1[1],
            full_line=False,
            precision=precision,
        )
        itx_pt2 = circle_line_segment_intersection(
            circle_center=disk_center_pt,
            circle_radius=r,
            pt1=segment2[0],
            pt2=segment2[1],
            full_line=False,
            precision=precision,
        )
        if len(itx_pt1) != 1 or len(itx_pt2) != 1:
            raise ValueError("Unexpected number of intersections",itx_pt1, itx_pt2)
        itx_pt1, itx_pt2 = itx_pt1[0], itx_pt2[0]
        triangle = 1/2 * abs(itx_pt1[0]-itx_pt2[0])*abs(itx_pt1[1]-itx_pt2[1])
        calculated_area += triangle    
    elif sum(vtx_in_r)==2:
        # circular segement + triangle + triangle
        # say vertex B and C are closest to circle center then circle intersect AB and CD
        v_closest1, v_secondclosest1 = [i for d,i in sorted([(d,i) for i,d in enumerate(vtx_dis_to_c)])][:2]
        offset = 1 if (v_closest1-1)%4 != v_secondclosest1 else -1 
        segment1 = (vtx_coords[(v_closest1-offset)%4], vtx_coords[v_closest1])
        segment2 = (vtx_coords[v_secondclosest1], vtx_coords[(v_secondclosest1+offset)%4])
        itx_pt1 = circle_line_segment_intersection(
            circle_center=disk_center_pt,
            circle_radius=r,
            pt1=segment1[0],
            pt2=segment1[1],
            full_line=False,
            precision=precision,
        )
        itx_pt2 = circle_line_segment_intersection(
            circle_center=disk_center_pt,
            circle_radius=r,
            pt1=segment2[0],
            pt2=segment2[1],
            full_line=False,
            precision=precision,
        )
        if len(itx_pt1) != 1 or len(itx_pt2) != 1:
            raise ValueError("Unexpected number of intersections",itx_pt1, itx_pt2)
        itx_pt1, itx_pt2 = itx_pt1[0], itx_pt2[0]
        # match: which intersection point is aligned to which vertex?
        # align_closesty_to_pt1y = (
        #     0 if vtx_coords[v_closest1][0]==itx_pt1[0] else # x closest = x pt1 
        #     1 if vtx_coords[v_closest1][1]==itx_pt1[1] else # y closest = y pt1
        #     -2 if vtx_coords[v_closest1][0]==itx_pt2[0] else # x closest = x pt2
        #     -1 #if vtx_coords[v_closest1][0]==itx_pt1[0] # y closest = y pt2
        # )
        # # triangle 1: closest1,secondclosest1,pt2
        # pt_A, pt_B = (itx_pt1, itx_pt2) if align_closesty_to_pt1y in [0,1] else (itx_pt2, itx_pt1)
        # x_is_aligned = int(align_closesty_to_pt1y%2==0)
        # # if x is aligned take y difference
        # if vtx_coords[v_closest1][x_is_aligned]!=vtx_coords[v_secondclosest1][x_is_aligned]:
        #     print("x_is_aligned",x_is_aligned,"closest1",vtx_coords[v_closest1],"secondclosest1",vtx_coords[v_secondclosest1])
        # triangles = 1/2 * grid_spacing * (
        #     abs(vtx_coords[v_closest1][x_is_aligned]-pt_B[x_is_aligned]) +
        #     abs(vtx_coords[v_secondclosest1][x_is_aligned]-pt_A[x_is_aligned])
        # ) 
       
        x_is_aligned = 1 if vtx_coords[v_closest1][0]==itx_pt1[0] or vtx_coords[v_closest1][0]==itx_pt2[0] else 0
        triangles = 1/2 * grid_spacing * (
            abs(vtx_coords[v_closest1][x_is_aligned]-itx_pt1[x_is_aligned]) +
            abs(vtx_coords[v_closest1][x_is_aligned]-itx_pt2[x_is_aligned])
        )

        calculated_area += triangles

        # triangle 2: closest1,pt2,pt1
        # triangle1 = 1/2 * abs(
        #     vtx_coords[v_closest1][(align_closesty_to_pt1y+1)%2]-itx_pt2[(align_closesty_to_pt1y+1)%2]) * abs(
        #         vtx_coords[v_closest1][(align_closesty_to_pt1y+0)%2]-itx_pt2[(align_closesty_to_pt1y+0)%2])
        # # triangle 2: closest1,pt2,pt1
        # triangle2 = 1/2 * abs(
        #     vtx_coords[v_closest1][(align_closesty_to_pt1y+1)%2]-itx_pt1[(align_closesty_to_pt1y+1)%2]) * abs(
        #     vtx_coords[v_closest1][(align_closesty_to_pt1y+0)%2]-itx_pt2[(align_closesty_to_pt1y+0)%2]
        # )
        # # if triangle1==0.0 or triangle2==0.0:
        # #     print("triangle1",triangle1, "triangle2", triangle2)
        # # else:
        # #     print("both,,,")
        # calculated_area += triangle1 + triangle2
    elif sum(vtx_in_r)==3:
        # rectangle - triangle + circular segement
        # say vertex B is most distant from circle center: then circle intersects line segments AB and BC.
        v_farthest1 = vtx_dis_to_c.index(max(vtx_dis_to_c))
        segment1 = (vtx_coords[(v_farthest1-1)%4], vtx_coords[v_farthest1])
        segment2 = (vtx_coords[v_farthest1], vtx_coords[(v_farthest1+1)%4])
        
        itx_pt1 = circle_line_segment_intersection(
            circle_center=disk_center_pt,
            circle_radius=r,
            pt1=segment1[0],
            pt2=segment1[1],
            full_line=False,
            precision=precision,
        )
        itx_pt2 = circle_line_segment_intersection(
            circle_center=disk_center_pt,
            circle_radius=r,
            pt1=segment2[0],
            pt2=segment2[1],
            full_line=False,
            precision=precision,
        )
        itx_pt1, itx_pt2 = itx_pt1[0], itx_pt2[0]
        triangle = 1/2 * abs(itx_pt1[0]-itx_pt2[0])*abs(itx_pt1[1]-itx_pt2[1])
        calculated_area = rectangle_area - triangle 
    
    # calcualte area of circle segement
    len_pt0_pt1 = ((itx_pt1[0]-itx_pt2[0])**2+(itx_pt1[1]-itx_pt2[1])**2)**.5
    angle_rad = _math_pi-2*_math_acos(((len_pt0_pt1/2)/r))
    circle_segment_area = 0.5 * r**2 * (angle_rad - _math_sin(angle_rad))
    calculated_area += circle_segment_area

    # return  (calculated_area, sum(vtx_in_r))
    if return_n_itx:
        return min(calculated_area, rectangle_area),sum(vtx_in_r)
    else:
        return min(calculated_area, rectangle_area)

#

def disk_cell_intersection_estimate(
    disk_center_pt:_np_array,      
    centroid:tuple=(0,0),
    grid_spacing:float=0.0075,
    r:float=0.0075,
    a:float=0,
    b:float=0,
        
):
    d = ((disk_center_pt[0]-centroid[0])**2+(disk_center_pt[0]-centroid[0])**2)**.5
    d_r = d/r
    s_r = grid_spacing/r

    # b and c are the same for all points
    b = 1 / (0.70628102 + _np_exp(0.57266908 * (s_r - 2))) # b
    c = 1 / (-0.21443453 + _np_exp(0.76899004 * (s_r - 2))) # c
    a = 1 - 1 / (1.0 + b * _np_exp(-c * (d_r - 1)))
    area = a * grid_spacing**2
    return area

def calculated_valid_area_around_pts(
        pts,
        grid,
        r:float,
        invalid_grid_cells,
        x:str='lon',
        y:str='lat',
        invalid_area_geometry=None,
        return_percentage:bool=True,
):
    """Calculates valid
    return_percentage if True returns share from [0,1] otherwise returns area in units of projection (meters)



    """
    full_circle = 2*_math_pi*r**2
    valid_area = full_circle
    # sort points by cell - cell_region - xy 
    # for cell: common contained cells sum invalid area
    # check if overlapped cells have an invalid area
    # if not jump to next cell
    # for cell-cell-region sum common contained area
    # check if overlapped cell have an invalid area
    # if not jump to next cell-region
    # for point check overlapped cells for invalid area
