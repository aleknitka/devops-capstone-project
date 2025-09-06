"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""

import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL, json=account.serialize(), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL, json=account.serialize(), content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...

    def test_get_account_list(self):
        """It should Get a list of Accounts"""
        self._create_accounts(5)
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 5)

    def test_get_account(self):
        """It should Read a single Account"""
        account = self._create_accounts(1)[0]
        resp = self.client.get(
            f"{BASE_URL}/{account.id}", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], account.name)

    def test_get_account_not_found(self):
        """It should not Read an Account that is not found"""
        resp = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_read_an_account(self):
        """It should read an account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL, json=account.serialize(), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_account = response.get_json()
        account_id = new_account["id"]
        response = self.client.get(f"{BASE_URL}/{account_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fetched_account = response.get_json()
        self.assertEqual(fetched_account["name"], account.name)
        self.assertEqual(fetched_account["email"], account.email)
        self.assertEqual(fetched_account["address"], account.address)
        self.assertEqual(fetched_account["phone_number"], account.phone_number)
        self.assertEqual(fetched_account["date_joined"], str(account.date_joined))
        self.assertEqual(fetched_account["id"], account_id)

    def test_update_an_account(self):
        """It should update an account"""
        # Create an account
        account_1 = AccountFactory()
        response_1 = self.client.post(
            BASE_URL,
            json=account_1.serialize(), 
            content_type="application/json"
        )
        self.assertEqual(
            response_1.status_code, 
            status.HTTP_201_CREATED)
        response_1_json = response_1.get_json()
        
        # Update an account
        account_2 = AccountFactory()
        response_2 = self.client.put(
            f"{BASE_URL}/{response_1_json['id']}",
            json=account_2.serialize(),
            content_type="application/json"
        )
        self.assertEqual(
            response_2.status_code,
            status.HTTP_200_OK)
        response_2_json = response_2.get_json()
        # ID should be as per response_1
        self.assertEqual(
            response_2_json['id'], response_1_json['id']
            )
        # NAME should be as per account 2
        self.assertEqual(
            response_2_json['name'],
            account_2.name
        )

    def test_update_nonexistings_account(self):
        """It shoudl fail to update an nonexisting account"""
        account = AccountFactory()
        response = self.client.put(
            f"{BASE_URL}/0",
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
            )

    def test_account_delete(self):
        """It should delete an account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL, json=account.serialize(), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_account = response.get_json()

        resp_delete = self.client.delete(
            f"{BASE_URL}/{new_account['id']}"
        )
        self.assertEqual(
            resp_delete.status_code, 
            status.HTTP_204_NO_CONTENT)

        resp = self.client.get(f"{BASE_URL}/{new_account['id']}")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_account_delete_not_existing(self):
        """It should fail to delete an account if it does not exist"""
        response = self.client.delete(
            f"{BASE_URL}/0"
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND)

    def test_method_not_allowed(self):
        """It should not allow an illegal method call"""
        resp = self.client.delete(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)