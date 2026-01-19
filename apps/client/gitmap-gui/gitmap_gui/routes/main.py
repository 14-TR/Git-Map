"""Main route handler."""
from flask import Blueprint, render_template

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Serve the main GUI page."""
    return render_template('base.html')
