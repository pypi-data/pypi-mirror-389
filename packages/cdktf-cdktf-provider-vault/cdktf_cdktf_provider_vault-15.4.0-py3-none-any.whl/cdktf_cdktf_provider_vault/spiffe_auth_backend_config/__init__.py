r'''
# `vault_spiffe_auth_backend_config`

Refer to the Terraform Registry for docs: [`vault_spiffe_auth_backend_config`](https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config).
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


class SpiffeAuthBackendConfig(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-vault.spiffeAuthBackendConfig.SpiffeAuthBackendConfig",
):
    '''Represents a {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config vault_spiffe_auth_backend_config}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        mount: builtins.str,
        profile: builtins.str,
        trust_domain: builtins.str,
        audience: typing.Optional[typing.Sequence[builtins.str]] = None,
        bundle: typing.Optional[builtins.str] = None,
        defer_bundle_fetch: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        endpoint_root_ca_truststore_pem: typing.Optional[builtins.str] = None,
        endpoint_spiffe_id: typing.Optional[builtins.str] = None,
        endpoint_url: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config vault_spiffe_auth_backend_config} Resource.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param mount: Mount path for the SPIFFE auth engine in Vault. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#mount SpiffeAuthBackendConfig#mount}
        :param profile: The mechanism to fetch or embed the trust bundle to use. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#profile SpiffeAuthBackendConfig#profile}
        :param trust_domain: The SPIFFE trust domain for this backend. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#trust_domain SpiffeAuthBackendConfig#trust_domain}
        :param audience: A list of audience values allowed to match claims in JWT-SVIDs. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#audience SpiffeAuthBackendConfig#audience}
        :param bundle: When profile is 'https_spiffe_bundle', the bootstrapping bundle in SPIFFE format; when profile is 'static', either a bundle in SPIFFE format or PEM-encoded CA certificate(s) Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#bundle SpiffeAuthBackendConfig#bundle}
        :param defer_bundle_fetch: Don't attempt to fetch a bundle immediately; only applies when profile != static. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#defer_bundle_fetch SpiffeAuthBackendConfig#defer_bundle_fetch}
        :param endpoint_root_ca_truststore_pem: PEM-encoded CA certificate(s) to validate the server reached by 'endpoint_url', if set this will override the default TLS trust store. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#endpoint_root_ca_truststore_pem SpiffeAuthBackendConfig#endpoint_root_ca_truststore_pem}
        :param endpoint_spiffe_id: The server's SPIFFE ID to validate when profile is 'https_spiffe_bundle'. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#endpoint_spiffe_id SpiffeAuthBackendConfig#endpoint_spiffe_id}
        :param endpoint_url: The URI to be used when profile is 'https_web_bundle' or 'https_spiffe_bundle'. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#endpoint_url SpiffeAuthBackendConfig#endpoint_url}
        :param namespace: Target namespace. (requires Enterprise). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#namespace SpiffeAuthBackendConfig#namespace}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bb7604b48c888526babea661ec2f87def7acd5366346de2d08bcf7922b5198f6)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = SpiffeAuthBackendConfigConfig(
            mount=mount,
            profile=profile,
            trust_domain=trust_domain,
            audience=audience,
            bundle=bundle,
            defer_bundle_fetch=defer_bundle_fetch,
            endpoint_root_ca_truststore_pem=endpoint_root_ca_truststore_pem,
            endpoint_spiffe_id=endpoint_spiffe_id,
            endpoint_url=endpoint_url,
            namespace=namespace,
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
        '''Generates CDKTF code for importing a SpiffeAuthBackendConfig resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the SpiffeAuthBackendConfig to import.
        :param import_from_id: The id of the existing SpiffeAuthBackendConfig that should be imported. Refer to the {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the SpiffeAuthBackendConfig to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7133543dff67199bdf58f1fc142774b9d7fc98642bbaa80bfbeff517253dc6df)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="resetAudience")
    def reset_audience(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAudience", []))

    @jsii.member(jsii_name="resetBundle")
    def reset_bundle(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetBundle", []))

    @jsii.member(jsii_name="resetDeferBundleFetch")
    def reset_defer_bundle_fetch(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDeferBundleFetch", []))

    @jsii.member(jsii_name="resetEndpointRootCaTruststorePem")
    def reset_endpoint_root_ca_truststore_pem(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEndpointRootCaTruststorePem", []))

    @jsii.member(jsii_name="resetEndpointSpiffeId")
    def reset_endpoint_spiffe_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEndpointSpiffeId", []))

    @jsii.member(jsii_name="resetEndpointUrl")
    def reset_endpoint_url(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEndpointUrl", []))

    @jsii.member(jsii_name="resetNamespace")
    def reset_namespace(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetNamespace", []))

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
    @jsii.member(jsii_name="audienceInput")
    def audience_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "audienceInput"))

    @builtins.property
    @jsii.member(jsii_name="bundleInput")
    def bundle_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "bundleInput"))

    @builtins.property
    @jsii.member(jsii_name="deferBundleFetchInput")
    def defer_bundle_fetch_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "deferBundleFetchInput"))

    @builtins.property
    @jsii.member(jsii_name="endpointRootCaTruststorePemInput")
    def endpoint_root_ca_truststore_pem_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "endpointRootCaTruststorePemInput"))

    @builtins.property
    @jsii.member(jsii_name="endpointSpiffeIdInput")
    def endpoint_spiffe_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "endpointSpiffeIdInput"))

    @builtins.property
    @jsii.member(jsii_name="endpointUrlInput")
    def endpoint_url_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "endpointUrlInput"))

    @builtins.property
    @jsii.member(jsii_name="mountInput")
    def mount_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "mountInput"))

    @builtins.property
    @jsii.member(jsii_name="namespaceInput")
    def namespace_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "namespaceInput"))

    @builtins.property
    @jsii.member(jsii_name="profileInput")
    def profile_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "profileInput"))

    @builtins.property
    @jsii.member(jsii_name="trustDomainInput")
    def trust_domain_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "trustDomainInput"))

    @builtins.property
    @jsii.member(jsii_name="audience")
    def audience(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "audience"))

    @audience.setter
    def audience(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b53e194cf4504571a43634d2bade499fe60d75ed7308f4940269f97e7a1ed65b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "audience", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="bundle")
    def bundle(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "bundle"))

    @bundle.setter
    def bundle(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__31a25f4d34d8e409911cd96c16bf708ad7b5567eafed3dd087b5cf4bdfe17433)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "bundle", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="deferBundleFetch")
    def defer_bundle_fetch(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "deferBundleFetch"))

    @defer_bundle_fetch.setter
    def defer_bundle_fetch(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bb54619afc5d2d8df0aca7aa875be76bd0b42349d52a120e699688f148fa71ac)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "deferBundleFetch", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="endpointRootCaTruststorePem")
    def endpoint_root_ca_truststore_pem(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "endpointRootCaTruststorePem"))

    @endpoint_root_ca_truststore_pem.setter
    def endpoint_root_ca_truststore_pem(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__62c3b71da341530addfd157918b95fbc1065a675565b080c69878759e1ab61ac)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "endpointRootCaTruststorePem", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="endpointSpiffeId")
    def endpoint_spiffe_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "endpointSpiffeId"))

    @endpoint_spiffe_id.setter
    def endpoint_spiffe_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8945044aa4be9eac884e75b7c75ef513eb0db2c75ba7ea79ed8c2f4e72bfc6d4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "endpointSpiffeId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="endpointUrl")
    def endpoint_url(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "endpointUrl"))

    @endpoint_url.setter
    def endpoint_url(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__42726e6691580eb7a721f91a2af298a38035a2f6f78f31c57b4d218455cb67c3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "endpointUrl", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="mount")
    def mount(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "mount"))

    @mount.setter
    def mount(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6743b811d712d127042d398a4327dbc5549f5949169919ab9bf98c2406940b57)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "mount", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="namespace")
    def namespace(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "namespace"))

    @namespace.setter
    def namespace(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9541b04ffc968d79fa4b2eedcff03291e6d4609a34e3ea11f475094dbc5603e8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "namespace", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="profile")
    def profile(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "profile"))

    @profile.setter
    def profile(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__826cb4fd255ba3ab7f26520c0fe5a4170beae9cabd0dec30077afba77758f150)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "profile", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="trustDomain")
    def trust_domain(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "trustDomain"))

    @trust_domain.setter
    def trust_domain(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7e41b966b0b5949a2c937626090996b25835361024be3b7c3804d75c8729321f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "trustDomain", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-vault.spiffeAuthBackendConfig.SpiffeAuthBackendConfigConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "mount": "mount",
        "profile": "profile",
        "trust_domain": "trustDomain",
        "audience": "audience",
        "bundle": "bundle",
        "defer_bundle_fetch": "deferBundleFetch",
        "endpoint_root_ca_truststore_pem": "endpointRootCaTruststorePem",
        "endpoint_spiffe_id": "endpointSpiffeId",
        "endpoint_url": "endpointUrl",
        "namespace": "namespace",
    },
)
class SpiffeAuthBackendConfigConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        mount: builtins.str,
        profile: builtins.str,
        trust_domain: builtins.str,
        audience: typing.Optional[typing.Sequence[builtins.str]] = None,
        bundle: typing.Optional[builtins.str] = None,
        defer_bundle_fetch: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        endpoint_root_ca_truststore_pem: typing.Optional[builtins.str] = None,
        endpoint_spiffe_id: typing.Optional[builtins.str] = None,
        endpoint_url: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param mount: Mount path for the SPIFFE auth engine in Vault. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#mount SpiffeAuthBackendConfig#mount}
        :param profile: The mechanism to fetch or embed the trust bundle to use. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#profile SpiffeAuthBackendConfig#profile}
        :param trust_domain: The SPIFFE trust domain for this backend. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#trust_domain SpiffeAuthBackendConfig#trust_domain}
        :param audience: A list of audience values allowed to match claims in JWT-SVIDs. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#audience SpiffeAuthBackendConfig#audience}
        :param bundle: When profile is 'https_spiffe_bundle', the bootstrapping bundle in SPIFFE format; when profile is 'static', either a bundle in SPIFFE format or PEM-encoded CA certificate(s) Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#bundle SpiffeAuthBackendConfig#bundle}
        :param defer_bundle_fetch: Don't attempt to fetch a bundle immediately; only applies when profile != static. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#defer_bundle_fetch SpiffeAuthBackendConfig#defer_bundle_fetch}
        :param endpoint_root_ca_truststore_pem: PEM-encoded CA certificate(s) to validate the server reached by 'endpoint_url', if set this will override the default TLS trust store. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#endpoint_root_ca_truststore_pem SpiffeAuthBackendConfig#endpoint_root_ca_truststore_pem}
        :param endpoint_spiffe_id: The server's SPIFFE ID to validate when profile is 'https_spiffe_bundle'. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#endpoint_spiffe_id SpiffeAuthBackendConfig#endpoint_spiffe_id}
        :param endpoint_url: The URI to be used when profile is 'https_web_bundle' or 'https_spiffe_bundle'. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#endpoint_url SpiffeAuthBackendConfig#endpoint_url}
        :param namespace: Target namespace. (requires Enterprise). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#namespace SpiffeAuthBackendConfig#namespace}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__951653c4a01d245456070e5edda3fca0c9ba795dc10489a3721601fc474271c5)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument mount", value=mount, expected_type=type_hints["mount"])
            check_type(argname="argument profile", value=profile, expected_type=type_hints["profile"])
            check_type(argname="argument trust_domain", value=trust_domain, expected_type=type_hints["trust_domain"])
            check_type(argname="argument audience", value=audience, expected_type=type_hints["audience"])
            check_type(argname="argument bundle", value=bundle, expected_type=type_hints["bundle"])
            check_type(argname="argument defer_bundle_fetch", value=defer_bundle_fetch, expected_type=type_hints["defer_bundle_fetch"])
            check_type(argname="argument endpoint_root_ca_truststore_pem", value=endpoint_root_ca_truststore_pem, expected_type=type_hints["endpoint_root_ca_truststore_pem"])
            check_type(argname="argument endpoint_spiffe_id", value=endpoint_spiffe_id, expected_type=type_hints["endpoint_spiffe_id"])
            check_type(argname="argument endpoint_url", value=endpoint_url, expected_type=type_hints["endpoint_url"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "mount": mount,
            "profile": profile,
            "trust_domain": trust_domain,
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
        if audience is not None:
            self._values["audience"] = audience
        if bundle is not None:
            self._values["bundle"] = bundle
        if defer_bundle_fetch is not None:
            self._values["defer_bundle_fetch"] = defer_bundle_fetch
        if endpoint_root_ca_truststore_pem is not None:
            self._values["endpoint_root_ca_truststore_pem"] = endpoint_root_ca_truststore_pem
        if endpoint_spiffe_id is not None:
            self._values["endpoint_spiffe_id"] = endpoint_spiffe_id
        if endpoint_url is not None:
            self._values["endpoint_url"] = endpoint_url
        if namespace is not None:
            self._values["namespace"] = namespace

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
    def mount(self) -> builtins.str:
        '''Mount path for the SPIFFE auth engine in Vault.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#mount SpiffeAuthBackendConfig#mount}
        '''
        result = self._values.get("mount")
        assert result is not None, "Required property 'mount' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def profile(self) -> builtins.str:
        '''The mechanism to fetch or embed the trust bundle to use.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#profile SpiffeAuthBackendConfig#profile}
        '''
        result = self._values.get("profile")
        assert result is not None, "Required property 'profile' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def trust_domain(self) -> builtins.str:
        '''The SPIFFE trust domain for this backend.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#trust_domain SpiffeAuthBackendConfig#trust_domain}
        '''
        result = self._values.get("trust_domain")
        assert result is not None, "Required property 'trust_domain' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def audience(self) -> typing.Optional[typing.List[builtins.str]]:
        '''A list of audience values allowed to match claims in JWT-SVIDs.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#audience SpiffeAuthBackendConfig#audience}
        '''
        result = self._values.get("audience")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def bundle(self) -> typing.Optional[builtins.str]:
        '''When profile is 'https_spiffe_bundle', the bootstrapping bundle in SPIFFE format;

        when profile is 'static', either a bundle in SPIFFE format or PEM-encoded CA certificate(s)

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#bundle SpiffeAuthBackendConfig#bundle}
        '''
        result = self._values.get("bundle")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def defer_bundle_fetch(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Don't attempt to fetch a bundle immediately; only applies when profile != static.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#defer_bundle_fetch SpiffeAuthBackendConfig#defer_bundle_fetch}
        '''
        result = self._values.get("defer_bundle_fetch")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def endpoint_root_ca_truststore_pem(self) -> typing.Optional[builtins.str]:
        '''PEM-encoded CA certificate(s) to validate the server reached by 'endpoint_url', if set this will override the default TLS trust store.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#endpoint_root_ca_truststore_pem SpiffeAuthBackendConfig#endpoint_root_ca_truststore_pem}
        '''
        result = self._values.get("endpoint_root_ca_truststore_pem")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def endpoint_spiffe_id(self) -> typing.Optional[builtins.str]:
        '''The server's SPIFFE ID to validate when profile is 'https_spiffe_bundle'.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#endpoint_spiffe_id SpiffeAuthBackendConfig#endpoint_spiffe_id}
        '''
        result = self._values.get("endpoint_spiffe_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def endpoint_url(self) -> typing.Optional[builtins.str]:
        '''The URI to be used when profile is 'https_web_bundle' or 'https_spiffe_bundle'.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#endpoint_url SpiffeAuthBackendConfig#endpoint_url}
        '''
        result = self._values.get("endpoint_url")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''Target namespace. (requires Enterprise).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/spiffe_auth_backend_config#namespace SpiffeAuthBackendConfig#namespace}
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SpiffeAuthBackendConfigConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "SpiffeAuthBackendConfig",
    "SpiffeAuthBackendConfigConfig",
]

publication.publish()

def _typecheckingstub__bb7604b48c888526babea661ec2f87def7acd5366346de2d08bcf7922b5198f6(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    mount: builtins.str,
    profile: builtins.str,
    trust_domain: builtins.str,
    audience: typing.Optional[typing.Sequence[builtins.str]] = None,
    bundle: typing.Optional[builtins.str] = None,
    defer_bundle_fetch: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    endpoint_root_ca_truststore_pem: typing.Optional[builtins.str] = None,
    endpoint_spiffe_id: typing.Optional[builtins.str] = None,
    endpoint_url: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__7133543dff67199bdf58f1fc142774b9d7fc98642bbaa80bfbeff517253dc6df(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b53e194cf4504571a43634d2bade499fe60d75ed7308f4940269f97e7a1ed65b(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__31a25f4d34d8e409911cd96c16bf708ad7b5567eafed3dd087b5cf4bdfe17433(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bb54619afc5d2d8df0aca7aa875be76bd0b42349d52a120e699688f148fa71ac(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__62c3b71da341530addfd157918b95fbc1065a675565b080c69878759e1ab61ac(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8945044aa4be9eac884e75b7c75ef513eb0db2c75ba7ea79ed8c2f4e72bfc6d4(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__42726e6691580eb7a721f91a2af298a38035a2f6f78f31c57b4d218455cb67c3(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6743b811d712d127042d398a4327dbc5549f5949169919ab9bf98c2406940b57(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9541b04ffc968d79fa4b2eedcff03291e6d4609a34e3ea11f475094dbc5603e8(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__826cb4fd255ba3ab7f26520c0fe5a4170beae9cabd0dec30077afba77758f150(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7e41b966b0b5949a2c937626090996b25835361024be3b7c3804d75c8729321f(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__951653c4a01d245456070e5edda3fca0c9ba795dc10489a3721601fc474271c5(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    mount: builtins.str,
    profile: builtins.str,
    trust_domain: builtins.str,
    audience: typing.Optional[typing.Sequence[builtins.str]] = None,
    bundle: typing.Optional[builtins.str] = None,
    defer_bundle_fetch: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    endpoint_root_ca_truststore_pem: typing.Optional[builtins.str] = None,
    endpoint_spiffe_id: typing.Optional[builtins.str] = None,
    endpoint_url: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
