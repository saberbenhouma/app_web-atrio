from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    person = db.relationship('Person', backref=db.backref('jobs', lazy=True))

@app.route('/add_person', methods=['POST'])
def add_person():
    data = request.get_json()
    birth_date = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
    age = (datetime.now().date() - birth_date).days // 365
    if age >= 150:
        return jsonify(error="Person is too old to be registered."), 400

    new_person = Person(first_name=data['first_name'], last_name=data['last_name'], date_of_birth=birth_date)
    db.session.add(new_person)
    db.session.commit()

    return jsonify(message="Person added successfully."), 201

@app.route('/add_job/<int:person_id>', methods=['POST'])
def add_job(person_id):
    person = Person.query.get(person_id)
    if not person:
        return jsonify(error="Person not found."), 404

    data = request.get_json()
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(data.get('end_date', ''), '%Y-%m-%d').date() if data.get('end_date') else None

    new_job = Job(company_name=data['company_name'], position=data['position'],
                  start_date=start_date, end_date=end_date, person=person)
    db.session.add(new_job)
    db.session.commit()

    return jsonify(message="Job added successfully."), 201

@app.route('/get_all_people', methods=['GET'])
def get_all_people():
    people = Person.query.order_by(Person.last_name, Person.first_name).all()
    result = []
    for person in people:
        age = (datetime.now().date() - person.date_of_birth).days // 365
        current_jobs = [job.serialize() for job in person.jobs if job.end_date is None]
        result.append({
            'id': person.id,
            'first_name': person.first_name,
            'last_name': person.last_name,
            'age': age,
            'current_jobs': current_jobs
        })

    return jsonify(result)

@app.route('/get_people_by_company/<string:company_name>', methods=['GET'])
def get_people_by_company(company_name):
    jobs = Job.query.filter_by(company_name=company_name).all()
    result = []
    for job in jobs:
        person = job.person
        age = (datetime.now().date() - person.date_of_birth).days // 365
        result.append({
            'person_id': person.id,
            'first_name': person.first_name,
            'last_name': person.last_name,
            'age': age,
            'position': job.position
        })

    return jsonify(result)

@app.route('/get_jobs_by_dates/<int:person_id>', methods=['GET'])
def get_jobs_by_dates(person_id):
    person = Person.query.get(person_id)
    if not person:
        return jsonify(error="Person not found."), 404

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    jobs = Job.query.filter_by(person_id=person_id).filter(
        (Job.start_date >= start_date) & (Job.end_date <= end_date if end_date else True)
    ).all()

    result = [job.serialize() for job in jobs]
    return jsonify(result)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True)