from pandas import DataFrame as _pd_DataFrame
from numpy import (
    array as _np_array, column_stack as _np_column_stack, ndarray as _np_ndarray, vstack as _np_vstack, ones as _np_ones, percentile as _np_percentile, bool_ as _np_bool
)
from numpy.random import ( random as _np_random,  randint as _np_randint, seed as _np_seed, )
from shapely.geometry import Polygon as _shapely_Polygon, Point as _shapely_Point
from aabpl.utils.general import flatten_list

def draw_random_points_in_sample_area(
    grid:dict,
    cell_width:float,
    n_random_points:int=int(1e5),
    sample_area:_shapely_Polygon=None,
    ids_rndm_sample:dict=None,
    random_seed:float=None,
    cell_height:float=None,
    extra_share_of_pts_to_create:float = 0.02,
    fix_extra_pts_to_create:int = 1000,
)->_np_array:
    """
    Draw n random points within non-excluded region
    if grid is provided it will first draw a grid cell that is not excluded 
    then it will choose a random point within that grid cell
    if the grid cell is partly excluded and the randomly generated point falls 
    into the excluded area the point is discarded and a new cell is drawn 

    Args:
    -------
    partly_or_fully_included_cells (??):
        list cells with attributes (centroid coords, excluded_property)
    cell_width (float):
        width of cells
    n_random_points (int):
        number of random points to be drawn (default=1e5)
    random_seed (int):
        seed to make random draws replicable. TODO not yet implemented.
    cell_height (float):
        height of cells. (default=None, cell_height will be set equal to cell_width)
    Returns:
    random_points_coordinates (array):
        vector of coordinates (x,y) of randomly drawn points within included area. shape=(n_random_points, 2)
    random_points_cell_ids (array):
        vector cell ids where random points fall into. TODO not yet implemented.  
    """
    if sample_area is None:
        sample_area = grid.sample_area
    if ids_rndm_sample is None:
        ids_rndm_sample = grid.ids_rndm_sample
    # SET RANDOM SEED IF ANY SUPPLIED AND ASSERT TYPE
    if type(random_seed)==int:
        _np_seed(random_seed)
    elif random_seed is not None:
        raise TypeError(
            "random_seed should be int if supplied, otherwise None (of type NoneType)."+
            "\nSeed suplied is of type "+str(type(random_seed))+
            ". Seed suplied:\n", random_seed
        )
    #
    
    # IF NOT SPECIFIED OTHERWISE CELL HEIGHT EQUAL CELL WIDTH
    if cell_height is None:
        cell_height = cell_width
    #
    
    # col_min = int((sample_area.bounds[0] - grid.total_bounds.xmin) // cell_width)
    # row_min = int((sample_area.bounds[1] - grid.total_bounds.ymin) // cell_height)
    # col_max = int((sample_area.bounds[2] - grid.total_bounds.xmin) // cell_width)
    # row_max = int((sample_area.bounds[3] - grid.total_bounds.ymin) // cell_height)
    col_min = grid.sample_col_min
    row_min = grid.sample_row_min
    col_max = grid.sample_col_max
    row_max = grid.sample_row_max
    centroid_left_x = grid.total_bounds.xmin + grid.spacing / 2 
    centroid_bottom_y = grid.total_bounds.ymin + grid.spacing / 2
    # grid.sample_grid_bounds = [
    #     grid.total_bounds.xmin + col_min * cell_width,
    #     grid.total_bounds.ymin + row_min * cell_height,
    #     grid.total_bounds.xmin + (col_max+1) * cell_width,
    #     grid.total_bounds.ymin + (row_max+1) * cell_height,
    # ]
    
    
    if type(ids_rndm_sample) == bool and ids_rndm_sample == True or len(ids_rndm_sample)==len(grid.ids):
        all_cells_eligible = True    
        share_of_invalid_cells = .0
    else:
        all_cells_eligible = len(grid.ids)==len(ids_rndm_sample)
        # estimate the share of invalid area to draw additionally to create points (as some get discarded when they fall in invalid area)
        share_of_invalid_cells = len(ids_rndm_sample)/((col_max-col_min+1)*(row_max-row_min+1)) 
    sample_cells = _np_array(flatten_list(
        [[(row_id, col_id) for col_id in range(col_min,col_max+1) if all_cells_eligible or (row_id, col_id) in ids_rndm_sample] for row_id in range(row_min,row_max+1)]
        ))
    # update ids_rndm_sample with grid cells outside the grid
    if not all_cells_eligible:
        grid.ids_rndm_sample = set([(int(row),int(col)) for row, col in sample_cells])
    
    grid_bbox = _shapely_Polygon([
            (grid.total_bounds.xmin,grid.total_bounds.ymin),
            (grid.total_bounds.xmax,grid.total_bounds.ymin),
            (grid.total_bounds.xmax,grid.total_bounds.ymax),
            (grid.total_bounds.xmin,grid.total_bounds.ymax),
    ])
    
    sample_area_contains_grid = grid_bbox.area == sample_area.intersection(grid_bbox).area
    # estimate the share of invalid area to draw additionally to create points (as some get discarded when they fall in invalid area)
    share_of_invalid_geometry = sample_area.intersection(grid_bbox).area / (((col_max-col_min+1)*(row_max-row_min+1))*cell_height*cell_width) 
    # make a guess upward biased guess how large the share of invalid random points may be. 
    share_of_invalid_area = 0.5 * (1-share_of_invalid_cells)*(1-share_of_invalid_geometry) + 0.25*share_of_invalid_cells +0.25*share_of_invalid_geometry
    # CREATE POINTS AND DISCARD POINTS UNTIL ENOUGH POINTS ARE DRWAN IN VALID AREA
    random_points_coordinates = _np_ndarray(shape=(0,2))
    pts_attempted_to_create = 0
    it = 0
    while random_points_coordinates.shape[0] < n_random_points:
        # update estimation of share of invalid area for iterations after first
        # TODO THIS MIGHT NOT BE NECESSARY ONCE PERCENTAGE OF INVALID AREA IS KNOWN
        if pts_attempted_to_create > 0:
            # otherwise update guess for iterations after first
            share_of_invalid_area = len(random_points_coordinates)/pts_attempted_to_create
        
        # set number of additional points to create
        attempt_to_create_n_points = int(
            (1+share_of_invalid_area+extra_share_of_pts_to_create*int(share_of_invalid_area>0)) * 
            (n_random_points-len(random_points_coordinates)) + 
            fix_extra_pts_to_create*(1+it)*int(share_of_invalid_area>0)
        )

        rndm_cells = sample_cells[_np_randint(0, len(sample_cells), attempt_to_create_n_points)]
        new_random_point_coordinates = (_np_random((attempt_to_create_n_points,2))-0.5)*_np_array([cell_width, cell_height]) + (
         rndm_cells[:,::-1] * _np_array([cell_width, cell_height]) + _np_array([centroid_left_x, centroid_bottom_y])
        )

        # if anywhere is valid area        
        if sample_area_contains_grid:
            new_random_point_coordinates_in_sample_area = new_random_point_coordinates
            # 
        else: # filter out points in invalid area
            new_random_point_coordinates_in_sample_area =_np_array([
                coords for coords in new_random_point_coordinates 
                if sample_area.contains(_shapely_Point(coords)) 
            ])
            #
        # save valid random points
        if len(new_random_point_coordinates_in_sample_area) > 0:
            random_points_coordinates = _np_vstack([random_points_coordinates, new_random_point_coordinates_in_sample_area])
        # update loop vars
        it += 1
        pts_attempted_to_create += attempt_to_create_n_points
    
    # return n_random_points coordinates
    return random_points_coordinates[:n_random_points]


def get_distribution_for_random_points(
    grid:dict,
    pts:_pd_DataFrame,
    sample_area:_shapely_Polygon=None,
    min_pts_to_sample_cell:int=1,
    n_random_points:int=int(1e5),
    k_th_percentile:float=[99.5],
    c:list=[],
    x:str='lon',
    y:str='lat',
    row_name:str='id_y',
    col_name:str='id_x',
    sum_suffix:str='_750m',
    random_seed:int=None,
    silent:bool=False,
):
    """Draws n_random_points within sample_area and aggregates data from points within search radius. 
    From those values it calculates the k_th_percentile threshold value for the variable(s). This 
    execute methods
    
    k_th_percentile: in [0,100] k-th percentile 

    1. draw n_random_points with draw_random_points_within_valid_area
    2. aggregate_point_data_to_disks_vectorized
    TODO Check if how cluster value 


    
    min_pts_to_sample_cell (int):
        minimum number of points in dataset that need to be in cell s.t. random points are allowed to be drawn within it. (default=1)
    """
    if type(k_th_percentile) != list:
        k_th_percentiles = [k_th_percentile for i in range(len(c))]
    else: 
        k_th_percentiles = k_th_percentile
    if any([k_th_percentile >= 100 or k_th_percentile <= 0 for k_th_percentile in k_th_percentiles]):
        raise ValueError(
            'Values for k_th_percentile must be >0 and <100. Provided values do not fullfill that condition',
            set([k_th_percentile for k_th_percentile in k_th_percentiles if k_th_percentile >= 100 or k_th_percentile <= 0])
        )
    grid_id_to_pt_ids = grid.id_to_pt_ids
    grid.ids_rndm_sample = True if min_pts_to_sample_cell == 0 else set([id for id in grid.ids if len(grid_id_to_pt_ids.get(id,[]))>=min_pts_to_sample_cell])
    grid.sample_area = sample_area

    random_point_coords = draw_random_points_in_sample_area(
        grid=grid,
        cell_width=grid.spacing,
        n_random_points=n_random_points,
        random_seed=random_seed,
        cell_height=grid.spacing,
    )

    rndm_pts = _pd_DataFrame(
        data = random_point_coords,
        columns=[x,y]
    )

    grid.search.set_source(
        pts=rndm_pts,
        c=c,
        x=x,
        y=y,
        row_name=row_name,
        col_name=col_name,
        sum_suffix=sum_suffix,
        silent=silent,
    )

    grid.search.set_target(
        pts=pts,
        c=c,
        x=x,
        y=y,
        row_name=row_name,
        col_name=col_name,
        silent=silent,
    )
    
    grid.rndm_pts = rndm_pts
    
    grid.search.perform_search(silent=silent,)

    sum_radius_names = [(cname+sum_suffix) for cname in c]
    disk_sums_for_random_points = rndm_pts[sum_radius_names].values

    cluster_threshold_values  = [_np_percentile(disk_sums_for_random_points[:,i], k_th_percentile,axis=0) for i, k_th_percentile in enumerate(k_th_percentiles)]
    
  
    return (cluster_threshold_values, rndm_pts)
