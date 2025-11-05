def show():
    code = """import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')
import sklearn
from sklearn import tree
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score,confusion_matrix,classification_report
patient_df=pd.read_csv("/content/kidney_disease.csv")
predictors=['rc','sc','pcv','sg','hemo']
target='diagnosis'
print(patient_df)
patient_df.sc.fillna(patient_df.sc.median(),inplace=True)
patient_df.hemo.fillna(patient_df.hemo.median(),inplace=True)
patient_df.rc.fillna(patient_df.rc.median(),inplace=True)
patient_df.pcv.fillna(patient_df.pcv.median(),inplace=True)
patient_df.sg.fillna(patient_df.sg.median(),inplace=True)
patient_df.describe()
plt.figure(figsize=(4,7))
sns.heatmap(patient_df.isna())
plt.show()
Xs=patient_df[predictors]
y=patient_df[target]
plt.figure(figsize=(15,15))
tree.plot_tree(classTree,feature_names=predictors,class_names=y.unique(),filled=True,impurity=False)
plt.show()
plt.figure(figsize=(16,10))
tree.plot_tree(classTree,feature_names=Xs.columns,class_names=[str(c) for c in y.unique()],filled=True,rounded=True)
plt.show()
#Get importance scores from the trained tree
importances=classTree.feature_importances_
#Create Dataframe
feat_imp=pd.DataFrame({'Feature':Xs.columns,'Importance':importances}).sort_values(by='Importance',ascending=False)
#Plot
plt.figure(figsize=(10,6))
plt.barh(feat_imp['Feature'],feat_imp['Importance'])
plt.gca().invert_yaxis()
plt.xlabel('Importance Score')
plt.title('Feature Importances from Decision Tree')
plt.show()
from sklearn.metrics import accuracy_score,confusion_matrix,classification_report
#Predictions on training or test data
y_pred=classTree.predict(Xs)
#Accuracy
print('Accuracy:',accuracy_score(y,y_pred))
#Confusion Matrix
print('Confusion Matrix:\n',confusion_matrix(y,y_pred))
#Precision, Recall, F1-Score
print('Classification Report:\n',classification_report(y,y_pred))
# Question 2
customer_loan = pd.read_csv("/content/CustomerLoan.csv")
print(customer_loan)
customer_loan.head()
customer_loan.isna().sum()
customer_loan.drop(columns=['Name'],inplace=True)
customer_loan
predictors=['income','score']
target='default'
Xs=customer_loan[predictors].drop(index=[20])
y=customer_loan[target].drop(index=[20])
classTree=DecisionTreeClassifier()
classTree.fit(Xs,y)
plt.figure(figsize=(15,15))
tree.plot_tree(classTree,feature_names=predictors,class_names=y.unique(),filled=True,impurity=False)
plt.show()
from sklearn.metrics import accuracy_score,confusion_matrix,classification_report
#Predictions on training or test data
y_pred=classTree.predict(Xs)
#Accuracy
print('Accuracy:',accuracy_score(y,y_pred))
#Confusion Matrix
print('Confusion Matrix:\n',confusion_matrix(y,y_pred))
#Precision, Recall, F1-Score
print('Classification Report:\n',classification_report(y,y_pred))
# Question 3
Churn_data = pd.read_csv("C:/Users/nmims.student/Downloads/Customer Churn.csv")
Churn_data.describe()
Churn_data.isna().sum()
Churn_data['Churn_New'] = np.where(churn_data['Churn'] == 0, "No Churn", "Churn")
predictors = Churn_data.drop(columns = ['Churn','Churn_New']).columns.tolist()
target = 'Churn_New'
X = Churn_data[predictors]
y = Churn_data[target]
Churn_Tree = DecisionTreeClassifier(max_depth=4)
Churn_Tree.fit(X,y)
plt.figure(figsize=(15,15))
plot_tree(Churn_Tree,
          feature_names=predictors,
          class_names=y.unique(),
          filled=True,
          rounded=True,
          impurity=False)
plt.show()
plt.figure(figsize=(16,10))
plot_tree(Churn_Tree,
          feature_names=predictors,
          class_names=y.unique(),
          filled=True,
          rounded=True)
plt.show()
# Predictions on entire data
y_pred = Churn_Tree.predict(X)
print("Accuracy: ", accuracy_score(y,y_pred))
print("Confusion Matrix \n: ", confusion_matrix(y,y_pred))
print("Classification report \n: ", classification_report(y,y_pred))
# Split the data into training and testing set
X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.3,random_state=4)
bagging_model = BaggingClassifier(estimator=Churn_Tree,n_estimators=10,random_state=4)
# Train the bagging model
bagging_model.fit(X_train,y_train)
# Make predictions on the test set
y_pred = bagging_model.predict(X_test)
# Evaluate model accuracy
accuracy = accuracy_score(y_test,y_pred)
print(f"Bagging Classifier Accuracy: {accuracy:.4f}")"""
    print(code)

