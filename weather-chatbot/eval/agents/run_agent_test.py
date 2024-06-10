import argparse
import glob
import os
from eval.library.utils.aml_utils import connect_to_aml
from eval.library.inner_loop.mlflow_helpers.core.run_mlflow_experiment import (
    run_mlflow_experiment)
from eval.agents.location.LocationExtractor.mlflow_experiment import LocationExtractorAgent
from eval.agents.location.LocationAssistant.mlflow_experiment import LocationAssistantAgent
from eval.agents.weather.WeatherExtractor.mlflow_experiment import WeatherExtractorAgent
from eval.agents.weather.WeatherAssistant.mlflow_experiment import WeatherAssistantAgent




class AgentTest:
    """
    Class to run an inner loop test of a POS agent or subagent as an MLflow experiment.
    Each agent and/or subagent has its own wrapper object used to invoke the test.
    """
    def __init__(self, agent_type, agent_name, test_data, output_folder):
        self.agent_type = agent_type
        self.agent_name = agent_name
        self.test_data = test_data
        self.output_folder = f'{output_folder}/{agent_type}/{agent_name}'
        self.all_paths = []
        if '*' in test_data:
            self.all_paths.extend(glob.glob(
                f"eval/agents/{agent_type}/{agent_name}/test-data/**", recursive=True))
            self.all_paths = [path for path in self.all_paths if os.path.isfile(path)]
        else:
            for data in test_data:
                full_path = f"eval/agents/{agent_type}/{agent_name}/test-data/{data}"
                self.all_paths.append(full_path)

    def get_wrapper(self):
        if self.agent_name == 'LocationExtractor':
            return LocationExtractorAgent()
        elif self.agent_name == 'LocationAssistant':
            return LocationAssistantAgent()
        elif self.agent_name == 'WeatherExtractor':
            return WeatherExtractorAgent()
        elif self.agent_name == 'WeatherAssistant':
            return WeatherAssistantAgent()

    def run_experiment(self):
        run_mlflow_experiment(self.get_wrapper(), self.all_paths,
                              output_folder=self.output_folder)

    @classmethod
    def from_args(cls, args):
        agent_type = args.agent_type
        agent_name = args.agent_name
        test_data = args.test_data
        output_folder = args.output_folder
        return cls(agent_type, agent_name, test_data, output_folder)


def main():
    parser = argparse.ArgumentParser(
        description='Run an inner loop test of a POS agent or subagent as an MLflow experiment.')
    parser.add_argument('--agent_type', type=str, required=True, help='Type of agent being tested')
    parser.add_argument('--agent_name', type=str, required=True, help='Name of agent being tested')
    parser.add_argument('--test_data',
                        nargs='+',
                        required=True,
                        help='Test data folder(s) or file(s) (make sure either exist under test-data \
                            folder of your agent). Can include multiple files, multiple subdirectories, \
                                a file + subdirectory, a file')
    parser.add_argument('--output_folder', type=str, required=False, default='eval/agents', help='Name of folder being outputed in aml')

    cli_args = parser.parse_args()
    connect_to_aml()
    agent_test = AgentTest.from_args(args=cli_args)
    agent_test.run_experiment()


if __name__ == "__main__":
    main()
