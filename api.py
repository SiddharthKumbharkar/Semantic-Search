from flask import Flask, request, jsonify
from vector_store import VectorStore
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for the Flask app
CORS(app, resources={r"/*": {"origins": "*"}})
# Initialize the VectorStore
vector_store = VectorStore()

@app.route('/generate', methods=['POST'])
def generate():
    """
    API endpoint to perform vector search based on the input query.
    """
    try:
        # Get the query from the request JSON
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Perform the hybrid search
        results = vector_store.hybrid_search(query)
        
        # Format the results
        formatted_results = [
            {
                "pdf_name": res['payload']['pdf_name'],
                "page": res['payload']['page'],
                "text": res['payload']['text'][:300] + ("..." if len(res['payload']['text']) > 300 else "")
            }
            for res in results
        ]
        print(f"Formatted results: {formatted_results}")
        return jsonify({"results": formatted_results}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)