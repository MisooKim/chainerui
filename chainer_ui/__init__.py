''' init.py '''


import os


from flask import Flask, render_template, url_for, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker


CHAINER_UI_ENV = os.getenv('CHAINER_UI_ENV', 'prouction')
CHAINER_UI_ROOT = os.path.abspath(
    os.path.expanduser(os.getenv('CHAINER_UI_ROOT', '~/.chainer_ui')))
PACKAGE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_FILE_DIR = os.path.join(CHAINER_UI_ROOT, 'db')
DB_FILE_PATH = os.path.join(DB_FILE_DIR, 'chainer-ui.db')
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DB_FILE_PATH
ENGINE = create_engine(
    SQLALCHEMY_DATABASE_URI,
    convert_unicode=True,
    connect_args={'check_same_thread': False},
    echo=(CHAINER_UI_ENV == 'development')
)
DB_BASE = declarative_base()
DB_SESSION = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)
)


def create_db():
    ''' create_db '''
    if not os.path.isdir(DB_FILE_DIR):
        os.makedirs(DB_FILE_DIR, exist_ok=True)
    print('DB_FILE_PATH: ', DB_FILE_PATH)


def create_db_session():
    ''' create_db_session '''
    session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)
    )
    return session()


def create_app(args):
    ''' create_app '''

    app = Flask(__name__)
    app.config['DEBUG'] = False

    def dated_url_for(endpoint, **values):
        ''' dated_url_for '''
        if endpoint == 'static':
            filename = values.get('filename', None)
            if filename:
                file_path = os.path.join(app.root_path, endpoint, filename)
                values['_'] = int(os.stat(file_path).st_mtime)
        return url_for(endpoint, **values)

    @app.context_processor
    def override_url_for():
        ''' override_url_for '''
        return dict(url_for=dated_url_for)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        DB_SESSION.remove()

    @app.route('/')
    @app.route('/projects/<int:project_id>')
    @app.route('/projects/<int:project_id>/results/<int:result_id>')
    def index(**kwargs):
        ''' render react app '''
        return render_template('index.html')

    from chainer_ui.views.project import ProjectAPI
    from chainer_ui.views.result import ResultAPI
    from chainer_ui.views.result_command import ResultCommandAPI

    project_resource = ProjectAPI.as_view('project_resource')
    result_resource = ResultAPI.as_view('result_resource')
    result_command_resource = ResultCommandAPI.as_view(
        'result_command_resource')

    # project API
    app.add_url_rule(
        '/api/v1/projects',
        defaults={'id': None}, view_func=project_resource, methods=['GET'])
    app.add_url_rule(
        '/api/v1/projects/<int:id>',
        view_func=project_resource, methods=['GET', 'PUT', 'DELETE'])

    # result API
    app.add_url_rule(
        '/api/v1/projects/<int:project_id>/results',
        defaults={'id': None}, view_func=result_resource, methods=['GET'])
    app.add_url_rule(
        '/api/v1/projects/<int:project_id>/results/<int:id>',
        view_func=result_resource, methods=['GET', 'PUT', 'DELETE'])

    # result command API
    app.add_url_rule(
        '/api/v1/projects/<int:project_id>/results/<int:result_id>/commands',
        view_func=result_command_resource, methods=['POST'])

    return app