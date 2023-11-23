import numpy as np
from tensorflow.keras.layers import Dense
from tensorflow.keras.models import Sequential

data = np.loadtxt('../data/training_data.csv', delimiter=',', skiprows=1)
predictors = data[:, :-1]
target = data[:, -1]
n_cols = predictors.shape[1]

model = Sequential()
model.add(Dense(50, activation='relu', input_shape=(n_cols,)))
model.add(Dense(32, activation='relu'))
model.add(Dense(1))

model.compile(optimizer='adam', loss='mean_squared_error')
model.fit(predictors, target, validation_split=0.5)
model.save('../data/stock_perf_model.h5')
