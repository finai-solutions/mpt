import os
import copy
import ast

from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
import matplotlib.pyplot as plt
import pandas as pd
import json
import numpy as np
from datetime import timedelta, datetime
import dateutil.parser

from portfolio.utils import get_write_path
from portfolio.portfolio import get_portfolio

granularity = 900
cycles= int(86400*45/granularity) # 45 days prediction second by second.
cycle_len = 60
market_cap = 10**10
start_date = '2024-01-01-00-00'
end_date = None
balance  = 10**10
bound = (0,0.4)
return_period = 45

def model(returns, granularity, file_name, cycles, verbose=False):

    # Convert the dataframe to a numpy array
    dataset = returns.values
    # training set is dataset - prediction length
    training_data_len = int(len(dataset) - cycle_len )


    scaler = MinMaxScaler(feature_range=(0,1))
    dataset = dataset.reshape(-1,1)
    scaled_data = scaler.fit_transform(dataset)

    # Create the training data set
    # Create the scaled training data set
    train_data = scaled_data[0:training_data_len, :]
    # Split the data into x_train and y_train data sets
    x_train = []
    y_train = []

    for i in range(60, len(train_data)):
        x_train.append(train_data[i-60:i, 0])
        y_train.append(train_data[i, 0])

    # Convert the x_train and y_train to numpy arrays
    x_train, y_train = np.array(x_train), np.array(y_train)
    # Reshape the data
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
    # x_train.shape
    # Create the testing data set
    # Create a new array containing scaled values from index 1543 to 2002
    test_data = scaled_data[training_data_len - 60: , :]
    # Create the data sets x_test and y_test
    x_test = []
    y_test = dataset[training_data_len:, :]
    for i in range(60, len(test_data)):
        x_test.append(test_data[i-60:i, 0])
    # Convert the data to a numpy array
    x_test = np.array(x_test)

    # Reshape the data
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1 ))
    # Build the LSTM model
    model = Sequential()
    model.add(LSTM(128, return_sequences=True, input_shape= (x_train.shape[1], 1)))
    model.add(LSTM(64, return_sequences=False))
    model.add(Dense(25))
    model.add(Dense(1))
    # Compile the model
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['acc'])
    # Train the model
    model.fit(x_train, y_train, batch_size=1, epochs=1, validation_data=(x_test, y_test))
    input_data = x_test
    actual_predictions = []
    #inputs = []
    #outputs = []
    for i in range(0, cycles):
        # Get the models predicted price values
        #inputs+=[input_data]
        predictions = model.predict(input_data)
        #outputs+=[predictions]
        actual_predictions += [predictions[-1].tolist()]
        predictions = predictions.reshape(1,predictions.shape[0], 1)
        input_data = np.concatenate([input_data, predictions])[1:,:]
    '''
    with open('/tmp/io.txt', 'w+') as f:
        io = {}
        io['in'] = inputs
        io['out'] = outputs
        io['fut scaled'] = actual_predictions
        f.write(str(io))
    '''
    return actual_predictions

def get_actual_predictions(returns, granularity, file_name, cycles, verbose=False):
    actual_predictions = []
    actual_predictions_path = get_write_path(start_date, end_date, granularity, balance, bound, return_period, file_name+'_predictions', ext='txt')
    if os.path.exists(actual_predictions_path):
        with open(actual_predictions_path, 'r') as f:
            buf = f.read()
        actual_predictions = ast.literal_eval(buf)
        #actual_predictions = np.array(actual_predictions)
    else:
        actual_predictions = model(returns, granularity, file_name, cycles, verbose)
        with open(actual_predictions_path, 'w+') as f:
            f.write(str(actual_predictions))
        # Convert the dataframe to a numpy array
    dataset = returns.values
    dataset = dataset.reshape(-1,1)
    scaler = MinMaxScaler(feature_range=(0,1))
    scaler.fit_transform(dataset)
    predictions = scaler.inverse_transform(actual_predictions)
    indices=[str(dateutil.parser.parse(returns.index[-1]).date()+timedelta(seconds=granularity*i)) for i in range(1, len(predictions)+1)]

    fut = pd.Series(data=predictions.flatten(), index=indices)
    fut.index = fut.index.rename('time')
    fut.rename('price', inplace=True)

    returns.index = returns.index.rename('time')
    returns.rename('price', inplace=True)
    return pd.concat([returns, fut])



por_path = get_write_path(start_date, end_date, granularity, balance, bound, return_period, 'portfolios', ext='csv')
if not os.path.exists(por_path):
    print("error! can't find portfolio in /data")
    res = get_portfolio(start_date, end_date, granularity, market_cap, bound, return_period, balance, verbose=False, singlecore=False)
    if not res:
        print("error! can't retrieve portfolio from get_portfolio, check your connection")
        exit()
df = pd.read_csv(por_path)
df=df.set_index('Unnamed: 0')
eq_por = df['equally_weighted_portfolio']
gmv_por = df['gmv_portfolio']
max_sharpe_por = df['max_sharpe_portfolio']

eq_por = get_actual_predictions(eq_por, granularity, 'equally_weighted', cycles)
gmv_por = get_actual_predictions(gmv_por, granularity, 'gmv', cycles)
max_sharpe_por = get_actual_predictions(max_sharpe_por, granularity, 'max_sharpe',  cycles)

# Visualize the data
plt.figure(figsize=(16,6))
plt.title('Portfolio')
plt.plot(eq_por, '-g', label='equally weighted portfolio')
plt.plot(gmv_por, '-c', label='global minimum variance portfolio')
plt.plot(max_sharpe_por, '-m', label='max sharpe portfolio')
plt.xlabel('Date', fontsize=18)
plt.ylabel('return ($)', fontsize=18)
plt.legend()
plt.savefig(get_write_path(start_date, end_date, granularity, balance, bound, return_period, 'portfolios', ext='png'))
