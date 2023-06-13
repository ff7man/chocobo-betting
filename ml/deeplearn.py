import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import OrdinalEncoder
import sklearn.preprocessing as preprocessing
import sklearn.model_selection as model_selection
import tensorflow as tf
import matplotlib.pyplot as plt

# A lot of this code is derived from:
# https://www.kaggle.com/code/cullensun/deep-learning-model-for-hong-kong-horse-racing

# Load the CSV file into a pandas DataFrame
data = pd.read_csv('all.csv')

# Things to consider:      
# Create models based on each class instead of learning on them all

# We need to clean up some of the data

# 6=short course, 0=long course, make 0 short and 1 long
data.loc[data['random'] == 0, 'random'] = 1
data.loc[data['random'] == 6, 'random'] = 0

# rename random to course_length
data = data.rename(columns={'random': 'course_length'})

# Fix jockey order
data.loc[data['jockey'] == 0, 'jockey'] = 9
data.loc[data['jockey'] == 1, 'jockey'] = 8
data.loc[data['jockey'] == 2, 'jockey'] = 7
data.loc[data['jockey'] == 3, 'jockey'] = 6

# bronze,silver,gold,plat
data.loc[data['jockey'] == 9, 'jockey'] = 3
data.loc[data['jockey'] == 8, 'jockey'] = 2
data.loc[data['jockey'] == 7, 'jockey'] = 0
data.loc[data['jockey'] == 6, 'jockey'] = 1

# Golds are better than plats at short courses swap 3 and 2
#data.loc[(data['course_length'] == 0) & (data['jockey'] == 3), 'jockey'] = 5
#data.loc[(data['course_length'] == 0) & (data['jockey'] == 2), 'jockey'] = 6
#data.loc[data['jockey'] == 5, 'jockey'] = 2
#data.loc[data['jockey'] == 6, 'jockey'] = 3

# Convert c,b,a,s to 0,1,2,3 to give them numeric values
ordinal_encoder = OrdinalEncoder(categories=[['c', 'b', 'a', 's']])
data['rank'] = ordinal_encoder.fit_transform(data[['rank']])

# Group each set of 6, assigning a unique raceid to each race
data['raceid'] = (data.index // 6)

# Create a column with where in the set of 6 a chocobo is aka draw order
data['draw'] = data.index %6+1

# Grab only columns we care about, rearrange, dropping extra
# Consider training on less data 
data = data[['raceid','draw','course_length','rank','ts', 'stamina1', 'sprinting', 'jockey', 'rs1', 'intel', 'coop', 'acc','winorder']]
#data = data[['raceid','draw','rs1','ts','winorder']]

# Expand a race into a single row, remove raceid and draw from expansion
# Who you are racing against matters not just the stats, so we merge them into a single row
# Another approach is to not do this and instead analyze stats for each chocobo individually
data = data.pivot(index='raceid', columns='draw', values=data.columns[2:])

# Sort columns alphabetically (cosmetic)
rearranged_columns = sorted(list(data.columns.values))
data = data[rearranged_columns]

# Create a copy of the data without the winorder (training data)
X = data[data.columns[:-6]] 
featureCount = X.shape[1]

# Create a copy of the winorders
W = data[data.columns[-6:]]

# Do standard deviation with magic math to normalize data ~20% higher success rates
ss = preprocessing.StandardScaler()
X = pd.DataFrame(ss.fit_transform(X),columns = X.columns)
#print(X.head(10))
#print(W.head(10))

# This is where the science takes a turn to a little trial and error
# We need to make a list of outputs as goals before we train the model

# The website trains so first place is the goal and assigns a 1 if you are in first, otherwise a 0.
# .42 success
y_won = W.applymap(lambda x: 1.0 if x < 2 else 0.0) 

# We actually care about knowing first, second, and third place with the order
# So we're going to asssign 1 for first, .67 for second, and .33 as third. 
# .32 success
#y_won = W.applymap(lambda x: 1.0 if x == 1 else 0.67 if x == 2 else 0.33 if x == 3 else 0.0)

# We could assign the top 3 as 1 and train on that as well
# .29 success
#y_won = W.applymap(lambda x: 1.0 if x < 4 else 0.0)

# We could not modify values and train that the entire placement matters
# .17 success
#y_won = W

#print(y_won.head(10)) 
print(X.shape)
print(y_won.shape)
outShape = y_won.shape[1]

# Split data into 80% train and 20% test sets
X_train, X_test, y_train, y_test = model_selection.train_test_split(X, y_won, train_size=0.8, test_size=0.2, random_state=1)
print('X_train', X_train.shape)
print('y_train', y_train.shape)
print('X_test', X_test.shape)
print('y_test', y_test.shape)
#print(y_test.head(10))

# We need to know who actually came in first and second for checking accuracy later so we're making a copy of the data with the same random seed
X_train1, X_test1, y_train1, y_test1 = model_selection.train_test_split(X, W, train_size=0.8, test_size=0.2, random_state=1)
#print(y_test1.head(10))

# Now we convert that to a list of all the races with who got 1 and 2 aka [[0,1,1,0,0,0],[1,1,0,0,0,0]]
# We'll use this later to see how well the model does
y_test1 = y_test1.applymap(lambda x: 1 if x == 1.0 else 1 if x == 2.0 else 0)
y_actual = y_test1.values.tolist()
#print(y_actual)

# Now we train the model using the website's code
# 96 is arbitrary afaik

model = tf.keras.Sequential([
    tf.keras.layers.Dense(96, activation='relu', input_shape=(featureCount,)),
    tf.keras.layers.Dense(outShape, activation='softmax')
])
model.compile(optimizer=tf.keras.optimizers.Adam(5e-04),
              loss=tf.keras.losses.CategoricalCrossentropy(),
              metrics=[tf.keras.metrics.Precision(name='precision')])

dataset = tf.data.Dataset.from_tensor_slices((X_train.values, y_train.values))
train_dataset = dataset.shuffle(len(X_train)).batch(500)
dataset = tf.data.Dataset.from_tensor_slices((X_test.values, y_test.values))
validation_dataset = dataset.shuffle(len(X_test)).batch(500)

print("Start training..\n")
# How many epochs to use here are trial and error. 
# I found 11 seems to have a high precision value before dropping
history = model.fit(train_dataset, epochs=11, validation_data=validation_dataset)
print("Done.")

# Make predictions on the test set
y_pred = model.predict(X_test)

# y_pred is full of values 0-1 for each horse ie [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
# They are out of order and use longer decimals
# process_result takes the highest 3 and uses them as the guesses  

def process_result(data):
    temp = data.copy()
    for index in range(len(data)):
        if temp[index] == max(temp):
            data[index] = 1
            temp[index] = 0
            break
    for index in range(len(data)):
        if temp[index] == max(temp):
            data[index] = 1
            temp[index] = 0
            break
    for index in range(len(data)):
        if temp[index] == max(temp):
            data[index] = 1
            temp[index] = 0
            break
    for index in range(len(data)):
        if data[index] != 1:
            data[index] = 0
    values = []
    for item in data:
     values.append(int(item))
    return values

# Print the first three races
print("\nOutputting first three races:")
print("Actual order")
for sublist in y_actual[:3]:
 print(sublist)

# Here are the predicted chances
print("Predicted chances ")
for sublist in y_pred[:3]:
 print(sublist)

# Here are the winning guesses
print("Guesses ")
for sublist in y_pred[:3]:
 print(process_result(sublist))

# We need to go through the predictions and take the chocobos with the highest chances of winning and give them a 1
# Aka [0.1,0.6,0.5,0.4,0.3,0.2] -> [0,1,1,1,0,0]
# Then we need to check if that guess has first and second place and tell us how good the model actually is
print("\nAll races: ")
count = 0
success = 0
for index,pred in enumerate(y_pred):
 #print(pred)
 predres = process_result(pred)
# print("Guess: "+str(predres))
# print("Actual: "+str(y_actual[index]))

 found = 0
 count = count+1
 n = 0
 for yval in y_actual[index]:
  if yval == 1:
   if predres[n] == 1:
    found = found +1
  n = n+1
 if found == 2:
  success = success+1
# input("waiting")

print("Success: %s" % success)
print("Total: %s" % count)
print(success/count)
