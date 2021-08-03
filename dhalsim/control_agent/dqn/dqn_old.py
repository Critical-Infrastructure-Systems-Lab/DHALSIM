import pandas as pd
import yaml
import pickle
from pathlib import Path

from mushroom_rl.core import Core
from mushroom_rl.algorithms.value import DQN
from mushroom_rl.approximators.parametric import TorchApproximator
from mushroom_rl.policy import EpsGreedy
from mushroom_rl.utils.parameters import LinearParameter, Parameter
from mushroom_rl.utils.replay_memory import ReplayMemory
from mushroom_rl.utils.callbacks import CollectDataset, CollectMaxQ
from mushroom_rl.utils.dataset import compute_metrics
from torch.optim.adam import Adam
from torch.nn import functional as F

from dhalsim.control_agent.dqn.env import WaterNetworkEnvironment
from dhalsim.control_agent.dqn import nn


class DQNAgent:
    """
    Handler of the agent and the DQN mushroom_rl class
    """
    def __init__(self, agent_config_file):
        """
        Initialize of the DQN control agent.
        Create of all the data structure needed to run the algorithm, retrieving data from the agent_config_file.
        Initialize the environment.
        """
        self.agent_config_file = agent_config_file
        with self.agent_config_file.open(mode='r') as config_file:
            self.config_agent = yaml.load(config_file, Loader=yaml.FullLoader)

        self.intermediate_yaml_data = None
        self.env = None
        self.agent = None

        # Creating the epsilon greedy policy
        self.epsilon_train = LinearParameter(value=1., threshold_value=.1, n=1000000)
        self.epsilon_test = Parameter(value=.05)
        self.epsilon_random = Parameter(value=1)
        self.pi = EpsGreedy(epsilon=self.epsilon_random)

        # Create the optimizer dictionary
        self.optimizer = dict()
        self.optimizer['class'] = Adam
        self.optimizer['params'] = self.config_agent['optimizer']

        self.replay_buffer = None
        self.dataset = None
        self.core = None
        self.scores = []
        self.results = {'train': [], 'eval': []}

    def build_model(self):
        """
        Build the entire model with all the relative data structure. We have to wait the creation of the environment
        to perform this operation.
        """
        if self.config_agent['agent']['load_model']:
            current_path = Path(__file__).absolute().parent / str(self.config_agent['agent']['model_to_load'])
            self.agent = DQN.load(current_path)
        else:
            # Set parameters of neural network taken by the torch approximator
            nn_params = dict(hidden_size=self.config_agent['nn']['hidden_size'])

            # Create the approximator from the neural network we have implemented
            approximator = TorchApproximator

            # Set parameters of approximator
            approximator_params = dict(
                network=nn.NN10Layers,
                input_shape=self.env.info.observation_space.shape,
                output_shape=(self.env.info.action_space.n,),
                n_actions=self.env.info.action_space.n,
                optimizer=self.optimizer,
                loss=F.smooth_l1_loss,
                batch_size=0,
                use_cuda=False,
                **nn_params
            )

            # Build replay buffer
            #self.replay_buffer = ReplayMemory(initial_size=self.config_agent['agent']['initial_replay_memory'],
            #                                  max_size=self.config_agent['agent']['max_replay_size'])

            self.agent = DQN(mdp_info=self.env.info,
                             policy=self.pi,
                             approximator=approximator,
                             approximator_params=approximator_params,
                             batch_size=self.config_agent['agent']['batch_size'],
                             target_update_frequency=self.config_agent['agent']['target_update_frequency'],
                             replay_memory=None,
                             initial_replay_size=self.config_agent['agent']['initial_replay_memory'],
                             max_replay_size=self.config_agent['agent']['max_replay_size']
                             )

        # Callbacks
        # self.dataset = CollectDataset()
        self.core = Core(self.agent, self.env)

    def reset_environment(self, intermediate_yaml_path):
        """
        Reset the environment before the start of a new simulation, but keeps the same agent

        :param intermediate_yaml_path: path of the intermediate_yaml of the current simulation
        """
        with intermediate_yaml_path.open(mode='r') as yaml_file:
            self.intermediate_yaml_data = yaml.load(yaml_file, Loader=yaml.FullLoader)
            # TODO: add test o train in the intermediate yaml of each simul
            # self.test_simulation = self.intermediate_yaml_data['test_simulation']

        if self.env is None:
            self.env = WaterNetworkEnvironment(self.agent_config_file, intermediate_yaml_path)
            self.build_model()
        else:
            self.env.set_intermediate_yaml(intermediate_yaml_path)

        self.run()

    def run(self):
        """
        Start the control agent and the related control problem.
        """
        # Fill replay memory with random data
        if self.intermediate_yaml_data['simulation_type'] == 'buffer':
            self.fill_replay_buffer()

        elif self.intermediate_yaml_data['simulation_type'] == 'train':
            self.train()

        elif self.intermediate_yaml_data['simulation_type'] == 'test':
            if self.config_agent['save_results']:
                dsr, dataset, qs = self.evaluate()
                res = {'dsr': dsr, 'dataset': dataset, 'q_values': qs}
                self.results['eval'].append(res)
            else:
                self.evaluate()
        else:
            raise Exception("Simulation type not recognized.")

        print(">>> Total DSR: ", self.env.dsr)

        if self.config_agent['agent']['save_model']:
            where = Path(__file__).absolute().parent / 'saved_models' / str(self.config_agent['agent']['save_as'])
            self.agent.save(path=where, full_save=True)

    def fill_replay_buffer(self):
        """
        First simulations used to fill the replay buffer until its minimum size.
        """
        print(">>> Filling replay buffer...")
        self.pi.set_epsilon(self.epsilon_random)
        self.core.learn(n_episodes=1, n_steps_per_fit=self.config_agent['learning']['train_frequency'])

    def train(self):
        """
        Train the model with the current simulation.
        """
        print(">>> Start training...")
        self.pi.set_epsilon(self.epsilon_train)
        self.core.learn(n_episodes=1, n_steps_per_fit=self.config_agent['learning']['train_frequency'])

    def evaluate(self):
        """
        Evaluate the model with the current simulation and save results if needed
        """
        print(">>> Start evaluation...")
        self.pi.set_epsilon(self.epsilon_test)

        self.agent.target_approximator.model.network.collect_qs_enabled(self.config_agent['learning']['collect_qs'])
        dataset = self.core.evaluate(n_episodes=1)

        df_dataset = None
        qs_list = None

        if self.config_agent['learning']['collect_data']:
            df_dataset = pd.DataFrame(dataset, columns=['current_state', 'action', 'reward', 'next_state',
                                                        'absorbing_state', 'last_step'])

        if self.config_agent['learning']['collect_qs']:
            qs_list = self.agent.target_approximator.model.network.retrieve_qs()
            self.agent.target_approximator.model.network.collect_qs_enabled(False)

        return self.env.dsr, df_dataset, qs_list

    def get_stats(self, dataset):
        """
        Compute metrics scores.
        """
        score = compute_metrics(dataset)
        print('min_reward: {}, max_reward: {}, mean_reward: {}, games_completed: {}'.format(
            score[0], score[1], score[2], score[3]))
        self.scores.append(score)

    def save_results(self):
        """
        Save results: dataset and q_values.
        TODO: create folder
        """
        output_file = Path(self.intermediate_yaml_data['output_path']).parent / 'control_results'
        with open(output_file, 'wb') as fp:
            pickle.dump(self.results, fp)
        print(self.results)
