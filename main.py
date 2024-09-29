import pandas as pd
from transformers import pipeline
import random

def load_users(file_path):
    users=pd.read_csv(filepath_or_buffer=file_path,sep='::',names=['UserId','Gender','Age','Occupation','ZipCode'],usecols=[0,1,2],engine='python')
    return users
    
def load_ratings(file_path):
    ratings = pd.read_csv(filepath_or_buffer=file_path, sep='::', names=['UserId', 'MovieId', 'Rating','timestep'], usecols=[0,1,2],engine='python')
    return ratings


def load_movies(file_path):
    movies=pd.read_csv(filepath_or_buffer=file_path,sep='::',names=['MovieId','Movietitle','Genre'],usecols=[0,1,2],encoding='latin1',engine='python')
    return movies
    
def merge_data(users, ratings, movies):
    # Merge users and ratings on UserId
    user_ratings = ratings.merge(users, on='UserId')
    # Merge the result with movies on MovieId
    full_data = user_ratings.merge(movies, on='MovieId')
    return full_data    
    
def recommend_movies(merged_data,user_age,genre):
    age_filtered_data = merged_data[merged_data['Age'] == user_age]
    
    
    
    # Filter by genre (movies that include the specified genre)
    #Also works when user doesn't type the full genre properly
    genre_filtered_data = age_filtered_data[age_filtered_data['Genre'].str.lower().str.contains(genre.lower())]
    
    if genre_filtered_data.empty:
        print(f"No movies found for age {user_age} and genre {genre}.")
        return None
    
    # Group by user's age and genre and calculates average of ratings of data in same category
    genre_ratings = genre_filtered_data.groupby('Movietitle').agg({'Rating': 'mean'}).reset_index()
    
    # Sort by the average rating in descending order
    genre_ratings = genre_ratings.sort_values(by='Rating', ascending=False)
    return genre_ratings
    
    

bert_classifier = pipeline("sentiment-analysis", model='nlptown/bert-base-multilingual-uncased-sentiment')


def detect_response_with_bert(response):
    # Use the BERT model to classify the sentiment
    result = bert_classifier(response)[0]
    
    
    # Map BERT's result to affirmative/negative
    # This is better instead of user just saying yes/no we can have more outputs and BERT will understand them
    if result['label'] in ['4 stars', '5 stars','3 stars']:
        return "affirmative"
    elif result['label'] in ['1 star', '2 stars']: 
        return "negative"

def get_age_from_response(response):
    age1=-1000
    age=None
    
    
    
    # This function extracts the age from the user's response
    words=response.split()
    for word in words:
        if word.isdigit():
            age=int(word)
            break
        
    # Added the line below because age is represented differently in users.dat
    if(age is not None):
        if(age<18):
            age1=1
        elif(age>=18 and age<=24):
            age1=18
        elif(age>=25 and age<=34):
            age1=25
        elif(age>=35 and age<=44):
            age1=35
        elif(age>=45 and age<=49):
            age1=45
        elif(age>=50 and age<=55):
            age1=50
        elif(age>=56):
            age1=56
        return age,age1
    return None,None

if __name__ == '__main__':
    
    ages=[1,18,25,35,45,50,56]

    
    
    users = load_users('ml-1m/users.dat')
    ratings = load_ratings('ml-1m/ratings.dat')
    movies = load_movies('ml-1m/movies.dat')
    merged_data = merge_data(users, ratings, movies)
  
    
    
    print("Welcome to the Movie Recommendation Bot!")
    
    
    
    while True:
        age,age1=None,None
        response = input("Would you want me to base some movie recommendations on your age? (yes/no): ").lower()
        # Detect if user agrees or not, works more than just yes/no outputs
        sentiment = detect_response_with_bert(response)

        
    
        if sentiment == "affirmative":
            # Try to extract the age from the user's initial response
            age,age1 = get_age_from_response(response)
            
            if age:
                print(f"Great! I'll base recommendations on your age: {age}.")
            else:
                # If age isn't provided, ask for it
                try:
                    response=input("How old are you? ")
                    
                    age,age1 = get_age_from_response(response)
                    
                        
                    print(f"Got it! You're {age} years old.")
                except ValueError:
                    print("Please enter a valid age.")
             
        # If user doesn't want to give an age, go straight to genre
        genre = input("What genre of movie are you looking for? ")
        if(age==None):
            age1=ages[random.randrange(0,7)]
        
        recommendations = recommend_movies(merged_data, age1, genre)
        
        
        if not recommendations.empty:
            print(f"Here are the top movies for {genre} based on your age ({age}):")
            for idx, row in recommendations.iterrows():
                print(f"{row['Movietitle']} with an average rating of {row['Rating']:.2f}")
        else:
            print("Sorry, no recommendations found for this age group and genre.")
        
        # Ask if the user wants to search again
        continue_search = input("Would you like another recommendation? (yes/no): ").lower()
        sentiment = detect_response_with_bert(continue_search)
        if sentiment == "negative":
            print("Goodbye!")
            break
       
   