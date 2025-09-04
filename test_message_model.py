import os
from unittest import TestCase

from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app
app.config['WTF_CSRF_ENABLED'] = False

db.create_all()

class MessageModelTestCase(TestCase):
    """Test the Message model."""

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

    def _create_test_users(self):
        '''Helper method to create and return two test users in the database.'''
        u1 = User(username='testuser1', email='test1@test.com', password='password123')
        db.session.add(u1)
        db.session.commit()
        return u1
    
    def test_message_model(self):
        ''' Makes sure basic model set up works for adding message to db.'''

        #adds user to db
        u1 = self._create_test_users()
        self.assertIsNotNone(u1)
        
        #creates/commits message for user 1
        m = Message(text='test message', user_id=u1.id)
        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(u1.messages), 1)
        self.assertEqual(u1.messages[0].text, 'test message')

    def test_user_realationship(self):
        
        #adds user to db
        u1 = self._create_test_users()
        self.assertIsNotNone(u1)

        # makes sure there are no messages before adding one
        self.assertEqual(len(u1.messages), 0)

        #creates/commits message for user 1
        m = Message(text='test message', user_id=u1.id)
        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(u1.messages), 1)
        self.assertIn('test message', u1.messages[0].text)

        # confirms message got added under user 1
        msg = Message.query.filter_by(id=m.id).first()
        self.assertEqual(msg.user.id, u1.id)
