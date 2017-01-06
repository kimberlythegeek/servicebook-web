from flask import render_template
from flask import Blueprint


frontend = Blueprint('frontend', __name__)


@frontend.route("/")
def home():
    projects = frontend.app.db.get_entries('project', order_by='name')
    return render_template('home.html', projects=projects)
