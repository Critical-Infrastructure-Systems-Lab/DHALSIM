import time

from tensorflow.keras.layers import Input, Dense, Activation, BatchNormalization, Lambda
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.initializers import glorot_normal

from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd


# This module was developed by Alessandro Erba, the original is found here:
# https://github.com/scy-phy/ICS-Evasion-Attacks/blob/master/Adversarial_Attacks/Black_Box_Attack/adversarial_AE.py

class Adversarial_AE:
    
    def __init__(self, feature_dims, hide_layers):
        # define parameters
        self.attacker_scaler = MinMaxScaler()
        self.feature_dims = feature_dims
        self.hide_layers = hide_layers
        self.generator_layers = [self.feature_dims, int(self.hide_layers /
                                                        2), self.hide_layers, int(self.hide_layers/2), self.feature_dims]
        optimizer = Adam(lr=0.001)

        # Build the generator
        self.generator = self.build_generator()
        self.generator.compile(optimizer=optimizer, loss='mean_squared_error')

    def build_generator(self):
        input = Input(shape=(self.feature_dims,))
        x = input
        for dim in self.generator_layers[1:]:
            x = Dense(dim, activation='sigmoid',
                      kernel_initializer=glorot_normal(seed=12345))(x)
        generator = Model(input, x, name='generator')

        return generator
    
    def train_advAE(self, ben_data, xset):
        ben_data[xset] = self.attacker_scaler.transform(
            ben_data[xset])
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
        

    def fix_sample(self, gen_examples, dataset):
        """
        Adjust discrete actuators values to the nearest allowed value
        Parameters
        ----------
        gen_examples : Pandas Dataframe
            adversarial examples that needs to be adjusted
        dataset : string
            name of the dataset the data come from to select the correct strategy
        Returns
        -------
        pandas DataFrame
            adversarial examples with distrete values adjusted 
        """
        if dataset == 'BATADAL':
            list_pump_status = list(gen_examples.filter(
                regex='STATUS_PU[0-9]|STATUS_V[0-9]').columns)
            
            for j, _ in gen_examples.iterrows():
                for i in list_pump_status:  #list(gen_examples.columns[31:43]):
                    if gen_examples.at[j, i] > 0.5:
                        gen_examples.at[j, i] = 1
                    else:
                        gen_examples.at[j, i] = 0
                        gen_examples.at[j, i.replace('STATUS', 'FLOW')] = 0 #gen_examples.columns[(
                           # gen_examples.columns.get_loc(i)) - 12]] = 0

        return gen_examples

    def decide_concealment(self, n, binary_dataframe, gen_examples, original_examples, xset):
        """
        Conceal only n variables among the modified ones by the autoencoder
        computes the squared error between original and concealed sample and forward only the first n wrongly reconstructed
        Parameters
        ----------
        n : int
            number of variables to be forwarded concealed
        gen_examples : Pandas Dataframe
            concealed tuples by the autoencoder
        original_examples : Pandas Dataframe
            original tuples
        Returns
        -------
        pandas series
            concealed tuple with exactly n concealed sensor readings
        pandas DataFrame
            one hot encoded table keeping track of which of the n variables have been manipulated
        """
        for j in range(0, len(gen_examples)):
            distance = (original_examples.iloc[j] - gen_examples.iloc[j])
            distance = np.sqrt(distance**2)
            distance = distance.sort_values(ascending=False)
            distance = distance.drop(distance.index[n:])
            binary_row = pd.DataFrame(
                index=[distance.name], columns=xset, data=0)
            for elem in distance.keys():
                binary_row.loc[distance.name, elem] = 1
            binary_dataframe = binary_dataframe.append(binary_row)
            for col, _ in distance.iteritems():
                original_examples.at[j, col] = gen_examples.at[j, col]

        return original_examples.values, binary_dataframe

    def conceal_fixed(self, constraints, gen_examples, original_examples):
        """
        Conceal only n variables according to the list of allowed ones. 
        
        Parameters
        ----------
        constraints : list
            list of sensor values that can be changed
        gen_examples : Pandas Dataframe
            concealed tuples by the autoencoder
        original_examples : Pandas Dataframe
            original tuples
        Returns
        -------
        pandas series
            adversarial examples with the allowed concealed sensor readings
        """
        for j in range(0, len(gen_examples)):
            #print(constraints)
            #print(original_examples.iloc[j])
            for col in constraints:
                original_examples.at[j, col] = gen_examples.at[j, col]
            #print(original_examples.iloc[j])
        return original_examples.values