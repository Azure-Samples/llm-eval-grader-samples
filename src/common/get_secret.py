from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def get_key_vault_secret(key_vault_url, secret_name):
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
    return secret_client.get_secret(secret_name).value