from flask import Flask, request, jsonify
from flask_cors import CORS
from vector_store import VectorStore

app = Flask(__name__)
CORS(app)

# Initialize your vector store or search engine here
vector_store = VectorStore()

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    query = data.get('query')
    filter_val = data.get('filter')
    if not query:
        return jsonify({"error": "Missing query"}), 400
    try:
        # Perform the real semantic search
        results = vector_store.hybrid_search(query)
        # Format results for frontend
        formatted = [
            {
                "pdf_name": res["payload"]["pdf_name"],
                "page": res["payload"]["page"],
                "text": res["payload"]["text"][:300] + ("..." if len(res["payload"]["text"]) > 300 else "")
            }
            for res in results
        ]
        return jsonify({"results": formatted})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002) 