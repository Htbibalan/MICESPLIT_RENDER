from flask import Flask, render_template, request, jsonify
import csv
import io

app = Flask(__name__)

# Store mouse data
mice_data = []

def split_list(lst, n):
    """
    Splits the list lst into n contiguous sublists.
    This preserves the order so that mice with similar weights (after sorting)
    will end up in the same group.
    """
    k, m = divmod(len(lst), n)
    result = []
    start = 0
    for i in range(n):
        end = start + k + (1 if i < m else 0)
        result.append(lst[start:end])
        start = end
    return result

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add_mouse', methods=['POST'])
def add_mouse():
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
    """Allows users to upload a CSV file with headers mouseID and bodyweight."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Only CSV files are allowed"}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)
        new_mice = []
        for row in reader:
            # Allow headers: either "mouseID" or "MouseID"
            if 'mouseID' in row:
                id_val = row['mouseID']
            elif 'MouseID' in row:
                id_val = row['MouseID']
            else:
                return jsonify({"error": "CSV must contain a 'mouseID' column"}), 400

            # Allow headers: either "bodyweight" or "Weight"
            if 'bodyweight' in row:
                weight_val = row['bodyweight']
            elif 'Weight' in row:
                weight_val = row['Weight']
            else:
                return jsonify({"error": "CSV must contain a 'bodyweight' column"}), 400

            try:
                weight_float = float(weight_val)
            except ValueError:
                return jsonify({"error": f"Invalid weight value for {id_val}"}), 400

            new_mice.append({"mouse_id": id_val, "weight": weight_float})
        global mice_data
        mice_data.extend(new_mice)
        return jsonify({"message": f"{len(new_mice)} mice added successfully from CSV.", "mice_data": mice_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/distribute', methods=['POST'])
def distribute():
    """
    Distributes the mice into groups by first sorting them by weight
    so that similar weights end up together.
    """
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

    # Sort mice by weight in ascending order so that similar weights are contiguous.
    sorted_mice = sorted(mice_data, key=lambda x: x['weight'])
    groups = split_list(sorted_mice, n_groups)
    
    # Calculate the total weight for each group.
    group_weights = [sum(mouse['weight'] for mouse in group) for group in groups]

    # Clear mice_data after distribution to avoid duplicate entries on subsequent runs.
    mice_data.clear()

    return jsonify({"groups": groups, "weights": group_weights})

@app.route('/health')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True)
