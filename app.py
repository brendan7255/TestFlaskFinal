from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, FileField, PasswordField
from wtforms.validators  import DataRequired
import pyrebase
from dataclasses import dataclass
from werkzeug.utils import secure_filename
import uuid as uuid
import os
#from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = "Fall22371FinalProjectKey"

firebaseConfig={
    'apiKey': "AIzaSyBHkeMSVurDqWWg0rS2A7cVo4H31dQKIQQ",
    'authDomain': "flask-outfit-app.firebaseapp.com",
    'databaseURL': "https://flask-outfit-app-default-rtdb.firebaseio.com",
    'projectId': "flask-outfit-app",
    'storageBucket': "flask-outfit-app.appspot.com",
    'messagingSenderId': "195477479624",
    'appId': "1:195477479624:web:f3923e00dfd070ff45c5fd",
    'storagebucket' : 'flask-outfit-app.appspot.com/ClothImages/'
}

firebase=pyrebase.initialize_app(firebaseConfig)

db=firebase.database()
auth=firebase.auth()
storage=firebase.storage()





class ClothingForm(FlaskForm):
    upload = FileField('Picture')

    title = StringField("Name this Item", validators=[DataRequired()])
    category = SelectField('Clothing Type', choices=[('Short Sleeve Shirt', 'Short Sleeve Shirt'),
                                                     ('Long Sleeve Shirt', 'Long Sleeve Shirt'),
                                                     ('Shorts', 'Shorts'),
                                                     ('Pants', 'Pants'),
                                                     ])

    pattern = SelectField('Patterb Type', choices=[('Solid', 'Solid'),
                                                ('Stripe', 'Stripe'),
                                                ('Pattern', 'Pattern'),
                                                 ])

    season = SelectField('Seaon ', choices=[('Fall', 'Fall'),
                                                ('Winter', 'Winter'),
                                                ('Spring', 'Spring'),
                                                ('Summer', 'Summer')
                                                 ])


    submit = SubmitField("Submit")


class UserForm(FlaskForm):
    firstName = StringField('First Name: ', validators=[DataRequired()])
    lastName = StringField('Last Name: ', validators=[DataRequired()])
    email = StringField('Email: ', validators=[DataRequired()])
    password = PasswordField('Password: ', validators=[DataRequired()])
    submit = SubmitField("Submit")


#class ClothingItem(title, category, season, pattern):
# make own file
@dataclass
class ClothingItem:
    title: str      
    category: str 
    season: str 
    pattern: str 
    url: str

# def loginFunc(email, password):
#     user = auth.sign_in_with_email_and_password(email,password)
#     user = auth.refresh(user['refreshToken'])
#     user_id = user['idToken']
#     session['usr'] = user_id
#     return 


################ HOME #######################
@app.route('/home')

def home():
    if('currUser' in  session):
        sID = session['currUser']
        return render_template('profile.html', sID=sID)
    else:
        return render_template('home.html')

################ LOGIN #######################
@app.route('/login', methods=['GET', 'POST'])

def login():

    form = UserForm()
    if request.method == "POST":
        email = form.email.data
        password = form.password.data
        

        try:
            user = auth.sign_in_with_email_and_password(email,password)
            session['currUser'] = user['localId']
            # user = auth.refresh(user['refreshToken'])
            # user_id = user['idToken']
            # session['usr'] = user_id
            # auth.current_user
            
            return redirect(url_for('home'))
        except:
            flash("Bad Login")
            return render_template('login.html', form=form)

    return render_template('login.html', form=form)

@app.route('/logout')


################ LOGOUT #######################
def logout():
    if('currUser' in session):
        session.pop('currUser')
        return render_template('home.html')
    
    return render_template('home.html')


################ CREATE USER #######################
@app.route('/createUser', methods=['GET', 'POST'])

def createUser():
    firstName = None
    lastName = None
    email = None
    password = None
    form = UserForm()

    if form.validate_on_submit():

        firstName = form.firstName.data
        lastName = form.lastName.data
        email = form.email.data
        password = form.password.data

        form.firstName.data = ''
        form.lastName.data = ''
        form.email.data = ''
        form.password.data = ''
        try:
            user = auth.create_user_with_email_and_password(email,password)
            
            id = session.get('currUser', None)
            #user = auth.sign_in_with_email_and_password(email,password)
            itemInfo={'firstName':firstName, 'lastName':lastName, 'email':email, 'userID': id}
            db.child("Users").push(itemInfo)
            
            
            # flash("User Created")
            return redirect(url_for('profile'))
        except:
            flash("Invalid Email/Password")
            return redirect(url_for('createUser'))

    return render_template('createUser.html', form=form, firstName=firstName, lastName=lastName, email=email)  



################ PROFILE #######################
@app.route('/profile')

def profile():

    return  render_template('profile.html')


################ ADD CLOTHES #######################
@app.route('/addClothes', methods=['GET', 'POST'])

def addClothes():
    if('currUser' in session):
        upload = None
        title = None
        category = None
        pattern = None
        season = None
        form = ClothingForm()

        id = session['currUser']
        if form.validate_on_submit():
            upload = form.upload.data
            title = form.title.data
            category = form.category.data
            pattern = form.pattern.data
            season = form.season.data
            
            form.upload.data = ''
            form.title.data = ''
            form.category.data = ''
            form.pattern.data = ''
            form.season.data = ''
            
            clothing_filename = secure_filename(upload.filename)

            cname = str(uuid.uuid1()) + "" + clothing_filename

            storage.child("ClothPics/" + cname).put(upload)
            url=storage.child("ClothPics/" + cname).get_url(None)

            
            flash("Clothes Added")
            itemInfo={'title':title, 'pattern':pattern, 'season':season, 'category':category, 'url':url, 'userID':id}

            db.child("Clothes").push(itemInfo)
            
        return render_template("addClothes.html", 
            upload = upload,
            title = title,
            category = category,
            pattern = pattern,
            season = season,
            form = form)
    else:
        return render_template('home.html')




################ CLOTHES LIST #######################
@app.route('/clothesList', methods=['GET','POST'])

def clothesList():

    clothes = db.child("Clothes").get().val()
    clothList = []
    if clothes:
        for key, value in clothes.items():
            clothList.append(ClothingItem(value["title"], value["category"], value["season"], value["pattern"], value["url"]))
    
        uID=db.child("Clothes").get()
        uIDList = []
        for i in uID.each():
            uIDList.append(i.key())

        return render_template('clothesList.html', clothList=clothList, uIDList=uIDList)
    else:
        return render_template('clothesList.html')
        



################ UPDATE ITEM #######################
@app.route('/updateItem/<id>', methods=['GET', 'POST'])

def updateItem(id):

    clothes = db.child("Clothes").child(id).get().val()

    form = ClothingForm()


    if request.method == "POST":

        title = request.form['title']
        category = request.form['category']
        season = request.form['season']
        pattern = request.form['pattern']
        itemInfo={'title':title, 'pattern':pattern, 'season':season, 'category':category}
        try:
            db.child("Clothes").child(id).update(itemInfo)
            return redirect(url_for('clothesList'))
        except:
            flash("Failed to Update")
            return render_template('updateItem.html', form=form, clothList=clothes)

    else:
        return render_template('updateItem.html', form=form, clothList=clothes)


################ DELETE ITEM #######################
@app.route('/deleteItem/<id>', methods=['GET','POST'])

def deleteItem(id):

    clothes = db.child("Clothes").get().val()
    clothList = []
    if clothes:
        for key, value in clothes.items():
            clothList.append(ClothingItem(value["title"], value["category"], value["season"], value["pattern"], value["url"]))

    uID=db.child("Clothes").get()
    uIDList = []
    for i in uID.each():
        uIDList.append(i.key())


    return redirect(url_for('clothesList'))


################ FAVORITES #######################
@app.route('/favorites')

def favorites():

    return render_template('favorites.html')


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))