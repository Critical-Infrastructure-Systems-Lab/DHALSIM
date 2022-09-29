from adversarial_AE import Adversarial_AE
import time

from tensorflow.keras.layers import Input, Dense, Activation, BatchNormalization, Lambda
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.initializers import glorot_normal

import os

import numpy as np
import pandas as pd
from str2bool import str2bool

import glob
from pathlib import Path

from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

# This module is based on the implementation by Alessandro Erba, original is found here:
# https://github.com/scy-phy/ICS-Evasion-Attacks/blob/master/Adversarial_Attacks/Black_Box_Attack/adversarial_AE.py

class ConcealmentAE:

    def preprocess_physical(self, path):
        a_pd = pd.read_csv(str(path), parse_dates=['timestamp'])
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

        # fit of the scaler is done at __init__
        xset = self.sensor_cols
        ben_data = self.physical_pd
        ben_data[xset] = self.attacker_scaler.transform(ben_data[xset])
        x_ben = pd.DataFrame(index=ben_data.index,
                            columns=xset, data=ben_data[xset])
        x_ben_train, x_ben_test, _, _ = train_test_split(
            x_ben, x_ben, test_size=0.33, random_state=42)
        earlyStopping = EarlyStopping(
            monitor='val_loss', patience=3, verbose=0,  min_delta=1e-4, mode='auto')
        lr_reduced = ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=1, verbose=0, min_delta=1e-4, mode='min')
        print(self.generator.summary())
        self.generator.fit(x_ben_train, x_ben_train,
                            epochs=500,
                            batch_size=64,
                            shuffle=False,
                            callbacks=[earlyStopping, lr_reduced],
                            verbose=2,
                            validation_data=(x_ben_test, x_ben_test))

    def save_model(self, filename):
        self.generator.save(filename)

    def build_generator(self):
        input = Input(shape=(self.feature_dims,))
        x = input
        for dim in self.generator_layers[1:]:
            x = Dense(dim, activation='sigmoid',
                      kernel_initializer=glorot_normal(seed=12345))(x)
        return Model(input, x, name='generator')

    def transform_fit_scaler(self):
        self.attacker_scaler.fit(self.physical_pd[self.sensor_cols])

    def fix_sample(self, gen_examples):
        # We want to select pumps and valves status only.
        list_pump_status = list(gen_examples.filter(regex='PU[0-9]+$|V[0-9]+$').columns)

        for j, _ in gen_examples.iterrows():
            for i in list_pump_status:  # list(gen_examples.columns[31:43]):
                if gen_examples.at[j, i] > 0.5:
                    gen_examples.at[j, i] = 1
                else:
                    gen_examples.at[j, i] = 0
                    #if status is 0, the flow is also 0
                    gen_examples.at[j, i+'F'] = 0  # gen_examples.columns[(
                    # gen_examples.columns.get_loc(i)) - 12]] = 0

    def predict(self, received_values_df):
        for index, row in received_values_df.iterrows():
            gen_examples = self.generator.predict(self.attacker_scaler.transform(received_values_df))
            gen_examples = self.fix_sample(pd.DataFrame(columns=self.sendor_cols,
                                                         data=self.attacker_scaler.inverse_transform(gen_examples)),
                                            dataset)
            if not os.path.exists('results/'+dataset + '/unconstrained_attack/'):
                os.makedirs(
                    'results/'+dataset + '/unconstrained_attack/')
            pd.DataFrame(columns=xset, data=gen_examples).to_csv(
                'results/'+dataset+'/unconstrained_attack/new_advAE_attack_'+str(i)+'_from_test_dataset.csv')


    def __init__(self, a_path):
        # Load and preprocess training data
        training_path = Path(__file__).parent/a_path/'training_data.csv'
        print('Reading training data from: ' + str(training_path))
        self.physical_pd = self.preprocess_physical(training_path)

        # Adversarial model for concealment
        # toDo: Ask about this parameter
        hide_layers = 128

        self.sensor_cols = [col for col in self.physical_pd.columns if
                            col not in ['Unnamed: 0', 'iteration', 'timestamp', 'Attack']]

        self.feature_dims = len(self.sensor_cols)

        self.hide_layers = hide_layers
        self.generator_layers = [self.feature_dims, int(self.hide_layers / 2), self.hide_layers,
                                 int(self.hide_layers / 2), self.feature_dims]

        optimizer = Adam(lr=0.001)
        # Build the generator
        self.generator = self.build_generator()
        self.generator.compile(optimizer=optimizer, loss='mean_squared_error')

        self.attacker_scaler = MinMaxScaler()
        self.transform_fit_scaler()



