# CineMatch | AI-Powered Movie Recommendation System

This project is a modern, high-end movie recommendation system built with **Flask** and powered by a machine learning model. It recommends movies based on a selected title using cosine similarity and displays high-quality movie posters fetched via the TMDB API.

## 🌟 Key Features
- **Professional UI**: A premium "Midnight & Amber Gold" theme with glassmorphism and smooth animations.
- **Dynamic Search**: Real-time search through 4,800+ movies.
- **Genre Discovery**: Explore movies by categories like Action, Sci-Fi, and more.
- **AI-Powered**: Uses NLP and Cosine Similarity to find perfect matches.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Dataset](#dataset)

## Overview
CineMatch helps users discover movies similar to their favorites. By selecting or searching for a movie, users receive a list of top 10 recommended cinematic matches. The system is built with a custom HTML/CSS/JS frontend and a Flask backend, providing a much more creative and premium experience than standard Streamlit apps.

## Installation
1. Clone the project and navigate to the directory:
    ```bash
    cd AI-power-recommendation-engine
    ```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage
1. Start the Flask application:
    ```bash
    python flask_app.py
    ```

2. Open your web browser and go to `http://127.0.0.1:5000`.

3. Use the search bar or genre pills to find a movie you love and click "Analyze & Match".

## Dataset

The dataset used for this project contains information about movies, including their titles and IDs. It is processed and stored in `movie_data.pkl`. The dataset is used to calculate the cosine similarity between movies.

## Model

The model for recommending movies is based on cosine similarity. Cosine similarity is used to measure the similarity between movie titles. The model computes the similarity scores and suggests the top 10 similar movies based on the selected movie title.

## Results

The system provides the top 10 recommended movies for any selected movie title. It also fetches and displays the posters of these recommended movies using the TMDB API.

![Screenshot 2024-07-12 103743](https://github.com/user-attachments/assets/fbc357a1-a6e6-472a-892b-95fe96767743)

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
