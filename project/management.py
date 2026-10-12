from flask import Blueprint, render_template

management_bp = Blueprint("management", __name__)


@management_bp.route("/management")
def management():
    return render_template("management.html")