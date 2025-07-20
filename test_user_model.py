"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

from sqlalchemy.exc import IntegrityError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app

app.config['WTF_CSRF_ENABLED'] = False

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        db.session.commit()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
    
    def test_repr(self):
        '''Does the __repr__ work correctly?'''
        u = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()
        
        self.assertEqual(str(u), f"<User #{u.id}: {u.username}, {u.email}>")

    def test_is_following(self):
        '''Does the is_following model function dectect an added follow?'''
        u1, u2 = self.sign_up_users_login(self.client)
        self.assertIsNotNone(u1)
        self.assertIsNotNone(u2)

        # checks if user 1 is following user 2 before follow route
        self.assertFalse(u1.is_following(u2))

        # makes user 1 follow user 2
        follow = self.client.post(f'/users/follow/{u2.id}', follow_redirects=False)
        self.assertEqual(follow.status_code, 302)

        # re-gets user 1 and user 2
        u1 = User.query.filter_by(username='testuser1').first()
        u2 = User.query.filter_by(username='testuser2').first()

        # checks if user 1 is following user 2 after follow route
        self.assertTrue(u1.is_following(u2))

        # makes user 1 unfollow user 2
        stop_following = self.client.post(f'/users/stop-following/{u2.id}', follow_redirects=False)
        self.assertEqual(stop_following.status_code, 302)

        # # re-gets user 1 and user 2
        u1 = User.query.filter_by(username='testuser1').first()
        u2 = User.query.filter_by(username='testuser2').first()

        # checks if user 1 is no longer following user 2
        self.assertFalse(u1.is_following(u2))

    
    def test_is_followed_by(self):
        u1, u2 = self.sign_up_users_login(self.client)

        # checks if user 1 is following user 2 before follow route
        self.assertFalse(u2.is_followed_by(u1))

        # makes user 1 follow user 2
        follow = self.client.post(f'/users/follow/{u2.id}', follow_redirects=False)
        self.assertEqual(follow.status_code, 302)

        # re-gets user 1 and user 2
        u1 = User.query.filter_by(username='testuser1').first()
        u2 = User.query.filter_by(username='testuser2').first()

        # checks if user 1 is following user 2 after follow route
        self.assertTrue(u2.is_followed_by(u1))

        # makes user 1 unfollow user 2
        stop_following = self.client.post(f'/users/stop-following/{u2.id}', follow_redirects=False)
        self.assertEqual(stop_following.status_code, 302)

        # # re-gets user 1 and user 2
        u1 = User.query.filter_by(username='testuser1').first()
        u2 = User.query.filter_by(username='testuser2').first()

        # checks if user 2 is no longer followed by user 1
        self.assertFalse(u2.is_followed_by(u1))

    def test_user_signup(self):
        plain_password = 'password123'

        # signs up user 1
        u1_signup = User.signup('testuser1', plain_password, 'test@test.com', '')
        db.session.commit()

        # makes sure sign up method creates a user
        self.assertEqual('testuser1', u1_signup.username)

        # gets user 1
        u1 = User.query.filter_by(username='testuser1').first()

        # makes sure user exists in database
        self.assertIsNotNone(u1)

        # tests empty username
        with self.assertRaises(ValueError) as context:
            User.signup('', plain_password, 'test2@test.com', '')
        self.assertEqual(str(context.exception), "Username cannot be empty")

        # tests taken username
        with self.assertRaises(ValueError) as context:
            User.signup('testuser1', 'differentpassword', 'different@test.com', '')
        self.assertEqual(str(context.exception), "Username 'testuser1' is already taken")




    def sign_up_users_login(self, client):
        ''' Helper Method to create 2 users and sign in user 1 '''
        plain_password = 'password123'

        # signs up user 1
        signup_data1 = {'username': 'testuser1', 'password': plain_password, 'email': 'test@test.com', 'image_url': ''}
        signup1 = client.post('/signup', data=signup_data1, follow_redirects=False)
        assert signup1.status_code == 302

        # signs up user 2
        signup_data2 = {'username': 'testuser2', 'password': plain_password, 'email': 'test2@test.com', 'image_url': ''}
        signup2 = client.post('/signup', data=signup_data2, follow_redirects=False)
        assert signup2.status_code == 302

        # logs in user 1
        login_data = {'username': signup_data1['username'], 'password': plain_password}
        login = client.post('/login', data=login_data, follow_redirects=False)
        assert login.status_code == 302

        # tests users exist in db by returning the user objects
        return User.query.filter_by(username=signup_data1['username']).first(), User.query.filter_by(username=signup_data2['username']).first()