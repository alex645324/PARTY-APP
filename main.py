import os
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import firestore
from flask import Flask, request
import re
import unicodedata

app = Flask(__name__)

# Initialize Firestore with the service account
db = firestore.Client()


def ask_for_gender(phone_number):
    # Send a message asking for gender
    user_ref = db.collection('users').document(phone_number)
    user_data = user_ref.get().to_dict()

    if user_data.get('partygoer_approved', False) and 'gender' not in user_data:
        # Prompt for gender if user is approved but hasn't provided gender
        send_message(phone_number, "Are you a boy or girl? Please reply with 'boy' or 'girl'.")

def send_message(phone_number, text):
    response = MessagingResponse()
    msg = response.message()
    msg.body(text)
    return str(response)

# Function to normalize text (to handle emojis consistently)
def normalize(text): 
    return unicodedata.normalize('NFC', text)

# Function to get or create a user in Firestore
def get_or_create_user(phone_number):
    user_ref = db.collection('users').document(phone_number)
    user = user_ref.get()

    if not user.exists:
        # If user doesn't exist, create a new one
        user_data = {
            'phone_number': phone_number,
            'joined': True,
            'partygoer_approved': False
        }
        user_ref.set(user_data)
        return user_data
    else:
        return user.to_dict()

# Function to update a user in Firestore
def update_user(phone_number, updates):
    user_ref = db.collection('users').document(phone_number)
    user_ref.update(updates)

# Function to save reviews in Firestore 
def save_review(party_id, review_text): 
    db.collection('parties').document(party_id).collection('reviews').add({'text': review_text})

# Function to get party details
def get_party_details(party_id):
    party_ref = db.collection('parties').document(party_id)
    party_details = party_ref.get().to_dict()
    return party_details

# Function to aggregate reviews
def aggregate_reviews(party_id):
    reviews_ref = db.collection('parties').document(party_id).collection('reviews')
    reviews = [review.to_dict()['text'] for review in reviews_ref.stream()]
    return "\n".join(reviews) if reviews else "No reviews yet."

# Function to check if a party has reviews
def has_reviews(party_id):
    reviews_ref = db.collection('parties').document(party_id).collection('reviews')
    return reviews_ref.limit(1).get() != []

# Webhook to handle incoming messages
@app.route("/webhook", methods=['POST'])
def webhook():
    incoming_msg = normalize(request.values.get('Body', '').strip()).lower()
    from_number = request.values.get('From', '')

    resp = MessagingResponse()
    msg = resp.message()

    # Debugging
    print(f"Incoming message: {incoming_msg} - Hex: {':'.join(f'{ord(i):X}' for i in incoming_msg)}")

    # Get or create the user
    user_data = get_or_create_user(from_number)

    if user_data.get('partygoer_approved', False) and 'gender' not in user_data:
        if incoming_msg in ['boy', 'girl']:
            update_user(from_number, {'gender': incoming_msg})
            msg.body(f"Thanks for letting us know! You're now all set to join the party. 🎉")


# Immediately show the partygoer options after gender input
            parties = db.collection('parties').stream()
            party_list = ["🥳 Ready to join the party? Here are some options:"]
            for i, party in enumerate(parties, start=1):
                party_data = party.to_dict()
                party_prompt = f"partygoer{i}"
                party_list.append(
                    f"🎉 {party_prompt.upper()}:\n"
                    f"   {party_data.get('type', 'Party')}\n"
                    f"   📍 {party_data.get('address', 'Unknown Address')}\n"
                    f"   Join by typing '{party_prompt}'\n"
                )
            msg.body("\n".join(party_list))
            update_user(from_number, {'party_list_shown': True, 'finding_party': False, 'partygoer_mode': True})
            return str(resp)
        else:
            msg.body("Please reply with either 'boy' or 'girl'.")
            return str(resp)







    # Define the menu message
    menu_message = (
        "Hey, what's up! 😎 I’m your go-to guide for all things party. Here’s how you can navigate around:\n\n"
        "To find what parties are lit tonight, type: 🕺\n"
        "To review parties and get free drinks (approval process), type: 🎉\n"
        "To learn more about us, check this out: [insert website link]"
    )

    # Menu command
    if incoming_msg == 'menu':
        msg.body(menu_message)

    # Join command
    elif incoming_msg == 'join':
        update_user(from_number, {'joined': True})
        msg.body("🎉 Awesome, you’re all set! Here’s what you can do:\n\n" + menu_message)


# Handle finding parties (🕺)
    elif incoming_msg == normalize('🕺'):
        parties = db.collection('parties').stream()
        party_list = ["🎉 Check out these spots:"]
        for i, party in enumerate(parties, start=1):
            party_data = party.to_dict()
            party_id = party.id
            if has_reviews(party_id):  # Only add the party if it has reviews
                party_prompt = f"party{i}"
                party_list.append(
                    f"   {party_data.get('type', 'Party')}\n"
                    f"   📍 {party_data.get('address', 'Unknown Address')}\n"
                    f"   Curious? Type '{party_prompt}'\n"
                )
        if len(party_list) > 1:
            party_list.append("👉 Type the word prompt for more details or reviews!")
            msg.body("\n".join(party_list))
            update_user(from_number, {'party_list_shown': True, 'finding_party': True, 'partygoer_mode': False})
        else:
            msg.body("Sorry, no parties with reviews are currently available.")





# Request to become a partygoer (🎉)
    elif incoming_msg == normalize('🎉'):
        update_user(from_number, {'requested_partygoer': True})
        partygoer_approved = user_data.get('partygoer_approved', False)

        if partygoer_approved:
            # Check if gender is provided
            if 'gender' not in user_data:
            # Prompt for gender if not provided
                msg.body("You're approved! Before we continue, are you a boy or girl? Please reply with 'boy' or 'girl'.")
            else:
            # If gender is already provided, show the partygoer list
                parties = db.collection('parties').stream()
                party_list = ["🥳 Ready to join the party? Here are some options:"]
                for i, party in enumerate(parties, start=1):
                    party_data = party.to_dict()
                    party_prompt = f"partygoer{i}"
                    party_list.append(
                        f"🎉 {party_prompt.upper()}:\n"
                        f"   {party_data.get('type', 'Party')}\n"
                        f"   📍 {party_data.get('address', 'Unknown Address')}\n"
                        f"   Join by typing '{party_prompt}'\n"
                )
                msg.body("\n".join(party_list))
                update_user(from_number, {'party_list_shown': True, 'finding_party': False, 'partygoer_mode': True})
        else:
            msg.body("Your request to be a partygoer has been received. Please wait for approval.")













# Handle selected party details
    elif 'party_list_shown' in user_data and user_data['party_list_shown']:
    # Match the input, allowing for flexible spacing like 'party 1' or 'party1'
        match = re.match(r'^partygoer\s*(\d+)$', incoming_msg)
        if match:
            party_number = int(match.group(1))  # Extract the party number
            parties = list(db.collection('parties').stream())  # Fetch parties from Firestore
            if 1 <= party_number <= len(parties):
                selected_party = parties[party_number - 1]  # Get the selected party by index
                party_id = selected_party.id  # Get the party ID
                update_user(from_number, {'selected_party': party_id})  # Update user data with the selected party
                party_details = get_party_details(party_id)  # Fetch party details

                if user_data.get('finding_party', False):  # Check if the user is in "finding party" mode
                    msg.body(
                        f"Details for {party_details.get('type', 'Party')}:\n\n"
                        f"📍 Address: {party_details.get('address', 'Unknown Address')}\n\n"
                        f"🎟️ Ticket Info: {party_details.get('ticket_info', 'No ticket info available')}\n\n"
                        f"To see live reviews, type: all"
                    )
                elif user_data.get('partygoer_mode', False):  # Check if the user is in "partygoer mode"
                    msg.body(
                        f"You've selected {party_details.get('type', 'Party')}:\n\n"
                        f"📍 Address: {party_details.get('address', 'Unknown Address')}\n"
                        f"{party_details.get('link', 'No link provided')}\n\n"
                        f"Instructions:\n- {party_details['instructions'][0]}\n- {party_details['instructions'][1]}\n\n"
                        f"Reward: {party_details.get('reward', 'No reward information available')}\n\n"
                        "At the party? Enter the check-in code displayed at the entrance."
                    )
            else:
                msg.body("Invalid party number. Please type a valid party prompt from the list.")
        else:
            msg.body("Invalid input. Please type 'party' followed by the number of the party (e.g., 'party2').")











    # Handle 'all' command to show reviews
    elif incoming_msg == 'all':
        if 'selected_party' in user_data and user_data['selected_party']:
            party_id = user_data['selected_party']
            reviews = aggregate_reviews(party_id)
            party_details = get_party_details(party_id)
            msg.body(
                f"Here are the reviews for {party_details.get('type', 'this party')}:\n\n"
                f"{reviews}"
            )
        else:
            msg.body("No party selected. Please select a party first by typing its word prompt.")

    # Handle partygoer check-in codes
    elif incoming_msg.startswith(('boy', 'girl')):
        if not user_data.get('partygoer_approved', False):
            msg.body("You are not approved as a partygoer. Please wait for admin approval.")
        else:
            checkin_code = incoming_msg.strip().lower()
            party_id = user_data.get('selected_party')
            party_details = get_party_details(party_id)
            actual_code_boy = party_details.get('checkin_code_boy', '').lower()
            actual_code_girl = party_details.get('checkin_code_girl', '').lower()

            if checkin_code == actual_code_boy:
                update_user(from_number, {'checked_in': True, 'gender': 'boy'})
                msg.body("Check-in successful! Type 'start' to start giving feedback.")
            elif checkin_code == actual_code_girl:
                update_user(from_number, {'checked_in': True, 'gender': 'girl'})
                msg.body("Check-in successful! Type 'start' to start giving feedback.")
            else:
                msg.body("Invalid check-in code. Please try again.")

    # Handle feedback start
    elif incoming_msg == 'start':
        gender = user_data.get('gender', 'unknown')
        if gender == 'girl':
            feedback_prompt = (
                "Hey girl, let's answer a few questions! Please separate your answers with a comma and be descriptive:\n\n"
                "1. How's the crowd? More guys, girls, or a good mix?\n"
                "2. Think this place is good for meeting cuties or just couples cuddling?\n"
                "3. Is it super packed or can we actually breathe?\n"
                "4. Line situation? Worth the wait or nah?\n"
                "5. What kind of music are they playing?\n"
                "6. What's the vibe? Are people dancing, chatting, just chilling, or being boring?\n"
                "7. Is there a place to sit if I need a break from dancing?\n"
                "8. Should I wear heels or stick with flats?\n"
                "9. Spill the tea on drink prices! Any specials happening?\n"
                "10. What's everyone wearing? Jeans and a tee okay, or should I get fancy?"
            )
        elif gender == 'boy':
            feedback_prompt = (
                "Sure, let's answer a few questions! Please separate your answers with a comma and be descriptive:\n\n"
                "1. How’s the ratio? More girls or guys?\n"
                "2. Is it a good spot for meeting people or na?\n"
                "3. How long’s the line to get in?\n"
                "4. What type of music are they playing?\n"
                "5. Is the place packed or chill?\n"
                "6. What’s the vibe? Are people dancing, talking, or just hanging out?\n"
                "7. How much are the drinks?\n"
                "8. Is there a dress code?\n"
                "9. Is there a place to sit if I need a break?\n"
                "10. What’s the crowd like? Crowded or there's space?\n"
                "11. Are the bouncers chill or strict?"
            )
        else:
            feedback_prompt = "Please check in first by typing either 'boy' or 'girl'."

        update_user(from_number, {'awaiting_feedback': True, 'party_list_shown': False, 'feedback_prompt': feedback_prompt})
        msg.body(feedback_prompt)

    # Handle feedback submission
    elif 'awaiting_feedback' in user_data and user_data['awaiting_feedback']:
        feedback = incoming_msg.split(',')
        gender = user_data.get('gender', 'unknown')
        required_answers = 10 if gender == 'girl' else 11
        feedback_prompt = user_data.get('feedback_prompt', '')

        if len(feedback) < required_answers:
            msg.body("It seems like you missed some questions. Please answer all questions correctly:\n\n" + feedback_prompt.split('\n\n', 1)[1])
        else:
            if gender == 'girl':
                review_text = (
                    f"👧 Girl's Review:\n"
                    f"1. Crowd: {feedback[0].strip()}\n"
                    f"2. Meeting Potential: {feedback[1].strip()}\n"
                    f"3. Capacity: {feedback[2].strip()}\n"
                    f"4. Line Situation: {feedback[3].strip()}\n"
                    f"5. Music: {feedback[4].strip()}\n"
                    f"6. Vibe: {feedback[5].strip()}\n"
                    f"7. Seating: {feedback[6].strip()}\n"
                    f"8. Dress Code: {feedback[7].strip()}\n"
                    f"9. Drink Prices: {feedback[8].strip()}\n"
                    f"10. Attire: {feedback[9].strip()}\n"
                )
            elif gender == 'boy':
                review_text = (
                    f"👦 Boy's Review:\n"
                    f"1. Ratio: {feedback[0].strip()}\n"
                    f"2. Meeting Potential: {feedback[1].strip()}\n"
                    f"3. Line: {feedback[2].strip()}\n"
                    f"4. Music: {feedback[3].strip()}\n"
                    f"5. Capacity: {feedback[4].strip()}\n"
                    f"6. Vibe: {feedback[5].strip()}\n"
                    f"7. Drink Prices: {feedback[6].strip()}\n"
                    f"8. Dress Code: {feedback[7].strip()}\n"
                    f"9. Seating: {feedback[8].strip()}\n"
                    f"10. Crowd: {feedback[9].strip()}\n"
                    f"11. Bouncers: {feedback[10].strip()}\n"
                )
            party_id = user_data.get('selected_party')
            save_review(party_id, review_text)
            update_user(from_number, {'awaiting_feedback': False})
            party_details = get_party_details(user_data.get('selected_party'))
            msg.body(
                "🎉 Thank you so much for your awesome input! Your feedback is invaluable to us. Here's how you can claim your reward, which expires at the listed time:\n"
                f"{party_details['reward_instructions']}\n\n"
                "🎁 Enjoy the party and have a blast! 🎊"
            )

    # Handle 'info' command
    elif incoming_msg == 'info':
        msg.body("📚 Learn more about our platform and how you can be the life of the party! Visit our website at [insert website link here].")

    else:
        msg.body("❗ Command not recognized. Type 'menu' to see available commands.")

    return str(resp)

# Main function to be used in Cloud Functions
def main(request):
    with app.app_context():
        return webhook()

if __name__ == "__main__":
    app.run(debug=True)
   








