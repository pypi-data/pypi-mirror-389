def code():
    print(r"""
------------------------------------------------------- Practical 2 ------------------------------------------------------------------------------------------------

import pytesseract
from PIL import Image
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Smit\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
img = Image.open("image1.png")
text = pytesseract.image_to_string(img)
print("Extracted Text:", text)



from pdf2image import convert_from_path
import pytesseract
from PIL import Image
# pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Smit\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
path = r'C:\Users\Smit\Release-24.08.0-0\poppler-24.08.0\Library\bin'
images = convert_from_path("test.pdf", poppler_path=path)
for i, img in enumerate(images):
    text = pytesseract.image_to_string(img)
    print("Page", i+1)
    print(text)
    
    
    
------------------------------------------------------- Practical 3 ------------------------------------------------------------------------------------------------

1.
import pandas as pd

file_path = 'BostonHousing.csv'
df = pd.read_csv(file_path)
df.head()

2.
import numpy as np
import matplotlib.pyplot as plt

# SIMPLE LINEAR REGRESSION WITH GRADIENT DESCENT AND VISUALIZATION

def simple_linear_regression_gd(X, y, lr=0.01, epochs=1000, visualize_step=200):
    m, b = 0, 0
    n = len(X)

    plt.ion()

    for epoch in range(1, epochs + 1):
        y_pred = m * X + b
        error = y_pred - y

        dm = (1 / n) * np.dot(error, X)
        db = (1 / n) * np.sum(error)

        m -= lr * dm
        b -= lr * db

        if epoch % visualize_step == 0 or epoch == 1 or epoch == epochs:
            plt.clf()
            plt.scatter(X, y, color='blue', label='Actual Data')
            plt.plot(X, m * X + b, color='red', label=f'Prediction Line (Epoch {epoch})')
            plt.xlabel('RM (Avg rooms per dwelling)')
            plt.ylabel('MEDV ($1000s)')
            plt.title('Simple Linear Regression - Gradient Descent')
            plt.legend()
            plt.pause(0.3)

    plt.ioff()
    plt.show()
    return m, b

X_simple = df['rm'].values
y_simple = df['medv'].values

m_final, b_final = simple_linear_regression_gd(X_simple, y_simple, lr=0.01, epochs=1000, visualize_step=200)
print("Final value of slop = " , m_final)
print("Final value of intersect = " , b_final)

3.
X = df[['rm']].values      
y = df['medv'].values      

X_b = np.c_[np.ones((X.shape[0], 1)), X]

theta_best = np.linalg.inv(X_b.T @ X_b) @ X_b.T @ y

bias = theta_best[0]   
weight = theta_best[1]

print("Bias (Intercept):", bias)
print("Weight (Slope):", weight)

4.
# MULTIPLE LINEAR REGRESSION WITH GRADIENT DESCENT
def multiple_linear_regression_gd(X, y, lr=0.0001, epochs=1000):
    n_samples, n_features = X.shape
    weights = np.zeros(n_features)
    bias = 0

    cost_history = []

    for epoch in range(epochs):
        y_pred = np.dot(X, weights) + bias
        error = y_pred - y

        dw = (1 / n_samples) * np.dot(X.T, error)
        db = (1 / n_samples) * np.sum(error)

        weights -= lr * dw
        bias -= lr * db

        cost = (1 / n_samples) * np.sum(error ** 2)
        cost_history.append(cost)

    return weights, bias, cost_history

X_multi = df.drop(columns=['medv']).values
y_multi = df['medv'].values

X_multi = (X_multi - X_multi.mean(axis=0)) / X_multi.std(axis=0)

weights_final, bias_final, cost_history = multiple_linear_regression_gd(X_multi, y_multi, lr=0.01, epochs=5000)

plt.plot(range(len(cost_history)), cost_history)
plt.xlabel('Epochs')
plt.ylabel('Mean Squared Error')
plt.title('Multiple Linear Regression - Cost over Time')
plt.show()

print("Final value of weight = " , weights_final)
print("Final value of intersect = " , bias_final)

5.
X = df.drop(columns=['medv']).values
y = df['medv'].values

X_b = np.c_[np.ones((X.shape[0], 1)), X]

theta_best = np.linalg.inv(X_b.T @ X_b) @ X_b.T @ y

bias = theta_best[0]
weights = theta_best[1:]

print("Bias (Intercept):", bias)
print("Weights:", weights)


------------------------------------------------------- Practical 4 ------------------------------------------------------------------------------------------------

1.
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

df = pd.read_csv("BostonHousing.csv")
X = df.drop(columns=['medv']).values  
y = df['medv'].values  
# .values converts the DataFrame into a NumPy array

M = len(X)
print("No of samples:", M)

X_train, X_test, Y_train, Y_test = train_test_split(X, y, test_size=0.25, shuffle=True, random_state=42)

model = LinearRegression()
model.fit(X_train, Y_train)

t0 = model.intercept_
t = model.coef_

print("Sklearn Multiple Linear Regression")
print("Coefficients:", t)
print(f"Intercept (t0) = {t0:.4f}")

y_pred_train = model.predict(X_train)
y_pred_test = model.predict(X_test)

mse_train = np.mean((y_pred_train - Y_train) ** 2)
mse_test = np.mean((y_pred_test - Y_test) ** 2)

print(f"MSE for training set: {mse_train:.4f}")
print(f"MSE for testing set: {mse_test:.4f}")

2.
import matplotlib.pyplot as plt

y_pred = model.predict(X)

plt.scatter(y, y_pred, color='blue', marker='o', alpha=0.6)
plt.xlabel('Actual MEDV (House Price in $1000s)')
plt.ylabel('Predicted MEDV')
plt.title('Predicted vs Actual House Prices')
plt.grid(True)

plt.plot([y.min(), y.max()], [y.min(), y.max()],
         color='red', linestyle='--', linewidth=2)

plt.show()



3.
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("BostonHousing.csv")
x = df.drop(columns=['medv']).values
y = df['medv'].values

M = len(x)
print(f"No of Samples: {M}")

X = np.column_stack([np.ones(x.shape[0]), x])
m, n = X.shape

alpha = 0.00001   
epochs = 1000
lam = 0.5      

theta = np.zeros(n)
losses = []

for i in range(epochs):
    y_pred = X @ theta
    error = y_pred - y
    grad = (1/m) * (X.T @ error)
    
    for j in range(1, n): 
        grad[j] += lam * np.sign(theta[j])
    
    theta -= alpha * grad
    
    loss = (1/m) * np.sum((y_pred - y)**2) + lam * np.sum(np.abs(theta[1:]))
    losses.append(loss)

print("Multiple Linear Regression using Lasso Regularization")
print(f"Intercept (Bias): {theta[0]:.4f}")

feature_names = ['Intercept'] + list(df.drop(columns=['medv']).columns)
for fname, coef in zip(feature_names, theta):
    print(f"{fname}: {coef:.4f}")

plt.plot(losses)
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title("Lasso Regression Loss Curve (Boston Housing)")
plt.show()



4.
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

df = pd.read_csv("BostonHousing.csv")

X = df.drop(columns=['medv']).values
y = df['medv'].values

X_b = np.column_stack([np.ones(X.shape[0]), X])
y_pred = X_b @ theta 

plt.scatter(y, y_pred, color='blue', marker='o', alpha=0.6)
plt.xlabel('Actual MEDV (House Price in $1000s)')
plt.ylabel('Predicted MEDV')
plt.title('Predicted vs Actual House Prices')
plt.grid(True)

plt.plot([y.min(), y.max()], [y.min(), y.max()],
         color='red', linestyle='--', linewidth=2)

plt.show()



5.
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

df = pd.read_csv("BostonHousing.csv")
x = df.drop(columns=['medv']).values
y = df['medv'].values

M = len(x)
print("No of samples:", M)

X_train, X_test, Y_train, Y_test = train_test_split(x, y, test_size=0.25, shuffle=True, random_state=42)

ridge = Ridge(alpha=1.0)
ridge.fit(X_train, Y_train)

y_pred = ridge.predict(X_test)

mse = mean_squared_error(Y_test, y_pred)

print("Ridge Regression Results")
print("Mean Squared Error:", mse)
print("Intercept:", ridge.intercept_)
print("Coefficients:", ridge.coef_)


6.
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Lasso, Ridge

# Load dataset
df = pd.read_csv("BostonHousing.csv")

# Features and target
X = df.drop(columns=['medv']).values
y = df['medv'].values

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, shuffle=True
)

# Train models
models = {
    "Linear Regression": LinearRegression(),
    "Lasso Regression": Lasso(alpha=0.5, max_iter=5000, random_state=42),
    "Ridge Regression": Ridge(alpha=1.0, max_iter=5000, random_state=42)
}

for name, model in models.items():
    model.fit(X_train, y_train)

# Predictions
y_pred_linear = models["Linear Regression"].predict(X_test)
y_pred_lasso  = models["Lasso Regression"].predict(X_test)
y_pred_ridge  = models["Ridge Regression"].predict(X_test)

# Plot all in one graph
plt.figure(figsize=(8, 6))

plt.scatter(y_test, y_pred_linear, alpha=0.6, label="Linear Regression", marker='o')
plt.scatter(y_test, y_pred_lasso, alpha=0.6, label="Lasso Regression", marker='s')
plt.scatter(y_test, y_pred_ridge, alpha=0.6, label="Ridge Regression", marker='^')

# Perfect-fit line (y = x)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()],
         color="red", linestyle="--", linewidth=2, label="Perfect Fit")

plt.xlabel("Actual MEDV (House Price in $1000s)")
plt.ylabel("Predicted MEDV")
plt.title("Predicted vs Actual (Test Set) - Linear, Lasso & Ridge")
plt.legend()
plt.grid(True)
plt.show()


------------------------------------------------------- Practical 5 ------------------------------------------------------------------------------------------------


1.
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import Binarizer, MinMaxScaler
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import BernoulliNB, MultinomialNB, GaussianNB
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, confusion_matrix


2.
# -------------------------
# Step 1: Load Data
# -------------------------

df = pd.read_csv('Naive-Bayes-Classification-Data.csv')  
print(df.head())
print(df.info())
print(df['diabetes'].value_counts())  


3.
# -------------------------
# Step 2: Data Preprocessing
# -------------------------

cont_features = ['glucose', 'bloodpressure']  
X_cont = df[cont_features].copy()

if 'text' in df.columns:
    texts = df['text'].astype(str)
    count_vect = CountVectorizer(stop_words='english')
    X_counts = count_vect.fit_transform(texts)
    binarizer = Binarizer(copy=False, threshold=0.0)
    X_binary = binarizer.fit_transform(X_counts.toarray())
else:
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X_cont)
    binarizer = Binarizer(threshold=0.5)
    X_binary = binarizer.fit_transform(X_scaled)
    X_counts = np.round(X_scaled * 10)

y = df['diabetes']

Xc_train, Xc_test, yc_train, yc_test = train_test_split(X_cont, y, test_size=0.3, random_state=42, stratify=y)
Xb_train, Xb_test, yb_train, yb_test = train_test_split(X_binary, y, test_size=0.3, random_state=42, stratify=y)
Xf_train, Xf_test, yf_train, yf_test = train_test_split(X_counts, y, test_size=0.3, random_state=42, stratify=y)
print(X_cont)
print(X_binary)
print(X_counts)


4.
# -------------------------
# Step 3: Build Models
# -------------------------

# Gaussian NB
gnb = GaussianNB()
gnb.fit(Xc_train, yc_train)
y_pred_g = gnb.predict(Xc_test)
acc_g = accuracy_score(yc_test, y_pred_g)
print("Gaussian NB Accuracy:", acc_g)
print(classification_report(yc_test, y_pred_g))

# Multinomial NB
mnb = MultinomialNB(alpha=1.0)
mnb.fit(Xf_train, yf_train)
y_pred_m = mnb.predict(Xf_test)
acc_m = accuracy_score(yf_test, y_pred_m)
print("Multinomial NB Accuracy:", acc_m)
print(classification_report(yf_test, y_pred_m))

# Bernoulli NB
bnb = BernoulliNB(alpha=1.0, binarize=0.5)
bnb.fit(Xb_train, yb_train)
y_pred_b = bnb.predict(Xb_test)
acc_b = accuracy_score(yb_test, y_pred_b)
print("Bernoulli NB Accuracy:", acc_b)
print(classification_report(yb_test, y_pred_b))


5.
# -------------------------
# Step 4: Plot Graphs for Comparison
# -------------------------

models = ['GaussianNB', 'MultinomialNB', 'BernoulliNB']
accuracies = [acc_g, acc_m, acc_b]

plt.figure(figsize=(8,6))
sns.barplot(x=models, y=accuracies)
plt.ylim(0,1)
plt.title('Comparison of NB models: Accuracy')
plt.ylabel('Accuracy')

for i, v in enumerate(accuracies):
    plt.text(i, v + 0.02, f"{v:.2f}", ha='center')

plt.show()


------------------------------------------------------- Practical 6 ------------------------------------------------------------------------------------------------

1.
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.preprocessing import LabelEncoder



2.
csv_path = "car.csv"

col_names = ['buying','maint','doors','persons','lug_boot','safety','class']

tmp = pd.read_csv(csv_path, header=0)
if tmp.shape[1] != 7:
    df = pd.read_csv(csv_path, header=None, names=col_names)
else:
    df = tmp.copy()
    if set(col_names).issubset(set(df.columns)) is False:
        df.columns = col_names

print("Dataset shape:", df.shape)
display(df.head())
print("\nColumns:", list(df.columns))


3.
target_col = 'class'

X_df = df.drop(columns=[target_col])
y_series = df[target_col]

print('Independent features (first 10 rows):')
display(X_df.head(10))
print('\nDependent features (first 30 values):')
print(y_series.values[:30])
print("\nUnique target values:", sorted(y_series.unique()))


4.
4.
X_encoded = X_df.copy()
label_encoders = {}
for col in X_encoded.columns:
    le = LabelEncoder()
    X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
    label_encoders[col] = le

# Encode target
target_le = LabelEncoder()
y_encoded = target_le.fit_transform(y_series.astype(str))

print("Encoded feature sample:")
display(X_encoded.head())
print("\nClasses (target):", target_le.classes_)
print("Encoded class distribution:")
(unique, counts) = np.unique(y_encoded, return_counts=True)
for u, c in zip(unique, counts):
    print(f"  {target_le.inverse_transform([u])[0]} : {c}")
    
    
5.
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X_encoded, y_encoded, test_size=0.33, random_state=42, stratify=y_encoded)
print("Stratified split successful.")
print('X_train shape:', X_train.shape)
print('X_test shape :', X_test.shape)


6.
id3_clf = DecisionTreeClassifier(criterion='entropy', random_state=42)
id3_clf.fit(X_train, y_train)


7.
y_pred = id3_clf.predict(X_test)
acc = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred, target_names=target_le.classes_)

print(f'Accuracy (test set): {acc:.4f}\n')
print('Classification Report:\n')
print(report)


8.
cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=target_le.classes_)
fig, ax = plt.subplots(figsize=(6,5))
disp.plot(ax=ax, values_format='d')
plt.title('Confusion Matrix - ID3 (Car Evaluation)')
plt.show()


9.
viz_clf = DecisionTreeClassifier(criterion='entropy', max_depth=3, random_state=42)
viz_clf.fit(X_train, y_train)

plt.figure(figsize=(16,10))
plot_tree(
    viz_clf,
    feature_names=X_encoded.columns,
    class_names=target_le.classes_,
    filled=True,
    rounded=True,
    fontsize=10
)
plt.title('Decision Tree (ID3 approx) - shallow view (max_depth=3)')
plt.show()


------------------------------------------------------- Practical 7 ------------------------------------------------------------------------------------------------
1.
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error


2.
url = 'http://archive.ics.uci.edu/ml/machine-learning-databases/auto-mpg/auto-mpg.data'

column_names = ['MPG', 'Cylinders', 'Displacement', 'Horsepower', 'Weight',
                'Acceleration', 'Model Year', 'Origin']

df = pd.read_csv(url, names=column_names, na_values='?', comment='\t',
                 sep=' ', skipinitialspace=True)

df = df.dropna()
df.head()


3.
X = df[['Horsepower', 'Weight']]
y = df['MPG']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


4.
param_grid = {
    'C': [0.1, 1, 10, 100],
    'gamma': ['scale', 'auto', 0.1, 0.01],
    'kernel': ['rbf'],
    'epsilon': [0.1, 0.2, 0.5]
}


5.
grid_search = GridSearchCV(SVR(), param_grid, refit=True, verbose=0, cv=5)

print("--- Running Grid Search for SVR ---")
grid_search.fit(X_train_scaled, y_train)

print("\nBest parameters found:", grid_search.best_params_)


6.
best_svr = grid_search.best_estimator_
y_pred = best_svr.predict(X_test_scaled)

mse = mean_squared_error(y_test, y_pred)
print(f"Test set Mean Squared Error: {mse:.4f}")


7.
print("\n--- Preparing 3D Plot ---")

x_min, x_max = X['Horsepower'].min(), X['Horsepower'].max()
y_min, y_max = X['Weight'].min(), X['Weight'].max()

xx, yy = np.meshgrid(np.linspace(x_min, x_max, 50),
                     np.linspace(y_min, y_max, 50))

mesh_scaled = scaler.transform(np.c_[xx.ravel(), yy.ravel()])
zz = best_svr.predict(mesh_scaled).reshape(xx.shape)

fig = plt.figure(figsize=(12, 9))
ax = fig.add_subplot(111, projection='3d')

ax.plot_surface(xx, yy, zz, alpha=0.4, cmap='viridis')
ax.scatter(X['Horsepower'], X['Weight'], y, color='red', s=20, edgecolors='k')

ax.set_title("SVR Regression Surface for Auto MPG", fontsize=16)
ax.set_xlabel("Horsepower")
ax.set_ylabel("Weight")
ax.set_zlabel("MPG")
ax.view_init(elev=20, azim=45)
plt.show()



------------------------------------------------------- Practical 8 ------------------------------------------------------------------------------------------------


1.
import numpy as np
import pandas as pd

X = np.array([[0,0],
              [0,1],
              [1,0],
              [1,1]])

y = np.array([0, 0, 0, 1])  

df = pd.DataFrame(X, columns=["x1","x2"])
df["label"] = y

print(df.to_string(index=False))



2.
class Perceptron:
    def __init__(self, input_dim, lr=0.1, epochs=10, random_state=None):
        self.lr = lr
        self.epochs = epochs
        self.rng = np.random.RandomState(random_state)
        self.w = None
        self.b = None
        self.history = {"epoch": [], "errors": []}
    
    def _activation(self, x):
        return np.where(x >= 0.0, 1, 0)
    
    def net_input(self, X):
        return np.dot(X, self.w) + self.b
    
    def predict(self, X):
        X = np.atleast_2d(X)
        return self._activation(self.net_input(X))
    
    def fit(self, X, y, verbose=False):
        n_samples, n_features = X.shape
        self.w = self.rng.normal(loc=0.0, scale=0.01, size=n_features)
        self.b = 0.0
        
        for epoch in range(1, self.epochs + 1):
            errors = 0
            for xi, target in zip(X, y):
                linear_output = np.dot(xi, self.w) + self.b
                predicted = 1 if linear_output >= 0 else 0
                update = self.lr * (target - predicted)
                if update != 0.0:
                    self.w += update * xi
                    self.b += update
                    errors += 1
            self.history["epoch"].append(epoch)
            self.history["errors"].append(errors)
            if verbose:
                print(f"Epoch {epoch:2d}: errors = {errors} | weights = {self.w} | bias = {self.b:.3f}")
        return self
        
        
        
  
  3.
  import matplotlib.pyplot as plt

p = Perceptron(input_dim=2, lr=0.2, epochs=10, random_state=42)
p.fit(X, y, verbose=True)

print("\nFinal weights:", p.w)
print("Final bias:", p.b)

plt.figure(figsize=(6,4))
plt.plot(p.history["epoch"], p.history["errors"], marker='o')
plt.title("Perceptron training: errors per epoch")
plt.xlabel("Epoch")
plt.ylabel("Number of updates (errors)")
plt.grid(True)
plt.show()



4.
print("Testing perceptron on AND inputs:")
for xi, yi in zip(X, y):
    pred = p.predict(xi)[0]
    print(f"Input: {xi.tolist()}  -> Predicted: {pred}  Expected: {yi}")
    
    
    
    
------------------------------------------------------- Practical 9 ------------------------------------------------------------------------------------------------


1.
import numpy as np
import matplotlib.pyplot as plt
np.random.seed(42)

X = np.array([[0,0],
              [0,1],
              [1,0],
              [1,1]], dtype=float)

y = np.array([[0],
              [1],
              [1],
              [0]], dtype=float)
              
              


2.
def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))
def sigmoid_derivative(x):
    s = sigmoid(x)
    return s * (1 - s)
def mse_loss(target, pred):
    return 0.5 * np.mean((target - pred) ** 2)


3.
n_input = 2
n_hidden = 2  
n_output = 1

rng = np.random.RandomState(42)
W1 = rng.normal(scale=0.1, size=(n_hidden, n_input))  
b1 = np.zeros((n_hidden,))                              

W2 = rng.normal(scale=0.1, size=(n_output, n_hidden))   
b2 = np.zeros((n_output,))                              

print("W1 shape:", W1.shape, "b1 shape:", b1.shape)
print("W2 shape:", W2.shape, "b2 shape:", b2.shape)




4.
def forward(X_batch, W1, b1, W2, b2):
    z1 = X_batch.dot(W1.T) + b1        
    a1 = sigmoid(z1)                   

    z2 = a1.dot(W2.T) + b2            
    a2 = sigmoid(z2)                  

    return z1, a1, z2, a2
    
    

5.
lr = 0.8          
epochs = 10000     
history = {"epoch": [], "loss": []}

for epoch in range(1, epochs + 1):
    z1, a1, z2, a2 = forward(X, W1, b1, W2, b2)

    loss = mse_loss(y, a2)
    
    n = X.shape[0]
    
    delta2 = (a2 - y) * sigmoid_derivative(z2)               
    
    dW2 = (delta2.T).dot(a1) / n                              
    db2 = np.mean(delta2, axis=0)                            
    
    delta1 = delta2.dot(W2) * sigmoid_derivative(z1)          
    
    dW1 = (delta1.T).dot(X) / n                            
    db1 = np.mean(delta1, axis=0)                           
    
    W2 -= lr * dW2
    b2 -= lr * db2
    W1 -= lr * dW1
    b1 -= lr * db1
    
    if epoch % 10 == 0:
        history["epoch"].append(epoch)
        history["loss"].append(loss)
    
    if epoch in (1, 10, 100, 1000, epochs):
        print(f"Epoch {epoch:5d} | loss = {loss:.6f}")
        
        
6.
plt.figure(figsize=(6,4))
plt.plot(history["epoch"], history["loss"], marker='o')
plt.xlabel("Epoch")
plt.ylabel("MSE Loss")
plt.title("Training loss (XOR via backprop)")
plt.grid(True)
plt.show()


7.
_, _, _, outputs = forward(X, W1, b1, W2, b2)
preds = (outputs >= 0.5).astype(int)

print("Inputs -> Predicted (prob) -> Class -> True")
for inp, prob, cl, true in zip(X, outputs.flatten(), preds.flatten(), y.flatten()):
    print(f"{inp.tolist()} -> {prob:.4f} -> {int(cl)} -> {int(true)}")

print("\nFinal weights and biases:")
print("W1 =\n", W1)
print("b1 =", b1)
print("W2 =\n", W2)
print("b2 =", b2)



8.
xx, yy = np.meshgrid(np.linspace(0, 1, 100),
                     np.linspace(0, 1, 100))

grid = np.c_[xx.ravel(), yy.ravel()]

_, a1, _, a2 = forward(grid, W1, b1, W2, b2)

Z = a2.reshape(xx.shape)

plt.figure(figsize=(8, 6))
plt.contourf(xx, yy, Z, levels=[0, 0.5, 1], alpha=0.6, cmap='coolwarm')
plt.colorbar(label='Output probability')

plt.scatter(X[:, 0], X[:, 1], c=y.ravel(), cmap='bwr', s=80, edgecolors='k')

plt.title("XOR Decision Boundary (Neural Network)")
plt.xlabel("Input X1")
plt.ylabel("Input X2")
plt.show()

------------------------------------------------------- Practical 10 ------------------------------------------------------------------------------------------------


import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris

np.random.seed(42)

data = load_iris()
X = data.data
y = data.target
num_samples, num_features = X.shape
num_classes = len(np.unique(y))


perm = np.random.permutation(num_samples)
train_idx = perm[:int(0.8 * num_samples)]
test_idx = perm[int(0.8 * num_samples):]

X_train, X_test = X[train_idx].astype(float), X[test_idx].astype(float)
y_train, y_test = y[train_idx], y[test_idx]


mean = X_train.mean(axis=0)
std = X_train.std(axis=0) + 1e-8
X_train = (X_train - mean) / std
X_test = (X_test - mean) / std

def one_hot_encode(y, num_classes):
    onehot = np.zeros((y.size, num_classes))
    onehot[np.arange(y.size), y] = 1
    return onehot

Y_train = one_hot_encode(y_train, num_classes)

hidden_units = 10
W1 = np.random.randn(num_features, hidden_units) * 0.1
b1 = np.zeros(hidden_units)
W2 = np.random.randn(hidden_units, num_classes) * 0.1
b2 = np.zeros(num_classes)
learning_rate = 0.05
epochs = 1000
losses = []

def softmax(x):
    x = x - x.max(axis=1, keepdims=True)
    exp_x = np.exp(x)
    return exp_x / exp_x.sum(axis=1, keepdims=True)

def tanh(x):
    return np.tanh(x)

def dtanh(x):
    return 1 - np.tanh(x) ** 2

for epoch in range(epochs):
    z1 = X_train.dot(W1) + b1
    a1 = tanh(z1)
    z2 = a1.dot(W2) + b2
    probs = softmax(z2)
    loss = -np.mean(np.sum(Y_train * np.log(probs + 1e-12), axis=1))
    losses.append(loss)

    grad_z2 = (probs - Y_train) / X_train.shape[0]
    grad_W2 = a1.T.dot(grad_z2)
    grad_b2 = grad_z2.sum(axis=0)
    grad_a1 = grad_z2.dot(W2.T)
    grad_z1 = grad_a1 * dtanh(z1)
    grad_W1 = X_train.T.dot(grad_z1)
    grad_b1 = grad_z1.sum(axis=0)

    W2 -= learning_rate * grad_W2
    b2 -= learning_rate * grad_b2
    W1 -= learning_rate * grad_W1
    b1 -= learning_rate * grad_b1

def predict_nn(X):
    z1 = X.dot(W1) + b1
    a1 = tanh(z1)
    z2 = a1.dot(W2) + b2
    probs = softmax(z2)
    return probs.argmax(axis=1), probs

y_pred_nn, _ = predict_nn(X_test)
accuracy_nn = (y_pred_nn == y_test).mean()

def confusion_matrix(y_true, y_pred, num_classes):
    matrix = np.zeros((num_classes, num_classes), dtype=int)
    for true, pred in zip(y_true, y_pred):
        matrix[true, pred] += 1
    return matrix

cm_nn = confusion_matrix(y_test, y_pred_nn, num_classes)

def precision_recall_f1(cm):
    precision, recall, f1 = [], [], []
    for i in range(cm.shape[0]):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        precision.append(p)
        recall.append(r)
        f1.append(f)
    return np.array(precision), np.array(recall), np.array(f1)

prec_nn, rec_nn, f1_nn = precision_recall_f1(cm_nn)

print("=== Neural Network (Manual Backpropagation) ===")
print("Accuracy:", round(accuracy_nn, 4))
print("Confusion Matrix:\n", cm_nn)
for i in range(num_classes):
    print(f"Class {i}: Precision {prec_nn[i]:.4f}, Recall {rec_nn[i]:.4f}, F1 {f1_nn[i]:.4f}")

plt.plot(losses)
plt.title("Neural Network Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.show()

num_clusters = 3
X_all = np.vstack([X_train, X_test])
y_all = np.concatenate([y_train, y_test])
num_all = X_all.shape[0]
X_all = (X_all - X_all.mean(axis=0)) / (X_all.std(axis=0) + 1e-8)

centers = X_all[np.random.choice(num_all, num_clusters, replace=False)].copy()
labels = np.zeros(num_all, dtype=int)

for _ in range(100):
    distances = np.linalg.norm(X_all[:, None, :] - centers[None, :, :], axis=2)
    new_labels = distances.argmin(axis=1)
    if np.all(new_labels == labels):
        break
    labels = new_labels
    for j in range(num_clusters):
        if (labels == j).sum() > 0:
            centers[j] = X_all[labels == j].mean(axis=0)

cm_kmeans = confusion_matrix(y_all, labels, num_clusters)


cluster_map = {}
for j in range(num_clusters):
    indices = np.where(labels == j)[0]
    if indices.size > 0:
        values, counts = np.unique(y_all[indices], return_counts=True)
        cluster_map[j] = int(values[counts.argmax()])
    else:
        cluster_map[j] = -1

mapped_labels = np.vectorize(cluster_map.get)(labels)
accuracy_kmeans = (mapped_labels == y_all).mean()
purity = np.sum([(y_all[labels == j] == cluster_map[j]).sum() for j in range(num_clusters)]) / num_all
prec_k, rec_k, f1_k = precision_recall_f1(confusion_matrix(y_all, mapped_labels, num_classes))

print("\n=== K-Means (Manual Implementation) ===")
print("Mapped Accuracy:", round(accuracy_kmeans, 4))
print("Purity:", round(purity, 4))
print("Confusion Matrix (True vs Cluster):\n", cm_kmeans)
for i in range(num_classes):
    print(f"Class {i}: Precision {prec_k[i]:.4f}, Recall {rec_k[i]:.4f}, F1 {f1_k[i]:.4f}")

X_centered = X_all - X_all.mean(axis=0)
U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
X_pca = X_centered.dot(Vt.T[:, :2])

plt.figure(figsize=(6, 4))
plt.scatter(X_pca[:, 0], X_pca[:, 1], c=labels, s=50)
plt.scatter(centers.dot(Vt.T[:, :2])[:, 0], centers.dot(Vt.T[:, :2])[:, 1], marker='X', s=120)
plt.title("K-Means Clusters")
plt.show()

plt.figure(figsize=(6, 4))
plt.scatter(X_pca[:, 0], X_pca[:, 1], c=y_all, s=50)
plt.title("True Labels")
plt.show()

""")