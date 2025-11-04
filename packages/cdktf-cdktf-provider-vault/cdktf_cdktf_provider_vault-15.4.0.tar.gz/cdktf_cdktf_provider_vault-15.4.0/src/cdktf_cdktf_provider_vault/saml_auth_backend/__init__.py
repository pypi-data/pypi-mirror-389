r'''
# `vault_saml_auth_backend`

Refer to the Terraform Registry for docs: [`vault_saml_auth_backend`](https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend).
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


class SamlAuthBackend(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-vault.samlAuthBackend.SamlAuthBackend",
):
    '''Represents a {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend vault_saml_auth_backend}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id_: builtins.str,
        *,
        acs_urls: typing.Sequence[builtins.str],
        entity_id: builtins.str,
        default_role: typing.Optional[builtins.str] = None,
        disable_remount: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        id: typing.Optional[builtins.str] = None,
        idp_cert: typing.Optional[builtins.str] = None,
        idp_entity_id: typing.Optional[builtins.str] = None,
        idp_metadata_url: typing.Optional[builtins.str] = None,
        idp_sso_url: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        path: typing.Optional[builtins.str] = None,
        tune: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["SamlAuthBackendTune", typing.Dict[builtins.str, typing.Any]]]]] = None,
        verbose_logging: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend vault_saml_auth_backend} Resource.

        :param scope: The scope in which to define this construct.
        :param id_: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param acs_urls: The well-formatted URLs of your Assertion Consumer Service (ACS) that should receive a response from the identity provider. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#acs_urls SamlAuthBackend#acs_urls}
        :param entity_id: The entity ID of the SAML authentication service provider. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#entity_id SamlAuthBackend#entity_id}
        :param default_role: The role to use if no role is provided during login. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#default_role SamlAuthBackend#default_role}
        :param disable_remount: If set, opts out of mount migration on path updates. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#disable_remount SamlAuthBackend#disable_remount}
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#id SamlAuthBackend#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param idp_cert: The PEM encoded certificate of the identity provider. Mutually exclusive with 'idp_metadata_url'. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#idp_cert SamlAuthBackend#idp_cert}
        :param idp_entity_id: The entity ID of the identity provider. Mutually exclusive with 'idp_metadata_url'. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#idp_entity_id SamlAuthBackend#idp_entity_id}
        :param idp_metadata_url: The metadata URL of the identity provider. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#idp_metadata_url SamlAuthBackend#idp_metadata_url}
        :param idp_sso_url: The SSO URL of the identity provider. Mutually exclusive with 'idp_metadata_url'. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#idp_sso_url SamlAuthBackend#idp_sso_url}
        :param namespace: Target namespace. (requires Enterprise). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#namespace SamlAuthBackend#namespace}
        :param path: Unique name of the auth backend to configure. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#path SamlAuthBackend#path}
        :param tune: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#tune SamlAuthBackend#tune}.
        :param verbose_logging: Log additional, potentially sensitive information during the SAML exchange according to the current logging level. Not recommended for production. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#verbose_logging SamlAuthBackend#verbose_logging}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__98f5f695d041c96a8252823e5139618ae5634a72faca05ced31c640e7c89137a)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id_", value=id_, expected_type=type_hints["id_"])
        config = SamlAuthBackendConfig(
            acs_urls=acs_urls,
            entity_id=entity_id,
            default_role=default_role,
            disable_remount=disable_remount,
            id=id,
            idp_cert=idp_cert,
            idp_entity_id=idp_entity_id,
            idp_metadata_url=idp_metadata_url,
            idp_sso_url=idp_sso_url,
            namespace=namespace,
            path=path,
            tune=tune,
            verbose_logging=verbose_logging,
            connection=connection,
            count=count,
            depends_on=depends_on,
            for_each=for_each,
            lifecycle=lifecycle,
            provider=provider,
            provisioners=provisioners,
        )

        jsii.create(self.__class__, self, [scope, id_, config])

    @jsii.member(jsii_name="generateConfigForImport")
    @builtins.classmethod
    def generate_config_for_import(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        import_to_id: builtins.str,
        import_from_id: builtins.str,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    ) -> _cdktf_9a9027ec.ImportableResource:
        '''Generates CDKTF code for importing a SamlAuthBackend resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the SamlAuthBackend to import.
        :param import_from_id: The id of the existing SamlAuthBackend that should be imported. Refer to the {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the SamlAuthBackend to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2a3c747d37a43926bde48cff573996c8cd1470f6e23c92fde74ae6d95cdde817)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putTune")
    def put_tune(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["SamlAuthBackendTune", typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__95d47451b14589cdec27d4c2af01199809eae692192b49b29e47f6f6c1fef909)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putTune", [value]))

    @jsii.member(jsii_name="resetDefaultRole")
    def reset_default_role(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDefaultRole", []))

    @jsii.member(jsii_name="resetDisableRemount")
    def reset_disable_remount(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDisableRemount", []))

    @jsii.member(jsii_name="resetId")
    def reset_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetId", []))

    @jsii.member(jsii_name="resetIdpCert")
    def reset_idp_cert(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIdpCert", []))

    @jsii.member(jsii_name="resetIdpEntityId")
    def reset_idp_entity_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIdpEntityId", []))

    @jsii.member(jsii_name="resetIdpMetadataUrl")
    def reset_idp_metadata_url(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIdpMetadataUrl", []))

    @jsii.member(jsii_name="resetIdpSsoUrl")
    def reset_idp_sso_url(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIdpSsoUrl", []))

    @jsii.member(jsii_name="resetNamespace")
    def reset_namespace(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetNamespace", []))

    @jsii.member(jsii_name="resetPath")
    def reset_path(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPath", []))

    @jsii.member(jsii_name="resetTune")
    def reset_tune(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTune", []))

    @jsii.member(jsii_name="resetVerboseLogging")
    def reset_verbose_logging(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetVerboseLogging", []))

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
    @jsii.member(jsii_name="tune")
    def tune(self) -> "SamlAuthBackendTuneList":
        return typing.cast("SamlAuthBackendTuneList", jsii.get(self, "tune"))

    @builtins.property
    @jsii.member(jsii_name="acsUrlsInput")
    def acs_urls_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "acsUrlsInput"))

    @builtins.property
    @jsii.member(jsii_name="defaultRoleInput")
    def default_role_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "defaultRoleInput"))

    @builtins.property
    @jsii.member(jsii_name="disableRemountInput")
    def disable_remount_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "disableRemountInput"))

    @builtins.property
    @jsii.member(jsii_name="entityIdInput")
    def entity_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "entityIdInput"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="idpCertInput")
    def idp_cert_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idpCertInput"))

    @builtins.property
    @jsii.member(jsii_name="idpEntityIdInput")
    def idp_entity_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idpEntityIdInput"))

    @builtins.property
    @jsii.member(jsii_name="idpMetadataUrlInput")
    def idp_metadata_url_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idpMetadataUrlInput"))

    @builtins.property
    @jsii.member(jsii_name="idpSsoUrlInput")
    def idp_sso_url_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idpSsoUrlInput"))

    @builtins.property
    @jsii.member(jsii_name="namespaceInput")
    def namespace_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "namespaceInput"))

    @builtins.property
    @jsii.member(jsii_name="pathInput")
    def path_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "pathInput"))

    @builtins.property
    @jsii.member(jsii_name="tuneInput")
    def tune_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["SamlAuthBackendTune"]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["SamlAuthBackendTune"]]], jsii.get(self, "tuneInput"))

    @builtins.property
    @jsii.member(jsii_name="verboseLoggingInput")
    def verbose_logging_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "verboseLoggingInput"))

    @builtins.property
    @jsii.member(jsii_name="acsUrls")
    def acs_urls(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "acsUrls"))

    @acs_urls.setter
    def acs_urls(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4d6ae92cc89f4cf7703cbaf406f7fe63b7c0cc86cea46f007703a70291966091)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "acsUrls", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="defaultRole")
    def default_role(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "defaultRole"))

    @default_role.setter
    def default_role(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3be9d88aed88b76cc0eec76ec62a6b61f0e5e48fd865a3ef437cd9f4a4c301e2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "defaultRole", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="disableRemount")
    def disable_remount(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "disableRemount"))

    @disable_remount.setter
    def disable_remount(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9c005fdc407b5790bff4cc815367c881c9ac1bf9517b46bde0a6280261a9632a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "disableRemount", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="entityId")
    def entity_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "entityId"))

    @entity_id.setter
    def entity_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fb21c4de080b03140e169ccc48db7e427d85148d040cd7d4a60869568026211e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "entityId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fef74d8bee9eb00d075e30f2e93a3f3f38304fcf2fb9cd82fca5325568050d54)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="idpCert")
    def idp_cert(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "idpCert"))

    @idp_cert.setter
    def idp_cert(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e42b1dbf80237b4cc2d37084092f0423cef04750c3c0394a5d7f15a9c25996ee)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "idpCert", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="idpEntityId")
    def idp_entity_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "idpEntityId"))

    @idp_entity_id.setter
    def idp_entity_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3014ffa60bd91dd8b30775a10e9a5ca52e58513d88021aa00419eed888885c12)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "idpEntityId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="idpMetadataUrl")
    def idp_metadata_url(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "idpMetadataUrl"))

    @idp_metadata_url.setter
    def idp_metadata_url(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1d8fe969c3064e6eaf48c6779804526a342ca23837b270377486f137dccf7a02)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "idpMetadataUrl", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="idpSsoUrl")
    def idp_sso_url(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "idpSsoUrl"))

    @idp_sso_url.setter
    def idp_sso_url(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__55f58dfa0771b700ff753c53c20d606a422d8009d536ab4234d5ccd19c164f49)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "idpSsoUrl", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="namespace")
    def namespace(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "namespace"))

    @namespace.setter
    def namespace(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fe4916887a9490eaa7c6e19a7e380090efacb6534be3ba46abc4c1ac3d6649eb)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "namespace", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="path")
    def path(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "path"))

    @path.setter
    def path(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1662459972190665c675383d65e79f7aadb5abbe1e535b83c6dea482ede16d5a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "path", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="verboseLogging")
    def verbose_logging(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "verboseLogging"))

    @verbose_logging.setter
    def verbose_logging(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cd47a830dc8c2547aa4418044339a7d32007d2182684232558d7d586aadb5173)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "verboseLogging", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-vault.samlAuthBackend.SamlAuthBackendConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "acs_urls": "acsUrls",
        "entity_id": "entityId",
        "default_role": "defaultRole",
        "disable_remount": "disableRemount",
        "id": "id",
        "idp_cert": "idpCert",
        "idp_entity_id": "idpEntityId",
        "idp_metadata_url": "idpMetadataUrl",
        "idp_sso_url": "idpSsoUrl",
        "namespace": "namespace",
        "path": "path",
        "tune": "tune",
        "verbose_logging": "verboseLogging",
    },
)
class SamlAuthBackendConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        acs_urls: typing.Sequence[builtins.str],
        entity_id: builtins.str,
        default_role: typing.Optional[builtins.str] = None,
        disable_remount: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        id: typing.Optional[builtins.str] = None,
        idp_cert: typing.Optional[builtins.str] = None,
        idp_entity_id: typing.Optional[builtins.str] = None,
        idp_metadata_url: typing.Optional[builtins.str] = None,
        idp_sso_url: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        path: typing.Optional[builtins.str] = None,
        tune: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["SamlAuthBackendTune", typing.Dict[builtins.str, typing.Any]]]]] = None,
        verbose_logging: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param acs_urls: The well-formatted URLs of your Assertion Consumer Service (ACS) that should receive a response from the identity provider. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#acs_urls SamlAuthBackend#acs_urls}
        :param entity_id: The entity ID of the SAML authentication service provider. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#entity_id SamlAuthBackend#entity_id}
        :param default_role: The role to use if no role is provided during login. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#default_role SamlAuthBackend#default_role}
        :param disable_remount: If set, opts out of mount migration on path updates. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#disable_remount SamlAuthBackend#disable_remount}
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#id SamlAuthBackend#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param idp_cert: The PEM encoded certificate of the identity provider. Mutually exclusive with 'idp_metadata_url'. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#idp_cert SamlAuthBackend#idp_cert}
        :param idp_entity_id: The entity ID of the identity provider. Mutually exclusive with 'idp_metadata_url'. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#idp_entity_id SamlAuthBackend#idp_entity_id}
        :param idp_metadata_url: The metadata URL of the identity provider. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#idp_metadata_url SamlAuthBackend#idp_metadata_url}
        :param idp_sso_url: The SSO URL of the identity provider. Mutually exclusive with 'idp_metadata_url'. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#idp_sso_url SamlAuthBackend#idp_sso_url}
        :param namespace: Target namespace. (requires Enterprise). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#namespace SamlAuthBackend#namespace}
        :param path: Unique name of the auth backend to configure. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#path SamlAuthBackend#path}
        :param tune: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#tune SamlAuthBackend#tune}.
        :param verbose_logging: Log additional, potentially sensitive information during the SAML exchange according to the current logging level. Not recommended for production. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#verbose_logging SamlAuthBackend#verbose_logging}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8e77bda44752e84941846f49a54eb57d53244e3f5e5f83a536d4edf9d455fb92)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument acs_urls", value=acs_urls, expected_type=type_hints["acs_urls"])
            check_type(argname="argument entity_id", value=entity_id, expected_type=type_hints["entity_id"])
            check_type(argname="argument default_role", value=default_role, expected_type=type_hints["default_role"])
            check_type(argname="argument disable_remount", value=disable_remount, expected_type=type_hints["disable_remount"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument idp_cert", value=idp_cert, expected_type=type_hints["idp_cert"])
            check_type(argname="argument idp_entity_id", value=idp_entity_id, expected_type=type_hints["idp_entity_id"])
            check_type(argname="argument idp_metadata_url", value=idp_metadata_url, expected_type=type_hints["idp_metadata_url"])
            check_type(argname="argument idp_sso_url", value=idp_sso_url, expected_type=type_hints["idp_sso_url"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
            check_type(argname="argument tune", value=tune, expected_type=type_hints["tune"])
            check_type(argname="argument verbose_logging", value=verbose_logging, expected_type=type_hints["verbose_logging"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "acs_urls": acs_urls,
            "entity_id": entity_id,
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
        if default_role is not None:
            self._values["default_role"] = default_role
        if disable_remount is not None:
            self._values["disable_remount"] = disable_remount
        if id is not None:
            self._values["id"] = id
        if idp_cert is not None:
            self._values["idp_cert"] = idp_cert
        if idp_entity_id is not None:
            self._values["idp_entity_id"] = idp_entity_id
        if idp_metadata_url is not None:
            self._values["idp_metadata_url"] = idp_metadata_url
        if idp_sso_url is not None:
            self._values["idp_sso_url"] = idp_sso_url
        if namespace is not None:
            self._values["namespace"] = namespace
        if path is not None:
            self._values["path"] = path
        if tune is not None:
            self._values["tune"] = tune
        if verbose_logging is not None:
            self._values["verbose_logging"] = verbose_logging

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
    def acs_urls(self) -> typing.List[builtins.str]:
        '''The well-formatted URLs of your Assertion Consumer Service (ACS) that should receive a response from the identity provider.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#acs_urls SamlAuthBackend#acs_urls}
        '''
        result = self._values.get("acs_urls")
        assert result is not None, "Required property 'acs_urls' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def entity_id(self) -> builtins.str:
        '''The entity ID of the SAML authentication service provider.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#entity_id SamlAuthBackend#entity_id}
        '''
        result = self._values.get("entity_id")
        assert result is not None, "Required property 'entity_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def default_role(self) -> typing.Optional[builtins.str]:
        '''The role to use if no role is provided during login.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#default_role SamlAuthBackend#default_role}
        '''
        result = self._values.get("default_role")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def disable_remount(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''If set, opts out of mount migration on path updates.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#disable_remount SamlAuthBackend#disable_remount}
        '''
        result = self._values.get("disable_remount")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#id SamlAuthBackend#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def idp_cert(self) -> typing.Optional[builtins.str]:
        '''The PEM encoded certificate of the identity provider. Mutually exclusive with 'idp_metadata_url'.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#idp_cert SamlAuthBackend#idp_cert}
        '''
        result = self._values.get("idp_cert")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def idp_entity_id(self) -> typing.Optional[builtins.str]:
        '''The entity ID of the identity provider. Mutually exclusive with 'idp_metadata_url'.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#idp_entity_id SamlAuthBackend#idp_entity_id}
        '''
        result = self._values.get("idp_entity_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def idp_metadata_url(self) -> typing.Optional[builtins.str]:
        '''The metadata URL of the identity provider.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#idp_metadata_url SamlAuthBackend#idp_metadata_url}
        '''
        result = self._values.get("idp_metadata_url")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def idp_sso_url(self) -> typing.Optional[builtins.str]:
        '''The SSO URL of the identity provider. Mutually exclusive with 'idp_metadata_url'.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#idp_sso_url SamlAuthBackend#idp_sso_url}
        '''
        result = self._values.get("idp_sso_url")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''Target namespace. (requires Enterprise).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#namespace SamlAuthBackend#namespace}
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def path(self) -> typing.Optional[builtins.str]:
        '''Unique name of the auth backend to configure.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#path SamlAuthBackend#path}
        '''
        result = self._values.get("path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tune(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["SamlAuthBackendTune"]]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#tune SamlAuthBackend#tune}.'''
        result = self._values.get("tune")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["SamlAuthBackendTune"]]], result)

    @builtins.property
    def verbose_logging(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Log additional, potentially sensitive information during the SAML exchange according to the current logging level. Not recommended for production.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#verbose_logging SamlAuthBackend#verbose_logging}
        '''
        result = self._values.get("verbose_logging")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SamlAuthBackendConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-vault.samlAuthBackend.SamlAuthBackendTune",
    jsii_struct_bases=[],
    name_mapping={
        "allowed_response_headers": "allowedResponseHeaders",
        "audit_non_hmac_request_keys": "auditNonHmacRequestKeys",
        "audit_non_hmac_response_keys": "auditNonHmacResponseKeys",
        "default_lease_ttl": "defaultLeaseTtl",
        "listing_visibility": "listingVisibility",
        "max_lease_ttl": "maxLeaseTtl",
        "passthrough_request_headers": "passthroughRequestHeaders",
        "token_type": "tokenType",
    },
)
class SamlAuthBackendTune:
    def __init__(
        self,
        *,
        allowed_response_headers: typing.Optional[typing.Sequence[builtins.str]] = None,
        audit_non_hmac_request_keys: typing.Optional[typing.Sequence[builtins.str]] = None,
        audit_non_hmac_response_keys: typing.Optional[typing.Sequence[builtins.str]] = None,
        default_lease_ttl: typing.Optional[builtins.str] = None,
        listing_visibility: typing.Optional[builtins.str] = None,
        max_lease_ttl: typing.Optional[builtins.str] = None,
        passthrough_request_headers: typing.Optional[typing.Sequence[builtins.str]] = None,
        token_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param allowed_response_headers: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#allowed_response_headers SamlAuthBackend#allowed_response_headers}.
        :param audit_non_hmac_request_keys: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#audit_non_hmac_request_keys SamlAuthBackend#audit_non_hmac_request_keys}.
        :param audit_non_hmac_response_keys: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#audit_non_hmac_response_keys SamlAuthBackend#audit_non_hmac_response_keys}.
        :param default_lease_ttl: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#default_lease_ttl SamlAuthBackend#default_lease_ttl}.
        :param listing_visibility: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#listing_visibility SamlAuthBackend#listing_visibility}.
        :param max_lease_ttl: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#max_lease_ttl SamlAuthBackend#max_lease_ttl}.
        :param passthrough_request_headers: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#passthrough_request_headers SamlAuthBackend#passthrough_request_headers}.
        :param token_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#token_type SamlAuthBackend#token_type}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2a32ddb0a4f6f825e1ddd6a76f83d680f8c40ba1218fb4f364cc360587898442)
            check_type(argname="argument allowed_response_headers", value=allowed_response_headers, expected_type=type_hints["allowed_response_headers"])
            check_type(argname="argument audit_non_hmac_request_keys", value=audit_non_hmac_request_keys, expected_type=type_hints["audit_non_hmac_request_keys"])
            check_type(argname="argument audit_non_hmac_response_keys", value=audit_non_hmac_response_keys, expected_type=type_hints["audit_non_hmac_response_keys"])
            check_type(argname="argument default_lease_ttl", value=default_lease_ttl, expected_type=type_hints["default_lease_ttl"])
            check_type(argname="argument listing_visibility", value=listing_visibility, expected_type=type_hints["listing_visibility"])
            check_type(argname="argument max_lease_ttl", value=max_lease_ttl, expected_type=type_hints["max_lease_ttl"])
            check_type(argname="argument passthrough_request_headers", value=passthrough_request_headers, expected_type=type_hints["passthrough_request_headers"])
            check_type(argname="argument token_type", value=token_type, expected_type=type_hints["token_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if allowed_response_headers is not None:
            self._values["allowed_response_headers"] = allowed_response_headers
        if audit_non_hmac_request_keys is not None:
            self._values["audit_non_hmac_request_keys"] = audit_non_hmac_request_keys
        if audit_non_hmac_response_keys is not None:
            self._values["audit_non_hmac_response_keys"] = audit_non_hmac_response_keys
        if default_lease_ttl is not None:
            self._values["default_lease_ttl"] = default_lease_ttl
        if listing_visibility is not None:
            self._values["listing_visibility"] = listing_visibility
        if max_lease_ttl is not None:
            self._values["max_lease_ttl"] = max_lease_ttl
        if passthrough_request_headers is not None:
            self._values["passthrough_request_headers"] = passthrough_request_headers
        if token_type is not None:
            self._values["token_type"] = token_type

    @builtins.property
    def allowed_response_headers(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#allowed_response_headers SamlAuthBackend#allowed_response_headers}.'''
        result = self._values.get("allowed_response_headers")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def audit_non_hmac_request_keys(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#audit_non_hmac_request_keys SamlAuthBackend#audit_non_hmac_request_keys}.'''
        result = self._values.get("audit_non_hmac_request_keys")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def audit_non_hmac_response_keys(
        self,
    ) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#audit_non_hmac_response_keys SamlAuthBackend#audit_non_hmac_response_keys}.'''
        result = self._values.get("audit_non_hmac_response_keys")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def default_lease_ttl(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#default_lease_ttl SamlAuthBackend#default_lease_ttl}.'''
        result = self._values.get("default_lease_ttl")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def listing_visibility(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#listing_visibility SamlAuthBackend#listing_visibility}.'''
        result = self._values.get("listing_visibility")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def max_lease_ttl(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#max_lease_ttl SamlAuthBackend#max_lease_ttl}.'''
        result = self._values.get("max_lease_ttl")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def passthrough_request_headers(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#passthrough_request_headers SamlAuthBackend#passthrough_request_headers}.'''
        result = self._values.get("passthrough_request_headers")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def token_type(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/vault/5.4.0/docs/resources/saml_auth_backend#token_type SamlAuthBackend#token_type}.'''
        result = self._values.get("token_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SamlAuthBackendTune(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class SamlAuthBackendTuneList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-vault.samlAuthBackend.SamlAuthBackendTuneList",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        wraps_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param wraps_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0b60d1e9371561bc83551d821b9d05e1e331be53587e9ab9f65d91c7649946f6)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(self, index: jsii.Number) -> "SamlAuthBackendTuneOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f3db19087b027d2a639464dcf7dcceda5f5bea9f37793e83fc4660a5af6a9306)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("SamlAuthBackendTuneOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5c685ca6c24f23b7d7931248345761852af1147a88ba644b39c95d7d3d1601c7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformAttribute", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="terraformResource")
    def _terraform_resource(self) -> _cdktf_9a9027ec.IInterpolatingParent:
        '''The parent resource.'''
        return typing.cast(_cdktf_9a9027ec.IInterpolatingParent, jsii.get(self, "terraformResource"))

    @_terraform_resource.setter
    def _terraform_resource(self, value: _cdktf_9a9027ec.IInterpolatingParent) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5d997e0d63991e2e46632993f721ba96938c12b0f1f0f8caa61b96b83f0ff0b0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformResource", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="wrapsSet")
    def _wraps_set(self) -> builtins.bool:
        '''whether the list is wrapping a set (will add tolist() to be able to access an item via an index).'''
        return typing.cast(builtins.bool, jsii.get(self, "wrapsSet"))

    @_wraps_set.setter
    def _wraps_set(self, value: builtins.bool) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7d622dbd5027c0f1243c93c19b43994f99599d26ac684854071a715eae1e8c0c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[SamlAuthBackendTune]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[SamlAuthBackendTune]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[SamlAuthBackendTune]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9cb5462a7e67bac2a27bfb086e0dbc193903499662e677cac75906a6838bc01f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class SamlAuthBackendTuneOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-vault.samlAuthBackend.SamlAuthBackendTuneOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        complex_object_index: jsii.Number,
        complex_object_is_from_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param complex_object_index: the index of this item in the list.
        :param complex_object_is_from_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e91c04ff4a2e478b9256f1999efe8e24f73ef54b8e2de92ab740d96b219da406)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="resetAllowedResponseHeaders")
    def reset_allowed_response_headers(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAllowedResponseHeaders", []))

    @jsii.member(jsii_name="resetAuditNonHmacRequestKeys")
    def reset_audit_non_hmac_request_keys(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAuditNonHmacRequestKeys", []))

    @jsii.member(jsii_name="resetAuditNonHmacResponseKeys")
    def reset_audit_non_hmac_response_keys(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAuditNonHmacResponseKeys", []))

    @jsii.member(jsii_name="resetDefaultLeaseTtl")
    def reset_default_lease_ttl(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDefaultLeaseTtl", []))

    @jsii.member(jsii_name="resetListingVisibility")
    def reset_listing_visibility(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetListingVisibility", []))

    @jsii.member(jsii_name="resetMaxLeaseTtl")
    def reset_max_lease_ttl(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMaxLeaseTtl", []))

    @jsii.member(jsii_name="resetPassthroughRequestHeaders")
    def reset_passthrough_request_headers(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPassthroughRequestHeaders", []))

    @jsii.member(jsii_name="resetTokenType")
    def reset_token_type(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTokenType", []))

    @builtins.property
    @jsii.member(jsii_name="allowedResponseHeadersInput")
    def allowed_response_headers_input(
        self,
    ) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "allowedResponseHeadersInput"))

    @builtins.property
    @jsii.member(jsii_name="auditNonHmacRequestKeysInput")
    def audit_non_hmac_request_keys_input(
        self,
    ) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "auditNonHmacRequestKeysInput"))

    @builtins.property
    @jsii.member(jsii_name="auditNonHmacResponseKeysInput")
    def audit_non_hmac_response_keys_input(
        self,
    ) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "auditNonHmacResponseKeysInput"))

    @builtins.property
    @jsii.member(jsii_name="defaultLeaseTtlInput")
    def default_lease_ttl_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "defaultLeaseTtlInput"))

    @builtins.property
    @jsii.member(jsii_name="listingVisibilityInput")
    def listing_visibility_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "listingVisibilityInput"))

    @builtins.property
    @jsii.member(jsii_name="maxLeaseTtlInput")
    def max_lease_ttl_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "maxLeaseTtlInput"))

    @builtins.property
    @jsii.member(jsii_name="passthroughRequestHeadersInput")
    def passthrough_request_headers_input(
        self,
    ) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "passthroughRequestHeadersInput"))

    @builtins.property
    @jsii.member(jsii_name="tokenTypeInput")
    def token_type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "tokenTypeInput"))

    @builtins.property
    @jsii.member(jsii_name="allowedResponseHeaders")
    def allowed_response_headers(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "allowedResponseHeaders"))

    @allowed_response_headers.setter
    def allowed_response_headers(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d2581e33d28ec32b3ba78b707e2e2ce8833c311e55fbfd5d3463a086d3c2160d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "allowedResponseHeaders", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="auditNonHmacRequestKeys")
    def audit_non_hmac_request_keys(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "auditNonHmacRequestKeys"))

    @audit_non_hmac_request_keys.setter
    def audit_non_hmac_request_keys(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ab2184c6dc18c85008f6aa17dbed5bf29cabb58ab1965b6cc29372a92662620c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "auditNonHmacRequestKeys", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="auditNonHmacResponseKeys")
    def audit_non_hmac_response_keys(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "auditNonHmacResponseKeys"))

    @audit_non_hmac_response_keys.setter
    def audit_non_hmac_response_keys(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__26b159baf7e65245f2a3df4b159b6a6fbae673c0472e6923a6fef783019e714f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "auditNonHmacResponseKeys", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="defaultLeaseTtl")
    def default_lease_ttl(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "defaultLeaseTtl"))

    @default_lease_ttl.setter
    def default_lease_ttl(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__39d726d9ee26b7fdecf69891a8072442e289b5b212f6e06a2f21150f8afe7f5d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "defaultLeaseTtl", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="listingVisibility")
    def listing_visibility(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "listingVisibility"))

    @listing_visibility.setter
    def listing_visibility(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__53b50a7af8ebe0dd3bfa5fe7ca2a215d1d782066cc2e7e7b97eeb6aca4ea1517)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "listingVisibility", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="maxLeaseTtl")
    def max_lease_ttl(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "maxLeaseTtl"))

    @max_lease_ttl.setter
    def max_lease_ttl(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0f31710f0258291dbc2a9e28a10543fda7e00b84c3937cd31a421823a2c7087f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "maxLeaseTtl", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="passthroughRequestHeaders")
    def passthrough_request_headers(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "passthroughRequestHeaders"))

    @passthrough_request_headers.setter
    def passthrough_request_headers(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9cd06a4de5e8999705470a558962578d78ae5c83d3c2b193611d75910bd4d700)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "passthroughRequestHeaders", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="tokenType")
    def token_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "tokenType"))

    @token_type.setter
    def token_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__739041c7c8127fcad29dd1e8918317e6f204f0fc0f858f39ea9b47ae99c89776)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "tokenType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, SamlAuthBackendTune]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, SamlAuthBackendTune]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, SamlAuthBackendTune]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__83cb244c13d0d4c7386526ba299fdcdc1ec810424faf596b57a03aa61ff8694c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "SamlAuthBackend",
    "SamlAuthBackendConfig",
    "SamlAuthBackendTune",
    "SamlAuthBackendTuneList",
    "SamlAuthBackendTuneOutputReference",
]

publication.publish()

def _typecheckingstub__98f5f695d041c96a8252823e5139618ae5634a72faca05ced31c640e7c89137a(
    scope: _constructs_77d1e7e8.Construct,
    id_: builtins.str,
    *,
    acs_urls: typing.Sequence[builtins.str],
    entity_id: builtins.str,
    default_role: typing.Optional[builtins.str] = None,
    disable_remount: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    id: typing.Optional[builtins.str] = None,
    idp_cert: typing.Optional[builtins.str] = None,
    idp_entity_id: typing.Optional[builtins.str] = None,
    idp_metadata_url: typing.Optional[builtins.str] = None,
    idp_sso_url: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
    path: typing.Optional[builtins.str] = None,
    tune: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[SamlAuthBackendTune, typing.Dict[builtins.str, typing.Any]]]]] = None,
    verbose_logging: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
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

def _typecheckingstub__2a3c747d37a43926bde48cff573996c8cd1470f6e23c92fde74ae6d95cdde817(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__95d47451b14589cdec27d4c2af01199809eae692192b49b29e47f6f6c1fef909(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[SamlAuthBackendTune, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4d6ae92cc89f4cf7703cbaf406f7fe63b7c0cc86cea46f007703a70291966091(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3be9d88aed88b76cc0eec76ec62a6b61f0e5e48fd865a3ef437cd9f4a4c301e2(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9c005fdc407b5790bff4cc815367c881c9ac1bf9517b46bde0a6280261a9632a(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fb21c4de080b03140e169ccc48db7e427d85148d040cd7d4a60869568026211e(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fef74d8bee9eb00d075e30f2e93a3f3f38304fcf2fb9cd82fca5325568050d54(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e42b1dbf80237b4cc2d37084092f0423cef04750c3c0394a5d7f15a9c25996ee(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3014ffa60bd91dd8b30775a10e9a5ca52e58513d88021aa00419eed888885c12(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1d8fe969c3064e6eaf48c6779804526a342ca23837b270377486f137dccf7a02(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__55f58dfa0771b700ff753c53c20d606a422d8009d536ab4234d5ccd19c164f49(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fe4916887a9490eaa7c6e19a7e380090efacb6534be3ba46abc4c1ac3d6649eb(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1662459972190665c675383d65e79f7aadb5abbe1e535b83c6dea482ede16d5a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cd47a830dc8c2547aa4418044339a7d32007d2182684232558d7d586aadb5173(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8e77bda44752e84941846f49a54eb57d53244e3f5e5f83a536d4edf9d455fb92(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    acs_urls: typing.Sequence[builtins.str],
    entity_id: builtins.str,
    default_role: typing.Optional[builtins.str] = None,
    disable_remount: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    id: typing.Optional[builtins.str] = None,
    idp_cert: typing.Optional[builtins.str] = None,
    idp_entity_id: typing.Optional[builtins.str] = None,
    idp_metadata_url: typing.Optional[builtins.str] = None,
    idp_sso_url: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
    path: typing.Optional[builtins.str] = None,
    tune: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[SamlAuthBackendTune, typing.Dict[builtins.str, typing.Any]]]]] = None,
    verbose_logging: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2a32ddb0a4f6f825e1ddd6a76f83d680f8c40ba1218fb4f364cc360587898442(
    *,
    allowed_response_headers: typing.Optional[typing.Sequence[builtins.str]] = None,
    audit_non_hmac_request_keys: typing.Optional[typing.Sequence[builtins.str]] = None,
    audit_non_hmac_response_keys: typing.Optional[typing.Sequence[builtins.str]] = None,
    default_lease_ttl: typing.Optional[builtins.str] = None,
    listing_visibility: typing.Optional[builtins.str] = None,
    max_lease_ttl: typing.Optional[builtins.str] = None,
    passthrough_request_headers: typing.Optional[typing.Sequence[builtins.str]] = None,
    token_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0b60d1e9371561bc83551d821b9d05e1e331be53587e9ab9f65d91c7649946f6(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f3db19087b027d2a639464dcf7dcceda5f5bea9f37793e83fc4660a5af6a9306(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5c685ca6c24f23b7d7931248345761852af1147a88ba644b39c95d7d3d1601c7(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5d997e0d63991e2e46632993f721ba96938c12b0f1f0f8caa61b96b83f0ff0b0(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7d622dbd5027c0f1243c93c19b43994f99599d26ac684854071a715eae1e8c0c(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9cb5462a7e67bac2a27bfb086e0dbc193903499662e677cac75906a6838bc01f(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[SamlAuthBackendTune]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e91c04ff4a2e478b9256f1999efe8e24f73ef54b8e2de92ab740d96b219da406(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d2581e33d28ec32b3ba78b707e2e2ce8833c311e55fbfd5d3463a086d3c2160d(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ab2184c6dc18c85008f6aa17dbed5bf29cabb58ab1965b6cc29372a92662620c(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__26b159baf7e65245f2a3df4b159b6a6fbae673c0472e6923a6fef783019e714f(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__39d726d9ee26b7fdecf69891a8072442e289b5b212f6e06a2f21150f8afe7f5d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__53b50a7af8ebe0dd3bfa5fe7ca2a215d1d782066cc2e7e7b97eeb6aca4ea1517(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0f31710f0258291dbc2a9e28a10543fda7e00b84c3937cd31a421823a2c7087f(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9cd06a4de5e8999705470a558962578d78ae5c83d3c2b193611d75910bd4d700(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__739041c7c8127fcad29dd1e8918317e6f204f0fc0f858f39ea9b47ae99c89776(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__83cb244c13d0d4c7386526ba299fdcdc1ec810424faf596b57a03aa61ff8694c(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, SamlAuthBackendTune]],
) -> None:
    """Type checking stubs"""
    pass
