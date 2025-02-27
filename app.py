import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Data structure to store (mouse_id, weight)
mice_data = []

@app.route('/')
def index():
    return render_template('index.html', mice_data=mice_data)

@app.route('/add_mouse', methods=['POST'])
def add_mouse():
    mouse_id = request.form['mouse_id']
    weight = request.form['weight']
    if not mouse_id or not weight:
        return jsonify({'error': 'Mouse ID and Weight are required.'}), 400
    try:
        weight = float(weight)
    except ValueError:
        return jsonify({'error': 'Weight must be a number.'}), 400
    
    mice_data.append((mouse_id, weight))
    return jsonify({'success': 'Mouse added successfully.'})

@app.route('/distribute', methods=['POST'])
def distribute():
    n_groups = request.form['groups']
    if not n_groups:
        return jsonify({'error': 'Please enter number of groups.'}), 400
    try:
        n_groups = int(n_groups)
        if n_groups <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'error': 'Number of groups must be a positive integer.'}), 400

    if len(mice_data) == 0:
        return jsonify({'error': 'No mice data to distribute.'}), 400

    groups = distribute_mice_by_weight(mice_data, n_groups)
    return jsonify(groups=groups)

def distribute_mice_by_weight(mice, n_groups):
    mice_sorted = sorted(mice, key=lambda x: x[1], reverse=True)
    groups = [[] for _ in range(n_groups)]
    sums = [0.0]*n_groups

    for mouse_id, wt in mice_sorted:
        idx = sums.index(min(sums))
        groups[idx].append((mouse_id, wt))
        sums[idx] += wt

    return groups

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
