key_map = {
    'Heater width': lambda x: {
        'heater_fluxmeter_width': x[0],
        'peltier_fluxmeter_width': x[0],
        'heater_fluxmeter_width_error': x[1],
        'peltier_fluxmeter_width_error': x[1]
    },
    'Heater thickness': lambda x: {
        'heater_fluxmeter_thickness': x[0],
        'peltier_fluxmeter_thickness': x[0],
        'heater_fluxmeter_thickness_error': x[1],
        'peltier_fluxmeter_thickness_error': x[1]
    },
    '# Temperature inputs': lambda x: {
        'experiment_name': x.split()[4:],
        'string_for_datacard': x.replace("Temperature inputs", "Output datacard"),
        'experiment_name_string': x.replace("# ", "")
    },
    '# Experiment conducted on': lambda x: {
        'date_experiment': x.replace("# ", "")
    },
    'Heater Distances': lambda x: {'vec_position_hfluxm_therm': array('f', x)},
    'HD Errors': lambda x: {'vec_position_hfluxm_therm_error': array('f', x)},
    'Heater Temperatures': lambda x: {
        'vec_temperature_hfluxm_therm': array('f', x - vec_numpy_heater_bias)
    },
    'HT Errors': lambda x: {'vec_temperature_hfluxm_therm_error': array('f', x)},
    'Heater Temperature differences': lambda x: {
        'vec_temperature_diff_hfluxm_therm': array('f', x - vec_numpy_heater_bias + vec_numpy_heater_bias[0])
    },
    'HTD Errors': lambda x: {'vec_temperature_diff_hfluxm_therm_error': array('f', x)},
    'Peltier Distances': lambda x: {'vec_position_pfluxm_therm': array('f', x)},
    'PD Errors': lambda x: {'vec_position_pfluxm_therm_error': array('f', x)},
    'Peltier Temperatures': lambda x: {
        'vec_temperature_pfluxm_therm': array('f', x - vec_numpy_peltier_bias)
    },
    'PT Errors': lambda x: {'vec_temperature_pfluxm_therm_error': array('f', x)},
    'Peltier Temperature differences': lambda x: {
        'vec_temperature_diff_pfluxm_therm': array('f', x - vec_numpy_peltier_bias + vec_numpy_peltier_bias[0])
    },
    'PTD Errors': lambda x: {'vec_temperature_diff_pfluxm_therm_error': array('f', x)}
}