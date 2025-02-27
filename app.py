from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Store mouse data
mice_data = []

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

@app.route('/distribute', methods=['POST'])
def distribute():
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

    # Sort mice by weight (descending)
    sorted_mice = sorted(mice_data, key=lambda x: x['weight'], reverse=True)
    groups = [[] for _ in range(n_groups)]
    group_sums = [0.0] * n_groups

    for mouse in sorted_mice:
        # Find the group with the lowest total weight
        lightest_group_idx = group_sums.index(min(group_sums))
        groups[lightest_group_idx].append(mouse)
        group_sums[lightest_group_idx] += mouse['weight']

    # Clear mice data after distribution to prevent duplicate entries on next run
    mice_data.clear()

    return jsonify({"groups": groups, "weights": group_sums})
@app.route('/health')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True)
