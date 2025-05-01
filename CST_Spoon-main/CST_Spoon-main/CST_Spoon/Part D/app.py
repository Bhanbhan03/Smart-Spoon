import streamlit as st
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
import io
import base64

# Download NLTK data (run once)
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('wordnet', quiet=True)

# Set random seed
np.random.seed(42)

# Streamlit app
st.title("South Indian Market Research Analysis")
st.write("Upload your dataset to analyze user sentiment and behavior.")

# File uploader
uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
if uploaded_file is not None:
    # Load dataset
    df = pd.read_excel(uploaded_file)
    st.write("Dataset loaded successfully!")
    st.write(df.head())

    # Preprocessing
    df.fillna({'Concerns': '', 'Additional Comments': ''}, inplace=True)
    df['Medical Condition'] = df['Medical Condition'].map({'Yes': 1, 'No': 0})
    df['Tech Awareness'] = df['Tech Awareness'].map({'Yes': 1, 'No': 0})
    df['Device Interest'] = df['Device Interest'].map({'Yes': 1, 'No': 0})

    salt_mapping = {'No Salt': 0, '¼ tsp': 0.25, '½ tsp': 0.5, 'More than 1 tsp': 1.5}
    salt_columns = [
        'Preferred salt amount for Dal', 'Preferred salt amount for Sambar',
        'Preferred salt amount for Biryani', 'Preferred salt amount for Curries',
        'Preferred salt amount for Dosa/Idly/Chaat/Snacks',
        'Preferred salt amount for Roti/Paratha/Chapathi',
        'Preferred salt amount for Pickles/Papad'
    ]
    for col in salt_columns:
        df[col] = df[col].map(salt_mapping)

    opinion_mapping = {'Perfect': 1, 'Too Salty': -1, 'Too Bland': -1}
    df['Overall opinion on current salt content at restaurants'] = df['Overall opinion on current salt content at restaurants'].map(opinion_mapping)

    # Sentiment Analysis
    analyzer = SentimentIntensityAnalyzer()
    def get_sentiment(text):
        return analyzer.polarity_scores(text)['compound']

    df['Concerns_Sentiment'] = df['Concerns'].apply(get_sentiment)
    df['Comments_Sentiment'] = df['Additional Comments'].apply(get_sentiment)
    df['Combined_Sentiment'] = (df['Concerns_Sentiment'] + df['Comments_Sentiment']) / 2

    def classify_sentiment(score):
        if score > 0.05:
            return 'Positive'
        elif score < -0.05:
            return 'Negative'
        else:
            return 'Neutral'

    df['Sentiment_Label'] = df['Combined_Sentiment'].apply(classify_sentiment)

    # Display Sentiment Results
    st.subheader("Sentiment Analysis")
    st.write("Sentiment Distribution:")
    fig, ax = plt.subplots()
    sns.countplot(x='Sentiment_Label', data=df, ax=ax)
    plt.title('Sentiment Distribution')
    st.pyplot(fig)

    # Clustering
    clustering_features = salt_columns + ['Combined_Sentiment', 'Age', 'Medical Condition']
    X = df[clustering_features].dropna()
    kmeans = KMeans(n_clusters=3, random_state=42)
    df['Cluster'] = kmeans.fit_predict(X)

    st.subheader("User Clusters")
    fig, ax = plt.subplots()
    sns.scatterplot(x='Age', y='Combined_Sentiment', hue='Cluster', data=df, ax=ax)
    plt.title('User Clusters by Age and Sentiment')
    st.pyplot(fig)

    # Prediction
    features = salt_columns + ['Age', 'Medical Condition', 'Tech Awareness', 'Device Interest', 'Combined_Sentiment']
    target = 'Overall opinion on current salt content at restaurants'
    X = df[features].dropna()
    y = df[target].dropna()
    X = X.loc[y.index]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    st.subheader("Prediction Results")
    st.write("Classification Report:")
    report = classification_report(y_test, y_pred, output_dict=True)
    st.write(pd.DataFrame(report).transpose())

    # Feature Importance
    feature_importance = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
    fig, ax = plt.subplots()
    sns.barplot(x=feature_importance, y=feature_importance.index, ax=ax)
    plt.title('Feature Importance')
    st.pyplot(fig)

    # Recommendations
    st.subheader("Recommendations")
    negative_health_users = df[(df['Sentiment_Label'] == 'Negative') & (df['Medical Condition'] == 1)]
    common_concerns = negative_health_users['Concerns'].value_counts().head()
    st.write("Common Concerns for Users with Medical Conditions and Negative Sentiment:")
    st.write(common_concerns)

    recommendations = {
        'Low-Salt Options': len(df[df['Medical Condition'] == 1]) / len(df) * 100,
        'Customization': df['Additional Comments'].str.contains('choose how much salt', case=False).sum(),
        'Healthier Cooking': df['Concerns'].str.contains('health', case=False).sum()
    }
    st.write("Recommendation Percentages:")
    st.write(recommendations)

    # Dish Recommendations
    def recommend_dish(row):
        if row['Preferred salt amount for Dal'] <= 0.25:
            return 'Low-Salt Dal'
        elif row['Preferred salt amount for Dal'] == 0.5:
            return 'Medium-Salt Dal'
        else:
            return 'High-Salt Dal'

    df['Recommended_Dish'] = df.apply(recommend_dish, axis=1)
    st.subheader("Sample Dish Recommendations")
    st.write(df[['Responder Name', 'Recommended_Dish']].head())

    # Download Processed Data
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    st.download_button(
        label="Download Processed Dataset",
        data=output,
        file_name="processed_south_indian_market_research.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )