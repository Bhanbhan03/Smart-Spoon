import pandas as pd
import numpy as np
import nltk
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import uuid

# Download NLTK data (run once)
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')

# Set random seed for reproducibility
np.random.seed(42)

# Step 1: Load the dataset
df = pd.read_excel('sorted_with_serial_south_indian_market_research.xlsx')

# Step 2: Preprocess the data
# Handle missing values in text columns
df.fillna({'Concerns': '', 'Additional Comments': ''}, inplace=True)

# Convert categorical columns to numerical
df['Medical Condition'] = df['Medical Condition'].map({'Yes': 1, 'No': 0})
df['Tech Awareness'] = df['Tech Awareness'].map({'Yes': 1, 'No': 0})
df['Device Interest'] = df['Device Interest'].map({'Yes': 1, 'No': 0})

# Encode salt preferences
salt_mapping = {'No Salt': 0, '¼ tsp': 0.25, '½ tsp': 0.5, 'More than 1 tsp': 1.5}
salt_columns = [
    'Preferred salt amount for Dal',
    'Preferred salt amount for Sambar',
    'Preferred salt amount for Biryani',
    'Preferred salt amount for Curries',
    'Preferred salt amount for Dosa/Idly/Chaat/Snacks',
    'Preferred salt amount for Roti/Paratha/Chapathi',
    'Preferred salt amount for Pickles/Papad'
]
for col in salt_columns:
    df[col] = df[col].map(salt_mapping)

# Encode overall opinion
opinion_mapping = {'Perfect': 1, 'Too Salty': -1, 'Too Bland': -1}
df['Overall opinion on current salt content at restaurants'] = df['Overall opinion on current salt content at restaurants'].map(opinion_mapping)

# Step 3: Sentiment Analysis
# Initialize VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Function to get sentiment scores
def get_sentiment(text):
    vader_scores = analyzer.polarity_scores(text)
    return vader_scores['compound']  # -1 (negative) to 1 (positive)

# Apply sentiment analysis to Concerns and Additional Comments
df['Concerns_Sentiment'] = df['Concerns'].apply(get_sentiment)
df['Comments_Sentiment'] = df['Additional Comments'].apply(get_sentiment)

# Combine sentiments (average)
df['Combined_Sentiment'] = (df['Concerns_Sentiment'] + df['Comments_Sentiment']) / 2

# Classify sentiment
def classify_sentiment(score):
    if score > 0.05:
        return 'Positive'
    elif score < -0.05:
        return 'Negative'
    else:
        return 'Neutral'

df['Sentiment_Label'] = df['Combined_Sentiment'].apply(classify_sentiment)

# Step 4: Detect Patterns in User Satisfaction
# Visualize sentiment distribution
plt.figure(figsize=(8, 6))
sns.countplot(x='Sentiment_Label', data=df)
plt.title('Sentiment Distribution')
plt.savefig('sentiment_distribution.png')
plt.close()

# Correlation between sentiment and demographics
correlation_cols = ['Age', 'Medical Condition', 'Tech Awareness', 'Device Interest', 'Combined_Sentiment']
plt.figure(figsize=(8, 6))
sns.heatmap(df[correlation_cols].corr(), annot=True, cmap='coolwarm')
plt.title('Correlation Matrix')
plt.savefig('correlation_matrix.png')
plt.close()

# Satisfaction by restaurant
plt.figure(figsize=(12, 6))
sns.countplot(x='Restaurant Name', hue='Overall opinion on current salt content at restaurants', data=df)
plt.xticks(rotation=45)
plt.title('Satisfaction by Restaurant')
plt.savefig('satisfaction_by_restaurant.png')
plt.close()

# Cluster users based on salt preferences and sentiment
clustering_features = salt_columns + ['Combined_Sentiment', 'Age', 'Medical Condition']
X = df[clustering_features].dropna()

kmeans = KMeans(n_clusters=3, random_state=42)
df['Cluster'] = kmeans.fit_predict(X)

# Visualize clusters
plt.figure(figsize=(8, 6))
sns.scatterplot(x='Age', y='Combined_Sentiment', hue='Cluster', data=df)
plt.title('User Clusters by Age and Sentiment')
plt.savefig('user_clusters.png')
plt.close()

# Step 5: User Behavior Prediction
# Features and target
features = salt_columns + ['Age', 'Medical Condition', 'Tech Awareness', 'Device Interest', 'Combined_Sentiment']
target = 'Overall opinion on current salt content at restaurants'

# Prepare data
X = df[features].dropna()
y = df[target].dropna()
X = X.loc[y.index]  # Align indices

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Random Forest model
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# Evaluate model
y_pred = model.predict(X_test)
print("Classification Report:")
print(classification_report(y_test, y_pred))

# Feature importance
feature_importance = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
plt.figure(figsize=(10, 6))
sns.barplot(x=feature_importance, y=feature_importance.index)
plt.title('Feature Importance for Satisfaction Prediction')
plt.savefig('feature_importance.png')
plt.close()

# Step 6: Predict Potential Improvements
# Identify users with negative sentiment and medical conditions
negative_health_users = df[(df['Sentiment_Label'] == 'Negative') & (df['Medical Condition'] == 1)]
common_concerns = negative_health_users['Concerns'].value_counts().head()
print("\nCommon Concerns for Users with Medical Conditions and Negative Sentiment:")
print(common_concerns)

# Recommendations
recommendations = {
    'Low-Salt Options': len(df[df['Medical Condition'] == 1]) / len(df) * 100,
    'Customization': df['Additional Comments'].str.contains('choose how much salt', case=False).sum(),
    'Healthier Cooking': df['Concerns'].str.contains('health', case=False).sum()
}
print("\nRecommendation Percentages:")
for key, value in recommendations.items():
    print(f"{key}: {value}")

# Step 7: Personalization - Recommend dishes based on salt preference
def recommend_dish(row):
    if row['Preferred salt amount for Dal'] <= 0.25:
        return 'Low-Salt Dal'
    elif row['Preferred salt amount for Dal'] == 0.5:
        return 'Medium-Salt Dal'
    else:
        return 'High-Salt Dal'

df['Recommended_Dish'] = df.apply(recommend_dish, axis=1)
print("\nSample Dish Recommendations:")
print(df[['Responder Name', 'Recommended_Dish']].head())

# Step 8: Summary Report
print("\nSummary Report")
print(f"Total Users: {len(df)}")
print(f"Sentiment Distribution: {df['Sentiment_Label'].value_counts().to_dict()}")
print(f"Top Concerns: {df['Concerns'].value_counts().head().to_dict()}")
print(f"Top Suggestions: {df['Additional Comments'].value_counts().head().to_dict()}")

# Step 9: Save processed data
df.to_excel('processed_south_indian_market_research.xlsx', index=False)
print("\nProcessed data saved to 'processed_south_indian_market_research.xlsx'")