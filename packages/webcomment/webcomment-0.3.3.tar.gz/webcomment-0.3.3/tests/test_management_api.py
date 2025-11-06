from saas_base.test import SaasTestCase


class TestCommentsAPI(SaasTestCase):
    user_id = SaasTestCase.OWNER_USER_ID
    base_url = "/api/comments/"

    def test_list_comments(self):
        self.force_login()
        resp = self.client.get(self.base_url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["count"], 3)

    def test_list_pending_comments(self):
        self.force_login()
        resp = self.client.get(self.base_url + "?status=pending")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["count"], 1)

    def test_list_approved_comments(self):
        self.force_login()
        resp = self.client.get(self.base_url + "?status=approved")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["count"], 2)

    def test_approve_comment(self):
        self.force_login()
        payload = {"status": "approved"}
        resp = self.client.patch(self.base_url + "2/", data=payload, format="json")
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(self.base_url + "?status=approved")
        data = resp.json()
        self.assertEqual(data["count"], 3)

    def test_set_invalid_comment_status(self):
        self.force_login()
        payload = {"status": "invalid"}
        resp = self.client.patch(self.base_url + "2/", data=payload, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_delete_comment(self):
        self.force_login()
        resp = self.client.delete(self.base_url + "2/")
        self.assertEqual(resp.status_code, 204)
        resp = self.client.get(self.base_url)
        data = resp.json()
        self.assertEqual(data["count"], 2)
