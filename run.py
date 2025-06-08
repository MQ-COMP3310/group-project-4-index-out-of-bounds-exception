import datetime
from functools import wraps
import os
import sys
import re
from importlib import reload
from flask import Flask, render_template, redirect, request, url_for, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import uuid
from flask_jwt_extended import JWTManager

#Database for user information is unimplemented but is titled User 
# User database contains user_id (uuid), username(unique), password, user_highscores(top 20) and user_past_scores(last 20)

# Needed for encoding to utf8   
reload(sys)

app = Flask(__name__) #Task 7 (a)
app.secret_key = 'some_secret'
app.config["JWT_SECRET_KEY"] = "some_secret_key"
data = []

def sanitisename(username): #Task 9 (a)
    #Only letters and numbers
    return re.sub(r'[^a-z0-9]','',username) # re.sub removes non letter and number symbols from the username

def traversalprevention(filename, mode): #Task 9 (a) #This is used whenever an open() method is used to check the filename for path transveral properties ie "../../etc"
    path = os.path.abspath(filename) #Declaring path
    if path.startswith("../"): #If the path starts with ../../ etc. 
        return error("Invalid File Path") #Return an error instead of displaying webpage

def write_to_file(filename, data):
    with open(filename, "a+") as file:
        file.writelines(data)


#This is where the riddles live
def riddle():
    riddles = []
    with open(traversalprevention("data/-riddles.txt", "r")) as e: 
        lines = e.read().splitlines()
    for line in lines:
        riddles.append(line)
    return riddles


# This is where the answers for the riddles live
def riddle_answers():
    answers = []
    with open(traversalprevention("data/-answers.txt", "r")) as e:
        lines = e.read().splitlines()
    for line in lines:
        answers.append(line)
    return answers


# Clear functions for wrong answers and score
def clear_guesses(username):
    with open(traversalprevention("data/user-" + username + "-guesses.txt", "w")):
        return

def clear_score(username):
    with open(traversalprevention("data/user-" + username + "-score.txt", "w")):
        return


# Wrong answer handling
def store_all_attempts(username):
    attempts = []
    with open(traversalprevention("data/user-" + username + "-guesses.txt", "r")) as incorrect_attempts:
        attempts = incorrect_attempts.readlines()
    return attempts

def num_of_attempts():
    attempts = store_all_attempts(username)
    return len(attempts)

def attempts_remaining():
    remaining_attempts = 3 - num_of_attempts()
    return remaining_attempts


# Score gets lower the more attempts used
def add_to_score():
    round_score = 4 - num_of_attempts()
    return round_score

#Adds all the scores from all riddles to make final score
def end_score(username):
    with open(traversalprevention("data/user-" + username + "-score.txt", "r")) as numbers_file:
        total = 0
        for line in numbers_file:
            try:
                total += int(line)
            except ValueError:
                pass
    return total

#Add final score to highscore list after the last riddle
def final_score(username):
    score = str(end_score(username))

    if username != "" and score != "":
        with open(traversalprevention("data/-highscores.txt", "a")) as file:
                file.writelines(username + "\n")
                file.writelines(score + "\n")
    else:
        return

#Used to retrieve scores from highscore file for use on highscore page
def get_scores():
    usernames = []
    scores = []

    with open(traversalprevention("data/-highscores.txt", "r")) as file:
        lines = file.read().splitlines()
    # Separates usernames and scores
    for i, text in enumerate(lines):
        if i%2 ==0:
            usernames.append(text)
        else:
            scores.append(text)
    # Sorts and zips all the highscore info up for use on highscore page
    usernames_and_scores = sorted(zip(usernames, scores), key=lambda x: x[1], reverse=True)
    return usernames_and_scores

#HOMEPAGE
@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        global username
        username = request.form['username'].lower()
        if username == "":
            return render_template("index.html", page_title="Home", username=username)
        else:
            return redirect(url_for('user', username=username))
    return render_template("index.html", page_title="Home")


#login function will become initial homepage
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST': # using POST method as forms need to be passed to this function
        unsafe_username = request.form['username'] # assume username is unsafe by default
        password = request.form['password']
        username = sanitisename(unsafe_username) # sanitise username so it is now safe before any query
        
        user = User.query.filter_by(username= username).first() # find user matching the safe username

        if not user or not check_password_hash(user.password, password): # checks if user doesn't exist or the password does not match
            # also hashes given password to compare with stored password so that the stored password is not explicitly revealed
            return jsonify({'message': 'Invalid username or password'}), 401
            #generic message so that traces or sensitive information is not revealed

        else:
            token = jwt.encode({'user_id': user.user_id, 'exp': datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)},
                           app.config['SECRET_KEY'], algorithm="HS256")
            response = make_response(redirect(url_for('user', username = username)))
            response.set_cookie('jwt_token', token)
            #if account and password matches a new JWT token is created with the user's id, and a response is crafted so that url for user setup 
            #and JWT token are passed along, with the JWT being encased in a cooki for later use

            return response

    return render_template('login.html') # if every other result fails or GET method used then the login page is rendered again

@app.route('/create_account', methods=['GET','POST'])
def create_account():
    if request.method == 'POST': # POST method as modifying data
        unsafe_username = request.form['username'] #assume input is unsafe
        password = request.form['password']
        username = sanitisename(unsafe_username) # ensure unsafe username is now made safe
        existing_user = User.query.filter_by(username= username).first() # find user that has the matching safe username
        if existing_user:
            return jsonify({'message': 'User already exists. Please login or use a different username'}), 400 
        #returning generic message so that sensitive information is not revealed

        hashed_password = generate_password_hash(password) # hashing provided password to be stored so that it is not easily accessible
        new_user = User(user_id=str(uuid.uuid4()), username=username,  password=hashed_password) 

        #new user will be added to unimplemented database named User

        return redirect(url_for('login')) # redirect to login so they can access their new or already existing account

    return render_template('create_account.html')# if every other result fails or GET method used, create_account page is rendered again 

#function to protect areas that need authentication mechanism to access, ensures token is supplied on access of function
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('jwt_token') #requests the JWT token that has been stored as a local cookie

        if not token: #ensures user actually has a token for their session
            return jsonify({'message': 'Missing Token!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(user_id=data['user_id']).first() 
            # gets the current user from the user_id contained in the JWT token
        except: # if any error or non existent user the request will be rejected with a 401 error
            return jsonify({'message': 'Invalid Token!'}), 401

        return f(current_user, *args, **kwargs) # returns the current user info to be used in required functions

    return decorated

# USER WELCOME PAGE
@app.route('/<username>', methods=["GET", "POST"])
def user(username):

    # Create a User Specific File for Score Keeping etc.
    open(traversalprevention("data/user-" + username + "-score.txt", 'a')).close()
    clear_score(username)
    open(traversalprevention("data/user-" + username + "-guesses.txt", 'a')).close()
    clear_guesses(username)

    if request.method =="POST":
        return redirect(url_for('game', username=username))

    return render_template("welcome.html",
                            username=username)


# GAME PAGE
@app.route('/<username>/game', methods=["GET", "POST"])
def game(username):
    if 'theme' not in session: #Sets the default theme to light mode if the user has not chosen a preference before
        session['theme'] = light

    remaining_attempts = 3
    riddles = riddle()
    riddle_index = 0
    answers = riddle_answers()
    hintuse = False #Check whether hint has been used
    score = 0

    if request.method == "POST":

        riddle_index = int(request.form["riddle_index"])
        #user_response = request.form["answer"].title()
        user_response = request.form.get("action", "answer")

        if user_response == "hint":
            hint_used = True

        write_to_file("data/user-" + username + "-guesses.txt", user_response + "\n")

        # Compare the user's answer to the correct answer of the riddle
        if answers[riddle_index] == user_response:
            # Correct answer
            if riddle_index < 9:
                # If riddle number is less than 10 & answer is correct: add score, clear wrong answers file and go to next riddle
                write_to_file("data/user-" + username + "-score.txt", str(add_to_score()) + "\n")
                clear_guesses(username)
                riddle_index += 1
            else:
                # If right answer on LAST riddle: add score, submit score to highscore file and redirect to congrats page
                write_to_file("data/user-" + username + "-score.txt", str(add_to_score()) + "\n")
                final_score(username)
                return redirect(url_for('congrats', username=username, score=end_score(username)))

        else:
            # Incorrect answer
            if attempts_remaining() > 0:
                # if answer was wrong and more than 0 attempts remaining, reload current riddle
                riddle_index = riddle_index
            else:
                # If all attempts are used up, redirect to Gameover page
                return redirect(url_for('gameover', username=username))
    
    hint_used = session.get(hint_used, False)

    return render_template("game.html",
                            username=username, riddle_index=riddle_index, riddles=riddles,
                            answers=answers, attempts=store_all_attempts(username), remaining_attempts=attempts_remaining(), score=end_score(username))

#Light & Dark Mode Toggle Task 9 (a)
@app.route('/theme-toggler', methods=["GET", "POST"]) #Endpoint/Routing
def lightanddark(): #Function Definition
    themecur = session.get('theme', 'light') #Current Theme
    if themecur == 'light': #If the theme is in light mode the theme will change to dark
        session['theme'] = 'dark' 
    else: #If the theme is in dark mode the theme will change to light
        session['theme'] = 'light'


#Display Hint Task 9 (a)
@app.route('/<username>/game', methods=["GET","POST"])
def displayhints(hint_used, riddle_index):
    if hint_used:
        display(hint, riddle_index) #Show the hint for X riddle when the button is clicked
    return displayhints

# GAMEOVER PAGE
@app.route('/<username>/gameover', methods=["GET", "POST"])
def gameover(username):

    clear_guesses(username)
    clear_score(username)

    rem_attempts = 3
    riddles = riddle()
    riddle_index = 0
    answers = riddle_answers()
    score = 0
    hintuse = False

    if request.method =="POST":

        return redirect(url_for('game', username=username))

    return render_template("gameover.html",
                            username=username)


# FINISH PAGE
@app.route('/<username>/congratulations', methods=["GET", "POST"])
def congrats(username):

    clear_guesses(username)

    if request.method =="POST":
        usernames_and_scores = get_scores()
        return redirect(url_for('highscores', usernames_and_scores=usernames_and_scores))

    return render_template("congratulations.html",
                            username=username, score=end_score(username))


# HIGHSCORE PAGE
@app.route('/highscores')
def highscores():

    usernames_and_scores = get_scores()

    return render_template("highscores.html", page_title="Highscores", usernames_and_scores=usernames_and_scores)

@app.route('/user_scores')
@token_required # function defined above that ensures the folowing code requires a specific token to access (least privilege followed)
def userScores(current_user):
    user_highscores = User.query.get(current_user.highscores)
    user_past_scores = User.query.get(current_user.past_scores)
    
    return render_template("user_scores.html", page_title= "User Scores", user_highscores = user_highscores, user_past_scores = user_past_scores)
    
    

if __name__ == '__main__':
    ip = "127.0.0.1"
    port = 8000
    app.run(host=ip,
            port=port,
            debug=False)
