from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def get_key_vault_secret(key_vault_url, secret_name):
    """
    Retrieves a secret from Azure Key Vault.

    Args:
        key_vault_url (str): The URL of the Azure Key Vault.
        secret_name (str): The name of the secret to retrieve.

    Returns:
        str: The value of the secret.

    Raises:
        AzureError: If an error occurs while retrieving the secret.
    """
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
    return secret_client.get_secret(secret_name).value