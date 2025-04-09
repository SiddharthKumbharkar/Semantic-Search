# from flask import Flask, request, jsonify
# from vector_store import VectorStore
# from flask_cors import CORS

# app = Flask(__name__)
# # Enable CORS for the Flask app
# CORS(app, resources={r"/*": {"origins": "*"}})
# # Initialize the VectorStore
# vector_store = VectorStore()    

# @app.route('/generate', methods=['POST'])
# def generate():
#     """
#     API endpoint to perform vector search based on the input query.
#     """
#     try:
#         # Get the query from the request JSON
#         data = request.get_json()
#         query = data.get('query', '').strip()
        
#         if not query:
#             return jsonify({"error": "Query is required"}), 400
        
#         # Perform the hybrid search
#         results = vector_store.hybrid_search(query)
        
#         # Format the results
#         formatted_results = [
#             {
#                 "pdf_name": res['payload']['pdf_name'],
#                 "page": res['payload']['page'],
#                 "text": res['payload']['text'][:300] + ("..." if len(res['payload']['text']) > 300 else "")
#             }
#             for res in results
#         ]
#         print(f"Formatted results: {formatted_results}")
#         return jsonify({"results": formatted_results}), 200
    
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     app.run(debug=True)


from flask import Flask, request, jsonify
from flask_cors import CORS
from vector_store import VectorStore
from pdf_processor import PDFProcessor
import os
from werkzeug.utils import secure_filename
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploaded_pdfs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

vector_store = VectorStore()
processor = PDFProcessor()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    """
    API endpoint to perform vector search based on the input query.
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Query is required"}), 400

        results = vector_store.hybrid_search(query)
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
        logger.exception("Error during search")
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_pdfs():
    """
    Upload and process multiple PDF files, chunk them, and index them in the vector store.
    """
    try:
        files = request.files.getlist('files')
        if not files or len(files) == 0:
            return jsonify({"error": "No files provided"}), 400

        results = []

        for file in files:
            if file.filename == '':
                continue  # Skip empty filenames

            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            logger.info(f"Processing uploaded file: {filename}")
            pages_text = processor.extract_text_from_pdf(save_path)
            chunks = processor.chunk_text(pages_text)

            if chunks:
                logger.info(f"Indexing {len(chunks)} chunks for {filename}")
                vector_store.create_index(chunks)
                results.append({"filename": filename, "chunks_indexed": len(chunks)})
            else:
                results.append({"filename": filename, "message": "No text extracted"})

        return jsonify({"results": results}), 200

    except Exception as e:
        logger.exception("Error while uploading or processing PDFs")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
