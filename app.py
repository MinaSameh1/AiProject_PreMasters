# Import app from src
from src import server
import os

port = int(os.environ.get('PORT', 5000))

# Run app
if __name__ == '__main__':
    print('Running app on port: ' + str(port)) 
    server.app.run(debug=True, port=port)
