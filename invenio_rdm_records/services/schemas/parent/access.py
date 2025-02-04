# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Access schema for RDM parent record."""

# TODO: Replace with invenio_records_resources.services.base.schema import *


from datetime import timezone

from marshmallow import Schema, fields, pre_load, validate
from marshmallow_utils.fields import (
    ISODateString,
    SanitizedHTML,
    SanitizedUnicode,
    TZDateTime,
)
from marshmallow_utils.permissions import FieldPermissionsMixin


class GrantSubject(Schema):
    """Schema for a grant subject."""

    id = fields.String(required=True)
    type = fields.String(
        required=True, validate=validate.OneOf(["user", "role", "system_role"])
    )


class Grant(Schema):
    """Schema for an access grant."""

    permission = fields.String(required=True)
    subject = fields.Nested(GrantSubject, required=True)
    origin = fields.String(required=False)


class SecretLink(Schema):
    """Schema for a secret link."""

    id = fields.String(dump_only=True)
    created_at = TZDateTime(
        timezone=timezone.utc, format="iso", required=False, dump_only=True
    )
    expires_at = ISODateString(required=False)
    permission = fields.String(
        required=False, validate=validate.OneOf(["view", "preview", "edit"])
    )
    description = SanitizedUnicode(required=False)
    origin = fields.String(required=False)
    token = SanitizedUnicode(dump_only=True)


class Agent(Schema):
    """An agent schema."""

    user = fields.Integer(required=True)


class AccessSettingsSchema(Schema):
    """Schema for a record's access settings."""

    # enabling/disabling guests or users to send access requests
    allow_user_requests = fields.Boolean()
    allow_guest_requests = fields.Boolean()

    accept_conditions_text = SanitizedHTML(allow_none=True)
    secret_link_expiration = fields.Integer(
        validate=validate.Range(max=365), allow_none=True
    )

    @pre_load
    def translate_expiration_date(self, data, **kwargs):
        """Translate secret_link_expiration from ui dropdown value."""
        expiration_days = data["secret_link_expiration"]
        if expiration_days == 0:
            data["secret_link_expiration"] = None
        else:
            data["secret_link_expiration"] = expiration_days

        return data


class ParentAccessSchema(Schema, FieldPermissionsMixin):
    """Access schema."""

    field_dump_permissions = {
        # omit fields from dumps except for users with 'manage' permissions
        # allow only 'settings'
        "grants": "manage",
        "owned_by": "manage",
        "links": "manage",
    }

    grants = fields.List(fields.Nested(Grant))
    owned_by = fields.Nested(Agent)
    links = fields.List(fields.Nested(SecretLink))
    settings = fields.Nested(AccessSettingsSchema)
