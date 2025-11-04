from numpy import array as _np_array, zeros as _np_zeros,exp as _np_exp 
from numpy.linalg import norm as _np_linalg_norm
from pandas import (DataFrame as _pd_DataFrame, cut as _pd_cut, concat as _pd_concat) 
from aabpl.utils.general import flatten_list
from aabpl.illustrations.illustrate_point_to_disk import illustrate_point_disk
from aabpl.illustrations.plot_pt_vars import create_plots_for_vars
from aabpl.testing.test_performance import time_func_perf
from math import pi as _math_pi
from aabpl.valid_area import disk_cell_intersection_area, disk_cell_intersection_estimate

################ aggregate_point_data_to_disks_vectorized ######################################################################################
@time_func_perf
def aggregate_point_data_to_disks_vectorized(
    grid:dict,
    pts_source:_pd_DataFrame,
    r:float,
    c:list=[],
    y:str='proj_lat',
    x:str='proj_lon',
    pts_target:_pd_DataFrame=None,
    row_name:str='id_y',
    col_name:str='id_x',
    cell_region_name:str='cell_region',
    sum_suffix:str=None,
    exclude_pt_itself:bool=True,
    weight_valid_area:str=None,
    plot_pt_disk:dict=None,
    silent:bool=False,
):
    """
    Aggregates Data around each point
    """
    if pts_target is None:
        pts_target = pts_source 
    # unpack grid_data 
    grid_id_to_pt_ids = grid.id_to_pt_ids
    grid_id_to_sums = grid.id_to_sums
    sparse_grid_ids = set(grid_id_to_pt_ids)
    ids_rndm_sample = grid.ids_rndm_sample
    grid_spacing = grid.spacing
    if type(ids_rndm_sample)==bool and ids_rndm_sample:
        weight_valid_area=False # as for each point 100% of area would be valid
    else:
        grid_padding = -int(-grid_spacing//r)
        # take all cells that are part of the sampling grid
        invalid_cells = set([id for id in 
                             tuple(flatten_list([
            [(int(row_id), int(col_id)) for col_id in range(min(grid.col_ids)-grid_padding, max(grid.col_ids)+grid_padding)] 
            for row_id in range(min(grid.row_ids)-grid_padding, max(grid.row_ids)+grid_padding)]))
             if not id in ids_rndm_sample])
    
    region_id_to_contained_cells = grid.search.region_id_to_contained_cells
    region_id_to_overlapped_cells = grid.search.region_id_to_overlapped_cells
    cells_contained_in_all_disks = grid.search.cells_contained_in_all_disks
    
    row_col_to_bounds = grid.row_col_to_bounds
    row_col_to_centroid = grid.row_col_to_centroid
    get_cell_centroid = grid.get_cell_centroid
    get_cell_bounds = grid.get_cell_bounds

    pt_id_to_xy_coords = grid.search.target.pt_id_to_xy_coords
    pt_id_to_vals = grid.search.target.pt_id_to_vals
    n_pts = len(pts_source)

    # initialize columns and/or reset to zero 
    if sum_suffix is None:
        sum_suffix = '_'+str(r)
    sum_radius_names = [(cname+sum_suffix) for cname in c]
    pts_source[sum_radius_names] = 0
    
  
    sums_within_disks = _np_zeros((n_pts, len(c)))
    valid_area_shares = _np_zeros(n_pts)
    valid_search_area = 2 * _math_pi * r**2
    
    if plot_pt_disk is not None:
        if not 'pt_id' in plot_pt_disk:
            plot_pt_disk['pt_id'] = pts_source.index[int(n_pts//2)]
        
    zero_sums = _np_zeros(len(c),dtype=int) if len(c) > 1 else 0
    pts_source['initial_sort'] = range(len(pts_source))
    pts_source.sort_values([row_name, col_name, cell_region_name], inplace=True)
    last_pt_row_col = (-1, -1)
    last_cell_region_id = -1
    counter_new_cell = 0
    counter_new_contain_region = 0
    counter_new_overlap_region = 0
    

    if len(c) > 1:
        if weight_valid_area:
            @time_func_perf
            def sum_contained_all_offset_regions(
                    pt_row,
                    pt_col,
            ):
                """
                returns sum for cells contained in search radius for all points within cell. Additionally returns invalid area as float
                """
                cells_cntd_by_pt_cell = sparse_grid_ids.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in cells_contained_in_all_disks])
                invalid_area = len(invalid_cells.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in cells_contained_in_all_disks])) * grid_spacing**2
                # cells_cntd_by_pt_cell = [cell_id for cell_id in (id_y_mult*(cells_contained_in_all_disks[:,0]+(pt_row))+(
                #     cells_contained_in_all_disks[:,1]+pt_col)) if cell_id in sparse_grid_ids] 
                if len(cells_cntd_by_pt_cell)>0:
                    return _np_array([grid_id_to_sums[g_id] for g_id in cells_cntd_by_pt_cell]).sum(axis=0), invalid_area 
                return zero_sums, invalid_area 
            #
        else:# not weight_valid_area
            @time_func_perf
            def sum_contained_all_offset_regions(
                    pt_row,
                    pt_col,
            ):
                """
                returns sum for cells contained in search radius for all points within cell. Additionally returns invalid area as float
                """
                cells_cntd_by_pt_cell = sparse_grid_ids.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in cells_contained_in_all_disks])
                if len(cells_cntd_by_pt_cell)>0:
                    return _np_array([grid_id_to_sums[g_id] for g_id in cells_cntd_by_pt_cell]).sum(axis=0) 
                return zero_sums 
            #
        #
    else: # len(c)==1
        if weight_valid_area:
            @time_func_perf
            def sum_contained_all_offset_regions(
                    pt_row,
                    pt_col,
            ):
                cells_cntd_by_pt_cell = sparse_grid_ids.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in cells_contained_in_all_disks])
                invalid_area = len(invalid_cells.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in cells_contained_in_all_disks])) * grid_spacing**2
                return sum([grid_id_to_sums[g_id] for g_id in cells_cntd_by_pt_cell]), invalid_area 
            #
        else:# not weight_valid_area
            @time_func_perf
            def sum_contained_all_offset_regions(
                    pt_row,
                    pt_col,
            ):
                cells_cntd_by_pt_cell = sparse_grid_ids.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in cells_contained_in_all_disks])
                return sum([grid_id_to_sums[g_id] for g_id in cells_cntd_by_pt_cell]) 
            #
        #
    if len(c) > 1:
        if weight_valid_area:
            @time_func_perf
            def sum_contained_by_offset_region(
                    pt_row,
                    pt_col,
                    cell_region_id,
            ):
                cells_contained_by_pt_region = sparse_grid_ids.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in region_id_to_contained_cells[cell_region_id]])
                invalid_area = len(invalid_cells.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in region_id_to_contained_cells[cell_region_id]])) * grid_spacing**2
                if len(cells_contained_by_pt_region)>0:
                    return _np_array([grid_id_to_sums[g_id] for g_id in cells_contained_by_pt_region]).sum(axis=0), invalid_area
                return zero_sums, invalid_area
            #
        else:# not weight_valid_area
            @time_func_perf
            def sum_contained_by_offset_region(
                    pt_row,
                    pt_col,
                    cell_region_id,
            ):
                cells_contained_by_pt_region = sparse_grid_ids.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in region_id_to_contained_cells[cell_region_id]])
                if len(cells_contained_by_pt_region)>0:
                    return _np_array([grid_id_to_sums[g_id] for g_id in cells_contained_by_pt_region]).sum(axis=0)
                return zero_sums
            #
        #
    else:# len(c)==1
        if weight_valid_area:
            @time_func_perf
            def sum_contained_by_offset_region(
                    pt_row,
                    pt_col,
                    cell_region_id,
            ):
                cells_contained_by_pt_region = sparse_grid_ids.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in region_id_to_contained_cells[cell_region_id]])
                invalid_area = len(invalid_cells.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in region_id_to_contained_cells[cell_region_id]])) * grid_spacing**2
                return sum([grid_id_to_sums[g_id] for g_id in cells_contained_by_pt_region]), invalid_area
            #
        else:# not weight_valid_area
            @time_func_perf
            def sum_contained_by_offset_region(
                    pt_row,
                    pt_col,
                    cell_region_id,
            ):
                cells_contained_by_pt_region = sparse_grid_ids.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in region_id_to_contained_cells[cell_region_id]])
                return sum([grid_id_to_sums[g_id] for g_id in cells_contained_by_pt_region])
            #
        #
    #

    if weight_valid_area:
        @time_func_perf
        def get_pts_overlapped_by_region(
                pt_row,
                pt_col,
                cell_region_id,
        ):  
            
            cells_overlapped_by_pt_region = sparse_grid_ids.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in region_id_to_overlapped_cells[cell_region_id]])
            overlapped_invalid_cells = invalid_cells.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in region_id_to_overlapped_cells[cell_region_id]])
            return _np_array(flatten_list([
                grid_id_to_pt_ids[cell_id] for cell_id in cells_overlapped_by_pt_region
            ])), overlapped_invalid_cells
        #
    else:# not weight_valid_area
        @time_func_perf
        def get_pts_overlapped_by_region(
                pt_row,
                pt_col,
                cell_region_id,
        ):  
            
            cells_overlapped_by_pt_region = sparse_grid_ids.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in region_id_to_overlapped_cells[cell_region_id]])
            return _np_array(flatten_list([
                grid_id_to_pt_ids[cell_id] for cell_id in cells_overlapped_by_pt_region
            ]))
        #
    

    if len(c) > 1:
        @time_func_perf
        def sum_overlapped_pts_in_radius(
            pts_in_cells_overlapped_by_pt_region,
            a_pt_xycoord
        ):
            if len(pts_in_cells_overlapped_by_pt_region) > 0:
                pts_in_radius = pts_in_cells_overlapped_by_pt_region[(_np_linalg_norm( # create a mask of boolean values indicating if point are within radius 
                    _np_array([pt_id_to_xy_coords[pt_id] for pt_id in pts_in_cells_overlapped_by_pt_region]) -
                    a_pt_xycoord, 
                axis=1) <= r)]
                
                return _np_array([pt_id_to_vals[pt_id] for pt_id in pts_in_radius]).sum(axis=0) if len(pts_in_radius) > 0 else zero_sums
                # else no points in radius thus return vector of _np_zeros
            return zero_sums
    else:# len(c)==1
        @time_func_perf
        def sum_overlapped_pts_in_radius(
            pts_in_cells_overlapped_by_pt_region,
            a_pt_xycoord
        ):
            if len(pts_in_cells_overlapped_by_pt_region) > 0:
                pts_in_radius = pts_in_cells_overlapped_by_pt_region[(_np_linalg_norm( # create a mask of boolean values indicating if point are within radius 
                    _np_array([pt_id_to_xy_coords[pt_id] for pt_id in pts_in_cells_overlapped_by_pt_region]) -
                    a_pt_xycoord, 
                axis=1) <= r)]
                
                return sum([pt_id_to_vals[pt_id] for pt_id in pts_in_radius]) if len(pts_in_radius) > 0 else 0
                # else no points in radius thus return vector of _np_zeros
            return 0
    
        # @time_func_perf
        # def sum_overlapped_pts_in_radius2(
        #     pts_in_cells_overlapped_by_pt_region,
        #     a_pt_xycoord
        # ):
        #     val = 0
        #     for pt_maybe_overlapped in pts_in_cells_overlapped_by_pt_region:
        #         xm,ym = pt_id_to_xy_coords[pt_maybe_overlapped]
        #         if (a_pt_xycoord[0]-xm)**2+((a_pt_xycoord[1]-ym))**2 <= r:
        #             val += pt_id_to_vals[pt_maybe_overlapped]
           
        #     return val

    if weight_valid_area == 'precise':
        if r**2<2*grid_spacing**2:
            print("WARNING: Precise intersection method of search circle and grid cells is only implemented for search radius >= (2*grid_spacing**2)**0.5. Calculation of valid area thus might be false.")
        @time_func_perf
        def calculate_overlapped_invalid_area(
            a_pt_xycoord,
            invalid_overlapped_cells,
            # row_col_to_bounds=row_col_to_bounds,
            # grid_spacing=grid_spacing,
            # r=r,
            # silent=True,
        ) -> float:
            # This is slow. Either increase the speed or make a simple function that maps centroid distance to area estimate.
            
            return sum([disk_cell_intersection_area(
                    a_pt_xycoord,
                    cell_bounds=row_col_to_bounds.get((int(row),int(col)),get_cell_bounds(row,col)),
                    # cell_bounds=row_col_to_bounds[(int(row),int(col))],
                    grid_spacing=grid_spacing,
                    r=r,
                    silent=True,
                    ) for row,col in invalid_overlapped_cells])
            
    elif weight_valid_area == 'estimate':
        
        # define here as it depends on grid_spacing / r
        def estimate_overlapped_area_share(
            disk_center_pt_s:_np_array,      
            centroid_s:tuple=_np_array,
            logit_Q:float=1 / (0.70628102 + _np_exp(0.57266908 * (grid_spacing / r - 2))),
            logit_B:float=1 / (-0.21443453 + _np_exp(0.76899004 * (grid_spacing / r - 2))),
            r:float=r,
        ) -> _np_array:
            """
            either disk_center_pt_s or centroid_s can be more than one element not both
            returns numpy.array with share of grid cells that is overlapped by radius each element is in [0,1] or in (0,1) if cell is truly only overlapped
            """
            return 1 - 1 / (
                1.0 + logit_Q * _np_exp(
                    -logit_B * 
                        (1/r * _np_linalg_norm(disk_center_pt_s-centroid_s, axis=1) - 1)
                    )
                ) 
        
        @time_func_perf
        def calculate_overlapped_invalid_area(
            a_pt_xycoord,
            invalid_overlapped_cells:set,
        ) -> float:
            """
            Call intersection area estimation function based on distance, radius and grid_spacing.
            Mean estimation error of 5% of cell area. Largest error for cells where only one vertex of cell lies within radius (~20%)
            """
            # This is slow. Either increase the speed or make a simple function that maps centroid distance to area estimate.
            return 0.0 if len(invalid_overlapped_cells)==0 else estimate_overlapped_area_share(
                    disk_center_pt_s=a_pt_xycoord,
                    centroid_s=_np_array([row_col_to_centroid.get((int(row),int(col)),get_cell_centroid(row,col)) for row,col in invalid_overlapped_cells]),
                    # centroid_s=_np_array([row_col_to_centroid[(int(row),int(col))] for row,col in invalid_overlapped_cells]),
                    ).sum() * grid_spacing ** 2
    
    else:
        
        if weight_valid_area != False and not weight_valid_area is None:
            # move to handle inputs
            print("Value for 'weight_valid_area' must be in ['precise', 'estimate', 'guess', False]. Instead",weight_valid_area,"was provided.")
        weight_valid_area = False

    @time_func_perf
    def do_nothing():
        pass
    
    for (i, pt_id, a_pt_xycoord, (pt_row,pt_col), contain_region_id, overlap_region_id, cell_region_id) in zip(
        range(n_pts),
        pts_source.index,
        pts_source[[x, y,]].values, 
        pts_source[[row_name, col_name]].values,
        pts_source[cell_region_name].values // grid.search.contain_region_mult,
        pts_source[cell_region_name].values % grid.search.contain_region_mult,
        pts_source[cell_region_name].values,
        
        
        ):
        # as pts are sorted by grid cell update only if grid cell changed
        if not (pt_row, pt_col) == last_pt_row_col:
            counter_new_cell += 1
            # cells_cntd_by_pt_cell = sparse_grid_ids.intersection([(row+pt_row,col+pt_col) for row,col in cells_contained_in_all_disks])
            # # cells_cntd_by_pt_cell = [cell_id for cell_id in (id_y_mult*(cells_contained_in_all_disks[:,0]+(pt_row))+(
            # #     cells_contained_in_all_disks[:,1]+pt_col)) if cell_id in sparse_grid_ids] 
            # sums_cells_cntd_by_pt_cell = (_np_array([grid_id_to_sums[g_id] for g_id in cells_cntd_by_pt_cell]).sum(axis=0) 
            #                           if len(cells_cntd_by_pt_cell)>0 else zero_sums)
            if weight_valid_area:
                sums_cells_cntd_by_pt_cell, invalid_search_area_cntd_by_pt_cell = sum_contained_all_offset_regions(pt_row, pt_col)
            else: 
                sums_cells_cntd_by_pt_cell = sum_contained_all_offset_regions(pt_row, pt_col)
            do_nothing()
        #
            
        if not (pt_row, pt_col) == last_pt_row_col or last_contain_region_id != contain_region_id:
            counter_new_contain_region += 1
            # if cell changed or cell region changed
            # this can be improve to capture only changes of cell region conatain ids 
            # cells_contained_by_pt_region = sparse_grid_ids.intersection([(row+pt_row,col+pt_col) for row,col in region_id_to_contained_cells[cell_region_id]])
            # # cells_contained_by_pt_region = [cell_id for cell_id in (id_y_mult*(region_id_to_contained_cells[cell_region_id][:,0]+(pt_row))+(
            # #     region_id_to_contained_cells[cell_region_id][:,1]+pt_col)) if cell_id in sparse_grid_ids]
                           
            # sums_contained_by_pt_region = (_np_array([grid_id_to_sums[g_id] for g_id in cells_contained_by_pt_region]).sum(axis=0) 
            #                                  if len(cells_contained_by_pt_region)>0 else zero_sums)
            if weight_valid_area:
                sums_contained_by_pt_region, invalid_search_area_cntd_by_pt_region = sum_contained_by_offset_region(pt_row, pt_col, cell_region_id)
            else: 
                sums_contained_by_pt_region = sum_contained_by_offset_region(pt_row, pt_col, cell_region_id)
            do_nothing()

        if not (pt_row, pt_col) == last_pt_row_col or last_overlap_region_id != overlap_region_id:
            counter_new_overlap_region += 1
            # cells_overlapped_by_pt_region = sparse_grid_ids.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in region_id_to_overlapped_cells[cell_region_id]])
            # # cells_overlapped_by_pt_region = [cell_id for cell_id in (id_y_mult*(region_id_to_overlapped_cells[cell_region_id][:,0]+(pt_row))+(
            # #     region_id_to_overlapped_cells[cell_region_id][:,1]+pt_col)) if cell_id in sparse_grid_ids]
            # pts_in_cells_overlapped_by_pt_region = _np_array(flatten_list([
            #     grid_id_to_pt_ids[cell_id] for cell_id in cells_overlapped_by_pt_region
            # ]))
            if weight_valid_area:
                pts_in_cells_overlapped_by_pt_region, invalid_overlapped_cells = get_pts_overlapped_by_region(pt_row, pt_col, cell_region_id)
            else: 
                pts_in_cells_overlapped_by_pt_region = get_pts_overlapped_by_region(pt_row, pt_col, cell_region_id)
        #
        
        # if len(pts_in_cells_overlapped_by_pt_region) > 0:
        #     pts_in_radius = pts_in_cells_overlapped_by_pt_region[(_np_linalg_norm( # create a mask of boolean values indicating if point are within radius 
        #         _np_array([pt_id_to_xy_coords[pt_id] for pt_id in pts_in_cells_overlapped_by_pt_region]) -
        #         a_pt_xycoord, 
        #     axis=1) <= r)]
            
        #     overlapping_cells_sums = _np_array([pt_id_to_vals[pt_id] for pt_id in pts_in_radius]).sum(axis=0) if len(pts_in_radius) > 0 else zero_sums
        # else:
        #     # else no points in radius thus return vector of _np_zeros
        #     overlapping_cells_sums = zero_sums
        
        overlapping_cells_sums = sum_overlapped_pts_in_radius(pts_in_cells_overlapped_by_pt_region, a_pt_xycoord)


        # combine sums from three steps.
        # append result 
        sums_within_disks[i,:] = sums_cells_cntd_by_pt_cell + sums_contained_by_pt_region + overlapping_cells_sums
        
        # calculate share of valid area
        if weight_valid_area:
            invalid_search_area_overlaps = calculate_overlapped_invalid_area(
                    a_pt_xycoord=a_pt_xycoord,
                    invalid_overlapped_cells=invalid_overlapped_cells,
                )
            valid_area_shares[i] = (
                valid_search_area - 
                invalid_search_area_cntd_by_pt_cell - 
                invalid_search_area_cntd_by_pt_region - 
                invalid_search_area_overlaps
                ) / valid_search_area
    
        # plot example pint
        if plot_pt_disk is not None and pt_id == plot_pt_disk['pt_id']:
            cells_cntd_by_pt_cell = sparse_grid_ids.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in cells_contained_in_all_disks])
            cells_contained_by_pt_region = sparse_grid_ids.intersection([(row+pt_row,col+pt_col) for lvl,(row,col) in region_id_to_contained_cells[cell_region_id]])
            pts_in_radius = pts_in_cells_overlapped_by_pt_region[(_np_linalg_norm( # create a mask of boolean values indicating if point are within radius 
                _np_array([pt_id_to_xy_coords[pt_id] for pt_id in pts_in_cells_overlapped_by_pt_region]) -
                a_pt_xycoord, 
            axis=1) <= r)] if len(pts_in_cells_overlapped_by_pt_region)>0 else _np_array([])
            illustrate_point_disk(
                grid=grid,
                pts_source=pts_source,
                pts_target=pts_target,
                r=r,
                c=c,
                x=x,
                y=y,
                cells_cntd_by_pt_cell=[(row+pt_row,col+pt_col) for lvl,(row,col) in cells_contained_in_all_disks],
                cells_contained_by_pt_region=[(row+pt_row,col+pt_col) for lvl,(row,col) in region_id_to_contained_cells[cell_region_id]],
                cells_overlapped_by_pt_region=[(row+pt_row,col+pt_col) for lvl,(row,col) in region_id_to_overlapped_cells[cell_region_id]],
                pts_in_cell_contained_by_pt_region=_np_array(flatten_list([
                        grid_id_to_pt_ids[cell_id] for cell_id in cells_cntd_by_pt_cell
                    ]+[
                        grid_id_to_pt_ids[cell_id] for cell_id in cells_contained_by_pt_region
                    ])),
                pts_in_cells_overlapped_by_pt_region=pts_in_cells_overlapped_by_pt_region,
                pts_in_radius=pts_in_radius,
                home_cell=tuple(pts_source[[row_name, col_name]].loc[pt_id]),
                **plot_pt_disk,
            )
        # #

        # set id as last id for next iteration
        last_pt_row_col = (pt_row, pt_col)
        last_contain_region_id = contain_region_id
        last_overlap_region_id = overlap_region_id
    #
    pts_source[sum_radius_names] = pts_source[sum_radius_names].values + sums_within_disks

    if exclude_pt_itself and grid.search.tgt_df_contains_src_df:
        # substract data from point itself unless specified otherwise
        for sum_radius_name, col_name in zip(sum_radius_names, c):
            pts_source[sum_radius_name] = pts_source[sum_radius_name].values - pts_source[col_name]
    
    if weight_valid_area:
        pts_source['valid_area_share'+sum_suffix] = valid_area_shares
        for sum_radius_name in sum_radius_names:
            pts_source[sum_radius_name] = pts_source[sum_radius_name].values / pts_source['valid_area_share'+sum_suffix].values
    # print(
    #     "Share of pts in",
    #     "\n- same cell as previous:", 100-int(counter_new_cell/len(pts_source)*100),"%",
    #     "\n- same cell and containing same surrounding cells:",100 - int(counter_new_contain_region/len(pts_source)*100),"%",
    #     "\n- same cell and overlapping same surrounding cells",100 - int(counter_new_overlap_region/len(pts_source)*100),"%")
    def plot_vars(
        self = grid,
        colnames = _np_array([c, sum_radius_names]), 
        filename:str='',
        **plot_kwargs:dict,
    ):
        return create_plots_for_vars(
            grid=self,
            colnames=colnames,
            filename=filename,
            plot_kwargs=plot_kwargs,
        )

    grid.plot.vars = plot_vars

    pts_source.sort_values(['initial_sort'], inplace=True)
    pts_source.drop('initial_sort', axis=1, inplace=True)

    return pts_source[sum_radius_names]
#


