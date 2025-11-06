# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 10:07:17 2025

@author: belie
"""

import numpy as np
import tauspeech
from tqdm import tqdm
from ._tau import ( 
    create_tau_model,    
    )
from ._optimization import ( 
    iterative_optimization,
    matrix_to_solution_vector,
    solution_vector_to_matrix
    )

def extract_tau_matrix(y, sr, sigma=0, velocity_weight=5):
    
    Traj = tauspeech.create_trajectory(y, sr)
    Traj.fit_trajectory(sigma=sigma, a=velocity_weight)

    pts_x = np.array([k for k in Traj.parameters.target]).reshape(-1, 1)
    T_x = np.array([k for k in Traj.parameters.duration]).reshape(-1, 1)
    ks_x = np.array([k if k is not None else 0.4 for k in Traj.parameters.shape]).reshape(-1, 1)         

    tau_matrix = np.expand_dims( 
        np.hstack((pts_x, ks_x, T_x)),
        axis=0
        )
    return tau_matrix, Traj.filtered_signal

def fine_fit(y, sr, N_max=None, N_min=1, sigma=0, velocity_weight=5, patience=5, tol=1e-4,
             dx=3, dt=0.1, verbosity=False):
    
    tau_matrix, y_ref = extract_tau_matrix(
        y, 
        sr, 
        sigma=sigma, 
        velocity_weight=velocity_weight
        )

    initial_position = np.array(y_ref[0]).reshape(1, 1)
    
    optimization_dict = {
        'initial position': True, 
        'offset target': True, 
        'k': True, 
        'duration': True
        }
    
    tau_matrices = []
    initial_positions = []
    tau_movements = []
    costs = []
    nb_movs = []
    
    if N_max is None:
        tau_model = create_tau_model(
            tau_matrix.shape[1], 
            sr=sr, 
            sequence_length=1
            )
        optim_x, cost = local_fine_fit(
            tau_matrix, initial_position, optimization_dict, 
            tau_model, sr, y_ref, velocity_weight, dx, dt, patience, 
            verbosity, tol 
            )
        
        best_tau_matrix, best_y0 = solution_vector_to_matrix(
            optim_x, 
            tau_matrix, 
            initial_position, 
            [tau_matrix.shape[1]],
            optimization_dict
            )
        tau_movement = tau_model(
            (best_tau_matrix, best_y0)
            ).numpy().squeeze()[:len(y_ref)]
        return best_tau_matrix, best_y0, cost, tau_movement, tau_matrix.shape[1]
    
    else:
      
        for n in tqdm(range(N_min, N_max+1)):
            
            new_tau_matrix = refine_tau_matrix(tau_matrix, n) 
            tau_model = create_tau_model(
                new_tau_matrix.shape[1], 
                sr=sr, 
                sequence_length=1
                )    
            optim_x, cost = local_fine_fit(
                new_tau_matrix, initial_position, optimization_dict, 
                tau_model, sr, y_ref, velocity_weight, dx, dt, patience, 
                verbosity, tol 
                )
            
            best_tau_matrix, best_y0 = solution_vector_to_matrix(
                optim_x, 
                new_tau_matrix, 
                initial_position, 
                [new_tau_matrix.shape[1]],
                optimization_dict
                )
            
            tau_matrices.append(best_tau_matrix)
            initial_positions.append(best_y0)
            costs.append(cost)
            tau_movements.append(tau_model((best_tau_matrix, best_y0)).numpy().squeeze()[:len(y_ref)])
            nb_movs.append(n)
                
        return tau_matrices, initial_positions, costs, tau_movements, nb_movs

def local_fine_fit(local_tau_matrix, initial_position, optimization_dict, 
                   tau_model, sr, y_ref, velocity_weight, dx, dt, patience, 
                   verbosity, tol):
       
    x0 = matrix_to_solution_vector(
        local_tau_matrix, 
        initial_position, 
        [local_tau_matrix.shape[1]],
        optimization_dict
        )

    args_dict = {
        'tau_matrix': local_tau_matrix,
        'initial_position': initial_position,
        'tau_length': [local_tau_matrix.shape[1]],
        'optimization_dict': optimization_dict,
        'tau_model': tau_model,
        'sampling_rate': sr,  
        'reference': y_ref,
        'velocity weight': velocity_weight,
        'dx': dx,
        'dt': dt
              }

    return iterative_optimization(
        args_dict, 
        x0, 
        patience=patience, 
        method='nelder-mead',
        verbosity=verbosity,                                     
        tol=tol
        )

    
    
    return sol_mtx, sol_y0, tau_model, cost
    
def refine_tau_matrix(tau_matrix, nb_movements):
    old_n = tau_matrix.shape[1]
    if nb_movements > old_n:
        new_tau_matrix = np.concat(
            (
                tau_matrix, 
                0.05*np.ones((tau_matrix.shape[0], nb_movements - old_n, 3))
            ),
            axis=1
        )
        new_tau_matrix[:, old_n:, 1] = 0.4
    elif nb_movements == 1:
        new_tau_matrix = np.array(
            [tau_matrix[0, -1, 0], 0.4, np.sum(tau_matrix[0, :, -1])]
            ).reshape(-1, 1, 3)
    else:
        new_tau_matrix = tau_matrix.copy()        
        while new_tau_matrix.shape[1] > nb_movements:
            duration = new_tau_matrix[:, :, -1].squeeze()
            n = np.argsort(duration)[0]
            if n == 0:
                new_tau_matrix[:, 1, 2] += new_tau_matrix[:, 0, 2]
            else:
                new_tau_matrix[:, n-1, 0] = new_tau_matrix[:, n, 0]
                new_tau_matrix[:, n-1, 2] += new_tau_matrix[:, n, 2]
            new_tau_matrix = np.delete(new_tau_matrix, n, axis=1)
    return new_tau_matrix
                
                
            
            
