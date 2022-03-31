# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 Esteban J. G. Gabancho
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test IIIF prezy serialization."""


from io import BytesIO

import flask_security
import pytest
from invenio_accounts.testutils import login_user_via_session


def create_record_with_images(client, record, headers):
    """Create record with a file."""
    record["files"]["enabled"] = True
    response = client.post("/records", json=record, headers=headers)
    assert response.status_code == 201
    recid = response.json['id']

    # Attach a file to it
    response = client.post(
        f'/records/{recid}/draft/files',
        headers=headers,
        json=[{'key': 'test.png'}],
    )
    assert response.status_code == 201
    response = client.put(
        f"/records/{recid}/draft/files/test.png/content",
        headers={
            'content-type': 'application/octet-stream',
            'accept': 'application/json',
        },
        data=BytesIO(b'testfile'),
    )
    assert response.status_code == 200
    response = client.post(
        f"/records/{recid}/draft/files/test.png/commit", headers=headers
    )
    assert response.status_code == 200

    # Publish it
    response = client.post(
        f"/records/{recid}/draft/actions/publish", headers=headers
    )
    assert response.status_code == 202

    return recid


def test_iiif_prezi_basic_generation(
    running_app, client_with_login, headers, minimal_record, es_clear
):
    """Test basic IIIF manifest generation."""
    client = client_with_login
    recid = create_record_with_images(client, minimal_record, headers)

    response = client.get(f'/records/{recid}/iiif/manifest')
    assert response.status_code == 200
    assert response.mimetype == 'application/ld+json'

    manifest = response.json
    assert manifest == {} # TODO
