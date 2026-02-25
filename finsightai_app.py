from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt  # Import Bcrypt for password hashing
from sqlalchemy.orm import class_mapper, ColumnProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy import func
from sqlalchemy import text
from sqlalchemy import Integer
import os
from werkzeug.security import generate_password_hash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_cors import CORS 
import smtplib
import random
import base64
import os
import uuid
from flask_restful import Api
from datetime import datetime, timedelta
from textblob import TextBlob

import pymysql
pymysql.install_as_MySQLdb()

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret')
bcrypt = Bcrypt(app)

db = SQLAlchemy(app)

class UserDetails(db.Model):
    __tablename__ = 'userdetails'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    phone_number = db.Column(db.String(15))
    email = db.Column(db.String(100))
    occupation = db.Column(db.String(100))
    income = db.Column(db.String(20))
    financial_goal = db.Column(db.String(50))
    risk = db.Column(db.String(10))
    location = db.Column(db.String(100))  # Added location field

    def __init__(self, name, phone_number, email, occupation, income, financial_goal, risk, location):
        self.name = name
        self.phone_number = phone_number
        self.email = email
        self.occupation = occupation
        self.income = income
        self.financial_goal = financial_goal
        self.risk = risk
        self.location = location  # Added location parameter

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone_number': self.phone_number,
            'email': self.email,
            'occupation': self.occupation,
            'income': self.income,
            'financial_goal': self.financial_goal,
            'risk': self.risk,
            'location': self.location  # Added location to dictionary
        }

    def __repr__(self):
        return f'<UserDetails {self.name}>'

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        # Create new user instance with location
        new_user = UserDetails(
            name=data.get('name'),
            phone_number=data.get('phone_number'),
            email=data.get('email'),
            occupation=data.get('occupation'),
            income=data.get('income'),
            financial_goal=data.get('financial_goal'),
            risk=data.get('risk'),
            location=data.get('location')  # Added location parameter
        )
        
        # Add to database
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "message": "User created successfully",
            "user": new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 400
    
import random
import smtplib
from flask import Flask, request, jsonify
from threading import Lock

otp_storage = {}
otp_lock = Lock()

EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def generate_otp():
    return str(random.randint(100000, 999999))


def send_email(to_email, otp):
    subject = "Your One-Time OTP Code for Verification"
    email_body = f"""Subject: {subject}

Hi there,

Thank you for choosing to verify your account with us. Below is your one-time password (OTP) to complete the verification process:

Your OTP code: {otp}

This code is valid for the next 10 minutes, so please enter it soon to complete your registration.

If you didn't request this OTP or need any assistance, feel free to contact us at tmsaipavan@gmail.com.

Thank you for your trust, and welcome to GREENAI!

Best regards,
GREENAI Team
tmsaipavan@gmail.com | 9962355558
"""
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, email_body)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


@app.route("/send_otp", methods=["POST"])
def send_otp():
    try:
        data = request.get_json()
        email = data.get("email")
        if not email:
            return jsonify({"status": "error", "message": "Email is required"}), 400

        otp = generate_otp()
        with otp_lock:
            otp_storage[email] = otp

        if send_email(email, otp):
            return jsonify({"status": "success", "message": "OTP sent successfully"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to send OTP"}), 500
    except Exception as e:
        print(f"Error in send_otp: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    try:
        data = request.get_json()
        email = data.get("email")
        user_otp = data.get("otp")

        if not email or not user_otp:
            return jsonify({"status": "error", "message": "Email and OTP are required"}), 400

        with otp_lock:
            stored_otp = otp_storage.get(email)

            if stored_otp and stored_otp == user_otp:
                del otp_storage[email]  # Remove OTP after successful verification
                
                # Add to active table
                existing_active = Active.query.filter_by(email=email).first()
                if not existing_active:
                    new_active = Active(email=email)
                    db.session.add(new_active)
                    db.session.commit()
                
                return jsonify({"status": "success", "message": "OTP verified successfully"}), 200
            else:
                return jsonify({"status": "error", "message": "Invalid OTP"}), 401
    except Exception as e:
        print(f"Error in verify_otp: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500



@app.route("/check_email", methods=["POST"])
def check_email():
    try:
        data = request.get_json()
        email = data.get("email")
        if not email:
            return jsonify({"status": "error", "message": "Email is required"}), 400

        # Query the UserDetails table to check if email exists
        user = UserDetails.query.filter_by(email=email).first()

        if user:
            return jsonify({"status": "success", "message": "Email exists"}), 200
        else:
            return jsonify({"status": "error", "message": "Email not registered"}), 404
    except Exception as e:
        print(f"Error in check_email: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

class Active(db.Model):
    __tablename__ = 'active'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mail = db.Column(db.String(100))

    def __init__(self, mail):
        self.mail = mail

    def to_dict(self):
        return {
            'id': self.id,
            'mail': self.mail
        }

    def __repr__(self):
        return f'<Active {self.mail}>'

@app.route('/add_active', methods=['POST'])
def add_active():
    try:
        data = request.get_json()
        
        # Create new active user instance (always add, no duplicate check)
        new_active = Active(
            mail=data.get('mail')
        )
        
        # Add to database without checking for existing email
        db.session.add(new_active)
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "message": "User added to active list successfully",
            "user": new_active.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 400



class Mood(db.Model):
    __tablename__ = 'mood'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mood = db.Column(db.String(50))

    def __init__(self, mood):
        self.mood = mood

    def to_dict(self):
        return {
            'id': self.id,
            'mood': self.mood
        }

    def __repr__(self):
        return f'<Mood {self.mood}>'

@app.route('/add_mood', methods=['POST'])
def add_mood():
    try:
        data = request.get_json()
        
        # Create new mood instance (always add, no duplicate check)
        new_mood = Mood(
            mood=data.get('mood')
        )
        
        # Add to database without checking for existing mood
        db.session.add(new_mood)
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "message": "Mood added successfully",
            "mood": new_mood.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 400
    
@app.route('/last_active_user', methods=['GET'])
def get_last_active_user():
    try:
        # Get the last entry from active table (highest ID = most recent)
        last_active = Active.query.order_by(Active.id.desc()).first()
        
        if not last_active:
            return jsonify({
                "status": "error",
                "message": "No active users found"
            }), 404
        
        # Get user details from userdetails table using the email
        user_details = UserDetails.query.filter_by(email=last_active.mail).first()
        
        if not user_details:
            return jsonify({
                "status": "error",
                "message": "User details not found for this email",
                "active_entry": last_active.to_dict()
            }), 404
        
        return jsonify({
            "status": "success",
            "message": "Last active user retrieved successfully",
            "active_entry": last_active.to_dict(),
            "user_details": user_details.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@app.route('/update_user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.get_json()
        
        # Find the user by ID
        user = UserDetails.query.get(user_id)
        
        if not user:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
        
        # Update user details
        user.name = data.get('name', user.name)
        user.phone_number = data.get('phone_number', user.phone_number)
        user.email = data.get('email', user.email)
        user.occupation = data.get('occupation', user.occupation)
        user.income = data.get('income', user.income)
        user.location = data.get('location', user.location)
        user.financial_goal = data.get('financial_goal', user.financial_goal)
        user.risk = data.get('risk', user.risk)
        
        # Save to database
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "User profile updated successfully",
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

# Alternative route to update by email
@app.route('/update_user_by_email', methods=['PUT'])
def update_user_by_email():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({
                "status": "error",
                "message": "Email is required"
            }), 400
        
        # Find the user by email
        user = UserDetails.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
        
        # Update user details
        user.name = data.get('name', user.name)
        user.phone_number = data.get('phone_number', user.phone_number)
        user.occupation = data.get('occupation', user.occupation)
        user.income = data.get('income', user.income)
        user.location = data.get('location', user.location)
        user.financial_goal = data.get('financial_goal', user.financial_goal)
        user.risk = data.get('risk', user.risk)
        
        # Save to database
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "User profile updated successfully",
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    
class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_email = db.Column(db.String(100))
    amount = db.Column(db.Numeric(10, 2))
    description = db.Column(db.String(255))
    category = db.Column(db.String(50))
    mood = db.Column(db.String(20))
    location = db.Column(db.String(100))
    transaction_date = db.Column(db.DateTime, default=datetime.now)
    transaction_type = db.Column(db.Enum('expense', 'income'), default='expense')

    def __init__(self, user_email, amount, description, category, mood, location, transaction_type='expense'):
        self.user_email = user_email
        self.amount = amount
        self.description = description
        self.category = category
        self.mood = mood
        self.location = location
        self.transaction_type = transaction_type

    def to_dict(self):
        return {
            'id': self.id,
            'user_email': self.user_email,
            'amount': float(self.amount),
            'description': self.description,
            'category': self.category,
            'mood': self.mood,
            'location': self.location,
            'transaction_date': str(self.transaction_date) if self.transaction_date else None,
            'transaction_type': self.transaction_type
        }

    def __repr__(self):
        return f'<Transaction {self.description}: {self.amount}>'
    
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    try:
        data = request.get_json()
        
        new_transaction = Transaction(
            user_email=data.get('user_email'),
            amount=data.get('amount'),
            description=data.get('description'),
            category=data.get('category'),
            mood=data.get('mood'),
            location=data.get('location', 'Current Location'),
            transaction_type=data.get('transaction_type', 'expense')
        )
        
        db.session.add(new_transaction)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Transaction added successfully",
            "transaction": new_transaction.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

# Get User Transactions Route
@app.route('/user_transactions/<email>', methods=['GET'])
def get_user_transactions(email):
    try:
        transactions = Transaction.query.filter_by(user_email=email).order_by(Transaction.transaction_date.desc()).all()
        
        return jsonify({
            "status": "success",
            "transactions": [transaction.to_dict() for transaction in transactions],
            "count": len(transactions),
            "message": f"Found {len(transactions)} transactions for {email}"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "transactions": [],
            "count": 0
        }), 200

# Get All Transactions Route
@app.route('/transactions', methods=['GET'])
def get_all_transactions():
    try:
        transactions = Transaction.query.order_by(Transaction.transaction_date.desc()).all()
        
        return jsonify({
            "status": "success",
            "transactions": [transaction.to_dict() for transaction in transactions],
            "count": len(transactions)
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

# Get Transaction Statistics Route
@app.route('/transaction_stats/<email>', methods=['GET'])
def get_transaction_stats(email):
    try:
        # Get user's income from userdetails table
        user_details = UserDetails.query.filter_by(email=email).first()
        if not user_details:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
        
        monthly_income = float(user_details.income) if user_details.income else 0
        
        # Get total expenses and income from transactions
        expense_total = db.session.query(func.sum(Transaction.amount)).filter_by(
            user_email=email, transaction_type='expense'
        ).scalar() or 0
        
        income_total = db.session.query(func.sum(Transaction.amount)).filter_by(
            user_email=email, transaction_type='income'
        ).scalar() or 0
        
        total_expenses = float(expense_total)
        savings = monthly_income - total_expenses
        savings_rate = (savings / monthly_income * 100) if monthly_income > 0 else 0
        
        # Get category-wise spending
        category_stats = db.session.query(
            Transaction.category,
            func.sum(Transaction.amount).label('total')
        ).filter_by(user_email=email, transaction_type='expense').group_by(Transaction.category).all()
        
        # Get mood-wise spending
        mood_stats = db.session.query(
            Transaction.mood,
            func.sum(Transaction.amount).label('total')
        ).filter_by(user_email=email, transaction_type='expense').group_by(Transaction.mood).all()
        
        return jsonify({
            "status": "success",
            "profile_income": monthly_income,
            "total_expenses": total_expenses,
            "transaction_income": float(income_total),
            "savings": savings,
            "savings_rate": round(savings_rate, 2),
            "expense_ratio": round((total_expenses / monthly_income * 100), 2) if monthly_income > 0 else 0,
            "category_breakdown": [{"category": cat, "amount": float(amt)} for cat, amt in category_stats],
            "mood_breakdown": [{"mood": mood, "amount": float(amt)} for mood, amt in mood_stats]
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "profile_income": 0,
            "total_expenses": 0,
            "savings": 0,
            "savings_rate": 0,
            "category_breakdown": [],
            "mood_breakdown": []
        }), 200

# Get User Dashboard Data Route
@app.route('/user_dashboard/<email>', methods=['GET'])
def get_user_dashboard(email):
    try:
        # Get user details including income
        user_details = UserDetails.query.filter_by(email=email).first()
        if not user_details:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
        
        monthly_income = float(user_details.income) if user_details.income else 0
        
        # Get transaction statistics
        expense_total = db.session.query(func.sum(Transaction.amount)).filter_by(
            user_email=email, transaction_type='expense'
        ).scalar() or 0
        
        recent_transactions = Transaction.query.filter_by(
            user_email=email
        ).order_by(Transaction.transaction_date.desc()).limit(5).all()
        
        return jsonify({
            "status": "success",
            "user_profile": user_details.to_dict(),
            "financial_summary": {
                "monthly_income": monthly_income,
                "total_expenses": float(expense_total),
                "current_savings": monthly_income - float(expense_total),
                "savings_rate": round(((monthly_income - float(expense_total)) / monthly_income * 100), 2) if monthly_income > 0 else 0
            },
            "recent_transactions": [transaction.to_dict() for transaction in recent_transactions]
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

# Initialize Sample Transactions Route
@app.route('/init_sample_transactions/<email>', methods=['POST'])
def init_sample_transactions(email):
    try:
        # Get user's income from userdetails table
        user_details = UserDetails.query.filter_by(email=email).first()
        if not user_details:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
        
        monthly_income = float(user_details.income) if user_details.income else 0
        
        if monthly_income == 0:
            return jsonify({
                "status": "error",
                "message": "User income not set"
            }), 400
        
        # Calculate proportional expenses based on income
        sample_transactions = [
            {
                'user_email': email,
                'amount': round(monthly_income * 0.007, 2),  # ~0.7% for lunch
                'description': 'Lunch at Cafe Coffee Day',
                'category': 'Food & Dining',
                'mood': 'Happy',
                'location': user_details.location or 'Current City',
                'transaction_type': 'expense'
            },
            {
                'user_email': email,
                'amount': round(monthly_income * 0.018, 2),  # ~1.8% for transport
                'description': 'Uber ride to office',
                'category': 'Transportation',
                'mood': 'Neutral',
                'location': user_details.location or 'Current City',
                'transaction_type': 'expense'
            },
            {
                'user_email': email,
                'amount': round(monthly_income * 0.038, 2),  # ~3.8% for shopping
                'description': 'Shopping at Reliance Trends',
                'category': 'Shopping',
                'mood': 'Happy',
                'location': user_details.location or 'Current City',
                'transaction_type': 'expense'
            },
            {
                'user_email': email,
                'amount': round(monthly_income * 0.054, 2),  # ~5.4% for utilities
                'description': 'Electricity Bill',
                'category': 'Bills & Utilities',
                'mood': 'Neutral',
                'location': 'Online Payment',
                'transaction_type': 'expense'
            },
            {
                'user_email': email,
                'amount': round(monthly_income * 0.23, 2),   # ~23% for rent
                'description': 'House Rent',
                'category': 'Bills & Utilities',
                'mood': 'Sad',
                'location': user_details.location or 'Current City',
                'transaction_type': 'expense'
            },
            {
                'user_email': email,
                'amount': round(monthly_income * 0.012, 2),  # ~1.2% for entertainment
                'description': 'Movie tickets',
                'category': 'Entertainment',
                'mood': 'Joyful',
                'location': 'PVR Cinemas',
                'transaction_type': 'expense'
            },
            {
                'user_email': email,
                'amount': round(monthly_income * 0.077, 2),  # ~7.7% for groceries
                'description': 'Groceries for month',
                'category': 'Food & Dining',
                'mood': 'Neutral',
                'location': 'BigBasket',
                'transaction_type': 'expense'
            },
            {
                'user_email': email,
                'amount': round(monthly_income * 0.031, 2),  # ~3.1% for petrol
                'description': 'Petrol',
                'category': 'Transportation',
                'mood': 'Sad',
                'location': 'HP Petrol Pump',
                'transaction_type': 'expense'
            },
            {
                'user_email': email,
                'amount': round(monthly_income * 0.023, 2),  # ~2.3% for healthcare
                'description': 'Doctor consultation',
                'category': 'Healthcare',
                'mood': 'Neutral',
                'location': 'Apollo Hospital',
                'transaction_type': 'expense'
            },
            {
                'user_email': email,
                'amount': round(monthly_income * 0.154, 2), # ~15.4% for investment
                'description': 'SIP Investment',
                'category': 'Investment',
                'mood': 'Happy',
                'location': 'Zerodha',
                'transaction_type': 'expense'
            },
            {
                'user_email': email,
                'amount': round(monthly_income * 0.046, 2),  # ~4.6% for travel
                'description': 'Weekend trip',
                'category': 'Travel',
                'mood': 'Joyful',
                'location': user_details.location or 'Current City',
                'transaction_type': 'expense'
            }
        ]
        
        added_transactions = []
        total_expenses = 0
        
        for transaction_data in sample_transactions:
            new_transaction = Transaction(
                user_email=transaction_data['user_email'],
                amount=transaction_data['amount'],
                description=transaction_data['description'],
                category=transaction_data['category'],
                mood=transaction_data['mood'],
                location=transaction_data['location'],
                transaction_type=transaction_data['transaction_type']
            )
            db.session.add(new_transaction)
            added_transactions.append({
                'description': transaction_data['description'],
                'amount': transaction_data['amount']
            })
            total_expenses += transaction_data['amount']
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"Added {len(added_transactions)} sample transactions",
            "user_income": monthly_income,
            "total_sample_expenses": round(total_expenses, 2),
            "savings": round(monthly_income - total_expenses, 2),
            "savings_rate": round(((monthly_income - total_expenses) / monthly_income * 100), 2),
            "transactions": added_transactions
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

# Delete Transaction Route
@app.route('/delete_transaction/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    try:
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({
                "status": "error",
                "message": "Transaction not found"
            }), 404
        
        db.session.delete(transaction)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Transaction deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

# Update Transaction Route
@app.route('/update_transaction/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    try:
        data = request.get_json()
        transaction = Transaction.query.get(transaction_id)
        
        if not transaction:
            return jsonify({
                "status": "error",
                "message": "Transaction not found"
            }), 404
        
        # Update transaction fields
        transaction.amount = data.get('amount', transaction.amount)
        transaction.description = data.get('description', transaction.description)
        transaction.category = data.get('category', transaction.category)
        transaction.mood = data.get('mood', transaction.mood)
        transaction.location = data.get('location', transaction.location)
        transaction.transaction_type = data.get('transaction_type', transaction.transaction_type)
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Transaction updated successfully",
            "transaction": transaction.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

# Get Recent Transactions Route
@app.route('/recent_transactions/<email>/<int:limit>', methods=['GET'])
def get_recent_transactions(email, limit=10):
    try:
        transactions = Transaction.query.filter_by(user_email=email).order_by(
            Transaction.transaction_date.desc()
        ).limit(limit).all()
        
        return jsonify({
            "status": "success",
            "transactions": [transaction.to_dict() for transaction in transactions],
            "count": len(transactions)
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

# Get Transactions by Category Route
@app.route('/transactions_by_category/<email>/<category>', methods=['GET'])
def get_transactions_by_category(email, category):
    try:
        transactions = Transaction.query.filter_by(
            user_email=email, 
            category=category
        ).order_by(Transaction.transaction_date.desc()).all()
        
        total_amount = sum([float(t.amount) for t in transactions])
        
        return jsonify({
            "status": "success",
            "category": category,
            "transactions": [transaction.to_dict() for transaction in transactions],
            "count": len(transactions),
            "total_amount": total_amount
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    


@app.route('/top_spending_locations/<email>', methods=['GET'])
def get_top_spending_locations(email):
    try:
        from sqlalchemy import func
        print(f"API called for email: {email}")
        
        # Get top 3 individual transactions (not grouped by location)
        top_transactions = Transaction.query.filter_by(
            user_email=email, 
            transaction_type='expense'
        ).order_by(
            Transaction.amount.desc()
        ).limit(3).all()
        
        print(f"Found {len(top_transactions)} transactions")
        
        # Location coordinates with more variety
        location_coordinates = {
            'Mumbai': {'lat': 19.0760, 'lng': 72.8777},
            'Delhi': {'lat': 28.6139, 'lng': 77.2090},
            'Bangalore': {'lat': 12.9716, 'lng': 77.5946},
            'Chennai': {'lat': 13.0827, 'lng': 80.2707},
            'FORUM MALL CHENNAI': {'lat': 13.0358, 'lng': 80.2297},
            'Phoenix Mall': {'lat': 19.0896, 'lng': 72.8656},
            'Cafe Coffee Day': {'lat': 13.0800, 'lng': 80.2750},  # Chennai CCD
            'PVR Cinemas': {'lat': 13.0450, 'lng': 80.2400},     # Chennai PVR
            'BigBasket': {'lat': 13.0900, 'lng': 80.2800},       # Chennai BigBasket
            'HP Petrol Pump': {'lat': 13.0750, 'lng': 80.2650}, # Chennai Petrol
            'Apollo Hospital': {'lat': 13.0878, 'lng': 80.2785}, # Chennai Apollo
            'Zerodha': {'lat': 13.0600, 'lng': 80.2500},
            'Online Payment': {'lat': 13.0827, 'lng': 80.2707},
            'Current Location': {'lat': 13.0827, 'lng': 80.2707},
            'Reliance Trends': {'lat': 13.0400, 'lng': 80.2350},
            'Metro Station': {'lat': 13.0820, 'lng': 80.2720},
            'Big Bazaar': {'lat': 13.0380, 'lng': 80.2320},
            'Current City': {'lat': 13.0827, 'lng': 80.2707}
        }
        
        category_colors = {
            'Food & Dining': '#EF4444',
            'Transportation': '#06B6D4',
            'Shopping': '#EC4899',
            'Entertainment': '#8B5CF6',
            'Bills & Utilities': '#F59E0B',
            'Healthcare': '#10B981',
            'Investment': '#6366F1',
            'Travel': '#84CC16',
            'Others': '#9CA3AF'
        }
        
        spending_locations = []
        for i, transaction in enumerate(top_transactions):
            print(f"Transaction {i+1}: {transaction.description}, Amount: {transaction.amount}, Location: {transaction.location}")
            
            # Get base coordinates
            base_coords = location_coordinates.get(transaction.location, {'lat': 13.0827, 'lng': 80.2707})
            
            # Add slight offset to separate markers if they're in the same location
            lat_offset = (i * 0.002) - 0.002  # Small offset for each marker
            lng_offset = (i * 0.002) - 0.002
            
            final_lat = base_coords['lat'] + lat_offset
            final_lng = base_coords['lng'] + lng_offset
            
            spending_locations.append({
                'name': f"{transaction.description}",  # Use description as name
                'location': transaction.location,      # Original location
                'total_amount': float(transaction.amount),
                'transaction_count': 1,  # Individual transaction
                'category': transaction.category,
                'latitude': final_lat,
                'longitude': final_lng,
                'color': category_colors.get(transaction.category, '#9CA3AF'),
                'transaction_id': transaction.id,
                'mood': transaction.mood,
                'date': str(transaction.transaction_date) if transaction.transaction_date else None
            })
        
        print(f"Returning {len(spending_locations)} individual spending points")
        
        return jsonify({
            "status": "success",
            "top_locations": spending_locations,
            "count": len(spending_locations)
        }), 200
        
    except Exception as e:
        print(f"Error in top_spending_locations: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "top_locations": [],
            "count": 0
        }), 200
    
from decimal import Decimal
from flask import jsonify

@app.route('/ai_suggestions/<email>', methods=['GET'])
def get_ai_suggestions(email):
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        print(f"Getting AI suggestions for: {email}")
        
        user_details = UserDetails.query.filter_by(email=email).first()
        if not user_details:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
        
        monthly_income = float(user_details.income) if user_details.income else 0
        
        expense_total = db.session.query(func.sum(Transaction.amount)).filter_by(
            user_email=email, transaction_type='expense'
        ).scalar() or 0
        
        if isinstance(expense_total, Decimal):
            expense_total = float(expense_total)
        
        current_savings = monthly_income - expense_total
        savings_rate = (current_savings / monthly_income * 100) if monthly_income > 0 else 0
        
        # Fetch grouped spending data as lists
        category_spending = db.session.query(
            Transaction.category,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).filter_by(user_email=email, transaction_type='expense').group_by(Transaction.category).all()
        
        # Convert Decimal to float in category spending
        category_spending = [
            (cat[0], float(cat[1]) if isinstance(cat[1], Decimal) else cat[1], cat[2])
            for cat in category_spending
        ]
        
        # Similarly for other data, omitted for brevity
        
        suggestions = []
        # Create some sample suggestion for demonstration
        suggestions.append({
            'id': 'savings_rate',
            'title': 'Improve Savings Rate',
            'description': f'Your savings rate is {savings_rate:.1f}%. Try to save more.',
            'type': 'savings_improvement',
            'impact': 'Improved budget health',
            'priority': 'high',
            'source': 'savings_analysis',
            'icon': 'savings',
            'color': '#EF4444',
            'actionable': True
        })
        
        return jsonify({
            "status": "success",
            "suggestions": suggestions,
            "count": len(suggestions),
            "user_stats": {
                "monthly_income": monthly_income,
                "total_expenses": expense_total,
                "current_savings": current_savings,
                "savings_rate": round(savings_rate, 2)
            }
        }), 200
    
    except Exception as e:
        print(f"Error generating AI suggestions: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "suggestions": [],
            "count": 0
        }), 200


from flask import jsonify, request
from datetime import datetime, timedelta
from collections import defaultdict

@app.route('/moods_transactions/<email>', methods=['GET'])
def get_moods_transactions(email):
    # Optional query param: period in days (7,30,90)
    period_days = int(request.args.get('days', 7))
    now = datetime.utcnow()
    start_date = now - timedelta(days=period_days)
    
    transactions = Transaction.query.filter(
        Transaction.user_email == email,
        Transaction.transaction_date >= start_date
    ).all()
    
    mood_data = defaultdict(list)
    for txn in transactions:
        mood_data[txn.mood].append({
            "amount": float(txn.amount),
            "description": txn.description,
            "date": str(txn.transaction_date)
        })
    
    # Group transactions by mood with total amount
    result = {}
    for mood, txns in mood_data.items():
        total = sum(txn["amount"] for txn in txns)
        result[mood] = {
            "transactions": txns,
            "total": total
        }
    
    return jsonify({"status": "success", "data": result})

class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    target_amount = db.Column(db.Float, nullable=True)
    saved_amount = db.Column(db.Float, nullable=True, default=0.0)
    location = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Route to get all calendar events for a user
@app.route('/calendar_events/<user_email>', methods=['GET'])
def get_calendar_events(user_email):
    events = CalendarEvent.query.filter_by(user_email=user_email).all()
    result = []
    for ev in events:
        progress_percent = 0
        if ev.target_amount and ev.target_amount > 0:
            progress_percent = min((ev.saved_amount or 0) / ev.target_amount * 100, 100)
        result.append({
            'id': ev.id,
            'title': ev.title,
            'description': ev.description,
            'start_date': str(ev.start_date),
            'end_date': str(ev.end_date) if ev.end_date else None,
            'target_amount': ev.target_amount or 0,
            'saved_amount': ev.saved_amount or 0,
            'progress_percent': progress_percent,
            'location': ev.location,
        })
    return jsonify({'status': 'success', 'events': result})

# Route to add/update event
@app.route('/calendar_event', methods=['POST'])
def add_update_event():
    data = request.json
    ev_id = data.get('id')
    if ev_id:
        ev = CalendarEvent.query.get(ev_id)
        if not ev:
            return jsonify({'status':'error', 'message':'Event not found'}), 404
    else:
        ev = CalendarEvent()
        ev.user_email = data['user_email']
    ev.title = data['title']
    ev.description = data.get('description')
    ev.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    ev.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None
    ev.target_amount = float(data.get('target_amount', 0))
    ev.saved_amount = float(data.get('saved_amount', 0))
    ev.location = data.get('location')
    db.session.add(ev)
    db.session.commit()
    return jsonify({'status':'success', 'event': {
        'id': ev.id,
        'title': ev.title,
        'description': ev.description,
        'start_date': str(ev.start_date),
        'end_date': str(ev.end_date) if ev.end_date else None,
        'target_amount': ev.target_amount,
        'saved_amount': ev.saved_amount,
        'progress_percent': ev.saved_amount/ev.target_amount*100 if ev.target_amount > 0 else 0,
        'location': ev.location,
    }})

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    target = db.Column(db.Float, nullable=False)
    current = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    deadline = db.Column(db.Date, nullable=False)
    color = db.Column(db.String(7), nullable=False)  # hex color
    icon = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    monthly_contribution = db.Column(db.Float, nullable=True)

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)
    icon = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), nullable=False)

@app.route('/goals/<user_email>', methods=['GET'])
def get_goals(user_email):
    goals = Goal.query.filter_by(user_email=user_email).all()
    result = []
    for g in goals:
        result.append({
            'id': str(g.id),
            'title': g.title,
            'target': g.target,
            'current': g.current,
            'category': g.category,
            'deadline': str(g.deadline),
            'color': g.color,
            'icon': g.icon,
            'description': g.description,
            'monthlyContribution': g.monthly_contribution
        })
    return jsonify({'status': 'success', 'goals': result})

@app.route('/achievements/<user_email>', methods=['GET'])
def get_achievements(user_email):
    achievements = Achievement.query.filter_by(user_email=user_email).all()
    result = []
    for a in achievements:
        result.append({
            'id': str(a.id),
            'title': a.title,
            'description': a.description,
            'date': str(a.date),
            'icon': a.icon,
            'color': a.color
        })
    return jsonify({'status': 'success', 'achievements': result})






if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))