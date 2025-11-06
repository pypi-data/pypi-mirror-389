# -*- coding: utf-8 -*-
"""
Created on Mon Jul  7 18:49:56 2025

@author: belie
"""

import tauspeech
import tensorflow as tf
from tensorflow.keras import layers, Model


def compute_tau_movements(ks, initial_positions, final_positions,
                          onsets, offsets, tvecs):
    
    durations = tf.cast(tf.subtract(offsets, onsets), dtype=tf.float32) 
    nb_segs = tf.shape(tvecs)[1]
    Ts = tf.cast(expand_tensor(durations, nb_segs), dtype=tf.float32)
    Ts = tf.where(Ts!=0, Ts, 1e-11*tf.ones_like(Ts))
    ks = tf.cast(expand_tensor(ks, nb_segs), dtype=tf.float32)
    initial_positions = expand_tensor(initial_positions, tvecs.shape[1])
    final_positions = expand_tensor(final_positions, tvecs.shape[1])
    T_div = tf.divide(tvecs, Ts)
    t_ratio = 1 - tf.square(T_div)
    f = tf.ones(tf.shape(t_ratio)).numpy()
    f[tvecs < 0] = 0
    f[T_div > 1] = 0
    f[ks < 0] = 0
    f[ks > 1] = 0
    t_ratio = tf.multiply(f, t_ratio)
    amplitude = tf.cast(tf.subtract(initial_positions, final_positions), 
                        dtype=tf.float32)   
    ampl_pow = tf.multiply(amplitude, tf.cast(tf.pow(t_ratio, 1/ks), dtype=tf.float32))
    return tf.multiply(tf.convert_to_tensor(f, dtype=tf.float32), 
                       ampl_pow + final_positions)

def create_tau_model(nb_movements, sr=200, sequence_length=1):
    
    pos_input = layers.Input(shape=(1,))
    tau_input = layers.Input(shape=(nb_movements, 3))
    tau_system = TauLayer(
        sr=sr, 
        order="concat", 
        time_step=int(nb_movements*sequence_length*sr) + 1,
        )(tau_input, pos_input)
  
    return Model([tau_input, pos_input], tau_system, 
                      name="Tau Trajectory Generator")    

def expand_tensor(x, b):
    return tf.reshape(x, (-1, 1)) + tf.zeros((1, b), dtype=tf.float32)

def fit_traj(y, sampling_rate, sigma=0, lower_bound=0, upper_bound=-1):
    Traj = tauspeech.create_trajectory(y, sampling_rate)
    Traj.fit_trajectory(sigma=sigma)
    return Traj

def param2mov(target_positions, ks, durs, time_step, sr):
    
    total_duration = tf.cast(tf.reduce_sum(durs, axis=-1), dtype=tf.float32)
    nb_points = tf.cast(tf.squeeze((total_duration*sr) + 1), dtype=tf.int32)  
    time_vector = tf.linspace(tf.zeros(shape=tf.shape(total_duration)), 
                              total_duration, nb_points)
   
    onsets = tf.concat((tf.zeros(1, dtype=tf.float32), 
                        tf.cast(tf.cumsum(durs[:-1]), 
                       dtype=tf.float32)), axis=-1)
    offsets = onsets + tf.cast(durs, dtype=tf.float32)
    tf_time = tf.cast(tf.reshape(time_vector, (-1, 1)), dtype=tf.float32)
    tf_onset = tf.cast(tf.reshape(onsets, (1, -1)), dtype=tf.float32)
    tvecs = tf.transpose(tf.subtract(tf_time,tf_onset))
    
    trajs = compute_tau_movements(
                                ks,
                                target_positions[:-1], 
                                target_positions[1:],
                                onsets,
                                offsets, 
                                tvecs
                                )
    trajs = tf.convert_to_tensor(trajs, dtype=tf.float32)  
    nb_ele = tf.cast(tf.math.count_nonzero(trajs!=0, axis=0, keepdims=True),
                     dtype=tf.float32)    
    nb_ele = tf.where(nb_ele!=0, nb_ele, tf.ones_like(nb_ele))
    trajs_sum = tf.experimental.numpy.nansum(trajs, axis=0)
    trajectory = tf.transpose(tf.divide(trajs_sum, nb_ele))
    
    time_step = time_step.numpy()    
    traj_len = tf.shape(trajectory)[0].numpy()
    if traj_len < time_step:
        padding = tf.constant([[0, time_step - traj_len], [0, 0]])
        return tf.squeeze(tf.pad(trajectory, 
                                 padding, 
                                 constant_values=trajectory[-1][0]))
    else:
        return tf.squeeze(trajectory[:time_step, :])

def sequential_tau(args):
    tau_parameters, sr, time_step, commands = args

    opt_positions = tf.gather(tau_parameters, indices=0, axis=-1)
    target_positions =  tf.concat((tf.reshape(commands, 1), 
                                   opt_positions), axis=0)
    ks = tf.gather(tau_parameters, indices=1, axis=-1)
    durs = tf.gather(tau_parameters, indices=2, axis=-1)
    
    return param2mov(target_positions, ks, durs, time_step, sr)

# @keras.saving.register_keras_serializable
class TauLayer(layers.Layer):  
    def __init__(self, sr=200, order="concat", time_step=302, **kwargs):
        super().__init__(**kwargs)
        # super(TauLayer, self).__init__()
        self.sr = sr
        self.order = order
        self.time_step = time_step

    def get_config(self):
        config = super(TauLayer, self).get_config()
        config.update({
            "sr": self.sr,
            "order": self.order,
            "time_step": self.time_step,
            })
        return config    
  
    def call(self, inputs, commands):      
        inputs, commands = [tf.cast(i, dtype=tf.float32) for
                            i in (inputs, commands)]   
        sr = tf.cast(tf.reshape(tf.repeat(self.sr, 
                                          tf.shape(inputs)[0], axis=-1), 
                                        (-1,)), dtype=tf.float32)
        time_step = tf.cast(tf.reshape(tf.repeat(self.time_step, 
                                          tf.shape(inputs)[0], axis=-1), 
                                        (-1,)), dtype=tf.int32)          
    
        return tf.map_fn( 
                        sequential_tau,
                        elems=(inputs, sr, time_step, 
                               commands),
                        dtype=(tf.float32, tf.float32, tf.float32,
                               tf.float32),
                        fn_output_signature=tf.float32
                        )

    def compute_output_shape(self, input_shape):
        return (None, input_shape[1], int(input_shape[-1]/3))  