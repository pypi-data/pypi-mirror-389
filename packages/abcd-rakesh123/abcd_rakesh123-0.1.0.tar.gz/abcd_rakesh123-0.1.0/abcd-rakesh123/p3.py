def show():
    code = """
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

### a) Read the data into the car_df pandas dataframe
car_df=pd.read_csv(r'C:\Users\nmims.student\Desktop\Abhishek Pracs\IMLT-Practical 2-Datasets\ToyotaCorolla_preprocessed.csv')

print(car_df)

### b) Using data visualization show the relationship mbetween the attribute price and rest of the attributes
car_df.hist()
plt.tight_layout()
plt.show()

X=['Age','Milage_KM','Quarterly_Tax','Weight','Fuel_Type_CNG','Fuel_Type_Diesel','Fuel_Type_Petrol']
y='Price'

df=pd.DataFrame(car_df)
print(df)

# Choose the variable to plot against all others
target_variable='Price'

# Get a list of all other numerical columns
other_variables=[col for col in df.columns if col != target_variable and pd.api.types.is_numeric_dtype(df[col])]
print(other_variables)

# Create scatter plots for the target variable against each other variable
for other_var in other_variables:
    plt.figure(figsize=(3,3)) #Create a new figure for each plot
    sns.scatterplot(x=df[target_variable],y=df[other_var])
    plt.title(f'Scatter Plot of {y} vs {other_var}')
    plt.xlabel('Price')
    plt.ylabel(other_var)
    plt.grid(True)
    plt.show()

sns.pairplot(df,x_vars=other_variables[0:4],y_vars=[target_variable],kind='scatter')
sns.pairplot(df,x_vars=other_variables[4:7],y_vars=[target_variable],kind='scatter')
plt.suptitle(f'Scatter Plots of {target_variable} vs. Other Variables',y=1.02)
plt.tight_layout()
plt.show()

print(other_variables[3:7])
df.plot(kind='density',subplots=True,layout=(3,3),sharex=False)
#sharex shares common X axis for all the graphs
plt.tight_layout()
plt.show()

df.hist()
plt.tight_layout()
plt.show()


### C) Use the visuals in  b) to describe the relationship
# of each attributes

### d)
correlations=df.corr()
print(correlations)
sns.heatmap(correlations,annot=True)
plt.show()

### f)
data_X=car_df[X]
data_y=car_df[y]

lm=LinearRegression()
lm.fit(data_X,data_y)

print('intercept (b0)',lm.intercept_)
coef_names=['b1','b2','b3','b4','b5','b6','b7']
print(pd.DataFrame({'Predictor':data_X.columns,'coefficient Name':coef_names}))

y_pred=lm.predict(data_X)
print(y_pred)
#Calculate R_squared using R2_score
r2=r2_score(data_y,y_pred) #Calculates the R-squared values
print(f'R-squared: {r2}')

#### Residual Analysis ####

### Residual Plots
residuals=data_y -y_pred
print(residuals)
x=np.arange(0,len(data_y))
sns.scatterplot(x=x,y=residuals,color='purple')
plt.axhline(y=0,color='blue',linestyle='--',linewidth=2)
plt.title("Residual plot")
plt.xlabel('Observation number')
plt.ylabel("Residuals")
plt.show()

# Residual vs Fitted Values plot
plt.figure(figsize=(8, 6)) #
sns.scatterplot(x=y_pred, y=residuals, alpha=0.6) #
plt.axhline(y=0, color='red', linestyle='--') # 
plt.xlabel("Fitted Values", fontsize=12) #
plt.ylabel("Residuals", fontsize=12) #
plt.title("Residuals vs. Fitted Values Plot", fontsize=14) #
plt.grid(True, linestyle='--', alpha=0.7) #
plt.show() #


import statsmodels.api as sm

# Normal Q-Q plot
plt.figure(figsize=(8, 6)) #
sm.qqplot(residuals, line='s') #
plt.title("Normal Q-Q Plot of Residuals", fontsize=14) #
plt.grid(True, linestyle='--', alpha=0.7) #
plt.show() #

# Residuals vs Independent Variable plot
plt.figure(figsize=(8, 6)) #
for x in X:
    sns.scatterplot(x=df[x], y=residuals, alpha=0.6) #
    plt.axhline(y=0, color='red', linestyle='--') #
    plt.xlabel(f"Independent Variable {x}", fontsize=12) #
    plt.ylabel("Residuals", fontsize=12) #
    plt.title(f"Residuals vs. Independent Variable {x} Plot", fontsize=14) #
    plt.grid(True, linestyle='--', alpha=0.7) #
    plt.show() #
    
#### Predict for new values ####

newData = pd.DataFrame({'Age':74, 'Milage_KM':124057,'Quarterly_Tax':69, 'Weight':1050, 'Fuel_Type_CNG':0, 'Fuel_Type_Diesel':0, 'Fuel_Type_Petrol':1},index=[1])
newData

predictions = lm.predict(newData)
print("Predicted price with given details:", np.round(predictions,4))

# Q2) The kidney_disease.csv dataset is used to classify between the cases of chronic kidney disease (CKD) 
# and those cases that are not CKD. The dataset shows the data of 400 patients and has 5 independent 
# attributes—namely, red blood cells (rc), serum creatinine (sc), packed cell volume (pcv), specific gravity (sg), 
# and hemoglobin (hemo). Of course, the dataset also has a dependent attribute named diagnosis whereby the patients 
# are labeled with either CKD or not CKD. Fit a logistic regression model and evaluate the performance.

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix

patient_df = pd.read_csv('C:\\Users\\Leena\\OneDrive - Shri Vile Parle Kelavani Mandal\\Leena-April18,2022\\M.Sc. ASA\\Assignments\\SC V\\2025\\IMLT-Practical 2-Datasets\\kidney_disease.csv')
predictors = ['rc', 'sc', 'pcv', 'sg', 'hemo']
target = 'diagnosis'
print(patient_df)

## Fill the missing values with median ##

patient_df.sc.fillna(patient_df.sc.median(),inplace=True)
patient_df.rc.fillna(patient_df.rc.mean(),inplace=True)
patient_df.pcv.fillna(patient_df.pcv.mean(),inplace=True)
patient_df.sg.fillna(patient_df.sg.mean(),inplace=True)
patient_df.hemo.fillna(patient_df.hemo.mean(),inplace=True)
patient_df.describe()

model = LogisticRegression(max_iter=1000)
model.fit(patient_df[predictors], patient_df[target])  

predicted = model.predict(patient_df[predictors])  
matrix = confusion_matrix(patient_df[target], predicted)
print(matrix)
patient_df.describe()


from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# Accuracy score
acc = accuracy_score(patient_df[target], predicted)
print("Accuracy:", acc)

# Confusion matrix
cm = confusion_matrix(patient_df[target], predicted)
print("Confusion Matrix:\n", cm)

# Detailed report (precision, recall, f1-score)
print("Classification Report:\n", classification_report(patient_df[target], predicted))


from sklearn.model_selection import train_test_split

# Splitting the data into train and test

X_train, X_test, Y_train, Y_test = train_test_split(patient_df[predictors], patient_df[target], test_size=0.2, random_state=42)
print(patient_df[predictors])
print(patient_df[target])
print("80% =len(X_train) = ",   len(X_train) )
print("20% =len(X_test)  = ",   len(X_test)  )
print("80% =len(Y_train) = ",   len(Y_train) )
print("20% =len(Y_test)  = ",   len(Y_test)  )


patient_df[target].value_counts()
Y_train.value_counts()
Y_test.value_counts()


model = LogisticRegression(max_iter=1000)
model.fit(X_train, Y_train)  

predicted = model.predict(X_test)  
matrix = confusion_matrix(Y_test, predicted)
print(matrix)
patient_df.describe()


from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# Accuracy score
acc = accuracy_score(Y_test, predicted)
print("Accuracy:", acc)

# Confusion matrix
cm = confusion_matrix(Y_test, predicted)
print("Confusion Matrix:\n", cm)

# Detailed report (precision, recall, f1-score)
print("Classification Report:\n", classification_report(Y_test, predicted))


# Accuracy score in the training data 
predicted = model.predict(X_train)  
acc = accuracy_score(Y_train, predicted)
print("Accuracy:", acc)

# Confusion matrix
cm = confusion_matrix(Y_train, predicted)
print("Confusion Matrix:\n", cm)

# Detailed report (precision, recall, f1-score)
print("Classification Report:\n", classification_report(Y_train, predicted))
"""
    print(code)