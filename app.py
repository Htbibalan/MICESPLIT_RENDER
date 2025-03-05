from flask import Flask, render_template, request, jsonify
import csv
import io
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster

app = Flask(__name__)

# Store mouse data
mice_data = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add_mouse', methods=['POST'])
def add_mouse():
    """Manually add a mouse with its weight"""
    data = request.json
    mouse_id = data.get("mouse_id")
    weight = data.get("weight")

    if not mouse_id or not weight:
        return jsonify({"error": "Mouse ID and weight are required"}), 400

    try:
        weight = float(weight)
    except ValueError:
        return jsonify({"error": "Weight must be a number."}), 400

    # Ensure no duplicate entries
    if any(mouse['mouse_id'] == mouse_id for mouse in mice_data):
        return jsonify({"error": f"Mouse ID {mouse_id} already exists!"}), 400

    mice_data.append({"mouse_id": mouse_id, "weight": weight})
    return jsonify({"message": f"Mouse {mouse_id} added successfully!", "mice_data": mice_data})

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    """ Accepts a CSV file and processes the data """
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Only CSV files are allowed"}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)
        new_mice = []

        for row in reader:
            if 'MouseID' not in row or 'Weight' not in row:
                return jsonify({"error": "CSV must contain 'MouseID' and 'Weight' columns"}), 400
            
            try:
                weight = float(row['Weight'])
            except ValueError:
                return jsonify({"error": f"Invalid weight value for {row['MouseID']}"}), 400

            new_mice.append({"mouse_id": row['MouseID'], "weight": weight})

        # Merge new data with manually added mice
        global mice_data
        mice_data.extend(new_mice)

        return jsonify({"message": f"{len(new_mice)} mice added successfully from CSV.", "mice_data": mice_data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/distribute', methods=['POST'])
def distribute():
    """Distribute mice into cages using hierarchical clustering"""
    data = request.json
    n_groups = data.get("n_groups")

    try:
        n_groups = int(n_groups)
        if n_groups <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Number of groups must be a positive integer."}), 400

    if len(mice_data) == 0:
        return jsonify({"error": "No mice data to distribute."}), 400

    # Convert data to numpy array for clustering
    weights = np.array([m["weight"] for m in mice_data]).reshape(-1, 1)

    # Perform Hierarchical Clustering
    Z = linkage(weights, method='ward')  # Ward minimizes variance
    labels = fcluster(Z, n_groups, criterion='maxclust')

    # Group mice according to clusters
    groups = {i: [] for i in range(1, n_groups+1)}
    for i, label in enumerate(labels):
        groups[label].append(mice_data[i])

    return jsonify({"groups": groups})

@app.route('/sample_csv')
def sample_csv():
    """ Provides a correctly formatted sample CSV file """
    sample_data = "MouseID,Weight\nM1,23.5\nM2,21.8\nM3,25.2\nM4,20.0\nM5,22.3\n"
    return sample_data, 200, {
        "Content-Type": "text/csv",
        "Content-Disposition": "attachment; filename=sample_mice.csv"
    }

@app.route('/health')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True)
