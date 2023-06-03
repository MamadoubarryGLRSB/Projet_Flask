from app import db
from app import User, Category, Location

# Ajouter les utilisateurs
user1 = User(phone_number='773456789', full_name='John Doe', address='Dakar', password='password')
user2 = User(phone_number='775678901', full_name='Jane Doe', address='Thiès', password='password')
user3 = User(phone_number='776789012', full_name='Bob Smith', address='Ziguinchor', password='password')

db.session.add_all([user1, user2, user3])
db.session.commit()

# Ajouter les catégories
category1 = Category(name='Electronique')
category2 = Category(name='Maison')
category3 = Category(name='Véhicules')
category4 = Category(name='Mode')
category5 = Category(name='Sports et Loisirs')
category6 = Category(name='Autres')

db.session.add_all([category1, category2, category3, category4, category5, category6])
db.session.commit()

# Ajouter les villes
location1 = Location(name='Dakar')
location2 = Location(name='Thiès')
location3 = Location(name='Saint-Louis')
location4 = Location(name='Ziguinchor')
location5 = Location(name='Tambacounda')

db.session.add_all([location1, location2, location3, location4, location5])
db.session.commit()
