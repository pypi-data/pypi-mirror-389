from savcfg.read import ConfigService, VarsReader
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


class KeyVaultReader(VarsReader):
    """Implementation of keys readers using Azure KeyVault"""

    def __init__(
        self,
        kv_name: str,
        credential: DefaultAzureCredential,
        word_separator: str = "_",
    ):
        url = f"https://{kv_name}.vault.azure.net/"
        self._secrets = SecretClient(url, credential)
        self._vars = []
        self._sep = word_separator

    def list_vars(self) -> list[str]:
        if not self._vars:
            self._vars = sorted(
                [
                    key.name.replace("--", ".").replace("-", self._sep)
                    for key in self._secrets.list_properties_of_secrets()
                    if key is not None and key.name is not None
                ],
                key=lambda x: x,
            )

        return self._vars

    def read(self, key: str) -> str | None:
        if not self._vars:
            self.list_vars()

        if key not in self._vars:
            return

        return self._secrets.get_secret(
            key.replace(".", "--").replace(self._sep, "-")
        ).value


def new_keyvault_config_service(
    prod_kv: str, pre_kv: str, devel_kv: str | None = None
) -> ConfigService:
    credentials = DefaultAzureCredential()
    prod_reader = KeyVaultReader(prod_kv, credentials)
    pre_reader = KeyVaultReader(pre_kv, credentials)
    devel_reader = KeyVaultReader(devel_kv, credentials) if devel_kv else None

    return ConfigService(prod_reader, pre_reader, devel_reader)
