from google.cloud import firestore

# Initialize Firestore with the service account
db = firestore.Client()

def delete_all_parties():
    parties_ref = db.collection('parties')
    parties = parties_ref.stream()

    for party in parties:
        print(f'Deleting party: {party.id}')
        party.reference.delete()

if __name__ == "__main__":
    delete_all_parties()
    print("All parties deleted successfully.")
