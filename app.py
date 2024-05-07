from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("firebasecss.json")
firebase_admin.initialize_app(cred,{"databaseURL":"https://ccs-faculty-default-rtdb.asia-southeast1.firebasedatabase.app/"})
section_data = [] 
app = Flask(__name__)
app.secret_key = "0NTheCI0ck_T3eam2024"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        f_email = request.form['f_email']
        f_pwd = request.form['f_pwd']
        
        modified_email = f_email.replace('.', ',')
        user_ref = db.reference(f"/students-accs/{modified_email}")
        
        user_data = user_ref.get()
        if user_data is None:
            return jsonify({"status": "error", "message": "Email does not exist."})
        
        stored_pwd = user_data.get('pwd')
        if stored_pwd != f_pwd:
            return jsonify({"status": "error", "message": "Incorrect password."})
        
        return jsonify({"status": "success", "message": "Login successful!"})
    
    return render_template('login.html')

@app.route('/sectionboard')
def section():
    global section_data
    section_data = []
    admins_ref = db.reference("/admins")
    admins = admins_ref.get()
    if admins:
        for email, _ in admins.items():
            print("Processing email:", email)  # Print the email being processed
            # Retrieve sections data for each email
            sections_ref = db.reference(f"/admins/{email}/sections")
            sections = sections_ref.get()
            if sections:
                for section_name, data in sections.items():
                    if isinstance(data, dict):  # Check if data is a dictionary
                        section_weekdays = {day: data.get(day, []) for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
                        # Store section data
                        section_data.append({"email": email, "section_name": section_name, "weekdays": section_weekdays})
                        # Print every subject
                        for day, subjects in section_weekdays.items():
                            for subject in subjects:
                                # Get the code for the subject
                                codes_ref = db.reference(f"/admins/{email}/sections/{section_name}/{day}/{subject}/code")
                                code = codes_ref.get()
                                print(f"Subject in {section_name} on {day}: {subject} - CODE: {code}")
    
    return render_template('secBoard.html', section_data=section_data)

@app.route('/check_code', methods=['GET'])
def check_code():
    section_data = []
    admins_ref = db.reference("/admins")
    admins = admins_ref.get()
    if admins:
        user_code = request.args.get('code')
        for email, _ in admins.items():
            # Retrieve sections data for each email
            sections_ref = db.reference(f"/admins/{email}/sections")
            sections = sections_ref.get()
            if sections:
                for section_name, data in sections.items():
                    if isinstance(data, dict):  # Check if data is a dictionary
                        section_weekdays = {day: data.get(day, []) for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
                        # Store section data
                        section_data.append({"email": email, "section_name": section_name, "weekdays": section_weekdays})
                        # Loop through each subject
                        for day, subjects in section_weekdays.items():
                            for subject in subjects:
                                # Get the code for the subject
                                codes_ref = db.reference(f"/admins/{email}/sections/{section_name}/{day}/{subject}/code")
                                code = codes_ref.get()
                                print(f"Subject in {section_name} on {day}: {subject} - CODE: {code}")
                                # Retrieve the stored code for the given section and subject from your Firebase database
                                stored_code = code
                                if user_code == stored_code:
                                    return jsonify({"matched": True, "section": section_name, "subject": subject})
    return jsonify({"matched": False})

@app.route('/register', methods=['POST'])
def register():
    print("Received request:", request.method)
    if request.method == 'POST':
        f_id = request.form['f_id']
        l_name = request.form['l_name']
        f_name = request.form['f_name']
        f_phone = request.form['f_phone']
        f_email = request.form['f_email']
        f_pwd = request.form['f_pwd']  # Add password field
        f_gender = request.form['f_gender']
        f_section = ""  # Initialize section as empty string
        subject_str = ""
        img_id = 0
        
        # Print fetched data
        print("Fetched data:")
        print("f_id:", f_id)
        print("l_name:", l_name)
        print("f_name:", f_name)
        print("f_phone:", f_phone)
        print("f_email:", f_email)
        print("f_pwd:", f_pwd)  # Print password
        print("f_gender:", f_gender)
        print("img_id:", img_id)
        
        modified_email = f_email.replace('.', ',')
        
        users_ref = db.reference("/students-accs")  # Reference to the node
        
        # Check if email node exists
        if users_ref.child(modified_email).get() is not None:
            return jsonify({"status": "error", "message": "Email already exists."})

        try:
            # Insert into Firebase under email node and return appropriate response
            details = {
                'id': f_id,
                'lname': l_name,
                'fname': f_name,
                'gender': f_gender,
                'phone': f_phone,
                'section': f_section,
                'img_id': img_id,
                'subjects': subject_str,
                "email": f_email
            }
            user_email_ref = users_ref.child(modified_email)
            user_email_ref.child('details').push(details)  # Push details under details node
            user_email_ref.child('pwd').set(f_pwd)  # Set password under pwd node
            return jsonify({"status": "success", "message": "Registration successful!"})
        except Exception as e:
            return f"An error occurred: {str(e)}"
    # Add a default return statement outside the if block
    return "Invalid request"

@app.route('/user-details/<email>', methods=['GET'])
def get_user_details(email):
    try:
        modified_email = email.replace('.', ',')
        users_ref = db.reference("/students-accs")
        user_details = users_ref.child(modified_email).child('details').get()

        if user_details:
            return jsonify({"status": "success", "user_details": user_details})
        else:
            return jsonify({"status": "error", "message": "User details not found."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    

@app.route('/update-details/<email>', methods=['POST'])
def update_user_details(email):
    try:
        data = request.json
        user_details = data.get('details')
        modified_email = email.replace('.', ',')
        users_ref = db.reference("/students-accs")
        user_email_ref = users_ref.child(modified_email)
        details_key = list(user_email_ref.child('details').get().keys())[0]
        existing_details = user_email_ref.child('details').child(details_key).get()
        print("Existing details in students-accs:", existing_details)
        existing_details['section'] = user_details.get('section')

                # Update the section if it's present in the user_details
        if 'section' in user_details:
            existing_details['section'] = user_details['section']
        
         # Get existing subjects and append the new subject
        existing_subjects = user_details.get('subjects', [])
        if 'subjects' in existing_details:
            existing_subjects.extend(existing_details['subjects'].split(','))
        existing_details['subjects'] = ', '.join(existing_subjects)
        print("Existing details with subjects and section:", existing_details)
        
        user_email_ref.child('details').child(details_key).update(existing_details) 

        # Copy the updated details to the 'users' node under the 'admin' node if the admin has the same section
        admins_ref = db.reference("/admins")
        admins = admins_ref.get()
        if admins:
            for admin_email, admin_data in admins.items():
                print(admin_email)
                admin_sections = admin_data.get('sections', {})
                                  
                if existing_details['section'] in admin_sections.keys():
                    admin_users_ref = db.reference(f"/admins/{admin_email}/users")
                    admin_users_ref.child(details_key).set(existing_details)
                    print("Details copied to admin:", admin_email, existing_details)
                    # Use the details key as the key under 'users' node
                    users_node_ref = admins_ref.child(admin_email).child('users').child(details_key)
                    # Get existing subjects from the admin data
                    existing_admin_subjects = admin_data['users'][details_key]['subjects'].split(', ')
                    # Append new subjects
                    new_subjects = user_details.get('subjects', [])
                    existing_admin_subjects.extend(new_subjects)
                    existing_admin_subjects = list(set(existing_admin_subjects))  # Remove duplicates
                    # Filter out empty strings and join subjects
                    existing_admin_subjects = list(filter(None, existing_admin_subjects))
                    admin_data['users'][details_key]['subjects'] = ', '.join(existing_admin_subjects)
                    users_node_ref.update(admin_data['users'][details_key])
                    print("Updated details in /admins:", admin_data['users'][details_key])

        # Reset subjects and section in students-accs node
        user_email_ref.child('details').child(details_key).child('subjects').set("")
        user_email_ref.child('details').child(details_key).child('section').set("")

        return jsonify({"status": "success", "message": "User details updated successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
