"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

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

    def tearDown(self):
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        db.session.commit()
    
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

        plain_password = 'password123'

        # signs up user 1
        signup_data1 = {'username': 'testuser1', 'password': plain_password, 'email': 'test@test.com', 'image_url': ''}
        signup1 = self.client.post('/signup', data=signup_data1, follow_redirects=False)
        self.assertEqual(signup1.status_code, 302)

        # signs up user 2
        signup_data2 = {'username': 'testuser2', 'password': plain_password, 'email': 'test2@test.com', 'image_url': ''}
        signup2 = self.client.post('/signup', data=signup_data2, follow_redirects=False)
        self.assertEqual(signup2.status_code, 302)

        # checks both users valid sign up
        u1 = User.query.filter_by(username=signup_data1['username']).first()
        u2 = User.query.filter_by(username=signup_data2['username']).first()
        self.assertIsNotNone(u1)
        self.assertIsNotNone(u2)

        # logs in user 1
        login_data = {'username': u1.username, 'password': plain_password}
        login = self.client.post('/login', data=login_data, follow_redirects=False)
        self.assertEqual(login.status_code, 302)

        # re gets user 2
        u1 = User.query.filter_by(username=signup_data1['username']).first()
        u2 = User.query.filter_by(username=signup_data2['username']).first()

        # checks if u1 is following u2 before follow route
        self.assertFalse(u1.is_following(u2))

        # makes user 1 follow user 2
        follow = self.client.post(f'/users/follow/{u2.id}', follow_redirects=False)
        self.assertEqual(follow.status_code, 302)

        # re gets user 2
        u1 = User.query.filter_by(username=signup_data1['username']).first()
        u2 = User.query.filter_by(username=signup_data2['username']).first()

        # checks if u1 is following u2 after follow route
        self.assertTrue(u1.is_following(u2))
        
        # has u1 unfollow u2
        stop_following = self.client.post(f'/users/stop-following/{u2.id}', follow_redirects=False)
        self.assertEqual(stop_following.status_code, 302)

        # re gets users 1 and 2
        u1 = User.query.filter_by(username=signup_data1['username']).first()
        u2 = User.query.filter_by(username=signup_data2['username']).first()

        # checks if u1 is no longer on u2 follow list
        self.assertFalse(u1.is_following(u2))

    
    def test_is_followed_by(self):
        pass
