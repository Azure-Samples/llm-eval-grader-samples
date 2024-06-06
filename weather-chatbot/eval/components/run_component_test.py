import argparse
import glob
import os
from eval.library.utils.aml_utils import connect_to_aml
from eval.library.inner_loop.mlflow_helpers.core.run_mlflow_experiment import (
    run_mlflow_experiment)
from eval.components.location.LocationExtractor.mlflow_experiment import LocationExtractorComponent
from eval.components.location.LocationAssistant.mlflow_experiment import LocationAssistantComponent
from eval.components.weather.WeatherExtractor.mlflow_experiment import WeatherExtractorComponent




class ComponentTest:
    """
    Class to run an inner loop test of a POS component or subcomponent as an MLflow experiment.
    Each component and/or subcomponent has its own wrapper object used to invoke the test.
    """
    def __init__(self, component_type, component_name, test_data, output_folder):
        self.component_type = component_type
        self.component_name = component_name
        self.test_data = test_data
        self.output_folder = f'{output_folder}/{component_type}/{component_name}'
        self.all_paths = []
        if '*' in test_data:
            self.all_paths.extend(glob.glob(
                f"eval/components/{component_type}/{component_name}/test-data/**", recursive=True))
            self.all_paths = [path for path in self.all_paths if os.path.isfile(path)]
        else:
            for data in test_data:
                full_path = f"eval/components/{component_type}/{component_name}/test-data/{data}"
                self.all_paths.append(full_path)

    def get_wrapper(self):
        if self.component_name == 'LocationExtractor':
            return LocationExtractorComponent()
        elif self.component_name == 'LocationAssistant':
            return LocationAssistantComponent()
        elif self.component_name == 'WeatherExtractor':
            return WeatherExtractorComponent()

    def run_experiment(self):
        run_mlflow_experiment(self.get_wrapper(), self.all_paths,
                              output_folder=self.output_folder)

    @classmethod
    def from_args(cls, args):
        component_type = args.component_type
        component_name = args.component_name
        test_data = args.test_data
        output_folder = args.output_folder
        return cls(component_type, component_name, test_data, output_folder)


def main():
    parser = argparse.ArgumentParser(
        description='Run an inner loop test of a POS component or subcomponent as an MLflow experiment.')
    parser.add_argument('--component_type', type=str, required=True, help='Type of component being tested')
    parser.add_argument('--component_name', type=str, required=True, help='Name of component being tested')
    parser.add_argument('--test_data',
                        nargs='+',
                        required=True,
                        help='Test data folder(s) or file(s) (make sure either exist under test-data \
                            folder of your component). Can include multiple files, multiple subdirectories, \
                                a file + subdirectory, a file')
    parser.add_argument('--output_folder', type=str, required=False, default='eval/components', help='Name of folder being outputed in aml')

    cli_args = parser.parse_args()
    connect_to_aml()
    component_test = ComponentTest.from_args(args=cli_args)
    component_test.run_experiment()


if __name__ == "__main__":
    main()
