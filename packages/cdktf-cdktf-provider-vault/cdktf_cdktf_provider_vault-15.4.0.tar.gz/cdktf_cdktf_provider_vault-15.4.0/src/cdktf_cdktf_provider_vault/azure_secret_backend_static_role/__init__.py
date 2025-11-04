r'''
# `vault_azure_secret_backend_static_role`

Refer to the Terraform Registry for docs: [`vault_azure_secret_backend_static_role`](https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role).
'''
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from .._jsii import *

import cdktf as _cdktf_9a9027ec
import constructs as _constructs_77d1e7e8


class AzureSecretBackendStaticRole(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-vault.azureSecretBackendStaticRole.AzureSecretBackendStaticRole",
):
    '''Represents a {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role vault_azure_secret_backend_static_role}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        application_object_id: builtins.str,
        backend: builtins.str,
        role: builtins.str,
        client_secret: typing.Optional[builtins.str] = None,
        expiration: typing.Optional[builtins.str] = None,
        metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        namespace: typing.Optional[builtins.str] = None,
        secret_id: typing.Optional[builtins.str] = None,
        skip_import_rotation: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        ttl: typing.Optional[jsii.Number] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role vault_azure_secret_backend_static_role} Resource.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param application_object_id: Application object ID for an existing service principal that is managed by the static role. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#application_object_id AzureSecretBackendStaticRole#application_object_id}
        :param backend: The path where the Azure secrets backend is mounted. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#backend AzureSecretBackendStaticRole#backend}
        :param role: Name of the static role to create. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#role AzureSecretBackendStaticRole#role}
        :param client_secret: The plaintext secret value of the credential you want to import. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#client_secret AzureSecretBackendStaticRole#client_secret}
        :param expiration: A future expiration time for the imported credential, in RFC3339 format. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#expiration AzureSecretBackendStaticRole#expiration}
        :param metadata: A map of string key/value pairs that will be stored as metadata on the secret. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#metadata AzureSecretBackendStaticRole#metadata}
        :param namespace: Target namespace. (requires Enterprise). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#namespace AzureSecretBackendStaticRole#namespace}
        :param secret_id: The secret ID of the Azure password credential you want to import. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#secret_id AzureSecretBackendStaticRole#secret_id}
        :param skip_import_rotation: If true, skip rotation of the client secret on import. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#skip_import_rotation AzureSecretBackendStaticRole#skip_import_rotation}
        :param ttl: Timespan of 1 year (31536000) or more during which the role credentials are valid. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#ttl AzureSecretBackendStaticRole#ttl}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b64629b42c9015a57ecb3eec3f7062a4e09c058deaa4ca7e92f49dd6474bdd9a)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = AzureSecretBackendStaticRoleConfig(
            application_object_id=application_object_id,
            backend=backend,
            role=role,
            client_secret=client_secret,
            expiration=expiration,
            metadata=metadata,
            namespace=namespace,
            secret_id=secret_id,
            skip_import_rotation=skip_import_rotation,
            ttl=ttl,
            connection=connection,
            count=count,
            depends_on=depends_on,
            for_each=for_each,
            lifecycle=lifecycle,
            provider=provider,
            provisioners=provisioners,
        )

        jsii.create(self.__class__, self, [scope, id, config])

    @jsii.member(jsii_name="generateConfigForImport")
    @builtins.classmethod
    def generate_config_for_import(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        import_to_id: builtins.str,
        import_from_id: builtins.str,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    ) -> _cdktf_9a9027ec.ImportableResource:
        '''Generates CDKTF code for importing a AzureSecretBackendStaticRole resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the AzureSecretBackendStaticRole to import.
        :param import_from_id: The id of the existing AzureSecretBackendStaticRole that should be imported. Refer to the {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the AzureSecretBackendStaticRole to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eda168bbdbc9308460a63f94985cdbe42f4e1abf95715ca8053d10807f882fc4)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="resetClientSecret")
    def reset_client_secret(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetClientSecret", []))

    @jsii.member(jsii_name="resetExpiration")
    def reset_expiration(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetExpiration", []))

    @jsii.member(jsii_name="resetMetadata")
    def reset_metadata(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMetadata", []))

    @jsii.member(jsii_name="resetNamespace")
    def reset_namespace(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetNamespace", []))

    @jsii.member(jsii_name="resetSecretId")
    def reset_secret_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSecretId", []))

    @jsii.member(jsii_name="resetSkipImportRotation")
    def reset_skip_import_rotation(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSkipImportRotation", []))

    @jsii.member(jsii_name="resetTtl")
    def reset_ttl(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTtl", []))

    @jsii.member(jsii_name="synthesizeAttributes")
    def _synthesize_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeAttributes", []))

    @jsii.member(jsii_name="synthesizeHclAttributes")
    def _synthesize_hcl_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeHclAttributes", []))

    @jsii.python.classproperty
    @jsii.member(jsii_name="tfResourceType")
    def TF_RESOURCE_TYPE(cls) -> builtins.str:
        return typing.cast(builtins.str, jsii.sget(cls, "tfResourceType"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @builtins.property
    @jsii.member(jsii_name="applicationObjectIdInput")
    def application_object_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "applicationObjectIdInput"))

    @builtins.property
    @jsii.member(jsii_name="backendInput")
    def backend_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "backendInput"))

    @builtins.property
    @jsii.member(jsii_name="clientSecretInput")
    def client_secret_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clientSecretInput"))

    @builtins.property
    @jsii.member(jsii_name="expirationInput")
    def expiration_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "expirationInput"))

    @builtins.property
    @jsii.member(jsii_name="metadataInput")
    def metadata_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "metadataInput"))

    @builtins.property
    @jsii.member(jsii_name="namespaceInput")
    def namespace_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "namespaceInput"))

    @builtins.property
    @jsii.member(jsii_name="roleInput")
    def role_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "roleInput"))

    @builtins.property
    @jsii.member(jsii_name="secretIdInput")
    def secret_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "secretIdInput"))

    @builtins.property
    @jsii.member(jsii_name="skipImportRotationInput")
    def skip_import_rotation_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "skipImportRotationInput"))

    @builtins.property
    @jsii.member(jsii_name="ttlInput")
    def ttl_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "ttlInput"))

    @builtins.property
    @jsii.member(jsii_name="applicationObjectId")
    def application_object_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "applicationObjectId"))

    @application_object_id.setter
    def application_object_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d7d23048dc49d5fb093551d0425ce12cd1fdd41825dc53ee41ca544ba5834d90)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "applicationObjectId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="backend")
    def backend(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "backend"))

    @backend.setter
    def backend(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__37cbf1b199f59a54f1dff339b59557782686e5fd85bed04ef54af937c47813f6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "backend", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="clientSecret")
    def client_secret(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "clientSecret"))

    @client_secret.setter
    def client_secret(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__66b14d76d47172e35533d5debfae29d4e55aadb1ea781368025cdfc01aa740f2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "clientSecret", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="expiration")
    def expiration(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "expiration"))

    @expiration.setter
    def expiration(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__797d2b964df04b6fd81b4efdcfc9f6d9351c761bbed1a7c157af87e27995fb12)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "expiration", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="metadata")
    def metadata(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "metadata"))

    @metadata.setter
    def metadata(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cd54aedbe42f787ca645f789bfdb05354840df1f9a5d62a6d62b9075026d0fe7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "metadata", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="namespace")
    def namespace(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "namespace"))

    @namespace.setter
    def namespace(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ca5775dd2ad628382ee9cd5d91352a0646404ceff8b3dc21e4aa6b12826660e8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "namespace", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="role")
    def role(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "role"))

    @role.setter
    def role(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ee5cd79737441ed54915a3ee89e01f0d76c522798bc23e0f3aacca48dae0ba60)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "role", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="secretId")
    def secret_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "secretId"))

    @secret_id.setter
    def secret_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__01ea5899f6c81fa0350b3ee05e0845af8cdccf11676f4da4fee7b54d7b535763)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "secretId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="skipImportRotation")
    def skip_import_rotation(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "skipImportRotation"))

    @skip_import_rotation.setter
    def skip_import_rotation(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c11be5c5bed3a44ae86b48bf4bd5e1d30fcd3cd4567939c36d4ed08f12047960)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "skipImportRotation", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="ttl")
    def ttl(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "ttl"))

    @ttl.setter
    def ttl(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fd425df3d0fad96b65d9f2f7454247236395e199a484dc29e60cb0ed883428d6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "ttl", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-vault.azureSecretBackendStaticRole.AzureSecretBackendStaticRoleConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "application_object_id": "applicationObjectId",
        "backend": "backend",
        "role": "role",
        "client_secret": "clientSecret",
        "expiration": "expiration",
        "metadata": "metadata",
        "namespace": "namespace",
        "secret_id": "secretId",
        "skip_import_rotation": "skipImportRotation",
        "ttl": "ttl",
    },
)
class AzureSecretBackendStaticRoleConfig(_cdktf_9a9027ec.TerraformMetaArguments):
    def __init__(
        self,
        *,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
        application_object_id: builtins.str,
        backend: builtins.str,
        role: builtins.str,
        client_secret: typing.Optional[builtins.str] = None,
        expiration: typing.Optional[builtins.str] = None,
        metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        namespace: typing.Optional[builtins.str] = None,
        secret_id: typing.Optional[builtins.str] = None,
        skip_import_rotation: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        ttl: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param application_object_id: Application object ID for an existing service principal that is managed by the static role. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#application_object_id AzureSecretBackendStaticRole#application_object_id}
        :param backend: The path where the Azure secrets backend is mounted. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#backend AzureSecretBackendStaticRole#backend}
        :param role: Name of the static role to create. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#role AzureSecretBackendStaticRole#role}
        :param client_secret: The plaintext secret value of the credential you want to import. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#client_secret AzureSecretBackendStaticRole#client_secret}
        :param expiration: A future expiration time for the imported credential, in RFC3339 format. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#expiration AzureSecretBackendStaticRole#expiration}
        :param metadata: A map of string key/value pairs that will be stored as metadata on the secret. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#metadata AzureSecretBackendStaticRole#metadata}
        :param namespace: Target namespace. (requires Enterprise). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#namespace AzureSecretBackendStaticRole#namespace}
        :param secret_id: The secret ID of the Azure password credential you want to import. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#secret_id AzureSecretBackendStaticRole#secret_id}
        :param skip_import_rotation: If true, skip rotation of the client secret on import. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#skip_import_rotation AzureSecretBackendStaticRole#skip_import_rotation}
        :param ttl: Timespan of 1 year (31536000) or more during which the role credentials are valid. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#ttl AzureSecretBackendStaticRole#ttl}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9be41f5d62a8a25cfaff738c53e3e07369ac63bb6d7867886b950f79b968ef0f)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument application_object_id", value=application_object_id, expected_type=type_hints["application_object_id"])
            check_type(argname="argument backend", value=backend, expected_type=type_hints["backend"])
            check_type(argname="argument role", value=role, expected_type=type_hints["role"])
            check_type(argname="argument client_secret", value=client_secret, expected_type=type_hints["client_secret"])
            check_type(argname="argument expiration", value=expiration, expected_type=type_hints["expiration"])
            check_type(argname="argument metadata", value=metadata, expected_type=type_hints["metadata"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument secret_id", value=secret_id, expected_type=type_hints["secret_id"])
            check_type(argname="argument skip_import_rotation", value=skip_import_rotation, expected_type=type_hints["skip_import_rotation"])
            check_type(argname="argument ttl", value=ttl, expected_type=type_hints["ttl"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "application_object_id": application_object_id,
            "backend": backend,
            "role": role,
        }
        if connection is not None:
            self._values["connection"] = connection
        if count is not None:
            self._values["count"] = count
        if depends_on is not None:
            self._values["depends_on"] = depends_on
        if for_each is not None:
            self._values["for_each"] = for_each
        if lifecycle is not None:
            self._values["lifecycle"] = lifecycle
        if provider is not None:
            self._values["provider"] = provider
        if provisioners is not None:
            self._values["provisioners"] = provisioners
        if client_secret is not None:
            self._values["client_secret"] = client_secret
        if expiration is not None:
            self._values["expiration"] = expiration
        if metadata is not None:
            self._values["metadata"] = metadata
        if namespace is not None:
            self._values["namespace"] = namespace
        if secret_id is not None:
            self._values["secret_id"] = secret_id
        if skip_import_rotation is not None:
            self._values["skip_import_rotation"] = skip_import_rotation
        if ttl is not None:
            self._values["ttl"] = ttl

    @builtins.property
    def connection(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, _cdktf_9a9027ec.WinrmProvisionerConnection]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("connection")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, _cdktf_9a9027ec.WinrmProvisionerConnection]], result)

    @builtins.property
    def count(
        self,
    ) -> typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("count")
        return typing.cast(typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]], result)

    @builtins.property
    def depends_on(
        self,
    ) -> typing.Optional[typing.List[_cdktf_9a9027ec.ITerraformDependable]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("depends_on")
        return typing.cast(typing.Optional[typing.List[_cdktf_9a9027ec.ITerraformDependable]], result)

    @builtins.property
    def for_each(self) -> typing.Optional[_cdktf_9a9027ec.ITerraformIterator]:
        '''
        :stability: experimental
        '''
        result = self._values.get("for_each")
        return typing.cast(typing.Optional[_cdktf_9a9027ec.ITerraformIterator], result)

    @builtins.property
    def lifecycle(self) -> typing.Optional[_cdktf_9a9027ec.TerraformResourceLifecycle]:
        '''
        :stability: experimental
        '''
        result = self._values.get("lifecycle")
        return typing.cast(typing.Optional[_cdktf_9a9027ec.TerraformResourceLifecycle], result)

    @builtins.property
    def provider(self) -> typing.Optional[_cdktf_9a9027ec.TerraformProvider]:
        '''
        :stability: experimental
        '''
        result = self._values.get("provider")
        return typing.cast(typing.Optional[_cdktf_9a9027ec.TerraformProvider], result)

    @builtins.property
    def provisioners(
        self,
    ) -> typing.Optional[typing.List[typing.Union[_cdktf_9a9027ec.FileProvisioner, _cdktf_9a9027ec.LocalExecProvisioner, _cdktf_9a9027ec.RemoteExecProvisioner]]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("provisioners")
        return typing.cast(typing.Optional[typing.List[typing.Union[_cdktf_9a9027ec.FileProvisioner, _cdktf_9a9027ec.LocalExecProvisioner, _cdktf_9a9027ec.RemoteExecProvisioner]]], result)

    @builtins.property
    def application_object_id(self) -> builtins.str:
        '''Application object ID for an existing service principal that is managed by the static role.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#application_object_id AzureSecretBackendStaticRole#application_object_id}
        '''
        result = self._values.get("application_object_id")
        assert result is not None, "Required property 'application_object_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def backend(self) -> builtins.str:
        '''The path where the Azure secrets backend is mounted.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#backend AzureSecretBackendStaticRole#backend}
        '''
        result = self._values.get("backend")
        assert result is not None, "Required property 'backend' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def role(self) -> builtins.str:
        '''Name of the static role to create.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#role AzureSecretBackendStaticRole#role}
        '''
        result = self._values.get("role")
        assert result is not None, "Required property 'role' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def client_secret(self) -> typing.Optional[builtins.str]:
        '''The plaintext secret value of the credential you want to import.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#client_secret AzureSecretBackendStaticRole#client_secret}
        '''
        result = self._values.get("client_secret")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def expiration(self) -> typing.Optional[builtins.str]:
        '''A future expiration time for the imported credential, in RFC3339 format.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#expiration AzureSecretBackendStaticRole#expiration}
        '''
        result = self._values.get("expiration")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def metadata(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''A map of string key/value pairs that will be stored as metadata on the secret.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#metadata AzureSecretBackendStaticRole#metadata}
        '''
        result = self._values.get("metadata")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''Target namespace. (requires Enterprise).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#namespace AzureSecretBackendStaticRole#namespace}
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def secret_id(self) -> typing.Optional[builtins.str]:
        '''The secret ID of the Azure password credential you want to import.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#secret_id AzureSecretBackendStaticRole#secret_id}
        '''
        result = self._values.get("secret_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def skip_import_rotation(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''If true, skip rotation of the client secret on import.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#skip_import_rotation AzureSecretBackendStaticRole#skip_import_rotation}
        '''
        result = self._values.get("skip_import_rotation")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def ttl(self) -> typing.Optional[jsii.Number]:
        '''Timespan of 1 year (31536000) or more during which the role credentials are valid.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/azure_secret_backend_static_role#ttl AzureSecretBackendStaticRole#ttl}
        '''
        result = self._values.get("ttl")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AzureSecretBackendStaticRoleConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "AzureSecretBackendStaticRole",
    "AzureSecretBackendStaticRoleConfig",
]

publication.publish()

def _typecheckingstub__b64629b42c9015a57ecb3eec3f7062a4e09c058deaa4ca7e92f49dd6474bdd9a(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    application_object_id: builtins.str,
    backend: builtins.str,
    role: builtins.str,
    client_secret: typing.Optional[builtins.str] = None,
    expiration: typing.Optional[builtins.str] = None,
    metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    namespace: typing.Optional[builtins.str] = None,
    secret_id: typing.Optional[builtins.str] = None,
    skip_import_rotation: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ttl: typing.Optional[jsii.Number] = None,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eda168bbdbc9308460a63f94985cdbe42f4e1abf95715ca8053d10807f882fc4(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d7d23048dc49d5fb093551d0425ce12cd1fdd41825dc53ee41ca544ba5834d90(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__37cbf1b199f59a54f1dff339b59557782686e5fd85bed04ef54af937c47813f6(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__66b14d76d47172e35533d5debfae29d4e55aadb1ea781368025cdfc01aa740f2(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__797d2b964df04b6fd81b4efdcfc9f6d9351c761bbed1a7c157af87e27995fb12(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cd54aedbe42f787ca645f789bfdb05354840df1f9a5d62a6d62b9075026d0fe7(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ca5775dd2ad628382ee9cd5d91352a0646404ceff8b3dc21e4aa6b12826660e8(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ee5cd79737441ed54915a3ee89e01f0d76c522798bc23e0f3aacca48dae0ba60(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__01ea5899f6c81fa0350b3ee05e0845af8cdccf11676f4da4fee7b54d7b535763(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c11be5c5bed3a44ae86b48bf4bd5e1d30fcd3cd4567939c36d4ed08f12047960(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fd425df3d0fad96b65d9f2f7454247236395e199a484dc29e60cb0ed883428d6(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9be41f5d62a8a25cfaff738c53e3e07369ac63bb6d7867886b950f79b968ef0f(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    application_object_id: builtins.str,
    backend: builtins.str,
    role: builtins.str,
    client_secret: typing.Optional[builtins.str] = None,
    expiration: typing.Optional[builtins.str] = None,
    metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    namespace: typing.Optional[builtins.str] = None,
    secret_id: typing.Optional[builtins.str] = None,
    skip_import_rotation: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ttl: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass
