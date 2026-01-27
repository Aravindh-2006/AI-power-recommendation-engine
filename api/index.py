import sys
import os
from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
import pickle

# Get the parent directory
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Create Flask app with absolute paths
app = Flask(__name__, 
            static_folder=os.path.join(current_dir, 'static'),
            template_folder=os.path.join(current_dir, 'templates'))

def load_data():
    """Load movie data from pickle or sample data as fallback"""
    try:
        pickle_path = os.path.join(current_dir, 'movie_data.pkl')
        if os.path.exists(pickle_path):
            with open(pickle_path, 'rb') as f:
                movies, cosine_sim = pickle.load(f)
            print(f"Loaded movie data from {pickle_path}")
            return movies, cosine_sim
    except Exception as e:
        print(f"Error loading pickle: {e}")
    
    # Try JSON as fallback
    try:
        json_path = os.path.join(current_dir, 'filtered_credits.json')
        if os.path.exists(json_path):
            import json
            with open(json_path, 'r') as f:
                data = json.load(f)
            movies = pd.DataFrame(data)
            cosine_sim = [[1.0] * len(movies) for _ in range(len(movies))]
            print("Loaded data from filtered_credits.json")
            return movies, cosine_sim
    except Exception as e:
        print(f"Error loading JSON: {e}")
    
    # Fallback sample data
    sample = {
        'title': ['The Shawshank Redemption', 'The Godfather', 'The Dark Knight', 'Pulp Fiction', 'Forrest Gump'],
        'movie_id': [278, 238, 155, 680, 13],
        'tags': ['Drama', 'Crime', 'Action', 'Crime', 'Drama']
    }
    movies = pd.DataFrame(sample)
    cosine_sim = [[1.0] * len(movies) for _ in range(len(movies))]
    return movies, cosine_sim

movies, cosine_sim = load_data()

def get_recommendations(title, cosine_sim=cosine_sim):
    """Get movie recommendations based on similarity"""
    if cosine_sim is None or movies.empty:
        return pd.DataFrame()
    
    try:
        idx = movies[movies['title'] == title].index[0]
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:11]
        movie_indices = [i[0] for i in sim_scores]
        cols = ['title', 'movie_id', 'tags'] if 'tags' in movies.columns else ['title', 'movie_id']
        return movies[cols].iloc[movie_indices]
    except:
        return pd.DataFrame()

def fetch_poster(movie_id, movie_title=None):
    """Fetch movie poster from TMDB"""
    api_key = '7b995d3c6fd91a2284b4ad8cb390c7b8'
    
    try:
        url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}'
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('poster_path'):
                return f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
    except:
        pass
    
    if movie_title:
        try:
            url = f'https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={requests.utils.quote(movie_title)}'
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                results = response.json().get('results', [])
                if results and results[0].get('poster_path'):
                    return f"https://image.tmdb.org/t/p/w500{results[0]['poster_path']}"
        except:
            pass
    
    return "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&h=750&auto=format&fit=crop"

@app.route('/')
def index():
    """Serve the main page"""
    if movies.empty:
        return render_template('index.html', genres=[], movies=[], trending_movies=[])
    
    genres_set = set()
    popular_genres = ['Action', 'Comedy', 'Drama', 'Horror', 'Sci-Fi', 'Animation', 'Thriller', 'Adventure']
    
    for tags in movies['tags'].dropna():
        for g in popular_genres:
            if g.lower() in str(tags).lower():
                genres_set.add(g)
    
    genre_list = sorted(list(genres_set))
    movie_list = sorted(movies['title'].tolist())
    
    trending_indices = list(range(min(5, len(movies))))
    trending_movies = []
    for i in trending_indices:
        row = movies.iloc[i]
        trending_movies.append({
            'title': row['title'],
            'poster_url': fetch_poster(row['movie_id'], row['title'])
        })
    
    return render_template('index.html', genres=genre_list, movies=movie_list, trending_movies=trending_movies)

@app.route('/recommend')
def recommend():
    """Get recommendations for a movie"""
    movie_title = request.args.get('movie')
    if not movie_title:
        return jsonify({'error': 'No movie title provided'}), 400
    
    try:
        movie_row = movies[movies['title'] == movie_title].iloc[0]
        searched_movie = {
            'title': movie_row['title'],
            'poster_url': fetch_poster(movie_row['movie_id'], movie_row['title'])
        }
        
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
        print(f"Error: {e}")
        return jsonify({'error': 'Movie not found'}), 404

@app.route('/movies-by-genre')
def movies_by_genre():
    """Get movies by genre"""
    genre = request.args.get('genre', '').lower()
    if not genre:
        return jsonify({'error': 'No genre provided'}), 400
    
    results = []
    if 'tags' in movies.columns:
        filtered = movies[movies['tags'].str.contains(genre, case=False, na=False)].head(12)
        for _, row in filtered.iterrows():
            results.append({
                'title': row['title'],
                'poster_url': fetch_poster(row['movie_id'], row['title'])
            })
    
    return jsonify({'movies': results})

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('index.html', genres=[], movies=[], trending_movies=[])

if __name__ == '__main__':
    app.run(debug=False)
