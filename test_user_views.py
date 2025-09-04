import os
from unittest import TestCase

from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app
app.config['WTF_CSRF_ENABLED'] = False

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
        '''Ensure all data is deleted. Clean slate.'''
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        db.session.commit()

    def _sign_up_users_login(self, client):
        ''' Helper Method to create 2 users and sign in user 1 '''
        plain_password = 'password123'

        # signs up user 1
        signup_data1 = {'username': 'testuser1', 'password': plain_password, 'email': 'test@test.com', 'image_url': ''}
        signup1 = client.post('/signup', data=signup_data1, follow_redirects=False)
        self.assertEqual(signup1.status_code, 302)

        # signs up user 2
        signup_data2 = {'username': 'testuser2', 'password': plain_password, 'email': 'test2@test.com', 'image_url': ''}
        signup2 = client.post('/signup', data=signup_data2, follow_redirects=False)
        self.assertEqual(signup2.status_code, 302)

        # logs in user 1
        login_data = {'username': signup_data1['username'], 'password': plain_password}
        login = client.post('/login', data=login_data, follow_redirects=False)
        self.assertEqual(login.status_code, 302)

        # tests users exist in db by returning the user objects
        return User.query.filter_by(username=signup_data1['username']).first(), User.query.filter_by(username=signup_data2['username']).first()
    
    def _add_u_to_db(self):
        ''' Helper function to add a user directly to the database'''
        u = User(
            email="testing@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        return u
    
    def _add_msg_to_db(self, user_id):
        msg = Message(
            text='test message',
            user_id = user_id
        )

        db.session.add(msg)
        db.session.commit()

        return msg

    def test_list_users(self):
        ''' Confirms /users pagge shows all users no matter if a user is logged in or not.'''
        # adds user to db
        u = self._add_u_to_db()

        # shows list of all users while no user is logged in
        res = self.client.get('/users')
        html = res.get_data(as_text=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn('@testuser', html)

        # adds users to test when logged in
        u1, u2 = self._sign_up_users_login(self.client)
        self.assertIsNotNone(u1)
        self.assertIsNotNone(u2)

        #shows list of users while user is logged in
        res = self.client.get('/users')
        html = res.get_data(as_text=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn('@testuser1', html)

    def test_users_show(self):
        ''' Confirms /users/{user_id} shows specific user page no matter if a user is logged in or not.'''

        # adds user to db
        u = self._add_u_to_db()

        # shows list of all users while no user is logged in
        res = self.client.get(f'/users/{u.id}')
        html = res.get_data(as_text=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn('@testuser', html)

        u1, u2 = self._sign_up_users_login(self.client)

        #route to show specific users page
        res = self.client.get(f'/users/{u1.id}')
        html = res.get_data(as_text=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn('@testuser1', html)

    def test_show_following(self):
        ''' Confirms /users/{user_id}/following shows a list of users "user_id" follows. A user must be logged in'''

        # cannot access before log in
        u = self._add_u_to_db()

        res = self.client.get(f'/users/{u.id}/following', follow_redirects=True)
        html = res.get_data(as_text=True)

        self.assertIn('Access unauthorized.', html)

        # signs up users 1 and 2/ logs in user 1
        u1, u2 = self._sign_up_users_login(self.client)

        # makes sure user 1 follow list is empty
        self.assertEqual(len(u1.following), 0)

        # user 1 follows user 2
        follow = self.client.post(f'/users/follow/{u2.id}')

        # hits route to show user 1's following
        res = self.client.get(f'/users/{u1.id}/following')
        html = res.get_data(as_text=True)
        
        self.assertEqual(res.status_code, 200)
        self.assertIn('@testuser2', html)   

    def test_users_followers(self):
        ''' Confirms /users/{user_id}/followers shows a list of users that follow "user_id". A user must be logged in'''

        # cannot access before log in
        u = self._add_u_to_db()

        res = self.client.get(f'/users/{u.id}/followers', follow_redirects=True)
        html = res.get_data(as_text=True)

        self.assertIn('Access unauthorized.', html)

        # signs up users 1 and 2/ logs in user 1
        u1, u2 = self._sign_up_users_login(self.client)
        u2_id = u2.id

        # makes sure user 1 follow list is empty
        self.assertEqual(len(u1.following), 0)

        # user 1 follows user 2
        follow = self.client.post(f'/users/follow/{u2.id}')

        # hits route to show user 2's followers
        res = self.client.get(f'/users/{u2_id}/followers')
        html = res.get_data(as_text=True)
        
        self.assertEqual(res.status_code, 200)
        self.assertIn('@testuser1', html)   

    def test_stop_following(self):
        ''' Confirms when a user can unfollow another user. A user must be logged in'''

        # cannot access before log in
        u = self._add_u_to_db()

        res = self.client.post(f'/users/stop-following/{u.id}', follow_redirects=True)
        html = res.get_data(as_text=True)

        self.assertIn('Access unauthorized.', html)

        # signs up users 1 and 2/ logs in user 1
        u1, u2 = self._sign_up_users_login(self.client)
        u1_id = u1.id
        u2_id = u2.id

        # makes sure user 1 follow list is empty
        self.assertEqual(len(u1.following), 0)

        # user 1 follows user 2
        follow = self.client.post(f'/users/follow/{u2.id}')

        # re gets user 1
        u1 = User.query.filter_by(id=u1_id).first()

        # makes sure user 1 follows user 2
        self.assertEqual(len(u1.following), 1)

        # hits route to have user 1 unfollow user 2
        res = self.client.post(f'/users/stop-following/{u2_id}', follow_redirects=True)
        html = res.get_data(as_text=True)
        
        u1 = User.query.filter_by(id=u1_id).first()
        self.assertEqual(len(u1.following), 0)

        self.assertEqual(res.status_code, 200)
        self.assertIn('@testuser1', html)  

    def test_show_likes(self):
        ''' Confirms /users/{user_id}/likes shows a list of liked messages'''

        # cannot access before log in
        u = self._add_u_to_db()

        res = self.client.post(f'/users/{u.id}/likes', follow_redirects=True)
        html = res.get_data(as_text=True)

        self.assertIn('Access unauthorized.', html)

        # signs up users 1 and 2/ logs in user 1
        u1, u2 = self._sign_up_users_login(self.client)
        u1_id = u1.id
        u2_id = u2.id

        # directly adds message to db
        msg = self._add_msg_to_db(u2_id)

        self.assertEqual(msg.user_id, u2_id)

        # has user 1 like user 2 message. tests message_like route
        like = self.client.post(f'/users/add_like/{msg.id}', follow_redirects=True)

        # hits route to show user 1 liked messages
        res = self.client.post(f'/users/{u1_id}/likes')
        html = res.get_data(as_text=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn('@testuser2', html)
        self.assertIn('test message', html)

    def test_message_like(self):
        ''' Adding a new like has already been tested in test_show_likes. Confirms /users/add_like/{message_id} does not let logged in user like own post. A user must be logged in'''

        # cannot access before log in
        u = self._add_u_to_db()
        msg = self._add_msg_to_db(u.id)

        res = self.client.post(f'/users/add_like/{msg.id}', follow_redirects=True)
        html = res.get_data(as_text=True)

        self.assertIn('Access unauthorized.', html)

        # signs up users 1 and 2/ logs in user 1
        u1, u2 = self._sign_up_users_login(self.client)

        # directly adds message to db
        msg = self._add_msg_to_db(u1.id)

        # has user 1 like user 1 message
        res = self.client.post(f'/users/add_like/{msg.id}', follow_redirects=True)
        html = res.get_data(as_text=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn('You cannot like your own post', html)

    def test_message_remove_like(self):
        ''' Confirms /users/remove_like/{message_id} removes a like on a message. A user must be logged in'''

        # cannot access before log in
        u = self._add_u_to_db()
        msg = self._add_msg_to_db(u.id)

        res = self.client.post(f'/users/remove_like/{msg.id}', follow_redirects=True)
        html = res.get_data(as_text=True)

        self.assertIn('Access unauthorized.', html)

        # signs up users 1 and 2/ logs in user 1
        u1, u2 = self._sign_up_users_login(self.client)
        u1_id = u1.id
        u2_id = u2.id

        # directly adds message to db
        msg = self._add_msg_to_db(u2_id)
        msg_id = msg.id

        # has user 1 like user 2 message
        like = self.client.post(f'/users/add_like/{msg.id}', follow_redirects=True)

        # re gets user 1
        u1 = User.query.filter_by(id=u1_id).first()

        # makes sure message got added
        self.assertEqual(len(u1.likes), 1) 

        # hits route for user 1 to unlike user 2 message
        res = self.client.post(f'/users/remove_like/{msg_id}', follow_redirects=True)
        html = res.get_data(as_text=True)

        self.assertEqual(res.status_code, 200)
        self.assertNotIn('@testuser2', html)
        self.assertNotIn('test message', html)

    def test_profile(self):
        ''' Confirms /users/profile shows update form on get request and uopdates profile on post request. A user must be logged in'''

        # cannot access before log in
        u = self._add_u_to_db()

        res = self.client.post(f'/users/profile', follow_redirects=True)
        html = res.get_data(as_text=True)

        self.assertIn('Access unauthorized.', html)

        # signs up users 1 and 2/ logs in user 1
        u1, u2 = self._sign_up_users_login(self.client)

        # makes sure form is shown on get request
        show_form = self.client.get('/users/profile')
        html = show_form.get_data(as_text=True)

        self.assertEqual(show_form.status_code, 200)
        self.assertIn('Edit Your Profile.', html)

        data = {
            'username':'newusername',
            'email':'newemail@test.com',
            'password':'password123'
        }
        # hits route to update user profile
        res = self.client.post('/users/profile', data=data, follow_redirects=True)
        html = res.get_data(as_text=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn('newusername', html)

    def test_delete_user(self):
        ''' Confirms /users/delete deletes a user. A user must be logged in.'''

        # cannot access before log in
        u = self._add_u_to_db()

        res = self.client.post(f'/users/delete', follow_redirects=True)
        html = res.get_data(as_text=True)

        self.assertIn('Access unauthorized.', html)

        # signs up users 1 and 2/ logs in user 1
        u1, u2 = self._sign_up_users_login(self.client)

        # hits route to delete user 1
        res = self.client.post('/users/delete', follow_redirects=True)
        html = res.get_data(as_text=True)
        
        # attempts to get user 1
        user = User.query.filter_by(username='testuser1').first()
        self.assertIsNone(user)

        self.assertEqual(res.status_code, 200)
        self.assertIn('Join Warbler today.', html)

