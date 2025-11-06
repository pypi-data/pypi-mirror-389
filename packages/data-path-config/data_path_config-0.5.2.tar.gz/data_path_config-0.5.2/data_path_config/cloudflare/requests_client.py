import requests

class CloudflareRequestsClient:
    def __init__(self, token):
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.account_id = None

    def validate_token(self):
        response = requests.get(f"{self.base_url}/user/tokens/verify", headers=self.headers)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.text

    def get_token_status(self):
        return self.validate_token()

    def get_id(self):
        success, data = self.validate_token()
        if success:
            return data['result']['id']
        else:
            return None

    def get_account_id_name(self):
        response = requests.get(f"{self.base_url}/accounts", headers=self.headers)
        if response.status_code == 200:
            accounts = response.json()['result']
            if accounts:
                self.account_id = accounts[0]['id']
                name = accounts[0]['name']
                return self.account_id, name
            else:
                return None, None
        else:
            return None, None

    def get_buckets(self):
        if not self.account_id:
            self.get_account_id_name()
        if self.account_id:
            response = requests.get(f"{self.base_url}/accounts/{self.account_id}/r2/buckets", headers=self.headers)
            if response.status_code == 200:
                buckets = response.json()['result']['buckets']
                return buckets
            else:
                return None
        else:
            return None

    def upload_file(self, bucket_name, key, content):
        if not self.account_id:
            self.get_account_id_name()
        if self.account_id:
            url = f"https://{self.account_id}.r2.cloudflarestorage.com/{bucket_name}/{key}"
            response = requests.put(url, data=content, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return True
            else:
                return False
        else:
            return False

    def delete_file(self, bucket_name, key):
        if not self.account_id:
            self.get_account_id_name()
        if self.account_id:
            url = f"https://{self.account_id}.r2.cloudflarestorage.com/{bucket_name}/{key}"
            response = requests.delete(url, headers=self.headers, timeout=10)
            if response.status_code == 204:
                return True
            else:
                return False
        else:
            return False