#Python modules used by the code
from ROOT import TFile, TCanvas, TH2D, TH1D, TLegend, gStyle, TGraph, TF1, TGraphAsymmErrors, TMath, TStyle, TPaveText, TLatex, TPaveLabel, TPad, TLine, TText
import numpy as np,re,math 
from array import array
from ROOT import kBlack, kBlue, kRed,kGreen,kYellow,kViolet
import key_map_inputs

class ThermalResistanceAnalyzer:
    def __init__(self, file_location: str, consider_heatloss: bool) -> None:
        """
        Initialize the analyzer.

        Args:
            file_location (str): Path to the directory containing input files.
            consider_heatloss (bool): Flag indicating whether to consider heat loss.
        """
        self.file_location = file_location
        self.metaslope_input_location = self.file_location.split('/')[0] + '/'
        self.consider_heatloss = consider_heatloss
        self.input_parameters = {}
        self.temperature_data = {}
        self.fit_results = {}
        self.flux_calculations = {}
        self.copper_conductivity = 355.0
        self.thermistor_diameter = 0.00127

    @staticmethod
    def error_in_quadrature( *args: float) -> float:
        """
        Calculate error in quadrature.

        Args:
            *args: Variable number of error values.

        Returns:
            float: Quadrature error.
        """
        return math.sqrt(sum([x**2 for x in args]))
    
    def read_input_files(self):
        """
        Read input parameters from files.
        """
        try:
            with open(self.file_location + 'Input_parameters.txt', 'r') as par_file:
                input_parameters_key_map = {
                    'Heat power error from ANSYS': lambda x: ('heat_loss_ratio_fea', array('f', np.float_(re.findall(r"[-+]?\d*\.\d+|\d+", x))[0] if consider_heatloss else 0)),

                }

                for line in par_file:
                    for prefix, func in input_parameters_key_map.items():
                        if line.startswith(prefix):
                            key, value = func(line)
                            self.input_parameters[key] = value


            with open(file_location + 'Input_temperatures.txt', 'r') as tem_file:
                for line in tem_file:
                    for prefix, func in key_map.items():
                        if line.startswith(prefix):
                            try:
                                values = func(np.float_(re.findall(r"[-+]?\d*\.\d+|\d+", line)))
                            except ValueError:
                                print(f"Error: Unable to parse values from line: {line}")
                            for key, value in values.items():
                                self.input_parameters[key] = value
        except FileNotFoundError:
            print(f"Error: Input file not found at {self.file_location}")
        except IOError:
            print("Error: Unable to read input files")

    def plot_thermistor_fits(self):
        """
        Plot thermistor linear fits to calculate heat fluxes.
        """
        vec_position_hfluxm_therm_error = vec_position_pfluxm_therm_error = array('f', [self.thermistor_diameter]*6)

        fits = [
            {"name": "Heater", "x": self.input_parameters['vec_position_hfluxm_therm'], "y": self.input_parameters['vec_temperature_hfluxm_therm'], "y_err": self.input_parameters['vec_temperature_hfluxm_therm_error'], "filename": "heater_flux", "par_limits": [(0.1, 50.0), (-50, -30)]},
            {"name": "Peltier", "x": self.input_parameters['vec_position_pfluxm_therm'], "y": self.input_parameters['vec_temperature_pfluxm_therm'], "y_err": self.input_parameters['vec_temperature_pfluxm_therm_error'], "filename": "peltier_flux", "par_limits": [(0.0, 30.1545), (-50, -30)]},
            {"name": "Heater Difference", "x": self.input_parameters['vec_position_hfluxm_therm'], "y": self.input_parameters['vec_temperature_diff_hfluxm_therm'], "y_err": self.input_parameters['vec_temperature_diff_hfluxm_therm_error'], "filename": "heater_difference_flux", "par_limits": [(-0.1, 0.1), (-50, -30)]},
            {"name": "Peltier Difference", "x": self.input_parameters['vec_position_pfluxm_therm'], "y": self.input_parameters['vec_temperature_diff_pfluxm_therm'], "y_err": self.input_parameters['vec_temperature_diff_pfluxm_therm_error'], "filename": "peltier_difference_flux", "par_limits": [(-0.1, 0.1), (-50, -30)]}
        ]

        for fit in fits:
            c = TCanvas(f"{fit['name']}_temp", f"{fit['name']}_temp", 2000, 2000)
            gr = TGraphAsymmErrors(6, fit['x'], fit['y'], vec_position_hfluxm_therm_error, vec_position_pfluxm_therm_error, fit['y_err'], fit['y_err'])
            gr.SetTitle("; Thermistor position (m); Thermistor temperature [^{#circ}C]")
            f = TF1(f"{fit['name']}_fit", "[0]+[1]*x",-0.005,0.045)
            
            f.SetParLimits(0, fit['par_limits'][0][0], fit['par_limits'][0][1])
            f.SetParLimits(1, fit['par_limits'][1][0], fit['par_limits'][1][1])
            
            gr.GetXaxis().SetLimits(-0.005,0.045)
            f.SetLineColor(kBlack)
            gr.Fit(f, "R+")
            gr.Draw("ap*")
            save_plot(c, self.file_location, fit['filename'])

    def calculate_flux_and_temperatures(self):
        """
        Calculate flux and temperatures.
        """
        try:
            # Heater flux calculation
            self.flux_calculations['heater_flux'] = -self.copper_conductivity * self.fit_results['heater_flux'].GetParameter(1)

            # Peltier flux calculation
            self.flux_calculations['peltier_flux'] = -self.copper_conductivity * self.fit_results['peltier_flux'].GetParameter(1)

            # Average flux calculation
            self.flux_calculations['average_flux'] = (self.flux_calculations['heater_flux'] + self.flux_calculations['peltier_flux']) / 2.0
            #Temperature extrapolations from the linear fits.
            self.flux_calculations['hot_end_tempeature'] = float(self.fit_results['heater_flux'].GetParameter(0)+(self.fit_results['heater_flux'].GetParameter(1))*0.048)
            self.flux_calculations['cold_end_tempeature'] = float(self.fit_results['peltier_flux'].GetParameter(0)+(self.fit_results['peltier_flux'].GetParameter(1)*-0.008))
            self.flux_calculations['deltaT'] = self.flux_calculations['hot_end_tempeature'] - self.flux_calculations['cold_end_tempeature']
        except ValueError:
            print(f"Error: Unable to calculate flux since fit parameters are not stable.")

    def calculate_flux_errors(self):
        """
        Calculate errors.
        """
        try:

            #Uncertainties/errors associated with thermal flux measurement
            self.flux_calculations['flux_loss_error'] = self.flux_calculations['average_flux'] * self.input_parameters['Heat power error from ANSYS']
            self.flux_calculations['flux_imbalance_error'] = float(abs((self.flux_calculations['heater_flux'] - self.flux_calculations['peltier_flux'])/2.0))
            self.flux_calculations['flux_error'] = analyzer.error_in_quadrature(self.flux_calculations['flux_loss_error'],self.flux_calculations['flux_imbalance_error'] )
        except ValueError:
            print(f"Error: Unable to calculate flux errors since fit parameters are not stable.")

    def write_output(self):
        """
        Write output data to files.
        """
        try:
            with open(self.file_location + 'Output_datacard.txt', 'w') as output_file:
                output_file.write("Thermal Resistance Analysis Results:\n")
                output_file.write(f"Heater Flux: {self.flux_calculations['heater_flux']} +/- {self.flux_calculations['heater_flux_error']}\n")
                output_file.write(f"Peltier Flux: {self.flux_calculations['peltier_flux']} +/- {self.flux_calculations['peltier_flux_error']}\n")
                output_file.write(f"Average Flux: {self.flux_calculations['average_flux']} +/- {self.flux_calculations['average_flux_error']}\n")
        except FileNotFoundError:
            print(f"Error: Not able to create/open Output file at {self.file_location}")
        except IOError:
            print("Error: Unable to read input files")
    def analyze_thermal_resistance(self):
        self.read_input_files()
        self.plot_thermistor_fits()
        self.calculate_flux_and_temperatures()
        self.calculate_flux_errors()
        self.write_output()

def analyze_single_sample(file_location, bool_hl):
    analyzer = ThermalResistanceAnalyzer(file_location, bool_hl)
    analyzer.analyze_thermal_resistance()


def analyze_multiple_samples(file_locations):
    for file_location in file_locations:
        print(f"Analyzing sample: {file_location}")
        analyze_single_sample(file_location, True)

if __name__ == "__main__":
    sample_groups = [
        ["INPL17/INPL17_5/"],
        ["INPL2/INPL2_1/", "INPL2/INPL2_2/", "INPL2/INPL2_3/", "INPL2/INPL2_4/", "INPL2/INPL2_5/"],
        ["INPL3/INPL3_1/", "INPL3/INPL3_2/", "INPL3/INPL3_3/", "INPL3/INPL3_4/", "INPL3/INPL3_5/"],
        ["INPL4/INPL4_2/", "INPL4/INPL4_3/", "INPL4/INPL4_4/", "INPL4/INPL4_5/"],
        ["INPL9/INPL9_1/", "INPL9/INPL9_2/", "INPL9/INPL9_3/", "INPL9/INPL9_4/", "INPL9/INPL9_5/"],
        ["INPL10/INPL10_1/", "INPL10/INPL10_2/", "INPL10/INPL10_3/", "INPL10/INPL10_4/", "INPL10/INPL10_5/"],
        ["INPL11/INPL11_1/", "INPL11/INPL11_3/", "INPL11/INPL11_4/", "INPL11/INPL11_5/"],
        ["INPL12/INPL12_1/", "INPL12/INPL12_2/", "INPL12/INPL12_3/", "INPL12/INPL12_4/", "INPL12/INPL12_5/"],
        ["INPL13/INPL13_1/", "INPL13/INPL13_2/", "INPL13/INPL13_3/", "INPL13/INPL13_4/", "INPL13/INPL13_5/"],
        ["INPL16/INPL16_1/", "INPL16/INPL16_2/", "INPL16/INPL16_3/", "INPL16/INPL16_4/", "INPL16/INPL16_5/"],
        ["INPL17/INPL17_1/","INPL17/INPL17_2/", "INPL17/INPL17_3/", "INPL17/INPL17_4/"],
        ["INPL21/INPL21_1/", "INPL21/INPL21_2/", "INPL21/INPL21_3/", "INPL21/INPL21_4/", "INPL21/INPL21_5/", "INPL21/INPL21_6/"],
        ["INPL21_irradiated_correct/INPL21_1/", "INPL21_irradiated_correct/INPL21_2/", "INPL21_irradiated_correct/INPL21_3/", "INPL21_irradiated_correct/INPL21_4/"],
    ]
        
    for sample_group in sample_groups:
        inplane_multiple_sample_analysis(sample_group)