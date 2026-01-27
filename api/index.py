import sys
import os

# Set up paths
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, current_dir)

try:
    from flask import Flask, render_template, request, jsonify
    import pandas as pd
    import requests
    import pickle
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Create Flask app with absolute paths
try:
    static_path = os.path.join(current_dir, 'static')
    template_path = os.path.join(current_dir, 'templates')
    
    app = Flask(__name__, 
                static_folder=static_path,
                static_url_path='/static',
                template_folder=template_path)
    app.config['JSON_SORT_KEYS'] = False
except Exception as e:
    print(f"Flask initialization error: {e}")
    raise

def load_data():
    """Load movie data from pickle or sample data as fallback"""
    try:
        pickle_path = os.path.join(current_dir, 'movie_data.pkl')
        if os.path.exists(pickle_path):
            with open(pickle_path, 'rb') as f:
                movies, cosine_sim = pickle.load(f)
            return movies, cosine_sim
    except Exception as e:
        print(f"Pickle load error: {e}")
    
    # Try JSON fallback
    try:
        json_path = os.path.join(current_dir, 'filtered_credits.json')
        if os.path.exists(json_path):
            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            movies = pd.DataFrame(data)
            cosine_sim = [[1.0] * len(movies) for _ in range(len(movies))]
            return movies, cosine_sim
    except Exception as e:
        print(f"JSON load error: {e}")
    
    # Fallback sample data
    try:
        sample = {
            'title': ['The Shawshank Redemption', 'The Godfather', 'The Dark Knight', 'Pulp Fiction', 'Forrest Gump'],
            'movie_id': [278, 238, 155, 680, 13],
            'tags': ['Drama', 'Crime', 'Action', 'Crime', 'Drama']
        }
        movies = pd.DataFrame(sample)
        cosine_sim = [[1.0] * len(movies) for _ in range(len(movies))]
        return movies, cosine_sim
    except Exception as e:
        print(f"Sample data error: {e}")
        return pd.DataFrame(), None

# Load data at startup
try:
    movies, cosine_sim = load_data()
    print(f"Loaded {len(movies)} movies")
except Exception as e:
    print(f"Critical error loading data: {e}")
    movies, cosine_sim = pd.DataFrame(), None

def get_recommendations(title, cosine_sim=cosine_sim):
    """Get movie recommendations based on similarity"""
    if cosine_sim is None or movies.empty:
        return pd.DataFrame()
    
    try:
        matches = movies[movies['title'] == title]
        if matches.empty:
            return pd.DataFrame()
        
        idx = matches.index[0]
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:11]
        movie_indices = [i[0] for i in sim_scores]
        
        cols = ['title', 'movie_id', 'tags'] if 'tags' in movies.columns else ['title', 'movie_id']
        return movies[cols].iloc[movie_indices]
    except Exception as e:
        print(f"Recommendation error: {e}")
        return pd.DataFrame()

def fetch_poster(movie_id, movie_title=None):
    """Fetch movie poster from TMDB"""
    api_key = '7b995d3c6fd91a2284b4ad8cb390c7b8'
    
    try:
        url = f'https://api.themoviedb.org/3/movie/{int(movie_id)}?api_key={api_key}'
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('poster_path'):
                return f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
    except Exception:
        pass
    
    if movie_title:
        try:
            search_url = f'https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={requests.utils.quote(str(movie_title))}'
            response = requests.get(search_url, timeout=2)
            if response.status_code == 200:
                results = response.json().get('results', [])
                if results and results[0].get('poster_path'):
                    return f"https://image.tmdb.org/t/p/w500{results[0]['poster_path']}"
        except Exception:
            pass
    
    return "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&h=750&auto=format&fit=crop"

@app.route('/')
def index():
    """Serve the main page"""
    try:
        if movies.empty:
            return jsonify({
                'status': 'ok',
                'genres': [],
                'movies': [],
                'trending_movies': []
            })
        
        genres_set = set()
        popular_genres = ['Action', 'Comedy', 'Drama', 'Horror', 'Sci-Fi', 'Animation', 'Thriller', 'Adventure']
        
        if 'tags' in movies.columns:
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
                'title': str(row['title']),
                'poster_url': fetch_poster(row['movie_id'], row['title'])
            })
        
        return jsonify({
            'status': 'ok',
            'genres': genre_list,
            'movies': movie_list,
            'trending_movies': trending_movies
        })
    except Exception as e:
        print(f"Index error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/recommend')
def recommend():
    """Get recommendations for a movie"""
    try:
        movie_title = request.args.get('movie', '').strip()
        if not movie_title:
            return jsonify({'error': 'No movie title provided'}), 400
        
        matches = movies[movies['title'] == movie_title]
        if matches.empty:
            return jsonify({'error': 'Movie not found'}), 404
        
        movie_row = matches.iloc[0]
        searched_movie = {
            'title': str(movie_row['title']),
            'poster_url': fetch_poster(movie_row['movie_id'], movie_row['title'])
        }
        
        recs_df = get_recommendations(movie_title)
        recommendations = []
        for _, row in recs_df.iterrows():
            recommendations.append({
                'title': str(row['title']),
                'poster_url': fetch_poster(row['movie_id'], row['title'])
            })
        
        return jsonify({
            'searched_movie': searched_movie,
            'recommendations': recommendations
        })
    except Exception as e:
        print(f"Recommend error: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/movies-by-genre')
def movies_by_genre():
    """Get movies by genre"""
    try:
        genre = request.args.get('genre', '').lower().strip()
        if not genre:
            return jsonify({'error': 'No genre provided'}), 400
        
        results = []
        if 'tags' in movies.columns:
            filtered = movies[movies['tags'].str.contains(genre, case=False, na=False)].head(12)
            for _, row in filtered.iterrows():
                results.append({
                    'title': str(row['title']),
                    'poster_url': fetch_poster(row['movie_id'], row['title'])
                })
        
        return jsonify({'movies': results})
    except Exception as e:
        print(f"Genre error: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found', 'status': 'not_found'}), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    print(f"Server error: {e}")
    import traceback
    traceback.print_exc()
    return jsonify({'error': 'Internal server error', 'status': 'error'}), 500

if __name__ == '__main__':
    app.run(debug=False)
