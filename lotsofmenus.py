from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Library, Base, Book, User

engine = create_engine('sqlite:///library.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Sadman Chowdhury", email="sadman923@gmail.com",
             picture='https://bit.ly/2RyWFaU')
session.add(User1)
session.commit()

User2 = User(name="Jordan Mike", email="rabbiteabon@gmail.com",
             picture='https://bit.ly/2roAx7y')
session.add(User2)
session.commit()

# Menu for UrbanBurger
Library1 = Library(user_id=1, name="Heirloom Library")

session.add(Library1)
session.commit()

Library2 = Library(user_id=2, name="Idle Hour Library")

session.add(Library2)
session.commit()

Library3 = Library(user_id=1, name="Epiphany Library")

session.add(Library3)
session.commit()

Library4 = Library(user_id=2, name="Illusions Library")

session.add(Library4)
session.commit()

Library5 = Library(user_id=1, name="Harmony Library")

session.add(Library5)
session.commit()

book0 = Book(user_id=1, name="The Lord of the Rings", description="An epic high fantasy novel written by English author and scholar J. R. R. Tolkien",
                     price="$19", genre="Fiction", library=Library1)

session.add(book0)
session.commit()

book1 = Book(user_id=1, name="Intro to AI", description="Easy start on AI",
                     price="$7.50", genre="Science", library=Library1)

session.add(book1)
session.commit()

book2 = Book(user_id=1, name="Nineteen Eighty-Four", description="Novel by George Orwell",
                     price="$20.50", genre="Novel", library=Library1)

session.add(book2)
session.commit()

book3 = Book(user_id=1, name="Murder on the Orient Express", description="A detective novel by British writer Agatha Christie featuring the Belgian detective Hercule Poirot",
                     price="$10.00", genre="Mystery", library=Library3)

session.add(book3)
session.commit()

book4 = Book(user_id=1, name="Fermat's Last Theorem", description="A popular science book by Simon Singh",
                     price="$40", genre="Science", library=Library5)

session.add(book4)
session.commit()

book5 = Book(user_id=1, name="The Code Book", description="The Science of Secrecy from Ancient Egypt to Quantum Cryptography is a book by Simon Singh",
                     price="$22.99", genre="Science", library=Library3)

session.add(book5)
session.commit()

book6 = Book(user_id=2, name="The Handmaid's Tale", description="A dystopian novel by Canadian author Margaret Atwood",
                     price="$59.99", genre="Fiction", library=Library2)

session.add(book6)
session.commit()

book7 = Book(user_id=2, name="Outlander", description="Outlander is the first in a series of eight historical multi-genre novels by Diana Gabaldon",
                     price="$7.50", genre="Romance", library=Library2)

session.add(book7)
session.commit()

book8 = Book(user_id=2, name="Brave New World", description="A dystopian novel written in 1931 by English author Aldous Huxley",
                     price="$10.50", genre="Fiction", library=Library4)

session.add(book8)
session.commit()

book9 = Book(user_id=2, name="Intro to AI", description="Easy start on AI",
                     price="$8.00", genre="Science", library=Library4)

session.add(book9)
session.commit()

book10 = Book(user_id=2, name="Il cerchio di pietre", description="Voyager is the third book in the Outlander series of novels by Diana Gabaldon",
                     price="$25", genre="Romance", library=Library2)

session.add(book10)
session.commit()

book11 = Book(user_id=2, name="Alice's Adventures in Wonderland", description=" An 1865 novel written by English author Charles Lutwidge Dodgson",
                     price="$37", genre="Novel", library=Library2)

session.add(book11)
session.commit()


print 'added'
