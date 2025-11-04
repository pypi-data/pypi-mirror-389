# intersection of two circles with same radius
from numpy import array as _np_array, sign as _np_sign, arange as _np_arange, invert as _np_invert, zeros as _np_zeros
from numpy.linalg import norm as _np_linalg_norm
from math import log10 as _math_log10
from matplotlib import pyplot as plt
from aabpl.utils.general import make_bins_from_vals, get_vals_from_bins
from aabpl.utils.distances_to_cell import (get_cell_closest_point_to_point, get_cell_farthest_vertex_to_point,
 check_if_never_contains_convex_set, check_if_always_overlaps_full_convex_set, 
 get_cells_relevant_for_disk_by_type, get_cells_by_lvl_relevant_for_disk_by_type)
from .offset_region_classes import OffsetRegion, Vertex, LineSegment, Circle, Edge
from aabpl.illustrations.illustrate_cell_pattern import plot_cell_pattern
from aabpl.testing.test_performance import time_func_perf
from shapely.geometry import Polygon, LineString, Point
from geopandas import GeoSeries, GeoDataFrame
import inspect # remove after testing


def create_triangle_1_region(
        clear_all:bool=True,
        convex_set_coordiantes:list=[(0.,0.), (0.5,0.), (0.5,0.5)]
) -> dict:
    """
    Delete all Regions, Edges, Vertices from dicts. Create new vertices, edges and region for triangle 1
    """
    if clear_all: 
        all_regions = dict()
        all_edges = dict()
        all_vtx = dict()
    
    vertices_set = [Vertex(x=x, y=y, all_vtx=all_vtx) for (x,y) in convex_set_coordiantes]
    edges_set = [LineSegment(vtx1=v1, vtx2=v2, all_edges=all_edges) for v1,v2 in zip(vertices_set, vertices_set[1:]+vertices_set[:1])]
    OffsetRegion(edges=edges_set, checks=[], all_regions=all_regions)
    
    return all_regions
#


def add_circle_check_to_dict(
        cell:_np_array,
        nev_cn:bool,
        alw_ov:bool,
        check_dict,
        r:float,
        grid_spacing:float,
):
    """
    TODO 
    updates check dicts with check(s)
    """
    trgl_pt = (0.25,0.125)
    point_in_triangle1 = _np_array([(0.25,0.125)]) # TODO remove wraping list
    
    if not alw_ov:
        closest_pt = tuple([float(v) for v in get_cell_closest_point_to_point(trgl_pt, cell)])
        if closest_pt not in check_dict:
            check_dict[closest_pt] = {'split_edge': Circle(center=closest_pt, r=r/grid_spacing)}
        check_dict[closest_pt]['overlaps'] = cell
        check_dict[closest_pt]['split_edge'].overlaps = tuple([*cell])
    #

    if not nev_cn:
        farthest_pt = tuple([float(v) for v in get_cell_farthest_vertex_to_point(point_in_triangle1, cell)[0]])
        if farthest_pt not in check_dict:
            check_dict[farthest_pt] = {'split_edge': Circle(center=farthest_pt, r=r/grid_spacing)}

        check_dict[farthest_pt]['contains'] = cell
        check_dict[farthest_pt]['split_edge'].contains = tuple([*cell])
    #
#

def add_line_check_to_dict(
        cell:_np_array,
        nev_cn:bool,
        alw_ov:bool,
        check_dict,
        all_regions:dict,
        r:float,
        grid_spacing:float,
):
    """
    TODO maybe already add more check logic here e.g the segment
    updates check dicts with check
    """
        
    row, col = [int(c) for c in cell]
    
    an_edge  = list(all_regions.values())[-1].edges[-1]
    all_edges = an_edge.all_edges
    all_vtx = an_edge.vtx1.all_vtx
    
    if row == 0 and col == 0:
        raise ValueError('Not implemented. Choose grid spacing s.t. search radius**2 > (2*grid_spacing**2).')    
    
    if not alw_ov:
        if col == 0.:
            split_edge = LineSegment(
                vtx1=Vertex(0.0 if row > 0 else 0.5,  (row - (.5 - r) * _np_sign(row)), all_vtx),
                vtx2=Vertex(0.0 if row < 0 else 0.5,  (row - (.5 - r) * _np_sign(row)), all_vtx), 
                all_edges=all_edges
            )
        else:
            split_edge = LineSegment(
                vtx1=Vertex((col - (.5 - r) * _np_sign(col)), 0.5 if col > 0 else 0.0, all_vtx),
                vtx2=Vertex((col - (.5 - r) * _np_sign(col)), 0.5 if col < 0 else 0.0, all_vtx), 
                all_edges=all_edges
            )
        split_edge.overlaps = (row, col)
        check_dict[split_edge] = {'split_edge': split_edge, 'overlaps': (row,col)}
    
    if not nev_cn:
        farthest_pt = (
            -0.5 if col == 0 else col + .5 * _np_sign(col),
            -0.5 if row == 0 else row + .5 * _np_sign(row)
        )
        if farthest_pt not in check_dict:
            check_dict[farthest_pt] = {'split_edge': Circle(center=farthest_pt, r=r/grid_spacing)}
        
        check_dict[farthest_pt]['split_edge'].contains = (row, col)
        check_dict[farthest_pt]['contains'] = cell
        # # THESE RESULTS WILL BE CHECKED ANYWAYS. AT THE END YOU CAN REQUEST THOSE RESULTS
        # check_dict[(x,y)] = {'cells_to_overlap': cells_to_overlap, 'contains': (x,y)}
    #
#

def create_check_dict(
    cells_to_check,
    all_regions:dict,
    r:float,
    grid_spacing:float=1,
    include_boundary: bool = False        
):
    """
    Gets all cells that are potentially overlap or conain or contain set if buffered by radius
    TODO ensure r/grid_spacing covers all cases
    """
    check_dict = dict()
    triangle_1_vertices = _np_array([[0, 0], [0.5, 0], [0.5, 0.5]])

    cells_always_overlapped = check_if_always_overlaps_full_convex_set(
        cells=cells_to_check,
        convex_set_vertices=triangle_1_vertices,
        r=r,
        grid_spacing=grid_spacing,
        vertex_is_inside_convex_set=True,
        include_boundary=include_boundary,
    )

    cells_never_contained = check_if_never_contains_convex_set(
        cells=cells_to_check,
        convex_set_vertices=triangle_1_vertices,
        r=r,
        grid_spacing=grid_spacing,
        vertex_is_inside_convex_set=True,
        include_boundary=include_boundary,
    )

    cells_alw_only_overlapped = []
    for cell, alw_ov, nev_cn in zip(cells_to_check, cells_always_overlapped, cells_never_contained):
        if alw_ov and nev_cn:
            cells_alw_only_overlapped.append(cell) # TODO this can be removed - no longer necessary to store those.
        if 0 in cell: # cell in same column or row
            add_line_check_to_dict(cell=cell, nev_cn=nev_cn, alw_ov=alw_ov, check_dict=check_dict, all_regions=all_regions, r=r, grid_spacing=grid_spacing,)
        else:
            add_circle_check_to_dict(cell=cell, nev_cn=nev_cn, alw_ov=alw_ov, check_dict=check_dict, r=r, grid_spacing=grid_spacing,)
        #
    #
    return check_dict, cells_to_check[cells_always_overlapped]
#

def apply_checks_to_create_regions(
        check_dict,
        trgl_regions:dict,
        r:float,
        plot_offset_checks:dict=None,
        axs = None
    ):
    """
    TODO get check(s) plural / singular clean.
    """
    if not plot_offset_checks is None:
        if axs is None:
            nrows = int(len(check_dict)**.5)
            ncols = -int(-len(check_dict.items())//nrows) 
            fig,axs = plt.subplots(nrows, ncols, figsize=(ncols*5,nrows*5))

    for i, (key, check) in enumerate(check_dict.items()):
        colors=[]
        split_edge = check['split_edge']
        regions = list(trgl_regions.values())
        for region in regions:
            # check if any pt is within readius
            colors.append(region.split_with_circle(split_edge, check))

        if not plot_offset_checks is None:
            ax = axs.flat[i]
            OffsetRegion.plot_many(regions=regions, ax=ax, color=colors, alpha=0.8, plot_edges=False)
            # OffsetRegion.plot_many(regions=list(trgl_regions.values()), ax=ax, color=colors, alpha=0.8, plot_edges=False)
            if split_edge.type != 'LineSegment':
                x,y = [float(c) for c in key]
                split_edge = check['split_edge']
                GeoSeries([Point((x,y)).buffer(r,30)]).plot(ax=ax, color='None', edgecolor='blue')
                ax.set_title(str((x,y))+ "center.")
            else:
                GeoSeries([LineString([split_edge.vtx1.xy, split_edge.vtx2.xy])]).plot(ax=ax, color='None', edgecolor='red')
    

    
    # Check if all checks are performaned on each, else throw error 
    n_checks = [len(region.checks) for region in list(trgl_regions.values())]
    if not n_checks.count(n_checks[0]) == len(n_checks):
        raise ValueError("The number of checks performed differ among micro regions. They are expected to be all of the same Length.", n_checks)
    #
#

def check_nested_subcells(
        r:float, 
        vtx_overlapped:dict,
        vtx_contained:dict,
        region,
        q_anchor_row=0,
        q_anchor_col=0,
        lvl:int=1,
        nest_depth:int=0,
        include_boundary:bool=False,
    ):
    """
    function that recursivey splits cell into quadrants until max nest_depth is reached or the cell/subquadrant is fully contained or not overlapped.
    """
    # for lvl in range(1, nest_depth+1):
    # split into 4 quadrants
    
    # QUADRANT 0 (bottom left)
    # QUADRANT 1 (bottom right)
    # QUADRANT 2 (top left)
    # QUADRANT 3 (top right)
    
    # lvl 1: 0.0 - 0.5     - 1.0    = 2**-1
    # lvl 2: 0.0 - 0.25    - 0.5    = 2**-2
    # lvl 3: 0.0 - 0.125   - 0.25   = 2**-3
    # lvl 4: 0.0 - 0.0625  - 0.125  = 2**-4
    # lvl 5: 0.0 - 0.03125 - 0.0625 = 2**-5

    q_vertices = [
        ( q_anchor_row,              q_anchor_col              ), #0 (  0%,   0%)
        ( q_anchor_row,              q_anchor_col + 2**(-lvl)  ), #1 (  0%,  50%)
        ( q_anchor_row + 2**(-lvl),  q_anchor_col              ), #2 ( 50%,   0%)
        ( q_anchor_row + 2**(-lvl),  q_anchor_col + 2**(-lvl)  ), #3 ( 50%,  50%)
        ( q_anchor_row,              q_anchor_col + 2**(1-lvl) ), #4 (  0%, 100%)
        ( q_anchor_row + 2**(1-lvl), q_anchor_col              ), #5 (100%,   0%)
        ( q_anchor_row + 2**(-lvl),  q_anchor_col + 2**(1-lvl) ), #6 ( 50%, 100%)
        ( q_anchor_row + 2**(1-lvl), q_anchor_col + 1/(2*lvl)  ), #7 (100%,  50%)
        ( q_anchor_row + 2**(1-lvl), q_anchor_col + 1/(lvl)    ), #8 (100%, 100%)
    ]
    
    q0 = [0,1,2,3]
    q1 = [1,3,4,6]
    q2 = [2,3,5,7]
    q3 = [3,6,7,8]
    
    for q_vtx in q_vertices:
        if q_vtx not in vtx_contained:
            max_dist_to_vtx = 0
            # loop over edges until an edge is found with a max distance greate than r. 
            for edge in region.edges:
                if edge.calc_max_dist_to_pt(q_vtx) > r:
                    # update max dist with arbitrary value > r.
                    max_dist_to_vtx = r+1
                    break 
            if max_dist_to_vtx <= r:
                vtx_contained[q_vtx] = True
                vtx_overlapped[q_vtx] = True
            else:
                vtx_contained[q_vtx] = False
        if q_vtx not in vtx_overlapped:
            min_dist_to_vtx = region.calc_min_dist_to_pt(q_vtx)
            vtx_overlapped[q_vtx] = min_dist_to_vtx < r if not include_boundary else min_dist_to_vtx <= r 
    
    for q,(a_r,a_c) in zip(
        [  q0,        q1,              q2,               q3           ],
        [(0,0), (0, 1/(2*lvl)), (1/(2*lvl), 0), (1/(2*lvl), 1/(2*lvl))]
    ):
        # print("a_r,a_c",a_r,a_c)
        if all([vtx_contained[q_vertices[i]] for i in q]):
            # print("--"*lvl, "contained", (q_anchor_row+a_r,q_anchor_col+a_c))
            region.contained_cells.append((lvl,(q_anchor_row+a_r,q_anchor_col+a_c)))
        elif any([vtx_overlapped[q_vertices[i]] for i in q]):
            if lvl < nest_depth:
                # print("--"*(lvl+1))
                # nest deeper if cell is overlapped
                check_nested_subcells(
                    r=r,
                    vtx_overlapped=vtx_overlapped,
                    vtx_contained=vtx_contained,
                    region=region,
                    q_anchor_row=q_anchor_row+a_r,
                    q_anchor_col=q_anchor_col+a_c,
                    lvl=lvl+1,
                    nest_depth=nest_depth,
                    include_boundary=include_boundary,
                )
            else:
                # print("--"*lvl, "overlapped", (q_anchor_row+a_r,q_anchor_col+a_c))
                region.overlapped_cells.append((lvl,(q_anchor_row+a_r,q_anchor_col+a_c)))
        # else: print("--"*lvl, "not touched", (q_anchor_row+a_r,q_anchor_col+a_c))
        # else if subcell quadrant neither contained nor overlapped, discard it
    # 
#     

def cleanup_region_check_results(
        trgl_regions:dict, 
        cells_contained_in_all_trgl_disks:_np_array,
        cells_always_overlapped:list,
        all_cells:_np_array,
        grid_spacing:float,
        r:float, 
        include_boundary:bool=False,
        nest_depth:int=0,
        plot_offset_regions:dict=None):
    """
    
    """
    cells_contained_in_all_trgl_disks = [(0,(int(x),int(y))) for x,y in cells_contained_in_all_trgl_disks]
    cells_always_overlapped = [(0,(int(x),int(y))) for x,y in cells_always_overlapped]
    # print("N always overlapped",len(cells_always_overlapped))
    # now all checks are added to regions
    # ensure that each region.checks has the same length!
    if not plot_offset_regions is None:
        fig, axs = plt.subplots(nrows=len(trgl_regions), ncols=2, figsize=(8, 4*len(trgl_regions)))
    n_regs, n_edges = 0,0
    for n, region in enumerate(list(trgl_regions.values())):
        n_regs+=1
        n_edges+=len(region.edges)
        region.contained_cells = []
        region.overlapped_cells = []
        for check in region.checks:
            if not check['result'] == True:
                continue
            if 'contains' in check:
                region.contained_cells.append((0,tuple([int(v) for v in check['contains']])))
            if 'overlaps' in check:
                region.overlapped_cells.append((0,tuple([int(v) for v in check['overlaps']])))
            #
        #
        # add all cells contained in cell for triangle 1 (not including cells that are contained for any pt inside cell)
        region.contained_cells = sorted(set(
            [lvl_xy for lvl_xy in cells_contained_in_all_trgl_disks] + 
            [lvl_xy for lvl_xy in region.contained_cells]
        ))

        # add all cells that are always at least overlapped and not contained in this one
        region.overlapped_cells = sorted(set(
            [lvl_xy for lvl_xy in cells_always_overlapped if not ( lvl_xy in region.contained_cells )] + 
            [lvl_xy for lvl_xy in region.overlapped_cells]
        ))

        # print("+++++++N overlapped region:",len(region.overlapped_cells),"++++++++"*5)
        
        if nest_depth > 0:
            overlapped_cells_unsplitted =  region.overlapped_cells
            region.overlapped_cells = []
            for lvl,(row,col) in overlapped_cells_unsplitted:
                # how shall the subcell be referenced? 
                # By its center? By its bottom left corner? By its closest corner? By its row/col indices at the level?
                # cell (0, 1) -> lvl:1 ((2,-1),(2, 1),(3,-1),(3, 1),)
                # ymin=.5,ymax=1.5,xmin=-.5,xmax=.5                      
                # cell (1, 1) -> lvl:1 ((2, 2),(2, 3),(3, 2),(3, 3),)
                # cell (1,-1) -> lvl:1 ((2,-2),(2,-3),(3,-2),(3,-3),)
                check_nested_subcells(
                    r=r,
                    vtx_overlapped={},
                    vtx_contained={},
                    region=region,
                    q_anchor_row=float(row)-0.5,
                    q_anchor_col=float(col)-0.5,
                    lvl=1,#lvl+1?
                    nest_depth=nest_depth,
                    include_boundary=include_boundary,
                )
        # print("region.contained_cells",region.contained_cells)
        # print("sorted region.contained_cells",sorted(region.contained_cells))
        # print("set region.contained_cells",set(region.contained_cells))
        # print("region.overlapped_cells",region.overlapped_cells)
        # print("sorted region.overlapped_cells",sorted(region.overlapped_cells))
        # print("set region.overlapped_cells",set(region.overlapped_cells))
        region.contained_cells = tuple(sorted(region.contained_cells))
        region.overlapped_cells = tuple(sorted(region.overlapped_cells))
        
        # TODO bundle cells to cell patches
        region.shared_along_vert = any([edge.vtx1.y==0 and edge.vtx2.y==0  for edge in region.edges])
        region.shared_along_diag = any([edge.vtx1.x==edge.vtx1.y and edge.vtx2.x==edge.vtx2.y for edge in region.edges])

        if not plot_offset_regions is None:
            region.plot_many(regions=list(trgl_regions.values()), ax=axs.flat[n*2], alpha=0.1, add_idxs=False)
            region.plot_single(ax=axs.flat[n*2], alpha=1, add_idx_edges=False)
            region.plot_single(ax=axs.flat[n*2+1], alpha=1, plot_edges=False, add_idx_edges=False)
            # TODO plot needs to be adjusted for subcell quadrants
            plot_cell_pattern(
                contained_cells=[row_col for _lvl, row_col in region.contained_cells],
                overlapped_cells=[row_col for _lvl, row_col in region.overlapped_cells],
                region_coords=[edge_coords[0] for edge_coords in region.coords],
                all_cells=all_cells,
                ax=axs.flat[n*2 + 1],
                r=r,
                grid_spacing=grid_spacing,
            )
        #
    #
    # print("n_regs, n_edges", n_regs, n_edges)
    #


def transform_region_to_remaining_triangles(trgl_regions):
    regions = list(trgl_regions.values())
    unique_contained_cells = dict()
    unique_overlapped_cells = dict()
    translate_trgl_reg_nr_to_reg_nr = dict()
    # create new regions for rotation if not similar
    condensed_regions = []
    all_regions = []
    
    for nr, region in enumerate(regions):
        region.nr = nr*10+1
        new_regions = []
        for i in [1,2,3,4,5,6,7,8]:
                # create new region!
                rotated_region = region.transform_to_trgl(i)
                rotated_region.nr = nr*10+i
                new_regions.append(rotated_region)
        
        all_regions.extend(new_regions)
        
        if region.shared_along_vert and region.shared_along_diag:
            condensed_regions.append(OffsetRegion.merge_regions(new_regions))
            translate_trgl_reg_nr_to_reg_nr.update({nr*10+j: nr*10+1 for j in [1,2,3,4,5,6,7,8]})
            pass
        elif region.shared_along_vert:
            condensed_regions.append(OffsetRegion.merge_regions([new_regions[-1], new_regions[0]]))
            condensed_regions.append(OffsetRegion.merge_regions(new_regions[1:3]))
            condensed_regions.append(OffsetRegion.merge_regions(new_regions[3:5]))
            condensed_regions.append(OffsetRegion.merge_regions(new_regions[5:7]))
            translate_trgl_reg_nr_to_reg_nr.update({
                nr*10+8: nr*10+1, nr*10+1: nr*10+1,
                nr*10+2: nr*10+3, nr*10+3: nr*10+3,
                nr*10+4: nr*10+5, nr*10+5: nr*10+5,
                nr*10+6: nr*10+7, nr*10+7: nr*10+7,
                })
            pass
        elif region.shared_along_diag:
            condensed_regions.append(OffsetRegion.merge_regions(new_regions[0:2]))
            condensed_regions.append(OffsetRegion.merge_regions(new_regions[2:4]))
            condensed_regions.append(OffsetRegion.merge_regions(new_regions[4:6]))
            condensed_regions.append(OffsetRegion.merge_regions(new_regions[6:8]))
            translate_trgl_reg_nr_to_reg_nr.update({
                nr*10+1: nr*10+1, nr*10+2: nr*10+1,
                nr*10+3: nr*10+3, nr*10+4: nr*10+3,
                nr*10+5: nr*10+5, nr*10+6: nr*10+5,
                nr*10+7: nr*10+7, nr*10+8: nr*10+7,
                })
            pass
        else:
            condensed_regions.extend(new_regions)
            translate_trgl_reg_nr_to_reg_nr.update({nr*10+j: nr*10+j for j in [1,2,3,4,5,6,7,8]})

    all_regions = condensed_regions
    trgl_reg_nr_to_id = dict() 
    all_regions.sort(key=lambda reg: (reg.trgl_nr))
    
    for region in all_regions:
        # TODO adjust this to also work with subcell quadrants
        if not region.contained_cells in unique_contained_cells:
            unique_contained_cells[region.contained_cells] = len(unique_contained_cells)
        if not region.overlapped_cells in unique_overlapped_cells:
            unique_overlapped_cells[region.overlapped_cells] = len(unique_overlapped_cells)
    
    contain_region_mult = 10**(int(_math_log10(len(unique_overlapped_cells)))+1)
    id_to_offset_regions = dict()
    
    for region in all_regions:
        # TODO adjust this to also work with subcell quadrants
        region.id = unique_contained_cells[region.contained_cells] * contain_region_mult + unique_overlapped_cells[region.overlapped_cells]
        
        if not region.id in id_to_offset_regions:
            id_to_offset_regions[region.id] = region
        
        for i in range(0, 8 + 1 - region.trgl_nr):
            trgl_reg_nr_to_id[region.nr + i] = region.id
    
    translate_reg_nr_to_reg_id = {k: trgl_reg_nr_to_id[v] for k,v in translate_trgl_reg_nr_to_reg_nr.items()}

    return id_to_offset_regions, translate_reg_nr_to_reg_id, contain_region_mult
    
#

# TODO ensure that row,col x,y is not mixed up

def assign_pts_to_offset_region(
        pts,
        potential_regions,
):
    [[pt for reg in potential_regions] for pt in pts]
    pass


def create_raster_plot(
        regions:list,
        raster_cell_to_regions:dict,
        offset_x_bins,
        offset_y_bins,
        lims=[-0.05, 0.55],
        add_raster_labels:bool=True
        
        ):
        fig, axs = plt.subplots(1,3,figsize=(50,30))

        gdf = GeoDataFrame(geometry=[Polygon([(_np_sign(ix)*x, _np_sign(iy)*y) for x,y in [
            (offset_x_bins[abs(ix)-1][0], offset_y_bins[abs(iy)-1][0]), (offset_x_bins[abs(ix)-1][1], offset_y_bins[abs(iy)-1][0]),
            (offset_x_bins[abs(ix)-1][1], offset_y_bins[abs(iy)-1][1]), (offset_x_bins[abs(ix)-1][0], offset_y_bins[abs(iy)-1][1])]]
        ) for (ix, iy) in raster_cell_to_regions])
        lens = [len(v) for v in raster_cell_to_regions.values()]
        gdf['rel'] = [(l/(max(lens)), l/(max(lens))/2,1- l/(max(lens))) for l in lens]
        gdf.plot(ax=axs.flat[0],  color=gdf['rel'], edgecolor='None', alpha=0.7, legend=True, linewidth=0.15)
        
        gdf.plot(ax=axs.flat[1],  color=gdf['rel'], edgecolor='None', alpha=0.7, legend=True, linewidth=0.15)
        region_comb_dict = dict()
        for l, region_comb in sorted([(len(v), tuple([r.id for r in v])) for v in raster_cell_to_regions.values()]):
            if not region_comb in region_comb_dict:
                region_comb_dict[region_comb] = len(region_comb_dict)
        region_comb_nrs = [region_comb_dict[tuple([r.id for r in v])] for v in raster_cell_to_regions.values()]
        gdf.plot(ax=axs.flat[2],  column=_np_array(region_comb_nrs), cmap='viridis', edgecolor='None', alpha=0.7, linewidth=0.15)
        
        if add_raster_labels:
            for (ix,iy), v in raster_cell_to_regions.items():
                (x_low, x_up), (y_low, y_up) = [_np_sign(ix)*x for x in offset_x_bins[abs(ix)-1]], [_np_sign(iy)*y for y in offset_y_bins[abs(iy)-1]]
                # axs.flat[1].annotate(text=".".join([str(v0) for v0 in v]), xy=((x_low+x_up)/2, (y_low+y_up)/2), horizontalalignment='center', fontsize=5)
                # axs.flat[2].annotate(text=".".join([str(v0) for v0 in v]), xy=((x_low+x_up)/2, (y_low+y_up)/2), horizontalalignment='center', fontsize=5)
                axs.flat[1].annotate(text=str(len(v)), xy=((x_low+x_up)/2, (y_low+y_up)/2), horizontalalignment='center', fontsize=8)
                axs.flat[2].annotate(text=str(region_comb_dict[tuple([r.id for r in v])]), xy=((x_low+x_up)/2, (y_low+y_up)/2), horizontalalignment='center', fontsize=8)
        else:
            for (ix,iy), v in raster_cell_to_regions.items():
                (x_low, x_up), (y_low, y_up) = [_np_sign(ix)*x for x in offset_x_bins[abs(ix)-1]], [_np_sign(iy)*y for y in offset_y_bins[abs(iy)-1]]
                text = str(len(v))#str(ix)#+"."+str(iy)
                # text = "+"
                axs.flat[1].annotate(text=text, xy=((x_low+x_up)/2, (y_low+y_up)/2), horizontalalignment='center', fontsize=7)
        
        OffsetRegion.plot_many(regions=regions, plot_edges=False, edgecolor='black', ax=axs.flat[0], facecolor='None', alpha=0.8, linewidth=0.4)
        OffsetRegion.plot_many(regions=regions, plot_edges=False, edgecolor='black', ax=axs.flat[1], facecolor='None', alpha=0.8, linewidth=0.4, add_idxs=False)
        OffsetRegion.plot_many(regions=regions, plot_edges=False, edgecolor='black', ax=axs.flat[2], facecolor='None', alpha=0.8, linewidth=0.4, add_idxs=False)
        for ax in axs.flat:
            ax.set_xlim(lims)
            ax.set_ylim(lims)
        axs.flat[-1].legend((i for i in sorted(set(lens))),loc='upper right')# To-Do legend not added


def sort_trgl_region_into_raster(
    trgl_regions:dict,
    plot_offset_raster:dict=None,
):
    """
    TODO CLEAN UP
    
    """
    # assign each cell to a region
    # start with triangle only
    regions_to_check = [reg for reg in trgl_regions.values() if reg.trgl_nr in [1,2]]
    regions_to_check.sort(key=lambda reg: (reg.xmin, reg.xmax, reg.ymin, reg.ymax))
    
    vertices = []
    for region in regions_to_check:
        if region.xmin >= region.xmax:
            print("xmin>=xmax", region.coords)
        vertices.extend(region.vertices)
    
    if False:
        unique_x_vals = sorted(set([vtx.x for vtx in vertices if vtx.x >= 0]))
        unique_y_vals = sorted(set([vtx.y for vtx in vertices if vtx.y >= 0]))
        make_bins_from_vals, get_vals_from_bins
        offset_x_bins = make_bins_from_vals(unique_x_vals) 
        offset_y_bins = make_bins_from_vals(unique_y_vals) 
    else:
        unique_x_or_y_vals = sorted(set([vtx.x for vtx in vertices if vtx.x >= 0] + [vtx.y for vtx in vertices if vtx.y >= 0]))
        offset_x_bins = make_bins_from_vals(unique_x_or_y_vals)
        offset_y_bins = make_bins_from_vals(unique_x_or_y_vals)
        
    
    # remember regions are not always convex - but maybe i guess they will be once splitted along lines
    raster_cell_to_regions = dict()
    unique_reg_id_combs_to_raster_cells = dict()
    i, j = 0, 0
    regions_to_check_at_x = regions_to_check
    for ix, (x_low, x_up) in zip(range(1, len(offset_x_bins)+1), offset_x_bins):
        
        # look for leftmost region that overlaps x_low  
        i = next((ix for ix, reg in enumerate(regions_to_check_at_x) if reg.xmax > x_low),-1)
        regions_to_check_at_x = regions_to_check_at_x[i:]
        
        if len(regions_to_check_at_x)==0:
            print("Break, no regions to check", x_low, x_up )
            break
        if j != -1:
            j = next((jx for jx, reg in enumerate(regions_to_check_at_x) if reg.xmin >= x_up),-1)
        else:
            print("-------------- j != -1 --------------",regions_to_check_at_x, x_low, x_up)

        regions_to_check_at_xy = regions_to_check_at_x[:j]
        for iy, (y_low, y_up) in zip(range(1, len(offset_y_bins)+1), offset_y_bins):
            if y_low >= x_up: 
                break
            # look for downmost region that overlaps y_low  
            n = len(regions_to_check_at_xy)
            regions_to_check_at_xy = [reg for reg in regions_to_check_at_xy if reg.ymax > y_low]
            
            # TODO leverage this performance gain later on. 
            # # extract all regions that within raster_cell
            # def check_if_raster_cell_overlaps_region(reg:OffsetRegion,x_low:float, y_low:float, x_up:float, y_up:float):
            #     raster_vertices = ((x_low, y_low), (x_up, y_low), (x_up, y_up), (x_low, y_up))
            #     for (x,y) in list(reg.get_coords()):
            #         for vx,vy in raster_vertices:
            #             if (vx)
            #     return False
            regions_at_raster_cell = []
            # region_nrs_at_raster_cell = set()
            region_ids_at_raster_cell = set()
            for reg in regions_to_check_at_xy:
                if reg.ymin < y_up and not reg.id in region_ids_at_raster_cell:
                    # region_nrs_at_raster_cell.add(reg.nr)
                    region_ids_at_raster_cell.add(reg.id)
                    regions_at_raster_cell.append(reg)

            # region_nrs_at_raster_cell = tuple(sorted(region_nrs_at_raster_cell))
            # if len(region_nrs_at_raster_cell)==0:
            #     print("(x_low, x_up)", (x_low, x_up), "(y_low, y_up)", (y_low, y_up), 'N', n, 'n', len(regions_to_check_at_xy), 'Nx', len(regions_to_check_at_x))
            
            region_ids_at_raster_cell = tuple(sorted(region_ids_at_raster_cell))
            
            if not region_ids_at_raster_cell in unique_reg_id_combs_to_raster_cells:
                unique_reg_id_combs_to_raster_cells[region_ids_at_raster_cell] = []
            
            unique_reg_id_combs_to_raster_cells[region_ids_at_raster_cell].append((ix,iy))
            raster_cell_to_regions[(ix, iy)] = regions_at_raster_cell
        #
    #

    # print("n cells in triangle:", len(raster_cell_to_regions))
    # print("mean regions at raster cell", sum([len(x) for x in raster_cell_to_regions.values()])/len(raster_cell_to_regions))
    # print("unique_reg_id_combs_to_raster_cells", unique_reg_id_combs_to_raster_cells)
    if not plot_offset_raster is None:
        create_raster_plot(regions=list(trgl_regions.values()), raster_cell_to_regions=raster_cell_to_regions, offset_x_bins=offset_x_bins, offset_y_bins=offset_y_bins)
    
    return raster_cell_to_regions, offset_x_bins, offset_y_bins, unique_reg_id_combs_to_raster_cells
#

def create_radius_check(edge, r:float, include_boundary:bool):
    """
    returns lambda function
    - that checks for an array of point coordinates whether they are within radius r (<= if include_boundary)
    - returns a boolean array (of length n where n is number of points)
    """
    (x,y) = edge.center
    if include_boundary:
        return lambda pts: _np_linalg_norm(pts - (x,y), axis=1) <= r
    return lambda pts: _np_linalg_norm(pts - (x,y), axis=1) < r
#

def create_line_check(edge, r:float, include_boundary:bool):
    """
    returns lambda function
    - that checks for an array of point coordinates whether they at a distance smaller than r to a horizontal or vertical line (<= if include_boundary)
    - returns a boolean array (of length n where n is number of points)
    """
    col_index = int(edge.vtx1.y == edge.vtx2.y)
    val = edge.vtx1.xy[col_index]
    if include_boundary:
        return lambda pts: abs(pts[:,col_index] - val) <= r
    return lambda pts: abs(pts[:,col_index] - val) < r

#

def create_pt_checks(edge, r:float, include_boundary:bool=False):
    """
    returns lambda function
    - that returns a boolean array (of length n where n is number of points) whether pts are within distance <= r. 
    """
    if edge.type == 'Arc':
        return create_radius_check(edge, r, include_boundary)
    return create_line_check(edge, r, include_boundary)
#

def edge_is_shared_with_region_id(
        reversed_edge_coords,
        remaining_regions,
):
    for reg in remaining_regions:
        for e in reg.edges:
            if reversed_edge_coords == e.coords:
                return reg.id
    return None
#

def edge_is_shared_with_region_id2(
        edge,
        remaining_regions,
):
    """
    First checks whether the edge is a 'contains' or 'overlaps' check
    Then loops through remaining regions looking through the region edges for an edge that 
    has the same 'contains' or 'overaps' attribute and then checks whether this attribute is 
    the same as from the edge. If its the same return the region id where the edge was in  
    """
    attr_to_check = 'contains' if hasattr(edge, 'contains') else 'overlaps'
    if not hasattr(edge, attr_to_check):
        return None

    for reg in remaining_regions:
        for e in reg.edges:
            if hasattr(e, attr_to_check) and getattr(edge, attr_to_check) == getattr(e, attr_to_check):
                return reg.id
    return None
#

def edge_is_shared_with_region_id3(
        edge,
        remaining_regions,
):
    """
    First checks whether the edge is a 'contains' or 'overlaps' check
    Then loops through remaining regions looking through the region edges for an edge that 
    has the same 'contains' or 'overaps' attribute and then checks whether this attribute is 
    the same as from the edge. If its the same return the region id where the edge was in  
    """
    attr_to_check = 'contains' if hasattr(edge, 'contains') else 'overlaps'
    if not hasattr(edge, attr_to_check):
        return []

    reg_ids = []
    for reg in remaining_regions:
        for e in reg.edges:
            if hasattr(e, attr_to_check) and getattr(edge, attr_to_check) == getattr(e, attr_to_check):
                reg_ids.append(reg.id)
    return list(set(reg_ids))
#

def vertex_is_shared_with_region(
        remaining_regions,
):
    """
    to-do this only returns the first edge that shares a vertex and the region that contains in. THink about what happens if there are more than 2 regions.
    """
    
    # finds a vertex that a pair of edges among two (?Does this work for three and more?!) regions share 
    edges_current_region = remaining_regions[0].edges
    for edge in edges_current_region:
        for reg in remaining_regions:
            for e in reg.edges:
                if any([coord in edge.coords for coord in e.coords]):
                    return (edge, reg.id)
                
        return None
#

# create (potentially recursive checks:)
def add_check_to_tree_at_pos(
        tree_pos,
        checks,
        remaining_regions
):
    """
    
    
    
    """
    # print("checks",checks)
    edge, check = checks[0]
    tree_pos['check'] = check
    if len(remaining_regions)<=1:
        raise ValueError("remaining_regions", len(remaining_regions), len(checks))
    # TODO check if this also works with subcell quadrants
    # print("edge.contains",edge.contains,"edge.overlaps",edge.overlaps)
    # print("regs contains", [{reg.id: reg.contained_cells} for reg in remaining_regions])
    # print("regs overlaps", [{reg.id: reg.overlapped_cells} for reg in remaining_regions])
    
    regions_if_true = [
        reg for reg in remaining_regions if (
            not hasattr(edge, 'contains') or (0,edge.contains) in reg.contained_cells
        ) and (
            not hasattr(edge, 'overlaps') or (0,edge.overlaps) in reg.overlapped_cells
        )]

    ids_if_true = [reg.id for reg in regions_if_true]
    regions_if_false = [reg for reg in remaining_regions if reg.id not in ids_if_true]
    # print("reg true:",len(regions_if_true),"reg false:",len(regions_if_false))
    # print("regs true:",[reg.id for reg in regions_if_true],"regs false:",[reg.id for reg in regions_if_false])
    if False and len(remaining_regions)>1 and (
        len(regions_if_true) * len(regions_if_false) > 0
    ) and (
        int(1001 in [reg.id for reg in remaining_regions]) + 
        int(19026 in [reg.id for reg in remaining_regions]) +
        int(9010 in [reg.id for reg in remaining_regions]) >= 2):
        fig, ax = plt.subplots(1,1,figsize=(6,6))
        for reg in regions_if_false:
            reg.plot_single(ax=ax, plot_edges=False, color='#ccc', hatch="//")
        for reg in regions_if_true:
            reg.plot_single(ax=ax, plot_edges=False, color='#ccc', hatch="o")
        OffsetRegion.plot_many(
            regions=remaining_regions, plot_vertices=False, #x_lim=(-.52,.52), y_lim=(-.52,.52),
            title='reg true: '+str(len(regions_if_true))+"reg false: "+str(len(regions_if_false)),
            ax=ax)
        edge.plot_single(ax=ax)
    
    if len(regions_if_true) == 0:
        pass
    elif len(regions_if_true) == 1:
        id_if_true = regions_if_true[0].id
        tree_pos[True] = id_if_true
    else:
        if len(regions_if_false) > 0:
            tree_pos[True] = {}
            add_check_to_tree_at_pos(tree_pos[True], checks[1:], regions_if_true)
        else:
            add_check_to_tree_at_pos(tree_pos, checks[1:], regions_if_true)

    if len(regions_if_false) == 0:
        pass
    elif len(regions_if_false)==1:
        id_if_false = regions_if_false[0].id
        tree_pos[False] = id_if_false
    else:
        if len(regions_if_true) > 0:
            tree_pos[False] = {}
            add_check_to_tree_at_pos(tree_pos[False], checks[1:], regions_if_false)
        else:
            add_check_to_tree_at_pos(tree_pos, checks[1:], regions_if_false)

    if len(regions_if_true)+len(regions_if_false) == 0:
        raise ValueError('remaining_regions', remaining_regions, 'checks', checks)
#

def determine_offset_region_for_pts_inner(
        pts:_np_array,
        check_tree
    ):

    if type(check_tree) != dict:
        return _np_zeros(len(pts), int) + check_tree
    res = _np_zeros(len(pts), int)
    check_res = check_tree['check'](pts)
    res[_np_arange(len(pts))[check_res]] = determine_offset_region_for_pts_inner(pts=pts[_np_arange(len(pts))[check_res]], check_tree=check_tree[True])
    res[_np_arange(len(pts))[_np_invert(check_res)]] = determine_offset_region_for_pts_inner(pts=pts[_np_arange(len(pts))[_np_invert(check_res)]], check_tree=check_tree[False])
    
    return res
#

def prepare_raster_to_offset_region_checks(
        id_to_offset_regions:dict,
        unique_reg_id_combs_to_raster_cells:dict,
        r:float, 
        include_boundary:bool,
    ) -> dict:
    """
    Creates a dict that maps each offeset region combination to a check tree that resolves in which of the offset regions a point falls
    
    """
    offset_reg_id_comb_to_check = dict()
    # print("unique_reg_id_combs_to_raster_cells",unique_reg_id_combs_to_raster_cells)
    # print("len(unique_reg_id_combs_to_raster_cells)",len(unique_reg_id_combs_to_raster_cells))
    for region_comb in unique_reg_id_combs_to_raster_cells:
        # print("region_comb",region_comb)
        regions = [id_to_offset_regions[id] for id in sorted(set(region_comb))]
        # print("regions",regions)

        if len(regions)==0:
            raise ValueError("PP", region_comb)
        if len(region_comb) == 1:
            region_id = regions[0].id
            offset_reg_id_comb_to_check[region_comb] = lambda pts, region_id=region_id: _np_zeros(len(pts),int)+region_id
            continue
        
        check_tree = dict()
        check_edges_for_regions = []
        # To-Do: Does this method of picking any shared edge work reliably for raster cells where one needs to distinguish between multiple (n>2) regions?
        
        for i, region in enumerate(regions[:-1]):
            for edge in region.edges:
                # reversed_coords = (edge.coords[1], edge.coords[0])
                # shared_with_reg_id = edge_is_shared_with_region_id(reversed_coords, regions[i+1:])
                shared_with_reg_id = edge_is_shared_with_region_id2(edge, regions[i+1:])
                shared_with_reg_ids = edge_is_shared_with_region_id3(edge, regions[i+1:])
                if not shared_with_reg_id is None:
                    edge_check = create_pt_checks(edge, r=r, include_boundary=include_boundary)
                    check_edges_for_regions.append((edge, edge_check))
                    
                if len(shared_with_reg_ids) > 0:
                    edge_check = create_pt_checks(edge, r=r, include_boundary=include_boundary)
                    check_edges_for_regions.append((edge, edge_check))
                
                #maybe the following steps needs to be applied always (that if theres not shared edge a shared vertex needs to be found)
        if len(check_edges_for_regions)==0:
            print("FOUND ZERO")
            if len(regions) > 2:
                print("WARNING ENSURE IF THIS METHOD IS RELIABLE WITH MORE THAN 2 REGIONS. n=",len(regions))
            # regions dont share an edge but they might share a vertex. thus an edge needs to be chosen (arbitrarily) 
            (edge_at_vertex, reg_at_vertex) = vertex_is_shared_with_region(regions[i:])
            edge_check = create_pt_checks(edge_at_vertex, r=r, include_boundary=include_boundary)
            check_edges_for_regions.append((edge_at_vertex, edge_check))
        #print("check_edges_for_regions",check_edges_for_regions)
        try:
            add_check_to_tree_at_pos(tree_pos=check_tree, checks=check_edges_for_regions, remaining_regions=regions)
            # OffsetRegion.plot_many(regions=regions, plot_vertices=False, x_lim=(-.52,.52), y_lim=(-.52,.52))
            pass
        except:
            print("S2")

            # OffsetRegion.plot_many(regions=regions, plot_vertices=False, x_lim=(-.52,.52), y_lim=(-.52,.52))
            ax = OffsetRegion.plot_many(regions=regions, plot_vertices=False, x_lim=(-.52,.52), y_lim=(-.52,.52))
            Edge.plot_many(edges={e.coords:e for e,c in check_edges_for_regions}, ax=ax)
        
            raise ValueError("trgl_nrs", [(reg.trgl_nr, reg.id, reg.trgl_nrs if hasattr(reg, 'trgl_nrs') else None) for reg in regions],"n regions", len(regions), "check edges", len(check_edges_for_regions), "checktree", check_tree)
        
        # def determine_offset_region_for_pts(
        #     pts: _np_array   
        # ): 
            
        #     return determine_offset_region_for_pts_inner(pts=pts, check_tree=check_tree)
        # offset_reg_id_comb_to_check[region_comb] = determine_offset_region_for_pts
        # if type(check_tree) != dict:
        #     raise ValueError("NOT A DICT")
        offset_reg_id_comb_to_check[region_comb] = lambda pts, check_tree=check_tree: determine_offset_region_for_pts_inner(pts=pts, check_tree=check_tree)
        if region_comb == (1001,9010,19026):
            # print("region_comb",region_comb)
            # print("check_tree:", check_tree)
            def repr_check_tree(check_tree, ct_r={}):
                if 'check' in check_tree.keys():
                    ct_r['check'] = inspect.getsource(check_tree['check'])
                if True in check_tree.keys():
                    ct_r[True] = check_tree[True] if type(check_tree[True])==int else repr_check_tree(check_tree[True])
                if False in check_tree.keys():
                    ct_r[False] = check_tree[False] if type(check_tree[False])==int else repr_check_tree(check_tree[False])
                return ct_r
            # print("repr_check_tree(check_tree)", repr_check_tree(check_tree))
            # print("lambda:",offset_reg_id_comb_to_check[region_comb])
    # print(offset_reg_id_comb_to_check.keys())
    # print("offset_reg_id_comb_to_check[(1001,9010,19026)]",offset_reg_id_comb_to_check[(1001,9010,19026)])
    # print("offset_reg_id_comb_to_check[(10,7)]",offset_reg_id_comb_to_check[(10,7)])
    return offset_reg_id_comb_to_check 
#

def increase_raster_to_offset_region_precision(
        raster_cell_to_regions,
        offset_reg_id_comb_to_check,
        offset_x_bins:list,
        offset_y_bins:list,
        id_to_offset_regions:dict=None,
        plot_offset_raster:bool=False,
):
    """
    Some can not be simplified: that is if one of the 4 corners of raster cell is a region vertex. hm not sure.
    """
    precise_raster = dict()

    offset_x_bins = offset_x_bins
    offset_y_bins = offset_y_bins
    lenchanges = set()
    all_precise_ids = set()
    for (ix, iy), regions_at_raster_cell in raster_cell_to_regions.items():
        if len(regions_at_raster_cell)>1:
            xmin, xmax = offset_x_bins[ix-1]
            ymin, ymax = offset_y_bins[iy-1]
            reg_ids = tuple(sorted([reg.id for reg in regions_at_raster_cell]))
            check = offset_reg_id_comb_to_check[reg_ids]
            pts = _np_array([(xmin,ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)])
            check_res = check(pts=pts)
            precise_ids = set(check_res)
            all_precise_ids.add(tuple(sorted(precise_ids)))
            preceise_regions_at_raster = [reg for reg in regions_at_raster_cell if reg.id in precise_ids]
            lenchanges.add((len(reg_ids), len(preceise_regions_at_raster)))
            if len(preceise_regions_at_raster) == 0:
                OffsetRegion.plot_many([reg for reg in regions_at_raster_cell]+[id_to_offset_regions[id] for id in precise_ids], plot_vertices=False)
                raise ValueError("regions_at_raster_cell", len(regions_at_raster_cell), [reg.id for reg in regions_at_raster_cell], "checkres", check_res, "precise_ids", precise_ids)

            precise_raster[(ix, iy)] = preceise_regions_at_raster
        else:
            precise_raster[(ix, iy)] = regions_at_raster_cell

    if not plot_offset_raster is None:
        create_raster_plot(regions=list(id_to_offset_regions.values()), raster_cell_to_regions=precise_raster, offset_x_bins=offset_x_bins, offset_y_bins=offset_y_bins)
    
    return precise_raster
#

def transform_raster_to_remaining_triangle(
        id_to_offset_regions:dict, 
        raster_cell_to_regions:dict,
        offset_x_bins:list,
        offset_y_bins:list,
        translate_reg_nr_to_reg_id:dict,
        plot_offset_raster:dict=None
    ):
    
    raster_cell_id_to_bounds = dict()
    unique_reg_id_combs_to_raster_cells = dict()
    
    for sign_x in [-1, 1]:
        for sign_y in [-1, 1]:
            # sorting 1 if abs(x)>abs(y) else -1
            for sorting in [1, -1]:
                triangle_nr = (
                    (
                        1 if sorting>0 else 2
                    ) if sign_y>0 else (
                        8 if sorting>0 else 7
                    )
                ) if sign_x>0 else (
                    (
                        4 if sorting>0 else 3
                    ) if sign_y>0 else (
                        5 if sorting>0 else 6 
                    )
                )

                for ix, (x_low, x_up) in zip(range(1,len(offset_x_bins)+1), offset_x_bins):
                    for iy, (y_low, y_up) in zip(range(1,len(offset_y_bins)+1), offset_y_bins):
                        if iy > ix:
                            break 
                        regions_at_raster_cell = raster_cell_to_regions[(ix, iy)]
                        # raster_cell_to_regions[(ix*sign_x, iy*sign_y) if sorting>0 else (iy*sign_y, ix*sign_x)] = list(set([translate_reg_nr_to_reg_id[region_nr] for region_nr in region_nrs]))
                        i_min, i_max = (iy, ix) if sorting > 0 else (ix, iy)
                        x, y = (i_max*sign_x, i_min*sign_y)
                        raster_cell_id_to_bounds[(x,y)] = ((x_low, x_up), (y_low, y_up))
                        region_nrs = [reg.nr for reg in regions_at_raster_cell] # if abs(reg.trgl_nr - triangle_nr)%7 <= 1 else reg.nr+1 
                        # try:
                        # region_ids = []
                        # for region_nr in region_nrs:
                        #     new_nr = region_nr//10*10+triangle_nr
                        #     new_reg = id_to_offset_regions[translate_reg_nr_to_reg_id[new_nr]]
                        #     if abs(new_reg.trgl_nr  - triangle_nr)%7 <= 1:
                        #         pass
                        #         if hasattr(new_reg, 'trgl_nrs'):
                        #             pass
                        #             # print("ATTT", triangle_nr,  new_reg.trgl_nr, new_reg.trgl_nrs)
                        #     else:
                        #         old_new_nr = new_nr
                        #         old_reg = new_reg
                        #         new_nr += 1 if triangle_nr < 8 else -7
                        #         new_reg = id_to_offset_regions[translate_reg_nr_to_reg_id[new_nr]]
                        #         # print(
                        #         #     "TN", triangle_nr, "new",new_nr%10, "old",old_new_nr%10,  
                        #         #     "\nnew:", (new_reg.trgl_nr, new_reg.trgl_nrs if hasattr(new_reg,'trgl_nrs') else ''),
                        #         #     "\nold:", (old_reg.trgl_nr, old_reg.trgl_nrs if hasattr(old_reg,'trgl_nrs') else ''))
                        #     region_ids.append(translate_reg_nr_to_reg_id[new_nr])
                        # region_ids = tuple(region_ids)

                        region_ids = tuple(sorted(set([translate_reg_nr_to_reg_id[region_nr//10*10+triangle_nr] for region_nr in region_nrs])))
                        # except:
                        #     print("translate_reg_nr_to_reg_id", translate_reg_nr_to_reg_id)
                        #     raise ValueError("region_nrs", region_nrs, "A",[region_nr//10*10+triangle_nr for region_nr in region_nrs])
                        if not region_ids in unique_reg_id_combs_to_raster_cells:
                            unique_reg_id_combs_to_raster_cells[region_ids] = []
                        unique_reg_id_combs_to_raster_cells[region_ids].append((x, y))

                        raster_cell_to_regions[(x,y)] = [id_to_offset_regions[id] for id in region_ids]

    if not plot_offset_raster is None:
        create_raster_plot(
            regions=list(id_to_offset_regions.values()),
            raster_cell_to_regions=raster_cell_to_regions,
            offset_x_bins=offset_x_bins,
            offset_y_bins=offset_y_bins,
            lims=[-.55,.55], add_raster_labels=True)

    offset_x_vals = get_vals_from_bins(offset_x_bins) 
    offset_y_vals = get_vals_from_bins(offset_y_bins) 
    offset_all_x_vals = [-x for x in reversed(offset_x_vals[1:])] + offset_x_vals
    offset_all_y_vals = [-y for y in reversed(offset_y_vals[1:])] + offset_y_vals

    
    return raster_cell_to_regions, offset_all_x_vals, offset_all_y_vals, unique_reg_id_combs_to_raster_cells
#


def create_region_comb_nr_to_check_lookup(
        raster_cell_to_regions,
        offset_reg_id_comb_to_check,
):
    """
    
    """
     
    # region_comb_to_nr = dict()
    # if not region_ids in region_comb_to_nr:
    #     region_comb_to_nr[region_ids] = len(region_comb_to_nr)
    raster_cell_to_region_comb_nr = dict()
    offset_region_comb_nr_to_check = dict()
    region_comb_to_nr = dict()
    for key, regions in raster_cell_to_regions.items():
        region_ids = tuple([reg.id for reg in regions])
        if not region_ids in region_comb_to_nr:
            region_comb_to_nr[region_ids] = len(region_comb_to_nr)
            offset_region_comb_nr_to_check[region_comb_to_nr[region_ids]] = offset_reg_id_comb_to_check[region_ids]
        #
        raster_cell_to_region_comb_nr[key] = region_comb_to_nr[region_ids]
    return raster_cell_to_region_comb_nr, offset_region_comb_nr_to_check
#

@time_func_perf
def prepare_offset_regions(
        grid_spacing:float,
        r:float,
        include_boundary:bool=False,
        nest_depth:int=0,
        plot_offset_checks:dict=None,
        plot_offset_regions:dict=None,
        plot_offset_raster:dict=None,
        silent:bool=True,
):
    """
    This function retrieves regions within a cell that 
    """
    (cells_contained_in_all_disks,
     cells_contained_in_all_trgl_disks,
     cells_maybe_overlapping_a_disk,
     cells_maybe_overlapping_a_trgl_disk
    ) = get_cells_relevant_for_disk_by_type(grid_spacing=grid_spacing, r=r, include_boundary=False)
    
    (cells_contained_in_all_disks,
     cells_contained_in_all_trgl_disks,
     cells_maybe_overlapping_a_disk,
     cells_maybe_overlapping_a_trgl_disk
    ) = get_cells_by_lvl_relevant_for_disk_by_type(grid_spacing=grid_spacing, r=r, include_boundary=False, nest_depth=nest_depth)

    trgl_regions = create_triangle_1_region()
    check_dict, cells_always_overlapped = create_check_dict(cells_maybe_overlapping_a_trgl_disk, trgl_regions, r=r)

    apply_checks_to_create_regions(check_dict=check_dict, trgl_regions=trgl_regions, r=r, plot_offset_checks=plot_offset_checks)
    
    cleanup_region_check_results(
        trgl_regions=trgl_regions, 
        cells_contained_in_all_trgl_disks=cells_contained_in_all_trgl_disks, 
        cells_always_overlapped=cells_always_overlapped,
        all_cells=cells_maybe_overlapping_a_trgl_disk,
        plot_offset_regions=plot_offset_regions,
        r=r,
        include_boundary=include_boundary,
        grid_spacing=grid_spacing,
        nest_depth=nest_depth,
    )
    
    # OffsetRegion.plot_many(regions=list(trgl_regions.values()))
    (id_to_offset_regions,
     translate_reg_nr_to_reg_id,
     contain_region_mult
    ) = transform_region_to_remaining_triangles(trgl_regions=trgl_regions)
    
    (trgl_raster_cell_to_region,
     offset_x_bins,
     offset_y_bins,
     unique_reg_id_combs_in_trgl_raster_cells,
     ) = sort_trgl_region_into_raster(trgl_regions=id_to_offset_regions, plot_offset_raster=plot_offset_raster)
    
    offset_reg_id_comb_to_check = prepare_raster_to_offset_region_checks(
        id_to_offset_regions=id_to_offset_regions,
        unique_reg_id_combs_to_raster_cells=unique_reg_id_combs_in_trgl_raster_cells,
        r=r,
        include_boundary=True,
        )

    trgl_precise_raster_cell = increase_raster_to_offset_region_precision(
        raster_cell_to_regions=trgl_raster_cell_to_region,
        offset_reg_id_comb_to_check=offset_reg_id_comb_to_check,
        offset_x_bins=offset_x_bins,
        offset_y_bins=offset_y_bins,
        id_to_offset_regions=id_to_offset_regions,
        plot_offset_raster=plot_offset_raster,
        )
    

    (raster_cell_to_regions,
     offset_all_x_vals,
     offset_all_y_vals,
     unique_reg_id_combs_to_raster_cells
     ) = transform_raster_to_remaining_triangle(
         id_to_offset_regions=id_to_offset_regions,
         raster_cell_to_regions=trgl_precise_raster_cell,
         translate_reg_nr_to_reg_id=translate_reg_nr_to_reg_id,
         offset_x_bins=offset_x_bins,
         offset_y_bins=offset_y_bins,
         plot_offset_raster=plot_offset_raster)
    
    offset_reg_id_comb_to_check = prepare_raster_to_offset_region_checks( 
        id_to_offset_regions=id_to_offset_regions,
        unique_reg_id_combs_to_raster_cells=unique_reg_id_combs_to_raster_cells,
        r=r,
        include_boundary=include_boundary,
        )
    
    raster_cell_to_region_comb_nr, offset_region_comb_nr_to_check = create_region_comb_nr_to_check_lookup(
        raster_cell_to_regions=raster_cell_to_regions,
        offset_reg_id_comb_to_check=offset_reg_id_comb_to_check
    )
    
    return raster_cell_to_region_comb_nr, offset_region_comb_nr_to_check, offset_all_x_vals, offset_all_y_vals, id_to_offset_regions, contain_region_mult

