# -*- coding: utf-8 -*-
"""
Created on Sun Jul 20 16:26:44 2025

@author: belie
"""

import numpy as np
from scipy.optimize import minimize, direct


def cost_function_velocity(y_obs, y_model, idx_comp=None, sr=1, a=0):
    """ Compute the error function between the observed and the modeled trajectories """

    vi = np.gradient(y_obs, 1/sr, edge_order=2)
    if idx_comp is not None:
        y_obs = np.array([y_obs[i] for i in idx_comp if i < len(y_obs)])
        y_model = np.array([y_model[i] for i in idx_comp if i < len(y_model)])
        vi = np.array([vi[i] for i in idx_comp if i < len(vi)])
        
    if a != 0:
        vmax = np.max(vi)
        wi = 1 + a * vi**2/vmax**2
    else:
        wi = np.ones(vi.shape)
    range_y = max(y_obs) - min(y_obs)
    return np.sqrt(np.sum(wi*(y_obs - y_model)**2) / np.sum(wi)) / range_y

def global_optimization(args_dict, bias=False):
    bounds = make_bounds(
        args_dict['tau_length'], 
        args_dict['optimization_dict']
        )
    return direct(objective, bounds, args=(args_dict,),
                    locally_biased=bias)

def iterative_optimization(args_dict, x0, patience, 
                           method='nelder-mead',
                           verbosity=True, tol=1e-4):
    optimal_cost = objective(x0, args_dict)
    optimal_x = [x for x in x0]
    if verbosity:
        print('Initialization. Cost:', optimal_cost, flush=True)
    remaining = patience * 1
    start = True 
    while remaining > 0 or start:
        results = local_optimization(args_dict, x0, method=method)
        if results['fun'] - optimal_cost < -tol:
            optimal_cost = results['fun']
            optimal_x = results['x']
            remaining = patience * 1            
        else:
            remaining -= 1
            if results['fun'] < optimal_cost:
                optimal_cost = results['fun']
                optimal_x = results['x']
        x0 = (np.array(optimal_x) * (1 + 0.05*np.random.randn(len(x0)))).tolist()
        start = False
        if verbosity:
            print('Patience ' + str(remaining) + '/' + str(patience) + 
                  '. Cost: ' + str(optimal_cost) + '. Last cost: ' +
                  str(results['fun']), flush=True)

    return optimal_x, optimal_cost        

def local_optimization(args_dict, x0, method='nelder-mead'):
    bounds = make_bounds(
        args_dict['tau_length'], 
        args_dict['optimization_dict'], 
        x0, 
        args_dict['dx'],
        args_dict['dt']
        )
    return minimize(objective, x0, bounds=bounds, args=(args_dict,),
                    method=method)
    
def make_bounds(tau_length, optimization_dict, x0, dx, dt):
    bounds = ()
    x_idx = 0
    for l in tau_length:
        if optimization_dict['initial position']:
            bounds += ((x0[x_idx] - dx, x0[x_idx] + dx), )
            x_idx += 1
        if optimization_dict['offset target']:
            for _ in range(l):
                bounds += ((x0[x_idx] - dx, x0[x_idx] + dx), )
                x_idx += 1
        if optimization_dict['k']:
            bounds += ((0, 1), ) * l
            x_idx += l
        if optimization_dict['duration']:
            for _ in range(l):
                bounds += ((x0[x_idx] - dt, x0[x_idx] + dt), )
                x_idx += 1   
    return bounds

def matrix_to_solution_vector(tau_matrix, initial_position, 
                              tau_length, optimization_dict):

    x = []
    for l, t, i in zip(tau_length, tau_matrix, initial_position):
        if optimization_dict['initial position']:
            x.append(i[0])
        if optimization_dict['offset target']:
            x += t[:l, 0].tolist()
        if optimization_dict['k']:
            x += t[:l, 1].tolist()
        if optimization_dict['duration']:
            x += t[:l, 2].tolist()
    return np.array(x).tolist()

def objective(x, *args):
    
    args_dict = args[0]
    new_matrix, new_y0 = solution_vector_to_matrix(
        x, 
        args_dict['tau_matrix'], 
        args_dict['initial_position'], 
        args_dict['tau_length'], 
        args_dict['optimization_dict'],        
        )

    idx_end = len(args_dict['reference'])    
    
    y_pred = args_dict['tau_model']((new_matrix, new_y0)).numpy().squeeze()[:idx_end]
    return cost_function_velocity(args_dict['reference'], y_pred, 
                                  idx_comp=None, 
                                  sr=args_dict['sampling_rate'],
                                  a=args_dict['velocity weight'])
 
def solution_vector_to_matrix(x, tau_matrix, initial_position, 
                              tau_length, optimization_dict):
    new_matrix = tau_matrix.copy()
    new_initial_position = initial_position.copy()

    x_idx = 0

    for n, l in enumerate(tau_length):
        l = tau_length[n]
        if optimization_dict['initial position']:
            new_initial_position[n] = x[x_idx]
            x_idx += 1
        if optimization_dict['offset target']:
            new_matrix[n, :l, 0] = x[x_idx:x_idx+l]
            x_idx += l
        if optimization_dict['k']:
            new_matrix[n, :l, 1] = x[x_idx:x_idx+l]
            x_idx += l
        if optimization_dict['duration']:
            new_matrix[n, :l, 2] = x[x_idx:x_idx+l]
            x_idx += l
    return new_matrix, new_initial_position