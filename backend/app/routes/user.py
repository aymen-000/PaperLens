from flask import Blueprint, request, jsonify
from agents.data.embedding import handle_paper_interaction, get_paper_recommendations
from backend.app.auth.auth_utils import hash_password, verify_password
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.models import User
# Create Blueprint
user_bp = Blueprint("user_api", __name__, url_prefix="/api/user")

# =====================
# Get paper recommendation endpoint 
# =====================
@user_bp.route('/recommendations', methods=['POST'])
@jwt_required()
def get_recommendations():
    """Get paper recommendations for a user"""
    try:
        data = request.get_json()
        papers = data.get('papers', [])
        user_id = data.get("user_id", "")
        
        if not papers:
            return jsonify({"error": "papers array is required"}), 400
        
        recommendations = get_paper_recommendations(user_id, papers)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "recommendations": recommendations,
            "count": len(recommendations)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===========================
# Interact with paper endpoint 
# ===========================
@user_bp.route('/paper-interaction', methods=['POST'])
@jwt_required()
def paper_interaction():
    """Handle user interaction with papers (LIKE/DISLIKE)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        paper = data.get('paper')
        interaction = data.get('interaction')  # "LIKE" or "DISLIKE"
        
        if not all([user_id, paper, interaction]):
            return jsonify({"error": "user_id, paper, and interaction are required"}), 400
        
        if interaction not in ["LIKE", "DISLIKE"]:
            return jsonify({"error": "interaction must be 'LIKE' or 'DISLIKE'"}), 400
        
        handle_paper_interaction(user_id, paper, interaction)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "interaction": interaction,
            "message": f"Interaction '{interaction}' recorded successfully"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
    


# ===========================
# Register endpoint
# ===========================
@user_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    name = data.get("name")
    password = data.get("password")

    if not all([email, password]):
        return jsonify({"error": "email and password required"}), 400

    db: Session = SessionLocal()
    if db.query(User).filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400

    new_user = User(email=email, name=name, password=hash_password(password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return jsonify({"id": new_user.id, "email": new_user.email, "name": new_user.name}), 201


# ===========================
# Login endpoint
# ===========================
@user_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    db: Session = SessionLocal()
    user = db.query(User).filter_by(email=email).first()
    if not user or not verify_password(password, user.password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=user.id)
    return jsonify({"token": token, "token_type": "bearer" , "id" : user.id})


# ===========================
# Get current user profile
# ===========================
@user_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    db: Session = SessionLocal()
    user = db.query(User).get(user_id)
    return jsonify({
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "created_at": user.created_at.isoformat()
    })