from google.cloud import firestore

# Initialize Firestore with the service account
db = firestore.Client()

# Example parties data
example_parties = [
    {
        'description': 'Amazing rooftop party',
        'address': '123 Party St, Cityville',
        'type': 'Rooftop Party',
        'ticket_info': 'Free entry before 10 PM',
        'instructions': ['Show this message at the entrance.', 'Keep this ticket with you.'],
        'link': 'http://example.com/tickets',
        'checkin_code_boy': 'boy123',
        'checkin_code_girl': 'girl123',
        'reward': 'Free drink at the bar.',
        'reward_instructions': 'Show this message to the bartender for a free drink.'
    },
    {
        'description': 'Underground techno rave',
        'address': '456 Club Ave, Party Town',
        'type': 'Techno Rave',
        'ticket_info': 'Tickets available at the door',
        'instructions': ['Show this message at the entrance.', 'Keep this ticket with you.'],
        'link': 'http://example.com/tickets',
        'checkin_code_boy': 'boy456',
        'checkin_code_girl': 'girl456',
        'reward': 'VIP access to the lounge.',
        'reward_instructions': 'Show this message to the staff for VIP access.'
    },
    {
        'description': 'Chill beach party',
        'address': '789 Beach Blvd, Sun City',
        'type': 'Beach Party',
        'ticket_info': 'Buy tickets online',
        'instructions': ['Show this message at the entrance.', 'Keep this ticket with you.'],
        'link': 'http://example.com/tickets',
        'checkin_code_boy': 'boy789',
        'checkin_code_girl': 'girl789',
        'reward': 'Free beach towel.',
        'reward_instructions': 'Show this message at the gift booth for a free beach towel.'
    }
]

# Add example parties to Firestore
for party in example_parties:
    db.collection('parties').add(party)

print("Example parties added to Firestore.")
