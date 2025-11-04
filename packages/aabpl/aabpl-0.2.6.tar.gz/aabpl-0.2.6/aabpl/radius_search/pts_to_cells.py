from numpy import (
    array as _np_array,
    zeros as _np_zeros,
    linspace as _np_linspace
)
from pandas import (DataFrame as _pd_DataFrame, cut as _pd_cut, concat as _pd_concat) 
from aabpl.utils.general import find_column_name,arr_to_tpls
from aabpl.testing.test_performance import time_func_perf
# from aabpl.doc.docstrings import fixdocstring

################ assign_points_to_cells ######################################################################################
# @fixdocstring
@time_func_perf
def assign_points_to_cells(
    grid:dict,
    pts:_pd_DataFrame,
    y:str='lat',
    x:str='lon',
    row_name:str='id_y',
    col_name:str='id_x',
    silent:bool=False,
) -> _pd_DataFrame:
    """
    # TODO Move to class and Properly describe.
    # TODO it modifies pts AND grid?
    Modifies input pandas.DataFrame grid and pts: 
    sorts by 1) y coordinate and 2) by x coordinate

    Args:
    <y>
    
    Returns:
    gridcell_id_name: name to be appended in pts to indicate gridcell. If False then information will not be stored in pts 
    """
    if not silent:
        print(
            'Aggregate Data from '+str(len(pts))+' points'+
            ' into '+str(len(grid.row_ids))+'x'+str(len(grid.col_ids))+
            '='+str(len(grid.ids))+' cells.' 
        )
    # to do change to cut
    # for each row select relevant points, then refine selection with columns to obtain cells
    pts[row_name] = ((pts[y]-grid.total_bounds.ymin) // grid.spacing).astype(int)
    pts[col_name] = ((pts[x]-grid.total_bounds.xmin) // grid.spacing).astype(int)
    
    return pts[[row_name, col_name]]

def translate_subcell_row_col_to_value(row_nr, col_nr, lvl, nest_depth):
    """TODO create function that that translates subcell row col to value"""
    subcell_value = 0
    for i in range(1,nest_depth+1):
            n = 2**(i)
            subcell_mult = 2**((nest_depth-i)*2)
            print("nest_depth", nest_depth, "i", i, "subcell_mult",subcell_mult, "n", n)
            print([int(x//(1/n)%n%2) for x in _np_linspace(0,1,10)])
            # TODO this is not yet ready.
            subcell_value += (col_nr//(1/n)%n%2 * subcell_mult  + row_nr//(1/n)%n%2 * 2 * subcell_mult).astype(int)
        #
    return subcell_value

@time_func_perf
def aggregate_point_data_to_cells(
    grid:dict,
    pts:_pd_DataFrame,
    c:list=['employment'],
    y:str='lat',
    x:str='lon',
    row_name:str='id_y',
    col_name:str='id_x',
    nest_depth:int=5,
    silent:bool=False,
) -> _pd_DataFrame:
    """
    TODO
    """
    # what is points data initally sorted by

    # aggregate cells to super cells to save lookup time 
    aggregate_level = 0

    # sort by row, then by col = resulting in cell wise sorting
    # then sort for quadrants 
    cols_for_sort = [row_name, col_name]
    subcell_nr = find_column_name('sc_nr', existing_columns=pts.columns)

    
    if nest_depth > 0:
        # offsets normalized to 0-1
        offset_x = 0.5 + (((pts[x]-grid.total_bounds.xmin)%grid.spacing)-grid.spacing/2) / grid.spacing
        offset_y = 0.5 + (((pts[y]-grid.total_bounds.ymin)%grid.spacing)-grid.spacing/2) / grid.spacing
        pts[subcell_nr] = 0

        # loop through nest levels starting from the broadest/most aggregate end with smallest/most narrow
        for i in range(1,nest_depth+1):
            n = 2**(i)
            subcell_mult = 2**((nest_depth-i)*2)
            # print("nest_depth", nest_depth, "i", i, "subcell_mult",subcell_mult, "n", n)
            # print([int(x//(1/n)%n%2) for x in _np_linspace(0,1,10)])
            pts[subcell_nr] += (offset_x//(1/n)%n%2 * subcell_mult  + offset_y//(1/n)%n%2 * 2 * subcell_mult).astype(int)
        #
        cols_for_sort.append(subcell_nr)
    #
    
    pts.sort_values(cols_for_sort,inplace=True)
    
    # extract variables from dataframe for faster access speed
    row_ids = pts[row_name].unique().tolist()
    col_ids = pts[col_name].unique().tolist()
    pts_rows = pts[row_name].tolist()
    pts_cols = pts[col_name].values
    pts_cols_list = pts[col_name].tolist()
    pts_vals = pts[c].values
    pts_ids = pts.index.values #tuple([int(x) for x in pts.index])
    pts_subcell_nrs = pts[subcell_nr].values if nest_depth > 0 else _np_zeros(len(pts_cols))
    n_pts, col_max = len(pts), col_ids[-1]

    # save position of first point in row
    pos, row_id_indexes = 0, []
    for i, row_id in enumerate(row_ids):
        row_id_indexes.append(pos+next((idx for idx, val in enumerate(pts_rows[pos:]) if val==row_id),None))   
        pos = row_id_indexes[i]+1 
    
    # output dictionarys
    id_to_sums, id_to_pt_ids = {}, {}
    id_to_pt_ids_by_lvl = {i: {} for i in range(1, nest_depth+1)}
    id_to_sums_by_lvl = {i: {} for i in range(1, nest_depth+1)}
    
    # TODO: remove next line after testing
    tot = {"0":sum(pts_vals), **{i:0 for i in range(1, nest_depth+1) }}

    def nest_next_lvl(
            pos_min:int,
            pos_max:int,
            subcell_val:int=0,
            lvl:int=1,
            row_col:tuple=(0,0)):
        """
        function that recursively splits cell into quadrants until nest_depth is reached: 
        2 subcell rows and 2 subcell columns and store the result of each non empty quadrant in dictionary
        """

        subcell_mult = 2**((nest_depth-lvl)*2)
        
        for cur_quad_nr in range(4):
            # 
            if pos_min >= pos_max:
                break
            # if there are no points in quadrant, continue with next
            if (pts_subcell_nrs[pos_min]-subcell_val) // subcell_mult > cur_quad_nr:
                continue
            # otherwise there are points in quadrant
            # find first point not in quadrant, if none include all remaining points 
            pos_next = next((i+pos_min for i, subcell_nr in enumerate(pts_subcell_nrs[pos_min:pos_max]) if (subcell_nr-subcell_val)//subcell_mult>cur_quad_nr), pos_max)
            # TODO: remove next line after testing
            tot[lvl] += sum(pts_vals[pos_min:pos_next].sum(axis=0))
            id_to_sums_by_lvl[lvl][
                (row_col, lvl, subcell_val + cur_quad_nr * subcell_mult)
                ] = pts_vals[pos_min:pos_next].sum(axis=0)
            id_to_pt_ids_by_lvl[lvl][
                (row_col, lvl, subcell_val + cur_quad_nr * subcell_mult)
                ] = pts_ids[pos_min:pos_next]

            if lvl+1 <= nest_depth:
                nest_next_lvl(
                    pos_min=pos_min,
                    pos_max=pos_next,
                    subcell_val=subcell_val + cur_quad_nr * subcell_mult,
                    lvl=lvl+1, row_col=row_col
                )
            pos_min = pos_next
        #
    #

    # loop over rows
    for cur_row, cur_col_i, next_row_i, cur_col in zip(row_ids, row_id_indexes, row_id_indexes[1:]+[n_pts], pts_cols[row_id_indexes]):
        # somwhere np.int64 was introduced thus reapply int() type. Could be done more elagantly if source of np.int64 is identified
        cur_row, cur_col_i, next_row_i, cur_col = int(cur_row), int(cur_col_i), int(next_row_i), int(cur_col)
        # find next column to the right until all points from row an included in a column of the row
        while True:
            # for points of the same row that are to the right of current column, find first and return its position and column 
            next_col_i, next_col = next(((i+cur_col_i,c) for i,c in enumerate(pts_cols_list[cur_col_i:next_row_i]) if cur_col<c),(next_row_i,col_max+1)) 
            # if there are no points to the right of the column break to continue with the next row
            if cur_col_i >= next_col_i:
                break
            
            # for points within resulting cell:
            # aggregate data
            id_to_sums[(cur_row,cur_col)] = pts_vals[cur_col_i:next_col_i].sum(axis=0)
            # store point ids
            id_to_pt_ids[(cur_row,cur_col)] = pts_ids[cur_col_i:next_col_i]
            
            id_to_sums_by_lvl[((cur_row,cur_col), 0)] = pts_vals[cur_col_i:next_col_i].sum(axis=0)
            id_to_pt_ids_by_lvl[((cur_row,cur_col),0)] = pts_ids[cur_col_i:next_col_i]
            # now create subcells and aggregate data within it
            if nest_depth > 0:
                nest_next_lvl(
                    pos_min=cur_col_i,
                    pos_max=next_col_i,
                    subcell_val=0,
                    lvl=1, row_col=(cur_row,cur_col)
                )
            cur_col_i, cur_col = next_col_i, next_col
        #
    #

    # TODO dictionaries that are no longer needed
    grid.id_to_sums = id_to_sums
    grid.id_to_pt_ids = id_to_pt_ids
    grid.id_to_pt_ids_by_lvl = id_to_pt_ids_by_lvl
    grid.id_to_sums_by_lvl = id_to_sums_by_lvl
    subsubtypes_sparse_grid = set()
    for x in set(id_to_pt_ids):
        for y in x:
            subsubtypes_sparse_grid.add(type(y))
    # TODO drop column 
    # if nest_depth > 0:
    #     pts.drop(columns=[subcell_nr], inplace=True)
    
    if not silent:
        print('Total(s) for grid cells:', _np_array([s for s in grid.id_to_sums.values()]).sum(axis=0), 'Total(s) for points:', pts[c].values.sum(axis=0))
    #
    return 
#
