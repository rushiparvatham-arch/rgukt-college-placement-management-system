from app import create_app

app = create_app()

if __name__ == "__main__":
    # threaded=True is required here: the dashboards fire several API calls in
    # parallel (profile, notifications, stats, lists) on every navigation, and
    # Flask's default single-threaded dev server can refuse simultaneous
    # connections outright — which surfaces in the browser as "Failed to fetch".
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
