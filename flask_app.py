from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
import pickle

app = Flask(__name__)

# Load the processed data and similarity matrix
def load_data():
    try:
        pickle_path = 'movie_data.pkl'
        with open(pickle_path, 'rb') as file:
            movies, cosine_sim = pickle.load(file)
        print(f"Movie data loaded successfully from {pickle_path}!")
        return movies, cosine_sim
    except FileNotFoundError:
        print("Error: movie_data.pkl not found. Make sure it is in the same directory as flask_app.py.")
        return pd.DataFrame(), None
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame(), None

movies, cosine_sim = load_data()

# Function to get movie recommendations
def get_recommendations(title, cosine_sim=cosine_sim):
    if cosine_sim is None or movies.empty:
        return pd.DataFrame()
    
    try:
        idx = movies[movies['title'] == title].index[0]
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:11]  # Get top 10 similar movies
        movie_indices = [i[0] for i in sim_scores]
        return movies[['title', 'movie_id', 'tags']].iloc[movie_indices]
    except Exception:
        return pd.DataFrame()

# Fetch movie poster from TMDB API with fallbacks
def fetch_poster(movie_id, movie_title=None):
    api_key = '7b995d3c6fd91a2284b4ad8cb390c7b8'
    
    # Try 1: Fetch directly by ID
    try:
        url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}'
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('poster_path'):
                return f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
    except Exception:
        pass

    # Try 2: Fetch by Title (if movie_id failed or was wrong)
    if movie_title:
        try:
            search_url = f'https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={requests.utils.quote(movie_title)}'
            search_response = requests.get(search_url, timeout=2)
            if search_response.status_code == 200:
                results = search_response.json().get('results', [])
                if results and results[0].get('poster_path'):
                    return f"https://image.tmdb.org/t/p/w500{results[0]['poster_path']}"
        except Exception:
            pass

    # Final Fallback
    return "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&h=750&auto=format&fit=crop"

@app.route('/')
def index():
    if movies.empty:
        return "Movie data not found. Please ensure movie_data.pkl is in the project directory."
    
    # Extract unique genres
    genres_set = set()
    popular_genres = ['Action', 'Comedy', 'Drama', 'Horror', 'Sci-Fi', 'Animation', 'Thriller', 'Adventure']
    for tags in movies['tags'].dropna():
        for g in popular_genres:
            if g.lower() in tags.lower():
                genres_set.add(g)
    
    genre_list = sorted(list(genres_set))
    movie_list = sorted(movies['title'].tolist())
    
    # Selection of "Trending" movies (just static indices for now)
    trending_indices = [30, 15, 82, 120, 250, 480, 10, 5]
    trending_movies = []
    for i in trending_indices:
        if i < len(movies):
            row = movies.iloc[i]
            trending_movies.append({
                'title': row['title'],
                'poster_url': fetch_poster(row['movie_id'], row['title'])
            })
    
    return render_template('index.html', genres=genre_list, movies=movie_list, trending_movies=trending_movies)

@app.route('/recommend')
def recommend():
    movie_title = request.args.get('movie')
    if not movie_title:
        return jsonify({'error': 'No movie title provided'}), 400
    
    try:
        # Details of searched movie
        movie_row = movies[movies['title'] == movie_title].iloc[0]
        searched_movie = {
            'title': movie_row['title'],
            'poster_url': fetch_poster(movie_row['movie_id'], movie_row['title'])
        }
        
        # Recommendations
        recs_df = get_recommendations(movie_title)
        recommendations = []
        for _, row in recs_df.iterrows():
            recommendations.append({
                'title': row['title'],
                'poster_url': fetch_poster(row['movie_id'], row['title'])
            })
            
        return jsonify({
            'searched_movie': searched_movie,
            'recommendations': recommendations
        })
    except Exception as e:
        print(f"Recommendation error: {e}")
        return jsonify({'error': 'Movie not found or analysis failed'}), 404

@app.route('/movies-by-genre')
def movies_by_genre():
    genre = request.args.get('genre', '').lower()
    if not genre:
        return jsonify({'error': 'No genre provided'}), 400
    
    results = []
    # Filter movies by tag
    filtered = movies[movies['tags'].str.contains(genre, case=False, na=False)].head(12)
    for _, row in filtered.iterrows():
        results.append({
            'title': row['title'],
            'poster_url': fetch_poster(row['movie_id'], row['title'])
        })
    
    return jsonify({'movies': results})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
