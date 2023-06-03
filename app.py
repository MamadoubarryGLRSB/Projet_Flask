from flask import Flask, render_template, redirect, url_for, flash, request,abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, login_required, current_user,LoginManager,UserMixin
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, FileField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'passer123'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///expat.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

db = SQLAlchemy(app)
with app.app_context():
    db.create_all()
login_manager = LoginManager(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    ads = db.relationship('Ad', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def _repr_(self):
        return f'<User {self.phone_number}><{self.full_name}>'




class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    ads = db.relationship('Ad', backref='category', lazy=True)

    def _repr_(self):
        return f'<Category {self.name}>'


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    ads = db.relationship('Ad', backref='location', lazy=True)

    def _repr_(self):
        return f'<Location {self.name}>'

class Ad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.String(20), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    image = db.Column(db.String(20), nullable=False, default='default.jpg')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)

    def _repr_(self):
        return f'<Ad {self.title}>'
        

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    categories = Category.query.all()
    locations= Location.query.all()
    category_choices = [(c.name, c.name) for c in categories]
    location_choices = [(l.name, l.name) for l in locations]


    
class LoginForm(FlaskForm):
    phone_number = StringField('Numéro de téléphone', validators=[DataRequired(), Length(min=10, max=10)])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

    def validate_password(self, field):
        user = User.query.filter_by(phone_number=self.phone_number.data).first()
        if user is None:
            raise ValidationError('Numéro de téléphone ou mot de passe incorrect.')
        if not check_password_hash(user.password_hash, field.data):
            raise ValidationError('Numéro de téléphone ou mot de passe incorrect.')


class RegisterForm(FlaskForm):
    phone_number = StringField('Numéro de téléphone', validators=[DataRequired(), Length(min=9, max=15)])
    full_name = StringField('Nom complet', validators=[DataRequired()])
    address = SelectField('Catégorie', choices=location_choices, validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmez le mot de passe', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('S\'inscrire')

    def validate_phone_number(self, phone_number):
        user = User.query.filter_by(phone_number=phone_number.data).first()
        if user:
            raise ValidationError('Ce numéro de téléphone est déjà utilisé, veuillez en choisir un autre.')

class AdForm(FlaskForm):
    title = StringField('Titre', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    category = SelectField('Catégorie', choices=category_choices, validators=[DataRequired()])
    price = StringField('Prix', validators=[DataRequired()])
    location = SelectField('Catégorie', choices=location_choices, validators=[DataRequired()])
    image = FileField('Image', validators=[])
    submit = SubmitField('Publier')

class ConfirmationForm(FlaskForm):
    submit = SubmitField('Confirmer')



@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    ads = Ad.query.order_by(Ad.date_created.desc()).paginate(page=page, per_page=5)
    ads1 = Ad.query.order_by(Ad.views.desc()).limit(10).all()
    return render_template('index.html', ads=ads,ads1=ads1)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(phone_number=form.phone_number.data).first()
        login_user(user)
        flash('Vous êtes maintenant connecté.', 'success')
        return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous êtes maintenant déconnecté.', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        password_hash = generate_password_hash(form.password.data)
        user = User(phone_number=form.phone_number.data, full_name=form.full_name.data, address=form.address.data, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        flash('Votre compte a été créé avec succès, veuillez vous connecter.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)



@app.route('/ad/new', methods=['GET', 'POST'])
@login_required
def new_ad():
    form = AdForm()
    if form.validate_on_submit():
        image_file = form.image.data
        if image_file:
            filename = secure_filename(image_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image = Image.open(image_file)
            image.thumbnail((500, 500))
            image.save(filepath)
        with app.app_context():
            category = Category.query.filter_by(name=form.category.data).first()
            category_id2 = category.id
            location = Location.query.filter_by(name=form.location.data).first()
            location_id2 = location.id        
        ad = Ad(title=form.title.data, description=form.description.data, price=form.price.data, image=filename,
                user_id=current_user.id, category_id=category_id2, location_id=location_id2)
        db.session.add(ad)
        db.session.commit()
        flash('Votre annonce a été créée avec succès.', 'success')
        return redirect(url_for('index'))
    return render_template('new_ad.html', form=form)

@app.route('/ad/<int:id>')
def view_ad(id):
    ad = Ad.query.get_or_404(id)
    ad.views += 1
    db.session.commit()
    return render_template('view_ad.html', ad=ad)

@app.route('/ad/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ad(id):
    ad = Ad.query.get_or_404(id)
    if current_user != ad.user:
        flash('Vous n\'êtes pas autorisé à modifier cette annonce.', 'danger')
        return redirect(url_for('index'))
    form = AdForm(obj=ad)
    if form.validate_on_submit():
        ad.title = form.title.data
        ad.description = form.description.data
        category = Category.query.filter_by(name=form.category.data).first()
        ad.category_id = category.id
        ad.price = form.price.data
        location = Location.query.filter_by(name=form.location.data).first()
        ad.location_id = location.id
        db.session.commit()
        flash('Votre annonce a été modifiée avec succès.', 'success')
        return redirect(url_for('view_ad', id=ad.id))
    return render_template('edit_ad.html', form=form, ad=ad)


@app.route('/ad/<int:ad_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_ad(ad_id):
    ad = Ad.query.get_or_404(ad_id)
    if ad.user != current_user:
        abort(403)  # HTTP 403 Forbidden error

    form = ConfirmationForm()

    if form.validate_on_submit():
        db.session.delete(ad)
        db.session.commit()
        flash('Votre annonce a été supprimée avec succès.', 'success')
        return redirect(url_for('index'))

    return render_template('delete_ad.html', ad=ad, form=form)



@app.route('/user/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    user = User.query.get_or_404(id)
    if current_user != user:
        flash('Vous n\'êtes pas autorisé à modifier ce profil.', 'danger')
        return redirect(url_for('index'))
    form = RegisterForm(obj=user)
    if form.validate_on_submit():
        form.populate_obj(user)
        db.session.commit()
        flash('Votre profil a été modifié avec succès.', 'success')
        return redirect(url_for('index'))
    return render_template('edit_user.html', form=form, user=user)

@app.route('/category/<category_id>')
def show_category(category_id):
    category = Category.query.get(category_id)
    ads = Ad.query.filter_by(category=category).all()
    return render_template('category.html', category=category, ads=ads)

@app.route('/search')
def search():
    query = request.args.get('query')
    if not query:
        return render_template('search.html')
    ads = Ad.query.filter(Ad.title.ilike(f"%{query}%")).all()
    return render_template('search.html', query=query, ads=ads)

@app.route('/all-ads')
def all_ads():
    ads = Ad.query.all()
    return render_template('all_ads.html', ads=ads)

@app.route('/list_ads')
def list_ads():
    category = request.args.get('category')
    location = request.args.get('location')
    ads = Ad.query.all()
    if category and location:
        # filtrer par catégorie et emplacement
        category_ads = [ad for ad in ads if ad.category.name == category]
        location_ads = [ad for ad in ads if ad.location.name == location]
        ads = [ad for ad in category_ads if ad in location_ads]
    elif category:
        # filtrer par catégorie seulement
        ads = [ad for ad in ads if ad.category.name == category]
    elif location:
        # filtrer par emplacement seulement
        ads = [ad for ad in ads if ad.location.name == location]
    categories = Category.query.all()
    locations = Location.query.all()    
    return render_template('all_ads.html', ads=ads, categories=categories, locations=locations)

@app.route('/my-ads')
@login_required
def my_ads():
    ads = Ad.query.filter_by(user_id=current_user.id).all()
    return render_template('my_ads.html', ads=ads)



if __name__ == '_main_':
    app.run(debug=True)
    
@app.context_processor
def inject_categories():
    categories = Category.query.all()
    return dict(categories=categories)
@app.context_processor   
def inject_locations():
    locations = Location.query.all()
    return dict(locations=locations)