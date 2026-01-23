/**
 * CineMatch - Modern Movie Recommendation System
 * Frontend Logic with Global Global Search
 */

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    const searchInput = document.getElementById('movie-search');
    const dropdown = document.getElementById('movie-dropdown');
    const movieSelect = document.getElementById('movie-select');

    // Load movies from JSON script tag
    const dataTag = document.getElementById('movies-data');
    if (dataTag) {
        try {
            window.ALL_MOVIES = JSON.parse(dataTag.textContent);
        } catch (e) {
            console.error("Failed to parse movie data", e);
            window.ALL_MOVIES = [];
        }
    }

    // UI Events
    searchInput.addEventListener('focus', () => {
        dropdown.classList.add('show');
        if (searchInput.value.trim() === '') {
            renderSearchResults([]); // Show hint if empty
        }
    });

    // Helper to trigger search from landing page
    window.selectMovie = (title) => {
        searchInput.value = title;
        movieSelect.value = title;
        getRecommendations();
    };

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        movieSelect.value = ''; // Clear selection on manual type to prevent stale data
        if (query.length > 0) {
            const matches = findMatches(query);
            renderSearchResults(matches);
        } else {
            renderSearchResults([]);
        }
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.input-wrapper')) {
            dropdown.classList.remove('show');
        }
    });

    // Handle Dropdown Clicks (Delegation)
    dropdown.addEventListener('click', (e) => {
        const item = e.target.closest('.dropdown-item');
        if (!item) return;

        const value = item.getAttribute('data-value');
        const type = item.getAttribute('data-type');

        if (type === 'genre') {
            loadGenreMovies(value);
        } else if (type === 'movie') {
            const text = item.innerText.trim();
            searchInput.value = text;
            movieSelect.value = text;
            dropdown.classList.remove('show');
            getRecommendations(); // Auto-search on select
        }
    });

    // Keyboard navigation
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const movie = searchInput.value.trim();
            if (movie) {
                movieSelect.value = movie;
                getRecommendations();
                dropdown.classList.remove('show');
            }
        }
    });
}

/**
 * Finds matches in the global movies array
 */
function findMatches(query) {
    if (!window.ALL_MOVIES) return [];
    const lowerQuery = query.toLowerCase();

    // Filter and limit to top 50 results for performance
    return window.ALL_MOVIES
        .filter(title => title.toLowerCase().includes(lowerQuery))
        .slice(0, 50);
}

/**
 * Renders search results into the dropdown
 */
function renderSearchResults(matches) {
    const container = document.getElementById('movie-list-container');
    const title = document.getElementById('dropdown-results-title');

    if (matches.length === 0) {
        title.innerText = "Suggested Movies";
        container.innerHTML = '<div class="dropdown-item hint-item">Type to find any of the 4,800+ movies...</div>';
        return;
    }

    title.innerText = `Matches (${matches.length})`;
    container.innerHTML = matches.map(movie => `
        <div class="dropdown-item movie-item" data-value="${movie}" data-type="movie">
            <i class="fas fa-play-circle"></i> ${movie}
        </div>
    `).join('');
}

async function loadGenreMovies(genre) {
    const loading = document.getElementById('loading');
    const results = document.getElementById('recommendations');
    const grid = document.getElementById('movies-grid');
    const dashboardInit = document.getElementById('dashboard-init');
    const featuredContainer = document.getElementById('featured-movie-container');
    const searchInput = document.getElementById('movie-search');
    const dropdown = document.getElementById('movie-dropdown');

    // Show Loading
    loading.style.display = 'block';
    results.style.display = 'none';
    if (dashboardInit) dashboardInit.style.display = 'none';
    grid.innerHTML = '';
    featuredContainer.innerHTML = '';
    dropdown.classList.remove('show');

    try {
        const response = await fetch(`/movies-by-genre?genre=${encodeURIComponent(genre)}`);
        const data = await response.json();

        if (data.movies) {
            // Update UI for Genre Results
            document.querySelector('#recommendations .section-header h2').innerText = `${genre} Movies`;
            document.querySelector('.featured-section').style.display = 'none'; // Hide "Now Selected" for genre view

            data.movies.forEach((movie, idx) => {
                const card = createMovieCard(movie, idx);
                grid.appendChild(card);
            });

            loading.style.display = 'none';
            results.style.display = 'block';
            results.scrollIntoView({ behavior: 'smooth' });
            searchInput.placeholder = `Search in ${genre}...`;
        }
    } catch (err) {
        loading.style.display = 'none';
        console.error("Genre fetch error:", err);
    }
}

async function getRecommendations() {
    const movieInput = document.getElementById('movie-search');
    const movieSelect = document.getElementById('movie-select');
    const movie = movieSelect.value || movieInput.value;

    if (!movie) return;

    const loading = document.getElementById('loading');
    const results = document.getElementById('recommendations');
    const grid = document.getElementById('movies-grid');
    const featuredContainer = document.getElementById('featured-movie-container');
    const dashboardInit = document.getElementById('dashboard-init');

    // Show Loading
    loading.style.display = 'block';
    results.style.display = 'none';
    if (dashboardInit) dashboardInit.style.display = 'none';
    grid.innerHTML = '';
    featuredContainer.innerHTML = '';

    // Reset UI state for search
    document.querySelector('#recommendations .section-header h2').innerText = "Similar Movies You'll Love";
    document.querySelector('.featured-section').style.display = 'block';

    try {
        const response = await fetch(`/recommend?movie=${encodeURIComponent(movie)}`);
        const data = await response.json();

        if (data.searched_movie) {
            // Render the movie that was searched for
            const featuredCard = createMovieCard(data.searched_movie, 0, true);
            featuredContainer.appendChild(featuredCard);

            // Render recommendations
            if (data.recommendations && data.recommendations.length > 0) {
                data.recommendations.forEach((rec, idx) => {
                    const card = createMovieCard(rec, idx + 1);
                    grid.appendChild(card);
                });
            } else {
                grid.innerHTML = '<div class="no-results">No similar movies found.</div>';
            }

            loading.style.display = 'none';
            results.style.display = 'block';
            results.scrollIntoView({ behavior: 'smooth' });
        } else {
            throw new Error(data.error || "Movie details not found");
        }
    } catch (err) {
        loading.style.display = 'none';
        alert("Sorry, we couldn't find that movie in our database. Try selecting from the dropdown!");
    }
}

function createMovieCard(movie, index, isFeatured = false) {
    const div = document.createElement('div');
    div.className = isFeatured ? 'movie-card featured-card' : 'movie-card';
    div.style.animation = `fadeInUp 0.6s ease forwards ${index * 0.1}s`;
    div.style.opacity = '0';

    // Use a better fallback image if the API or poster fails
    const fallbackImage = 'https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=300&h=450&auto=format&fit=crop';
    const posterUrl = movie.poster_url && !movie.poster_url.includes('placeholder')
        ? movie.poster_url
        : fallbackImage;

    div.innerHTML = `
        <img class="movie-poster" src="${posterUrl}" alt="${movie.title}" onerror="this.onerror=null; this.src='${fallbackImage}';">
        <div class="movie-overlay">
            <h3 class="movie-title">${movie.title}</h3>
            <div class="movie-meta">
                <span class="view-btn"><i class="fas fa-plus"></i> ${isFeatured ? 'Currently Selected' : 'Details'}</span>
            </div>
        </div>
    `;

    if (!isFeatured) {
        div.addEventListener('click', () => {
            document.getElementById('movie-search').value = movie.title;
            document.getElementById('movie-select').value = movie.title;
            getRecommendations();
        });
    }

    return div;
}

// Global Animation
if (!document.getElementById('dynamic-animations')) {
    const style = document.createElement('style');
    style.id = 'dynamic-animations';
    style.textContent = `
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    `;
    document.head.appendChild(style);
}
