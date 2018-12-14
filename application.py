from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   jsonify,
                   url_for,
                   flash)

from functools import wraps

from sqlalchemy import exc
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Library, Book, User

from flask import session as login_session
import random
import string

# imports for OAuth
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

# Saving Client information
CLIENT_ID = json.loads(
        open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = 'Library app'

# Connect to Database and create database session
engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if a user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius:'
    output += '150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;">'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except exc.SQLAlchemyError:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(redirect(url_for('showLibraries')))
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Library informations
@app.route('/library/api/JSON/')
def librariesJSON():
    libraries = session.query(Library).all()
    return jsonify(libraries=[l.serialize for l in libraries])


@app.route('/library/api/<int:library_id>/book/JSON/')
def libraryMenuJSON(library_id):
    books = session.query(Book).filter_by(library_id=library_id).all()
    return jsonify(books=[i.serialize for i in books])


@app.route('/library/api/<int:library_id>/book/<int:book_id>/JSON/')
def bookJSON(library_id, book_id):
    book = session.query(Book).filter_by(id=book_id).one()
    return jsonify(book=book.serialize)


@app.route('/')
@app.route('/library/')
def showLibraries():
    libraries = session.query(Library).order_by(asc(Library.name))
    if 'username' not in login_session:
        return render_template('publicLibrary.html',libraries=libraries)
    else:
        return render_template('library.html',
                                libraries=libraries,
                                user=login_session['username'])


def is_logged_in():
    if 'username' not in login_session:
        return False
    return True


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You are not allowed to access there")
            return redirect('/login')
    return decorated_function


@app.route('/library/new', methods=['GET', 'POST'])
@login_required
def newLibrary():
    """
    Method: Create a new library.
    Return:
        New library form.
    """
    if request.method == 'POST':
        newLibrary = Library(name=request.form['name'],
                             user_id=login_session['user_id'])
        session.add(newLibrary)
        flash('New library %s added to the Library list' % newLibrary.name)
        session.commit()
        return redirect(url_for('showLibraries'))
    else:
        return render_template('newLibrary.html',
                                user=login_session['username'])


@app.route('/library/<int:library_id>/edit', methods=['GET', 'POST'])
@login_required
def editLibrary(library_id):
    """
    Method: Allows to edit a library.
    Args:
        library_id (data type: int): Id of the library to edit.
    Return:
        edit library page of the site.
    """
    editedLibrary = session.query(Library).filter_by(id=library_id).one()
    if editedLibrary.user_id != login_session['user_id']:
        flash('You are not authorized to edit this Library')
        return redirect(url_for('showLibraries'))
    if request.method == 'POST':
        if request.form['name']:
            editedLibrary.name = request.form['name']
            session.commit()
            flash('Library successfully edited %s' % editedLibrary.name)
            return redirect(url_for('showLibraries'))
    else:
        return render_template('editLibrary.html',
                                library=editedLibrary,
                                user=login_session['username'])


@app.route('/library/<int:library_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteLibrary(library_id):
    """
    Method: Allows to delete a library.
    Args:
        library_id (data type: int): Id of the library to delete.
    Return:
        Delete library page of the site.
    """
    libraryToDelete = session.query(Library).filter_by(id=library_id).one()
    if libraryToDelete.user_id != login_session['user_id']:
        flash('You are not authorized to delete this Library')
        return redirect(url_for('showLibraries'))
    if request.method == 'POST':
        session.delete(libraryToDelete)
        flash('%s Successfully Deleted' % libraryToDelete.name)
        session.commit()
        return redirect(url_for('showLibraries'))
    else:
        return render_template('deleteLibrary.html', library=libraryToDelete)


@app.route('/library/<int:library_id>/book/')
def showBook(library_id):
    """
    Method: List all the books of the library.
    Args:
        library_id (data type: int): Id of the library.
    Return:
        book page containig list of books of the library.
    """
    library = session.query(Library).filter_by(id=library_id).one()
    books = session.query(Book).filter_by(library_id=library_id).all()
    creator = getUserInfo(library.user_id)
    if ('username' not in login_session or
        creator.id != login_session['user_id']):
        return render_template('publicbook.html',
                               books=books, library=library, creator=creator)
    else:
        return render_template('book.html',books=books,
                               library=library, creator=creator,
                               user=login_session['username'])


@app.route('/library/<int:library_id>/book/new', methods=['GET', 'POST'])
@login_required
def newBook(library_id):
    """
    Method: Create a new book in the library.
    Args:
        library_id (data type: int): Id of the library.
    Return:
        New book form.
    """
    library = session.query(Library).filter_by(id=library_id).one()
    if login_session['user_id'] != library.user_id:
        flash('You are not authorized to Edit this Library')
        return redirect(url_for('showLibraries'))
    if request.method == 'POST':
        newBook = Book(name=request.form['name'],
                       description=request.form['description'],
                       price=request.form['price'],
                       genre=request.form['genre'],
                       library_id=library_id)
        session.add(newBook)
        session.commit()
        flash('New Book %s added to the library successfully' % (newBook.name))
        return redirect(url_for('showBook', library_id=library_id))
    else:
        return render_template('newbook.html',
                               library_id=library_id,
                               user=login_session['username'])


@app.route('/library/<int:library_id>/book/<int:book_id>/edit/',
           methods=['GET', 'POST'])
@login_required
def editBook(library_id, book_id):
    """
    Method: Allows changing name, genre, description of book.
    Args:
        library_id (data type: int): Id of the library the book belongs.
        boook_id (data type: int): Id of the book to edit.
    Return:
        Edit book page of the site.
    """
    editedBook = session.query(Book).filter_by(id=book_id).one()
    library = session.query(Library).filter_by(id=library_id).one()
    if login_session['user_id'] != library.user_id:
        flash('You are not authorized to Edit this book')
        return redirect(url_for('showBook', library_id=library_id))
    if request.method == 'POST':
        if request.form['name']:
            editedBook.name = request.form['name']
        if request.form['description']:
            editedBook.description = request.form['description']
        if request.form['price']:
            editedBook.price = request.form['price']
        if request.form['genre']:
            editedBook.genre = request.form['genre']
        session.add(editedBook)
        session.commit()
        flash('Book info successfully edited')
        return redirect(url_for('showBook', library_id=library_id))
    else:
        return render_template('editbook.html', library_id=library_id,
                               book_id=book_id,
                               book=editedBook,
                               user=login_session['username'])


@app.route('/library/<int:library_id>/book/<int:book_id>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteBook(library_id, book_id):
    """
    Method: Allows to delete a book.
    Args:
        library_id (data type: int): Id of the library the book belongs.
        boook_id (data type: int): Id of the book to delete.
    Return:
        delete book page of the site.
    """
    library= session.query(Library).filter_by(id=library_id).one()
    bookToDelete = session.query(Book).filter_by(id=book_id).one()
    if login_session['user_id'] != library.user_id:
        flash('You are not authorized to delete this book')
        return redirect(url_for('showBook', library_id=library_id))
    if request.method == 'POST':
        session.delete(bookToDelete)
        session.commit()
        flash('Book deleted successfully')
        return redirect(url_for('showBook', library_id=library_id))
    else:
        return render_template('deleteBook.html',
                               book=bookToDelete,
                               user=login_session['username'])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000, threaded=False)
