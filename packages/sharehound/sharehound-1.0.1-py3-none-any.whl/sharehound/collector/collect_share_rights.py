#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : collect_share_rights.py
# Author             : Remi Gascou (@podalirius_)
# Date created       : 12 Aug 2025

from enum import IntFlag
from typing import Union

from impacket.ldap import ldaptypes
from shareql.evaluate.evaluator import RulesEvaluator

import sharehound.kinds as kinds
from sharehound.core.Logger import Logger, TaskLogger
from sharehound.core.SMBSession import SMBSession


class AccessMaskFlags(IntFlag):
    """
    AccessMaskFlags: Enum class that defines constants for access mask flags.

    This class defines constants for various access mask flags as specified in the Microsoft documentation. These flags represent permissions or rights that can be granted or denied for security principals in access control entries (ACEs) of an access control list (ACL).

    The flags include permissions for creating or deleting child objects, listing contents, reading or writing properties, deleting a tree of objects, and controlling access. Additionally, it includes generic rights like GENERIC_ALL, GENERIC_EXECUTE, GENERIC_WRITE, and GENERIC_READ.

    The values for these flags are derived from the following Microsoft documentation sources:
    - https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-dtyp/7a53f60e-e730-4dfe-bbe9-b21b62eb790b
    - https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-adts/990fb975-ab31-4bc1-8b75-5da132cd4584
    - https://learn.microsoft.com/en-us/windows/win32/api/iads/ne-iads-ads_rights_enum

    Attributes:
        DS_CREATE_CHILD (int): Permission to create child objects.
        DS_DELETE_CHILD (int): Permission to delete child objects.
        DS_LIST_CONTENTS (int): Permission to list contents.
        DS_WRITE_PROPERTY_EXTENDED (int): Permission to write properties (extended).
        DS_READ_PROPERTY (int): Permission to read properties.
        DS_WRITE_PROPERTY (int): Permission to write properties.
        DS_DELETE_TREE (int): Permission to delete a tree of objects.
        DS_LIST_OBJECT (int): Permission to list objects.
        DS_CONTROL_ACCESS (int): Permission for access control.
        DELETE (int): Permission to delete.
        READ_CONTROL (int): Permission to read security descriptor.
        WRITE_DAC (int): Permission to modify discretionary access control list (DACL).
        WRITE_OWNER (int): Permission to change the owner.
        GENERIC_ALL (int): Generic all permissions.
        GENERIC_EXECUTE (int): Generic execute permissions.
        GENERIC_WRITE (int): Generic write permissions.
        GENERIC_READ (int): Generic read permissions.
    """

    DS_CREATE_CHILD = 0x00000001
    DS_DELETE_CHILD = 0x00000002
    DS_LIST_CONTENTS = 0x00000004
    DS_WRITE_PROPERTY_EXTENDED = 0x00000008
    DS_READ_PROPERTY = 0x00000010
    DS_WRITE_PROPERTY = 0x00000020
    DS_DELETE_TREE = 0x00000040
    DS_LIST_OBJECT = 0x00000080
    DS_CONTROL_ACCESS = 0x00000100
    DELETE = 0x00010000
    READ_CONTROL = 0x00020000
    WRITE_DAC = 0x00040000
    WRITE_OWNER = 0x00080000
    # Generic rights
    GENERIC_ALL = 0x10000000
    GENERIC_EXECUTE = 0x20000000
    GENERIC_WRITE = 0x40000000
    GENERIC_READ = 0x80000000


def collect_share_rights(
    smb_session: SMBSession,
    share_name: str,
    rules_evaluator: RulesEvaluator,
    logger: Union[Logger, TaskLogger],
):
    """
    Process share rights for a share and create corresponding edges.

    This function retrieves the security descriptor for a file or directory,
    processes the DACL to extract access rights, and creates edges between
    principals (SIDs) and the share with the appropriate share rights.

    Args:
        smb_session: The SMB session object for connecting to the share
        ogc: The opengraph context object
        share_name: The name of the share
        rules_evaluator: The rules evaluator object
        node: The share node to process rights for
        path: The path of the share
        logger: Logger object for logging operations
    """

    try:
        sd = smb_session.get_share_security_descriptor(share_name)
        share_rights = {}

        if sd is not None and len(sd) > 0:
            # Parse the security descriptor
            security_descriptor = ldaptypes.SR_SECURITY_DESCRIPTOR()
            security_descriptor.fromString(sd)

            # Process each ACE in the DACL
            if (
                security_descriptor["Dacl"] is not None
                and len(security_descriptor["Dacl"]["Data"]) > 0
            ):
                for ace in security_descriptor["Dacl"]["Data"]:
                    if len(ace["Ace"]["Sid"]) == 0:
                        continue

                    aceType = ace["AceType"]
                    # aceFlags = ace["AceFlags"]
                    aceMask = ace["Ace"]["Mask"]
                    maskValue = aceMask.fields["Mask"]
                    aceSid = ace["Ace"]["Sid"]

                    ACCESS_ALLOWED_ACE_TYPE = 0x00
                    if aceType != ACCESS_ALLOWED_ACE_TYPE:
                        continue

                    sid = aceSid.formatCanonical()

                    # Check for specific rights and create edges
                    access_flags = [
                        flag for flag in AccessMaskFlags if flag.value & maskValue
                    ]

                    map_rights = {
                        kinds.edge_kind_can_ds_create_child: AccessMaskFlags.DS_CREATE_CHILD,
                        kinds.edge_kind_can_ds_delete_child: AccessMaskFlags.DS_DELETE_CHILD,
                        kinds.edge_kind_can_ds_list_contents: AccessMaskFlags.DS_LIST_CONTENTS,
                        kinds.edge_kind_can_ds_write_extended_properties: AccessMaskFlags.DS_WRITE_PROPERTY_EXTENDED,
                        kinds.edge_kind_can_ds_read_property: AccessMaskFlags.DS_READ_PROPERTY,
                        kinds.edge_kind_can_ds_write_property: AccessMaskFlags.DS_WRITE_PROPERTY,
                        kinds.edge_kind_can_ds_delete_tree: AccessMaskFlags.DS_DELETE_TREE,
                        kinds.edge_kind_can_ds_list_object: AccessMaskFlags.DS_LIST_OBJECT,
                        kinds.edge_kind_can_ds_control_access: AccessMaskFlags.DS_CONTROL_ACCESS,
                        kinds.edge_kind_can_delete: AccessMaskFlags.DELETE,
                        kinds.edge_kind_can_read_control: AccessMaskFlags.READ_CONTROL,
                        kinds.edge_kind_can_write_dac: AccessMaskFlags.WRITE_DAC,
                        kinds.edge_kind_can_write_owner: AccessMaskFlags.WRITE_OWNER,
                        kinds.edge_kind_can_generic_all: AccessMaskFlags.GENERIC_ALL,
                        kinds.edge_kind_can_generic_execute: AccessMaskFlags.GENERIC_EXECUTE,
                        kinds.edge_kind_can_generic_write: AccessMaskFlags.GENERIC_WRITE,
                        kinds.edge_kind_can_generic_read: AccessMaskFlags.GENERIC_READ,
                    }

                    for edgeName, edgeValue in map_rights.items():
                        if edgeValue in access_flags:
                            if sid not in share_rights:
                                share_rights[sid] = []
                            share_rights[sid].append(edgeName)

    except Exception as err:
        logger.debug(f"Error processing share rights for {share_name}: {err}")
        raise err

    return share_rights
