import os
from flask import Flask, redirect
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from google.cloud import firestore
from flask_migrate import Migrate




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///admin.db'  # Using SQLite for simplicity
app.config['SECRET_KEY'] = 'mysecret'  # A secret key for security purposes
db = SQLAlchemy(app)
migrate = Migrate(app, db)
admin = Admin(app, name='Party Admin', template_mode='bootstrap3')

# Initialize Firestore
firestore_db = firestore.Client()


# SQLAlchemy models for admin interface
class Party(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(200))
    party_type = db.Column(db.String(50))
    ticket_info = db.Column(db.String(200))
    instructions = db.Column(db.Text)
    link = db.Column(db.String(200))

class UserCreatedParty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    music = db.Column(db.String(200))
    theme = db.Column(db.String(200))
    venue = db.Column(db.String(200))
    location = db.Column(db.String(200))
    dates = db.Column(db.String(200))
    created_by = db.Column(db.String(100))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20))
    joined = db.Column(db.Boolean, default=False)
    partygoer_approved = db.Column(db.Boolean, default=False)  # New field for approval status

with app.app_context():
    db.create_all()

# Admin views
class PartyModelView(ModelView):
    column_list = ('id', 'address', 'party_type', 'ticket_info', 'instructions', 'link')
    form_columns = ('address', 'party_type', 'ticket_info', 'instructions', 'link')

    def create_model(self, form):
        # Create a new party in Firestore
        new_party = {
            'address': form.address.data,
            'type': form.party_type.data,
            'ticket_info': form.ticket_info.data,
            'instructions': form.instructions.data,
            'link': form.link.data
        }
        doc_ref = firestore_db.collection('parties').add(new_party)
        return super(PartyModelView, self).create_model(form)

    def update_model(self, form, model):
        # Update the party in Firestore
        party_ref = firestore_db.collection('parties').document(str(model.id))
        updated_party = {
            'address': form.address.data,
            'type': form.party_type.data,
            'ticket_info': form.ticket_info.data,
            'instructions': form.instructions.data,
            'link': form.link.data
        }
        party_ref.set(updated_party, merge=True)
        return super(PartyModelView, self).update_model(form, model)

    def delete_model(self, model):
        # Delete the party from Firestore
        party_ref = firestore_db.collection('parties').document(str(model.id))
        party_ref.delete()
        return super(PartyModelView, self).delete_model(model)

class UserCreatedPartyModelView(ModelView):
    column_list = ('id', 'music', 'theme', 'venue', 'location', 'dates', 'created_by')
    form_columns = ('music', 'theme', 'venue', 'location', 'dates', 'created_by')

    def create_model(self, form):
        # Create a new user-created party in Firestore
        new_party = {
            'music': form.music.data,
            'theme': form.theme.data,
            'venue': form.venue.data,
            'location': form.location.data,
            'dates': form.dates.data,
            'created_by': form.created_by.data
        }
        doc_ref = firestore_db.collection('user_created_parties').add(new_party)
        return super(UserCreatedPartyModelView, self).create_model(form)

    def update_model(self, form, model):
        # Update the user-created party in Firestore
        party_ref = firestore_db.collection('user_created_parties').document(str(model.id))
        updated_party = {
            'music': form.music.data,
            'theme': form.theme.data,
            'venue': form.venue.data,
            'location': form.location.data,
            'dates': form.dates.data,
            'created_by': form.created_by.data
        }
        party_ref.set(updated_party, merge=True)
        return super(UserCreatedPartyModelView, self).update_model(form, model)

    def delete_model(self, model):
        # Delete the user-created party from Firestore
        party_ref = firestore_db.collection('user_created_parties').document(str(model.id))
        party_ref.delete()
        return super(UserCreatedPartyModelView, self).delete_model(model)

class UserModelView(ModelView):
    column_list = ('id', 'phone_number', 'joined', 'partygoer_approved')
    form_columns = ('phone_number', 'joined', 'partygoer_approved')  # Allow toggling approval status in the admin UI

admin.add_view(PartyModelView(Party, db.session))
admin.add_view(UserCreatedPartyModelView(UserCreatedParty, db.session))
admin.add_view(UserModelView(User, db.session))

@app.route('/')
def index():
    return redirect('/admin')

if __name__ == "__main__":
    app.run(debug=True)
