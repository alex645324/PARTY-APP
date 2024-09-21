from flask import Flask, render_template, redirect, request, url_for
from google.cloud import firestore

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'

# Initialize Firestore
firestore_db = firestore.Client()

# Default route to redirect to the admin dashboard
@app.route('/')
def index():
    return redirect(url_for('admin_dashboard'))

# Admin dashboard route to display users, parties, and statistics
@app.route('/admin')
def admin_dashboard():
    # Fetch all users
    users_ref = firestore_db.collection('users')
    users = [user.to_dict() for user in users_ref.stream()]
    total_users = len(users)

    # Calculate total messages and average messages per user
    total_messages = sum(user.get('messages_sent', 0) for user in users)
    avg_messages_per_user = total_messages // total_users if total_users > 0 else 0

    # Fetch all parties
    parties_ref = firestore_db.collection('parties')
    parties = [{**party.to_dict(), 'id': party.id} for party in parties_ref.stream()]

    return render_template('admin_dashboard.html', users=users, total_users=total_users, 
                           avg_messages_per_user=avg_messages_per_user, parties=parties)

# Route to add new parties
@app.route('/add_party', methods=['POST'])
def add_party():
    address = request.form['address']
    party_type = request.form['party_type']
    ticket_info = request.form['ticket_info']
    instructions = request.form['instructions']
    link = request.form['link']

    new_party = {
        'address': address,
        'type': party_type,
        'ticket_info': ticket_info,
        'instructions': instructions,
        'link': link
    }
    firestore_db.collection('parties').add(new_party)
    return redirect(url_for('admin_dashboard'))

# Route to delete parties
@app.route('/delete_party/<party_id>', methods=['POST'])
def delete_party(party_id):
    firestore_db.collection('parties').document(party_id).delete()
    return redirect(url_for('admin_dashboard'))

# Route to approve partygoers
@app.route('/approve/<phone_number>', methods=['POST'])
def approve_partygoer(phone_number):
    user_ref = firestore_db.collection('users').document(phone_number)
    user_ref.update({'partygoer_approved': True})
    return redirect(url_for('admin_dashboard'))

# Route to disapprove (unapprove) partygoers
@app.route('/disapprove/<phone_number>', methods=['POST'])
def disapprove_partygoer(phone_number):
    user_ref = firestore_db.collection('users').document(phone_number)
    user_ref.update({'partygoer_approved': False})
    return redirect(url_for('admin_dashboard'))

# Route to delete users
@app.route('/delete_user/<phone_number>', methods=['POST'])
def delete_user(phone_number):
    firestore_db.collection('users').document(phone_number).delete()
    return redirect(url_for('admin_dashboard'))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001)
