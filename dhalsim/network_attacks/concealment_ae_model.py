from adversarial_AE import Adversarial_AE
import time
from tensorflow.keras.models import Model, load_model
import os

import numpy as np
import pandas as pd
from str2bool import str2bool

import glob


class ConcealmentAE:

    def preprocess_physical(self, path):
        a_pd = pd.read_csv(path + '/scada_values.csv', parse_dates=['timestamp'])
        a_pd = a_pd.dropna()

        # We drop rows with Bad input values
        for column in a_pd.columns:
            a_pd = a_pd.drop(a_pd[a_pd[column] == 'Bad Input'].index)

        alarms = [col for col in a_pd.columns if 'AL' in col]

        for alarm in alarms:
            exp = (a_pd[alarm] == 'Inactive')
            a_pd.loc[exp, alarm] = 0

            exp = (a_pd[alarm] == 'Active')
            a_pd.loc[exp, alarm] = 1

        return a_pd

    def train_model(self):

        # Adversarial model for concealment
        # toDo: Ask about this parameter
        hide_layers = 128

        sensor_cols = [col for col in self.physical_pd .columns if
                       col not in ['Unnamed: 0', 'iteration', 'timestamp', 'Attack']]

        self.advAE = Adversarial_AE(len(sensor_cols), hide_layers)

        self.advAE.attacker_scaler = self.advAE.attacker_scaler.fit(self.physical_pd[sensor_cols])

        self.advAE.train_advAE(self.physical_pd, sensor_cols)
        self.advAE.generator.save('adversarial_models/generator_100_percent.h5')

    def __init__(self, training_path):
        ### Load and preprocess training data
        #data_path = '../../ideal_conditions/batch_custom_ideal/output/'
        file_expr = training_path + '*'
        paths = glob.glob(file_expr)

        self.physical_pd = None
        for path in paths:
            aux = self.preprocess_physical(path)
            self.physical_pd  = pd.concat([self.physical_pd , aux])

        if 'Unnamed: 0' in self.physical_pd .columns:
            self.physical_pd  = self.physical_pd .drop(columns=['Unnamed: 0'])
        if 'ATTACK' in self.physical_pd .columns:
            self.physical_pd  = self.physical_pd .drop(columns=['ATTACK'])