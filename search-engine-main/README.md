# Simple Search Engine
Welcome to the Simple Search Engine! This application allows you to crawl and index data, then search through it using a web-based interface powered by Flask.

## Getting Started
To get started with the Simple Search Engine, follow the instructions below. Make sure you have installed all the required dependencies before proceeding.

### Prerequisites
Ensure you have the following Python packages installed:

**python**
**requests**
**beautifulsoup4**
**flask**
**whoosh**
You can install these dependencies using the following command:

```bash
pip install requests beautifulsoup4 flask whoosh
```
or 
```bash
pip install -r requirements.txt
```

### Running the Application
Follow these steps to run the application:

1. Start the Crawler
Run the `crawler.py` script to crawl and index the data:

```bash
python crawler.py
```

2. Configure the Application
Next, run the `config.py` script to set up the application’s configuration:

```bash
python config.py
```

3. Launch the Flask Application
Finally, start the Flask server by running the `flask_app.py` script:

```bash
python flask_app.py
```
Upon successful execution, the Flask server will start, and the application will be accessible through your web browser, usually at:
http://localhost:5000

#### Usage
Once the application is running, you can use the web interface to perform searches. Simply enter your search query, and the engine will display results based on the data indexed by the crawler.

#### Contributing
We welcome contributions to enhance the project! To contribute:

Fork the repository.
Create a new branch for your feature or bugfix.
Submit a pull request once your changes are ready.
Thank you for helping us improve the Simple Search Engine!
